from __future__ import annotations

import ipaddress
import socket
from dataclasses import dataclass

import psutil


@dataclass(slots=True)
class ServerIdentity:
    hostname: str
    ip_address: str
    dashboard_url: str


def get_server_identity(port: int) -> ServerIdentity:
    hostname = socket.gethostname()
    ip_address = get_best_local_ipv4()
    return ServerIdentity(
        hostname=hostname,
        ip_address=ip_address,
        dashboard_url=f"http://{ip_address}:{port}",
    )


def get_best_local_ipv4() -> str:
    candidate_addresses = []
    routed_ip = _get_routed_ipv4()

    for interface_name, address in _iter_interface_ipv4_addresses():
        if not _is_usable_ipv4(address):
            continue
        score = _score_ip(address)
        candidate_addresses.append((score, interface_name.lower(), address))

    if routed_ip and _is_usable_ipv4(routed_ip):
        routed_match = next(
            (item for item in candidate_addresses if item[2] == routed_ip),
            None,
        )
        if routed_match:
            return routed_match[2]
        candidate_addresses.append((_score_ip(routed_ip) + 10, "route", routed_ip))

    if candidate_addresses:
        candidate_addresses.sort(key=lambda item: item[0], reverse=True)
        return candidate_addresses[0][2]

    return routed_ip or "127.0.0.1"


def _iter_interface_ipv4_addresses() -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []
    interface_stats = psutil.net_if_stats()

    for interface_name, addresses in psutil.net_if_addrs().items():
        stats = interface_stats.get(interface_name)
        if stats and not stats.isup:
            continue

        lowered_name = interface_name.lower()
        if "loopback" in lowered_name:
            continue

        for address in addresses:
            if getattr(address, "family", None) != socket.AF_INET:
                continue
            if address.address:
                results.append((interface_name, address.address))

    return results


def _get_routed_ipv4() -> str | None:
    for target in ("10.255.255.255", "192.168.255.255", "8.8.8.8"):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.connect((target, 1))
            routed_ip = sock.getsockname()[0]
            if routed_ip:
                return routed_ip
        except OSError:
            continue
        finally:
            sock.close()

    return None


def _is_usable_ipv4(address: str) -> bool:
    try:
        parsed = ipaddress.IPv4Address(address)
    except ipaddress.AddressValueError:
        return False

    return not any(
        (
            parsed.is_loopback,
            parsed.is_link_local,
            parsed.is_multicast,
            parsed.is_unspecified,
        )
    )


def _score_ip(address: str) -> int:
    parsed = ipaddress.IPv4Address(address)

    if parsed.is_private:
        return 100
    if parsed.is_global:
        return 50
    return 10
