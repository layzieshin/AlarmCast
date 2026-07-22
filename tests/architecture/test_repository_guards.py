"""Fixture tests for repository file and content safety guards."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from tests.architecture.guards import (
    check_repository_safety,
    format_violations,
    git_repository_files,
)


def _write(repo_root: Path, relative: str, content: str = "placeholder\n") -> Path:
    path = repo_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    "relative",
    ["host.json", "config/client.json", "mode.txt", ".env", ".env.local"],
)
def test_local_configuration_files_fail(tmp_path: Path, relative: str) -> None:
    forbidden = _write(tmp_path, relative)

    violations = check_repository_safety(tmp_path, [forbidden])

    message = format_violations(violations)
    assert "forbidden-file" in message
    assert forbidden.relative_to(tmp_path).as_posix() in message


@pytest.mark.parametrize(
    "relative",
    [
        "server.pem",
        "server.key",
        "identity.p12",
        "identity.pfx",
        "id_rsa",
        "id_ed25519",
        "credentials.json",
        "secrets.json",
    ],
)
def test_credential_and_private_key_files_fail(tmp_path: Path, relative: str) -> None:
    forbidden = _write(tmp_path, relative)

    violations = check_repository_safety(tmp_path, [forbidden])

    assert "credential or private-key file" in format_violations(violations)


def test_documented_env_example_and_harmless_addresses_pass(tmp_path: Path) -> None:
    example = _write(tmp_path, ".env.example", "ALARMCAST_SERVER=192.0.2.10\n")
    addresses = _write(
        tmp_path,
        "docs/addresses.txt",
        "127.0.0.1\n0.0.0.0\n224.0.0.251\n192.0.2.5\n198.51.100.8\n203.0.113.9\n",
    )

    assert check_repository_safety(tmp_path, [example, addresses]) == []


def test_private_key_header_fails_with_line_number(tmp_path: Path) -> None:
    private_key_header = "-----BEGIN " + "PRIVATE KEY-----"
    forbidden = _write(tmp_path, "notes.txt", f"first line\n{private_key_header}\n")

    violations = check_repository_safety(tmp_path, [forbidden])

    message = format_violations(violations)
    assert "notes.txt:2" in message
    assert "private-key-header" in message


@pytest.mark.parametrize("prefix", ["ghp_", "gho_", "ghu_", "ghs_", "ghr_"])
def test_classic_github_token_prefixes_fail(tmp_path: Path, prefix: str) -> None:
    token = prefix[:2] + prefix[2:] + ("A" * 36)
    forbidden = _write(tmp_path, "token.txt", token)

    violations = check_repository_safety(tmp_path, [forbidden])

    assert "github-token" in format_violations(violations)


def test_fine_grained_github_token_fails(tmp_path: Path) -> None:
    token = "github" + "_pat_" + ("A" * 30)
    forbidden = _write(tmp_path, "token.txt", token)

    violations = check_repository_safety(tmp_path, [forbidden])

    assert "github-token" in format_violations(violations)


@pytest.mark.parametrize(
    ("first", "remainder"), [("10", "23.45.67"), ("172", "20.4.5"), ("192", "168.7.8")]
)
def test_rfc1918_product_addresses_fail(tmp_path: Path, first: str, remainder: str) -> None:
    address = first + "." + remainder
    forbidden = _write(tmp_path, "config/defaults.txt", first + "." + remainder)

    violations = check_repository_safety(tmp_path, [forbidden])

    message = format_violations(violations)
    assert "rfc1918-address" in message
    assert address in message


def test_documentation_addresses_in_test_file_pass(tmp_path: Path) -> None:
    fixture = _write(
        tmp_path,
        "tests/test_network.py",
        'HOSTS = ("192.0.2.5", "198.51.100.8", "203.0.113.9")\n',
    )

    assert check_repository_safety(tmp_path, [fixture]) == []


def test_rfc1918_address_in_test_file_fails(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    fixture_address = "10" + ".0.0.5"
    _write(tmp_path, "tests/test_network.py", f'HOST = "{fixture_address}"\n')
    subprocess.run(["git", "add", "tests/test_network.py"], cwd=tmp_path, check=True)

    violations = check_repository_safety(tmp_path)

    message = format_violations(violations)
    assert "tests/test_network.py:1" in message
    assert "rfc1918-address" in message
    assert fixture_address in message


def test_git_file_listing_includes_tracked_and_nonignored_untracked(tmp_path: Path) -> None:
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    tracked = _write(tmp_path, "tracked.txt")
    subprocess.run(["git", "add", "tracked.txt"], cwd=tmp_path, check=True)
    untracked = _write(tmp_path, "untracked.txt")
    ignored = _write(tmp_path, "ignored.txt")
    gitignore = _write(tmp_path, ".gitignore", "ignored.txt\n")

    listed = {path.relative_to(tmp_path).as_posix() for path in git_repository_files(tmp_path)}

    assert tracked.relative_to(tmp_path).as_posix() in listed
    assert untracked.relative_to(tmp_path).as_posix() in listed
    assert gitignore.relative_to(tmp_path).as_posix() in listed
    assert ignored.relative_to(tmp_path).as_posix() not in listed
