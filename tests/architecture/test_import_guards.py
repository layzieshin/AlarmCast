"""Fixture tests for the legacy module import boundaries."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.architecture.guards import check_import_boundaries, format_violations


def _write_module(source_root: Path, relative: str, source: str) -> Path:
    path = source_root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


@pytest.mark.parametrize(
    ("relative", "source"),
    [
        ("alarmcast/core/allowed.py", "import alarmcast.core.protocol\n"),
        ("alarmcast/host/allowed.py", "from alarmcast.core import protocol\n"),
        ("alarmcast/client/allowed.py", "from alarmcast.core.protocol import HostMessage\n"),
        (
            "alarmcast/host/allowed_relative.py",
            "from . import capture\nfrom ..core import config\n",
        ),
        ("alarmcast/client/allowed_relative.py", "from .output import AudioOutput\n"),
    ],
)
def test_allowed_absolute_and_relative_imports_pass(
    tmp_path: Path, relative: str, source: str
) -> None:
    _write_module(tmp_path, relative, source)

    assert check_import_boundaries(tmp_path) == []


@pytest.mark.parametrize(
    ("relative", "source", "forbidden_target"),
    [
        ("alarmcast/core/bad.py", "import alarmcast.host.server\n", "alarmcast.host.server"),
        (
            "alarmcast/core/bad.py",
            "from alarmcast.client import output\n",
            "alarmcast.client",
        ),
        (
            "alarmcast/host/bad.py",
            "from alarmcast.client.net import ClientNetwork\n",
            "alarmcast.client.net",
        ),
        ("alarmcast/client/bad.py", "import alarmcast.host\n", "alarmcast.host"),
    ],
)
def test_forbidden_absolute_imports_report_file_and_line(
    tmp_path: Path, relative: str, source: str, forbidden_target: str
) -> None:
    path = _write_module(tmp_path, relative, f"from __future__ import annotations\n{source}")

    violations = check_import_boundaries(tmp_path)

    assert violations
    message = format_violations(violations)
    assert path.relative_to(tmp_path).as_posix() in message
    assert ":2" in message
    assert forbidden_target in message
    assert "absolute-import" in message


@pytest.mark.parametrize(
    ("relative", "source", "forbidden_target"),
    [
        ("alarmcast/core/bad.py", "from ..host import server\n", "alarmcast.host"),
        ("alarmcast/host/bad.py", "from .. import client\n", "alarmcast.client"),
        ("alarmcast/client/bad.py", "from ..host.server import HostServer\n", "alarmcast.host"),
    ],
)
def test_forbidden_relative_imports_are_resolved(
    tmp_path: Path, relative: str, source: str, forbidden_target: str
) -> None:
    _write_module(tmp_path, relative, source)

    violations = check_import_boundaries(tmp_path)

    assert violations
    assert "relative-import" in format_violations(violations)
    assert forbidden_target in format_violations(violations)


@pytest.mark.parametrize(
    ("relative", "source", "forbidden_target"),
    [
        (
            "alarmcast/core/bad.py",
            'import importlib\nimportlib.import_module("alarmcast.host.server")\n',
            "alarmcast.host.server",
        ),
        (
            "alarmcast/host/bad.py",
            'from importlib import import_module\nimport_module("..client.net")\n',
            "alarmcast.client.net",
        ),
        (
            "alarmcast/client/bad.py",
            '__import__("alarmcast.host.capture")\n',
            "alarmcast.host.capture",
        ),
    ],
)
def test_forbidden_static_dynamic_imports_are_detected(
    tmp_path: Path, relative: str, source: str, forbidden_target: str
) -> None:
    _write_module(tmp_path, relative, source)

    violations = check_import_boundaries(tmp_path)

    message = format_violations(violations)
    assert "dynamic-import" in message
    assert forbidden_target in message
