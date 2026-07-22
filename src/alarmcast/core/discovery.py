"""mDNS service publish/browse helpers."""

from __future__ import annotations

import socket
import threading
from dataclasses import dataclass

from zeroconf import IPVersion, ServiceBrowser, ServiceInfo, ServiceListener, Zeroconf

SERVICE_TYPE = "_alarmcast._tcp.local."
SERVICE_NAME_TEMPLATE = "AlarmcastHost-{hostname}._alarmcast._tcp.local."


@dataclass
class DiscoveryResult:
    """Resolved host endpoint from discovery."""

    host: str
    port: int


class _FirstResultListener(ServiceListener):
    """Capture the first matching service result."""

    def __init__(self, zeroconf: Zeroconf) -> None:
        self._zeroconf = zeroconf
        self._event = threading.Event()
        self.result: DiscoveryResult | None = None

    def add_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
        info = self._zeroconf.get_service_info(service_type, name, timeout=1000)
        if info is None:
            return
        addresses = info.parsed_scoped_addresses()
        if not addresses:
            return
        port = info.port or 0
        if port <= 0:
            return
        self.result = DiscoveryResult(host=addresses[0], port=port)
        self._event.set()

    def update_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
        self.add_service(zc, service_type, name)

    def remove_service(self, zc: Zeroconf, service_type: str, name: str) -> None:
        return

    def wait(self, timeout: float) -> DiscoveryResult | None:
        self._event.wait(timeout)
        return self.result


class PublishedService:
    """Lifecycle wrapper around a registered mDNS service."""

    def __init__(self, zeroconf: Zeroconf, info: ServiceInfo) -> None:
        self._zeroconf = zeroconf
        self._info = info

    def close(self) -> None:
        """Unregister and close resources."""
        self._zeroconf.unregister_service(self._info)
        self._zeroconf.close()


def publish_host(port: int, hostname: str | None = None) -> PublishedService:
    """Publish the host endpoint via mDNS."""
    resolved_hostname = hostname or socket.gethostname()
    service_name = SERVICE_NAME_TEMPLATE.format(hostname=resolved_hostname)
    addresses = [socket.inet_aton(_get_local_ipv4())]
    info = ServiceInfo(
        type_=SERVICE_TYPE,
        name=service_name,
        addresses=addresses,
        port=port,
        properties={"version": "1"},
        server=f"{resolved_hostname}.local.",
    )
    zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
    zeroconf.register_service(info)
    return PublishedService(zeroconf, info)


def browse_for_host(timeout: float = 2.0) -> DiscoveryResult | None:
    """Return first discovered host or None if timed out."""
    zeroconf = Zeroconf(ip_version=IPVersion.V4Only)
    listener = _FirstResultListener(zeroconf)
    browser = ServiceBrowser(zeroconf, SERVICE_TYPE, listener=listener)
    try:
        return listener.wait(timeout)
    finally:
        browser.cancel()
        zeroconf.close()


def _get_local_ipv4() -> str:
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
        probe.connect(("8.8.8.8", 80))
        return str(probe.getsockname()[0])
