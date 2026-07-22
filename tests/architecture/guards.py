"""Test-only architecture and repository scope guards for Alarmcast."""

from __future__ import annotations

import ast
import ipaddress
import re
import subprocess
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from importlib.util import resolve_name
from pathlib import Path, PurePosixPath

ALLOWED_ENTRY_POINT = PurePosixPath("src/alarmcast/__main__.py")

_FORBIDDEN_IMPORTS = {
    "core": frozenset({"client", "host"}),
    "host": frozenset({"client"}),
    "client": frozenset({"host"}),
}
_LOCAL_CONFIG_NAMES = frozenset({"host.json", "client.json", "mode.txt"})
_CREDENTIAL_NAMES = frozenset({"id_rsa", "id_ed25519", "credentials.json", "secrets.json"})
_CREDENTIAL_SUFFIXES = frozenset({".pem", ".key", ".p12", ".pfx"})
_PRIVATE_KEY_PATTERN = re.compile(r"-----BEGIN (?:[A-Z0-9]+(?: [A-Z0-9]+)* )?PRIVATE KEY-----")
_GITHUB_TOKEN_PATTERN = re.compile(r"(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")
_IPV4_PATTERN = re.compile(r"(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])")
_PRIVATE_NETWORKS = (
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
)
_PRIVATE_RANGE_DEFINITIONS = {
    "10.0.0.0": "/8",
    "172.16.0.0": "/12",
    "192.168.0.0": "/16",
}


@dataclass(frozen=True, slots=True)
class GuardViolation:
    """One actionable guard finding."""

    rule: str
    path: str
    line: int | None
    kind: str
    detail: str

    def __str__(self) -> str:
        location = self.path if self.line is None else f"{self.path}:{self.line}"
        return f"{location} [{self.rule}/{self.kind}] {self.detail}"


def format_violations(violations: Iterable[GuardViolation]) -> str:
    """Format violations for pytest and CI output."""
    return "\n".join(f"- {violation}" for violation in violations)


def check_import_boundaries(source_root: Path) -> list[GuardViolation]:
    """Return forbidden imports originating in core, host, or client."""
    violations: list[GuardViolation] = []
    for path in sorted(source_root.rglob("*.py")):
        relative = path.relative_to(source_root)
        if len(relative.parts) < 3 or relative.parts[0] != "alarmcast":
            continue
        source_area = relative.parts[1]
        forbidden_areas = _FORBIDDEN_IMPORTS.get(source_area)
        if forbidden_areas is None:
            continue

        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            line = exc.lineno if isinstance(exc, SyntaxError) else None
            violations.append(
                GuardViolation(
                    rule="import-boundary",
                    path=relative.as_posix(),
                    line=line,
                    kind="unreadable-python",
                    detail=str(exc),
                )
            )
            continue

        package = _module_package(relative)
        for target, line, kind in _collect_import_targets(tree, package):
            target_area = _alarmcast_area(target)
            if target_area not in forbidden_areas:
                continue
            violations.append(
                GuardViolation(
                    rule="import-boundary",
                    path=relative.as_posix(),
                    line=line,
                    kind=kind,
                    detail=f"alarmcast.{source_area} must not import {target}",
                )
            )
    return violations


