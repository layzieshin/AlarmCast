"""Architecture tests for the implementation-free Alarmcast contract boundary."""

from __future__ import annotations

import ast
import types
from dataclasses import fields
from pathlib import Path
from typing import get_args, get_origin, get_type_hints

from alarmcast.alarmcast_runtime import contracts

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_PATH = REPOSITORY_ROOT / "src" / "alarmcast" / "alarmcast_runtime" / "contracts.py"

FORBIDDEN_MODULE_PREFIXES = (
    "PySide6",
    "socket",
    "threading",
    "asyncio",
    "numpy",
    "soundcard",
    "sounddevice",
    "zeroconf",
    "alarmcast.core",
    "alarmcast.host",
    "alarmcast.client",
)

CONTRACT_TYPES = (
    contracts.NetworkEndpoint,
    contracts.ConnectedMonitor,
    contracts.SourceSnapshot,
    contracts.MonitorSnapshot,
    contracts.AlarmResetRequest,
)


def _import_targets(tree: ast.AST) -> set[str]:
    targets: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            targets.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            targets.add(node.module)
    return targets


def test_contract_module_has_no_low_level_or_legacy_imports() -> None:
    tree = ast.parse(CONTRACTS_PATH.read_text(encoding="utf-8"), filename=str(CONTRACTS_PATH))
    imports = _import_targets(tree)

    forbidden = {imported for imported in imports if imported.startswith(FORBIDDEN_MODULE_PREFIXES)}
    assert forbidden == set()


def _annotation_modules(annotation: object) -> set[str]:
    origin = get_origin(annotation)
    if origin is not None:
        modules = _annotation_modules(origin)
        for argument in get_args(annotation):
            modules.update(_annotation_modules(argument))
        return modules
    if annotation is None or annotation is Ellipsis:
        return set()
    module = getattr(annotation, "__module__", None)
    return {module} if isinstance(module, str) else set()


def test_public_annotations_contain_only_builtin_or_contract_types() -> None:
    allowed_modules = {
        "builtins",
        "types",
        contracts.__name__,
    }

    for contract_type in CONTRACT_TYPES:
        hints = get_type_hints(contract_type)
        assert set(hints) == {field.name for field in fields(contract_type)}
        for annotation in hints.values():
            assert _annotation_modules(annotation) <= allowed_modules


def test_contract_module_does_not_define_protocols_callbacks_or_low_level_fields() -> None:
    public_field_names = {
        field.name for contract_type in CONTRACT_TYPES for field in fields(contract_type)
    }
    forbidden_terms = {
        "alarm_id",
        "callback",
        "socket",
        "thread",
        "audio",
        "payload",
        "frame",
        "device_id",
        "monitor_id",
    }

    assert public_field_names.isdisjoint(forbidden_terms)
    assert not hasattr(contracts, "Protocol")
    assert types.UnionType in {
        get_origin(hint) for hint in get_type_hints(contracts.AlarmResetRequest).values()
    }
