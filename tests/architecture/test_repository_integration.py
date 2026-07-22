"""Integration test that applies all B02 guards to this checkout."""

from __future__ import annotations

from pathlib import Path

from tests.architecture.guards import check_repository, format_violations

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def test_repository_satisfies_architecture_and_scope_guards() -> None:
    violations = check_repository(REPOSITORY_ROOT)

    assert not violations, format_violations(violations)