def _module_package(relative: Path) -> str:
    parts = list(relative.with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    else:
        parts.pop()
    return ".".join(parts)


def _collect_import_targets(tree: ast.AST, package: str) -> list[tuple[str, int, str]]:
    targets: list[tuple[str, int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets.extend((alias.name, node.lineno, "absolute-import") for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            base = _resolve_import_from(node, package)
            if base:
                kind = "relative-import" if node.level else "absolute-import"
                targets.append((base, node.lineno, kind))
                targets.extend(
                    (f"{base}.{alias.name}", node.lineno, kind)
                    for alias in node.names
                    if alias.name != "*"
                )
        elif isinstance(node, ast.Call):
            dynamic_target = _dynamic_import_target(node, package)
            if dynamic_target is not None:
                targets.append((dynamic_target, node.lineno, "dynamic-import"))
    return targets


def _resolve_import_from(node: ast.ImportFrom, package: str) -> str | None:
    if node.level == 0:
        return node.module
    relative_name = "." * node.level + (node.module or "")
    try:
        return resolve_name(relative_name, package)
    except ImportError:
        return None


def _dynamic_import_target(node: ast.Call, package: str) -> str | None:
    if not node.args or not isinstance(node.args[0], ast.Constant):
        return None
    imported_name = node.args[0].value
    if not isinstance(imported_name, str):
        return None

    is_import_module = (
        isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "importlib"
        and node.func.attr == "import_module"
    ) or (isinstance(node.func, ast.Name) and node.func.id == "import_module")
    is_dunder_import = isinstance(node.func, ast.Name) and node.func.id == "__import__"
    if not is_import_module and not is_dunder_import:
        return None

    if is_dunder_import:
        level = _constant_int_keyword(node, "level") or 0
        if level:
            imported_name = "." * level + imported_name

    if not imported_name.startswith("."):
        return imported_name

    resolution_package = package
    if is_import_module:
        package_argument = _import_module_package_argument(node)
        if package_argument is not None:
            resolution_package = package_argument
    try:
        return resolve_name(imported_name, resolution_package)
    except ImportError:
        return None


def _constant_int_keyword(node: ast.Call, name: str) -> int | None:
    for keyword in node.keywords:
        if keyword.arg == name and isinstance(keyword.value, ast.Constant):
            value = keyword.value.value
            return value if isinstance(value, int) else None
    return None


def _import_module_package_argument(node: ast.Call) -> str | None:
    argument: ast.expr | None = node.args[1] if len(node.args) > 1 else None
    for keyword in node.keywords:
        if keyword.arg == "package":
            argument = keyword.value
    if isinstance(argument, ast.Constant) and isinstance(argument.value, str):
        return argument.value
    return None


def _alarmcast_area(module: str) -> str | None:
    parts = module.split(".")
    if len(parts) >= 2 and parts[0] == "alarmcast" and parts[1] in _FORBIDDEN_IMPORTS:
        return parts[1]
    return None


def check_entry_points(repo_root: Path) -> list[GuardViolation]:
    """Return Python entry points outside the single approved allowlist item."""
    violations: list[GuardViolation] = []
    source_root = repo_root / "src"
    allowed_path = repo_root / Path(*ALLOWED_ENTRY_POINT.parts)
    if not allowed_path.is_file():
        violations.append(
            GuardViolation(
                rule="entry-point",
                path=ALLOWED_ENTRY_POINT.as_posix(),
                line=None,
                kind="missing-allowlisted-entry-point",
                detail="the approved Alarmcast entry point is missing",
            )
        )

    for path in sorted(source_root.rglob("*.py")):
        relative = PurePosixPath(path.relative_to(repo_root).as_posix())
        if path.name == "__main__.py" and relative != ALLOWED_ENTRY_POINT:
            violations.append(
                GuardViolation(
                    rule="entry-point",
                    path=relative.as_posix(),
                    line=1,
                    kind="additional-__main__",
                    detail=f"only {ALLOWED_ENTRY_POINT} is allowlisted",
                )
            )
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError) as exc:
            line = exc.lineno if isinstance(exc, SyntaxError) else None
            violations.append(
                GuardViolation(
                    rule="entry-point",
                    path=relative.as_posix(),
                    line=line,
                    kind="unreadable-python",
                    detail=str(exc),
                )
            )
            continue
        if relative == ALLOWED_ENTRY_POINT:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.If) and _is_main_guard(node.test):
                violations.append(
                    GuardViolation(
                        rule="entry-point",
                        path=relative.as_posix(),
                        line=node.lineno,
                        kind="additional-main-block",
                        detail=f"only {ALLOWED_ENTRY_POINT} may contain a __main__ block",
                    )
                )

    pyproject_path = repo_root / "pyproject.toml"
    if pyproject_path.is_file():
        try:
            pyproject_text = pyproject_path.read_text(encoding="utf-8")
            pyproject = tomllib.loads(pyproject_text)
        except (OSError, tomllib.TOMLDecodeError) as exc:
            violations.append(
                GuardViolation(
                    rule="entry-point",
                    path="pyproject.toml",
                    line=None,
                    kind="unreadable-pyproject",
                    detail=str(exc),
                )
            )
        else:
            project = pyproject.get("project", {})
            if isinstance(project, dict):
                for table_name in ("scripts", "gui-scripts"):
                    entries = project.get(table_name, {})
                    if not isinstance(entries, dict):
                        continue
                    for script_name, target in entries.items():
                        violations.append(
                            GuardViolation(
                                rule="entry-point",
                                path="pyproject.toml",
                                line=_toml_entry_line(
                                    pyproject_text, f"project.{table_name}", script_name
                                ),
                                kind=f"project-{table_name}",
                                detail=f"script {script_name!r} -> {target!r} is not allowlisted",
                            )
                        )
    return violations


def _is_main_guard(test: ast.expr) -> bool:
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or len(test.comparators) != 1:
        return False
    if not isinstance(test.ops[0], ast.Eq):
        return False
    left, right = test.left, test.comparators[0]
    return (_is_name_identifier(left) and _is_main_literal(right)) or (
        _is_main_literal(left) and _is_name_identifier(right)
    )


def _is_name_identifier(node: ast.expr) -> bool:
    return isinstance(node, ast.Name) and node.id == "__name__"


def _is_main_literal(node: ast.expr) -> bool:
    return isinstance(node, ast.Constant) and node.value == "__main__"


def _toml_entry_line(text: str, table_name: str, entry_name: str) -> int | None:
    in_table = False
    header = f"[{table_name}]"
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("["):
            in_table = stripped == header
        if in_table and stripped.partition("=")[0].strip().strip("\"'") == entry_name:
            return line_number
    return None


def git_repository_files(repo_root: Path) -> tuple[Path, ...]:
    """List tracked and non-ignored untracked files through Git."""
    completed = subprocess.run(
        ["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
        cwd=repo_root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    relative_paths = (Path(item.decode("utf-8")) for item in completed.stdout.split(b"\0") if item)
    return tuple(repo_root / relative for relative in relative_paths)


def check_repository_safety(
    repo_root: Path, files: Iterable[Path] | None = None
) -> list[GuardViolation]:
    """Return forbidden local files, secrets, tokens, and private product addresses."""
    violations: list[GuardViolation] = []
    repository_files = git_repository_files(repo_root) if files is None else tuple(files)
    for path in sorted(repository_files):
        relative = path.relative_to(repo_root).as_posix()
        forbidden_reason = _forbidden_file_reason(PurePosixPath(relative))
        if forbidden_reason is not None:
            violations.append(
                GuardViolation(
                    rule="repository-safety",
                    path=relative,
                    line=None,
                    kind="forbidden-file",
                    detail=forbidden_reason,
                )
            )

        try:
            data = path.read_bytes()
        except OSError as exc:
            violations.append(
                GuardViolation(
                    rule="repository-safety",
                    path=relative,
                    line=None,
                    kind="unreadable-file",
                    detail=str(exc),
                )
            )
            continue
        if b"\0" in data:
            continue
        text = data.decode("utf-8", errors="replace")
        violations.extend(_content_violations(relative, text))
    return violations


def _forbidden_file_reason(path: PurePosixPath) -> str | None:
    name = path.name.lower()
    if name in _LOCAL_CONFIG_NAMES:
        return f"local Alarmcast configuration {path.name!r} must not be committed"
    if name == ".env.example":
        return None
    if name == ".env" or name.startswith(".env."):
        return f"local environment file {path.name!r} must not be committed"
    if name in _CREDENTIAL_NAMES or path.suffix.lower() in _CREDENTIAL_SUFFIXES:
        return f"credential or private-key file {path.name!r} must not be committed"
    return None


def _content_violations(relative: str, text: str) -> list[GuardViolation]:
    violations: list[GuardViolation] = []
    for match in _PRIVATE_KEY_PATTERN.finditer(text):
        violations.append(
            GuardViolation(
                rule="repository-safety",
                path=relative,
                line=_line_number(text, match.start()),
                kind="private-key-header",
                detail="private-key material is forbidden",
            )
        )
    for match in _GITHUB_TOKEN_PATTERN.finditer(text):
        violations.append(
            GuardViolation(
                rule="repository-safety",
                path=relative,
                line=_line_number(text, match.start()),
                kind="github-token",
                detail=f"GitHub token with prefix {match.group(0).split('_', 1)[0]!r} is forbidden",
            )
        )
    if not _is_obvious_test_data_path(relative):
        for match in _IPV4_PATTERN.finditer(text):
            address_text = match.group(0)
            try:
                address = ipaddress.ip_address(address_text)
            except ValueError:
                continue
            if not any(address in network for network in _PRIVATE_NETWORKS):
                continue
            if _is_private_range_definition(text, match.end(), address_text):
                continue
            violations.append(
                GuardViolation(
                    rule="repository-safety",
                    path=relative,
                    line=_line_number(text, match.start()),
                    kind="rfc1918-address",
                    detail=f"private product address {address_text} is forbidden",
                )
            )
    return violations


def _is_obvious_test_data_path(relative: str) -> bool:
    parts = PurePosixPath(relative).parts
    return bool(parts) and parts[0] == "tests"


def _is_private_range_definition(text: str, end: int, address: str) -> bool:
    expected_suffix = _PRIVATE_RANGE_DEFINITIONS.get(address)
    return expected_suffix is not None and text[end : end + len(expected_suffix)] == expected_suffix


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def check_repository(repo_root: Path) -> list[GuardViolation]:
    """Run every B02 guard against a repository checkout."""
    return [
        *check_import_boundaries(repo_root / "src"),
        *check_entry_points(repo_root),
        *check_repository_safety(repo_root),
    ]
