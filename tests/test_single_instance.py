"""Tests for single-instance locking."""

from __future__ import annotations

import sys
import uuid

import pytest


@pytest.fixture
def qcore_app():
    from PySide6.QtCore import QCoreApplication

    app = QCoreApplication.instance()
    if app is None:
        app = QCoreApplication(sys.argv)
    yield app


def _unique_server_name() -> str:
    return f"Alarmcast_test_{uuid.uuid4().hex}"


def test_notify_returns_false_when_no_server(qcore_app: object) -> None:
    from alarmcast.core.single_instance import notify_existing_instance

    name = _unique_server_name()
    assert notify_existing_instance(server_name=name) is False


def test_second_process_notifies_first(qcore_app: object) -> None:
    from alarmcast.core.single_instance import (
        notify_existing_instance,
        start_single_instance_server,
    )

    name = _unique_server_name()
    assert start_single_instance_server(lambda: None, server_name=name) is True
    assert notify_existing_instance(server_name=name) is True
