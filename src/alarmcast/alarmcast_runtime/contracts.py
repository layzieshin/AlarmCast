"""Immutable, implementation-free contracts for the Alarmcast runtime."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class RuntimeState(StrEnum):
    """Whether an Alarmcast source or monitor is running."""

    STOPPED = "stopped"
    RUNNING = "running"


class AlarmState(StrEnum):
    """The current alarm state observed by a source or monitor."""

    INACTIVE = "inactive"
    ACTIVE = "active"


class ConnectionState(StrEnum):
    """The connection phase observed by an Alarmcast monitor."""

    DISCONNECTED = "disconnected"
    DISCOVERING = "discovering"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"


class ResetOrigin(StrEnum):
    """The observable origin of an alarm reset request."""

    LOCAL_SOURCE = "local_source"
    LOCAL_MONITOR = "local_monitor"
    REMOTE_MONITOR = "remote_monitor"


@dataclass(frozen=True, slots=True)
class NetworkEndpoint:
    """A validated network address without DNS or socket behavior."""

    host: str
    port: int

    def __post_init__(self) -> None:
        if not isinstance(self.host, str):
            raise TypeError("host must be a string")
        if not self.host or self.host != self.host.strip():
            raise ValueError("host must be non-empty and already trimmed")
        if isinstance(self.port, bool) or not isinstance(self.port, int):
            raise TypeError("port must be an integer")
        if not 1 <= self.port <= 65535:
            raise ValueError("port must be between 1 and 65535")


@dataclass(frozen=True, slots=True)
class ConnectedMonitor:
    """A currently connected monitor identified by its observed name and endpoint."""

    name: str
    endpoint: NetworkEndpoint

    def __post_init__(self) -> None:
        if not isinstance(self.name, str):
            raise TypeError("name must be a string")
        if not self.name or self.name != self.name.strip():
            raise ValueError("name must be non-empty and already trimmed")
        if not isinstance(self.endpoint, NetworkEndpoint):
            raise TypeError("endpoint must be a NetworkEndpoint")


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    """Immutable state of one Alarmcast source at an observation point."""

    runtime_state: RuntimeState
    alarm_state: AlarmState
    connected_monitors: tuple[ConnectedMonitor, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.runtime_state, RuntimeState):
            raise TypeError("runtime_state must be a RuntimeState")
        if not isinstance(self.alarm_state, AlarmState):
            raise TypeError("alarm_state must be an AlarmState")
        if not isinstance(self.connected_monitors, tuple):
            raise TypeError("connected_monitors must be a tuple")
        if not all(isinstance(monitor, ConnectedMonitor) for monitor in self.connected_monitors):
            raise TypeError("connected_monitors must contain only ConnectedMonitor values")
        if self.runtime_state is RuntimeState.STOPPED:
            if self.alarm_state is not AlarmState.INACTIVE:
                raise ValueError("a stopped source cannot have an active alarm")
            if self.connected_monitors:
                raise ValueError("a stopped source cannot have connected monitors")


@dataclass(frozen=True, slots=True)
class MonitorSnapshot:
    """Immutable runtime, connection, and alarm state of one monitor."""

    runtime_state: RuntimeState
    connection_state: ConnectionState
    alarm_state: AlarmState
    source_endpoint: NetworkEndpoint | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.runtime_state, RuntimeState):
            raise TypeError("runtime_state must be a RuntimeState")
        if not isinstance(self.connection_state, ConnectionState):
            raise TypeError("connection_state must be a ConnectionState")
        if not isinstance(self.alarm_state, AlarmState):
            raise TypeError("alarm_state must be an AlarmState")
        if self.source_endpoint is not None and not isinstance(
            self.source_endpoint, NetworkEndpoint
        ):
            raise TypeError("source_endpoint must be a NetworkEndpoint or None")

        if self.runtime_state is RuntimeState.STOPPED:
            if self.connection_state is not ConnectionState.DISCONNECTED:
                raise ValueError("a stopped monitor must be disconnected")
            if self.alarm_state is not AlarmState.INACTIVE:
                raise ValueError("a stopped monitor cannot have an active alarm")
            if self.source_endpoint is not None:
                raise ValueError("a stopped monitor cannot have a source endpoint")

        endpoint_required = self.connection_state in {
            ConnectionState.CONNECTING,
            ConnectionState.CONNECTED,
            ConnectionState.RECONNECTING,
        }
        if endpoint_required and self.source_endpoint is None:
            raise ValueError(f"{self.connection_state.value} requires a source endpoint")
        if not endpoint_required and self.source_endpoint is not None:
            raise ValueError(f"{self.connection_state.value} cannot have a source endpoint")


@dataclass(frozen=True, slots=True)
class AlarmResetRequest:
    """A reset request without a speculative alarm identifier."""

    origin: ResetOrigin
    requester: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.origin, ResetOrigin):
            raise TypeError("origin must be a ResetOrigin")
        if self.requester is not None and not isinstance(self.requester, str):
            raise TypeError("requester must be a string or None")

        if self.origin is ResetOrigin.REMOTE_MONITOR:
            if (
                self.requester is None
                or not self.requester
                or self.requester != self.requester.strip()
            ):
                raise ValueError("a remote monitor reset requires a trimmed requester")
        elif self.requester is not None:
            raise ValueError("a local reset cannot have a requester")
