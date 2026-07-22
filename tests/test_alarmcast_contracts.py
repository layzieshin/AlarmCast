"""Contract tests for the implementation-free Alarmcast runtime model."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, fields
from enum import StrEnum

import pytest

from alarmcast.alarmcast_runtime.contracts import (
    AlarmResetRequest,
    AlarmState,
    ConnectedMonitor,
    ConnectionState,
    MonitorSnapshot,
    NetworkEndpoint,
    ResetOrigin,
    RuntimeState,
    SourceSnapshot,
)


@pytest.fixture
def endpoint() -> NetworkEndpoint:
    return NetworkEndpoint(host="source.example.test", port=50050)


@pytest.fixture
def monitor(endpoint: NetworkEndpoint) -> ConnectedMonitor:
    return ConnectedMonitor(name="MONITOR-01", endpoint=endpoint)


@pytest.mark.parametrize(
    ("enum_type", "expected"),
    [
        (RuntimeState, {"STOPPED": "stopped", "RUNNING": "running"}),
        (AlarmState, {"INACTIVE": "inactive", "ACTIVE": "active"}),
        (
            ConnectionState,
            {
                "DISCONNECTED": "disconnected",
                "DISCOVERING": "discovering",
                "CONNECTING": "connecting",
                "CONNECTED": "connected",
                "RECONNECTING": "reconnecting",
            },
        ),
        (
            ResetOrigin,
            {
                "LOCAL_SOURCE": "local_source",
                "LOCAL_MONITOR": "local_monitor",
                "REMOTE_MONITOR": "remote_monitor",
            },
        ),
    ],
)
def test_enum_names_and_exact_string_values(
    enum_type: type[StrEnum], expected: dict[str, str]
) -> None:
    assert {member.name: member.value for member in enum_type} == expected
    assert all(isinstance(member, str) for member in enum_type)


def _valid_contracts() -> tuple[object, ...]:
    endpoint = NetworkEndpoint("source.example.test", 50050)
    monitor = ConnectedMonitor("MONITOR-01", endpoint)
    return (
        endpoint,
        monitor,
        SourceSnapshot(RuntimeState.RUNNING, AlarmState.INACTIVE, (monitor,)),
        MonitorSnapshot(
            RuntimeState.RUNNING,
            ConnectionState.CONNECTED,
            AlarmState.INACTIVE,
            endpoint,
        ),
        AlarmResetRequest(ResetOrigin.REMOTE_MONITOR, "MONITOR-01"),
    )


@pytest.mark.parametrize("contract", _valid_contracts())
def test_contracts_are_frozen_and_slotted(contract: object) -> None:
    assert getattr(type(contract), "__dataclass_params__").frozen is True
    assert hasattr(type(contract), "__slots__")
    assert not hasattr(contract, "__dict__")

    first_field = fields(contract)[0]
    with pytest.raises(FrozenInstanceError):
        setattr(contract, first_field.name, getattr(contract, first_field.name))


def test_contract_fields_are_exactly_the_approved_model() -> None:
    assert [field.name for field in fields(NetworkEndpoint)] == ["host", "port"]
    assert [field.name for field in fields(ConnectedMonitor)] == ["name", "endpoint"]
    assert [field.name for field in fields(SourceSnapshot)] == [
        "runtime_state",
        "alarm_state",
        "connected_monitors",
    ]
    assert [field.name for field in fields(MonitorSnapshot)] == [
        "runtime_state",
        "connection_state",
        "alarm_state",
        "source_endpoint",
    ]
    assert [field.name for field in fields(AlarmResetRequest)] == ["origin", "requester"]


@pytest.mark.parametrize(
    ("host", "port"),
    [("source.example.test", 1), ("192.0.2.20", 50050), ("::1", 65535)],
)
def test_network_endpoint_accepts_valid_address_strings(host: str, port: int) -> None:
    assert NetworkEndpoint(host, port) == NetworkEndpoint(host=host, port=port)


@pytest.mark.parametrize("host", ["", " ", " source.example.test", "source.example.test "])
def test_network_endpoint_rejects_empty_or_untrimmed_host(host: str) -> None:
    with pytest.raises(ValueError):
        NetworkEndpoint(host, 50050)


@pytest.mark.parametrize("host", [None, 123])
def test_network_endpoint_rejects_non_string_host(host: object) -> None:
    with pytest.raises(TypeError):
        NetworkEndpoint(host, 50050)  # type: ignore[arg-type]


@pytest.mark.parametrize("port", [0, -1, 65536])
def test_network_endpoint_rejects_out_of_range_port(port: int) -> None:
    with pytest.raises(ValueError):
        NetworkEndpoint("source.example.test", port)


@pytest.mark.parametrize("port", [True, 1.5, "50050"])
def test_network_endpoint_rejects_non_integer_port(port: object) -> None:
    with pytest.raises(TypeError):
        NetworkEndpoint("source.example.test", port)  # type: ignore[arg-type]


def test_connected_monitor_accepts_observed_name_and_endpoint(endpoint: NetworkEndpoint) -> None:
    assert ConnectedMonitor("MONITOR-01", endpoint).endpoint is endpoint


@pytest.mark.parametrize("name", ["", " ", " MONITOR-01", "MONITOR-01 "])
def test_connected_monitor_rejects_empty_or_untrimmed_name(
    name: str, endpoint: NetworkEndpoint
) -> None:
    with pytest.raises(ValueError):
        ConnectedMonitor(name, endpoint)


def test_connected_monitor_rejects_wrong_field_types(endpoint: NetworkEndpoint) -> None:
    with pytest.raises(TypeError):
        ConnectedMonitor(123, endpoint)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        ConnectedMonitor("MONITOR-01", ("source.example.test", 50050))  # type: ignore[arg-type]


def test_running_source_accepts_zero_or_multiple_monitors(
    endpoint: NetworkEndpoint, monitor: ConnectedMonitor
) -> None:
    empty = SourceSnapshot(RuntimeState.RUNNING, AlarmState.INACTIVE)
    second = ConnectedMonitor("MONITOR-02", NetworkEndpoint(endpoint.host, 50051))
    multiple = SourceSnapshot(RuntimeState.RUNNING, AlarmState.ACTIVE, (monitor, second))

    assert empty.connected_monitors == ()
    assert multiple.connected_monitors == (monitor, second)


def test_source_monitor_collection_must_be_a_typed_tuple(monitor: ConnectedMonitor) -> None:
    with pytest.raises(TypeError):
        SourceSnapshot(
            RuntimeState.RUNNING,
            AlarmState.INACTIVE,
            [monitor],  # type: ignore[arg-type]
        )
    with pytest.raises(TypeError):
        SourceSnapshot(
            RuntimeState.RUNNING,
            AlarmState.INACTIVE,
            ("MONITOR-01",),  # type: ignore[arg-type]
        )


def test_stopped_source_rejects_active_alarm() -> None:
    with pytest.raises(ValueError):
        SourceSnapshot(RuntimeState.STOPPED, AlarmState.ACTIVE)


def test_stopped_source_rejects_connected_monitors(monitor: ConnectedMonitor) -> None:
    with pytest.raises(ValueError):
        SourceSnapshot(RuntimeState.STOPPED, AlarmState.INACTIVE, (monitor,))


def test_source_snapshot_rejects_non_enum_states() -> None:
    with pytest.raises(TypeError):
        SourceSnapshot("running", AlarmState.INACTIVE)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        SourceSnapshot(RuntimeState.RUNNING, "inactive")  # type: ignore[arg-type]


def test_running_monitor_can_discover_without_endpoint() -> None:
    snapshot = MonitorSnapshot(
        RuntimeState.RUNNING,
        ConnectionState.DISCOVERING,
        AlarmState.INACTIVE,
    )

    assert snapshot.source_endpoint is None


@pytest.mark.parametrize(
    "connection_state",
    [ConnectionState.CONNECTING, ConnectionState.CONNECTED, ConnectionState.RECONNECTING],
)
def test_connected_phases_accept_endpoint(
    connection_state: ConnectionState, endpoint: NetworkEndpoint
) -> None:
    snapshot = MonitorSnapshot(
        RuntimeState.RUNNING,
        connection_state,
        AlarmState.INACTIVE,
        endpoint,
    )

    assert snapshot.source_endpoint is endpoint


@pytest.mark.parametrize(
    "connection_state",
    [ConnectionState.CONNECTING, ConnectionState.CONNECTED, ConnectionState.RECONNECTING],
)
def test_connected_phases_require_endpoint(connection_state: ConnectionState) -> None:
    with pytest.raises(ValueError):
        MonitorSnapshot(RuntimeState.RUNNING, connection_state, AlarmState.INACTIVE)


@pytest.mark.parametrize(
    "connection_state", [ConnectionState.DISCONNECTED, ConnectionState.DISCOVERING]
)
def test_unconnected_phases_reject_endpoint(
    connection_state: ConnectionState, endpoint: NetworkEndpoint
) -> None:
    with pytest.raises(ValueError):
        MonitorSnapshot(
            RuntimeState.RUNNING,
            connection_state,
            AlarmState.INACTIVE,
            endpoint,
        )


@pytest.mark.parametrize(
    ("connection_state", "alarm_state", "with_endpoint"),
    [
        (ConnectionState.CONNECTED, AlarmState.INACTIVE, True),
        (ConnectionState.DISCONNECTED, AlarmState.ACTIVE, False),
        (ConnectionState.DISCONNECTED, AlarmState.INACTIVE, True),
    ],
)
def test_stopped_monitor_rejects_connection_alarm_or_endpoint(
    connection_state: ConnectionState,
    alarm_state: AlarmState,
    with_endpoint: bool,
    endpoint: NetworkEndpoint,
) -> None:
    with pytest.raises(ValueError):
        MonitorSnapshot(
            RuntimeState.STOPPED,
            connection_state,
            alarm_state,
            endpoint if with_endpoint else None,
        )


def test_running_disconnected_monitor_may_retain_active_alarm() -> None:
    snapshot = MonitorSnapshot(
        RuntimeState.RUNNING,
        ConnectionState.DISCONNECTED,
        AlarmState.ACTIVE,
    )

    assert snapshot.alarm_state is AlarmState.ACTIVE


def test_monitor_snapshot_rejects_wrong_field_types() -> None:
    with pytest.raises(TypeError):
        MonitorSnapshot(  # type: ignore[arg-type]
            "running", ConnectionState.DISCONNECTED, AlarmState.INACTIVE
        )
    with pytest.raises(TypeError):
        MonitorSnapshot(  # type: ignore[arg-type]
            RuntimeState.RUNNING, "disconnected", AlarmState.INACTIVE
        )
    with pytest.raises(TypeError):
        MonitorSnapshot(  # type: ignore[arg-type]
            RuntimeState.RUNNING, ConnectionState.DISCONNECTED, "inactive"
        )
    with pytest.raises(TypeError):
        MonitorSnapshot(
            RuntimeState.RUNNING,
            ConnectionState.CONNECTED,
            AlarmState.INACTIVE,
            ("source.example.test", 50050),  # type: ignore[arg-type]
        )


def test_remote_reset_accepts_trimmed_requester() -> None:
    assert AlarmResetRequest(ResetOrigin.REMOTE_MONITOR, "MONITOR-01").requester == "MONITOR-01"


@pytest.mark.parametrize("requester", [None, "", " ", " MONITOR-01", "MONITOR-01 "])
def test_remote_reset_rejects_missing_empty_or_untrimmed_requester(
    requester: str | None,
) -> None:
    with pytest.raises(ValueError):
        AlarmResetRequest(ResetOrigin.REMOTE_MONITOR, requester)


@pytest.mark.parametrize("origin", [ResetOrigin.LOCAL_SOURCE, ResetOrigin.LOCAL_MONITOR])
def test_local_reset_accepts_no_requester(origin: ResetOrigin) -> None:
    assert AlarmResetRequest(origin).requester is None


@pytest.mark.parametrize("origin", [ResetOrigin.LOCAL_SOURCE, ResetOrigin.LOCAL_MONITOR])
def test_local_reset_rejects_requester(origin: ResetOrigin) -> None:
    with pytest.raises(ValueError):
        AlarmResetRequest(origin, "MONITOR-01")


def test_reset_request_rejects_wrong_field_types() -> None:
    with pytest.raises(TypeError):
        AlarmResetRequest("remote_monitor", "MONITOR-01")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        AlarmResetRequest(ResetOrigin.REMOTE_MONITOR, 123)  # type: ignore[arg-type]
