"""Fixture tests for the single Python entry-point allowlist."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.architecture.guards import check_entry_points, format_violations


def _write(repo_root: Path, relative: str, content: str) -> Path:
    path = repo_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _write_approved_entry_point(repo_root: Path) -> None:
    _write(
        repo_root,
        "src/alarmcast/__main__.py",
        'def main() -> int:\n    return 0\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n',
    )
    _write(repo_root, "pyproject.toml", '[project]\nname = "alarmcast"\nversion = "0"\n')


def test_only_approved_entry_point_passes(tmp_path: Path) -> None:
    _write_approved_entry_point(tmp_path)

    assert check_entry_points(tmp_path) == []


def test_additional_dunder_main_file_fails(tmp_path: Path) -> None:
    _write_approved_entry_point(tmp_path)
    forbidden = _write(tmp_path, "src/alarmcast/host/__main__.py", "print('host')\n")

    violations = check_entry_points(tmp_path)

    message = format_violations(violations)
    assert forbidden.relative_to(tmp_path).as_posix() in message
    assert "additional-__main__" in message


def test_additional_main_block_fails(tmp_path: Path) -> None:
    _write_approved_entry_point(tmp_path)
    forbidden = _write(
        tmp_path,
        "src/alarmcast/tool.py",
        'if "__main__" == __name__:\n    print("tool")\n',
    )

    violations = check_entry_points(tmp_path)

    message = format_violations(violations)
    assert f"{forbidden.relative_to(tmp_path).as_posix()}:1" in message
    assert "additional-main-block" in message


@pytest.mark.parametrize("table_name", ["scripts", "gui-scripts"])
def test_project_script_tables_fail(tmp_path: Path, table_name: str) -> None:
    _write_approved_entry_point(tmp_path)
    _write(
        tmp_path,
        "pyproject.toml",
        f'[project]\nname = "alarmcast"\nversion = "0"\n\n'
        f'[project.{table_name}]\nalarmcast-extra = "alarmcast.tool:main"\n',
    )

    violations = check_entry_points(tmp_path)

    message = format_violations(violations)
    assert f"project-{table_name}" in message
    assert "pyproject.toml:6" in message
    assert "alarmcast-extra" in message
