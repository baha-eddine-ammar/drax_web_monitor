from __future__ import annotations

import getpass
import platform
import socket
import threading
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import psutil

BYTES_PER_GB = 1024**3
BITS_PER_MEGABIT = 1_000_000
LINK_FAMILIES = {
    family
    for family in (getattr(psutil, "AF_LINK", None), getattr(socket, "AF_PACKET", None))
    if family is not None
}


@dataclass(slots=True)
class NetworkCounters:
    timestamp: float
    bytes_sent: int
    bytes_recv: int
    interface_key: str


class SystemMonitor:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        counters = psutil.net_io_counters()
        self._previous_network = NetworkCounters(
            timestamp=time.time(),
            bytes_sent=counters.bytes_sent,
            bytes_recv=counters.bytes_recv,
            interface_key="total",
        )
        psutil.cpu_percent(interval=None)

    def collect(self, ip_address: str) -> dict[str, Any]:
        with self._lock:
            cpu_percent = round(psutil.cpu_percent(interval=None), 1)
            memory = psutil.virtual_memory()
            disks, disk_totals = self._collect_disk_metrics()
            network = self._collect_network_metrics(ip_address)
            uptime_seconds = max(time.time() - psutil.boot_time(), 0)

            return {
                "hostname": socket.gethostname(),
                "ip_address": ip_address,
                "online": self._is_online(ip_address),
                "os_name": f"{platform.system()} {platform.release()}".strip(),
                "username": getpass.getuser(),
                "cpu_percent": cpu_percent,
                "cpu_temperature_c": self._collect_cpu_temperature(),
                "ram_percent": round(memory.percent, 1),
                "ram_used_gb": round(memory.used / BYTES_PER_GB, 1),
                "ram_total_gb": round(memory.total / BYTES_PER_GB, 1),
                "ram_available_gb": round(memory.available / BYTES_PER_GB, 1),
                "disks": disks,
                "disk_used_gb": disk_totals["used_gb"],
                "disk_free_gb": disk_totals["free_gb"],
                "disk_total_gb": disk_totals["total_gb"],
                "network": network,
                "uptime_human": self._format_uptime(uptime_seconds),
                "last_updated": datetime.now().astimezone().isoformat(timespec="seconds"),
            }

    def _collect_disk_metrics(self) -> tuple[list[dict[str, Any]], dict[str, float]]:
        disks: list[dict[str, Any]] = []
        seen_mounts: set[str] = set()
        total_used = 0.0
        total_free = 0.0
        total_size = 0.0

        for partition in psutil.disk_partitions(all=False):
            mount = partition.mountpoint.rstrip("\\") or partition.mountpoint
            if not mount or mount in seen_mounts:
                continue
            if "cdrom" in partition.opts.lower():
                continue

            try:
                usage = psutil.disk_usage(partition.mountpoint)
            except OSError:
                continue

            seen_mounts.add(mount)
            used_gb = round(usage.used / BYTES_PER_GB, 1)
            free_gb = round(usage.free / BYTES_PER_GB, 1)
            total_gb = round(usage.total / BYTES_PER_GB, 1)
            usage_percent = round(usage.percent, 1)

            disks.append(
                {
                    "mount": mount,
                    "used_gb": used_gb,
                    "free_gb": free_gb,
                    "total_gb": total_gb,
                    "usage_percent": usage_percent,
                }
            )
            total_used += used_gb
            total_free += free_gb
            total_size += total_gb

        disks.sort(key=lambda disk: disk["mount"])
        return disks, {
            "used_gb": round(total_used, 1),
            "free_gb": round(total_free, 1),
            "total_gb": round(total_size, 1),
        }

    def _collect_network_metrics(self, ip_address: str) -> dict[str, Any]:
        interface_details = self._collect_active_interface_details(ip_address)
        counters_by_interface = psutil.net_io_counters(pernic=True)
        interface_name = interface_details["interface_name"]
        counters = counters_by_interface.get(interface_name) if interface_name else None
        counter_scope = "adapter"

        if counters is None:
            counters = psutil.net_io_counters()
            counter_scope = "total"

        now = time.time()
        elapsed = max(now - self._previous_network.timestamp, 0.1)
        interface_key = interface_name or counter_scope

        if self._previous_network.interface_key != interface_key:
            upload_mbps = 0.0
            download_mbps = 0.0
        else:
            upload_mbps = round(
                max(counters.bytes_sent - self._previous_network.bytes_sent, 0)
                * 8
                / elapsed
                / BITS_PER_MEGABIT,
                2,
            )
            download_mbps = round(
                max(counters.bytes_recv - self._previous_network.bytes_recv, 0)
                * 8
                / elapsed
                / BITS_PER_MEGABIT,
                2,
            )

        self._previous_network = NetworkCounters(
            timestamp=now,
            bytes_sent=counters.bytes_sent,
            bytes_recv=counters.bytes_recv,
            interface_key=interface_key,
        )

        return {
            "upload_mbps": upload_mbps,
            "download_mbps": download_mbps,
            "bytes_sent": counters.bytes_sent,
            "bytes_recv": counters.bytes_recv,
            "packets_sent": counters.packets_sent,
            "packets_recv": counters.packets_recv,
            "errin": counters.errin,
            "errout": counters.errout,
            "dropin": counters.dropin,
            "dropout": counters.dropout,
            "counter_scope": counter_scope,
            **interface_details,
        }

    def _collect_active_interface_details(self, ip_address: str) -> dict[str, Any]:
        interface_name = ""
        ipv4_info = None
        mac_address = None
        interface_stats = psutil.net_if_stats()

        for current_name, addresses in psutil.net_if_addrs().items():
            current_ipv4 = next(
                (
                    entry
                    for entry in addresses
                    if getattr(entry, "family", None) == socket.AF_INET
                    and entry.address == ip_address
                ),
                None,
            )
            if current_ipv4 is None:
                continue

            interface_name = current_name
            ipv4_info = current_ipv4
            mac_address = next(
                (
                    entry.address
                    for entry in addresses
                    if getattr(entry, "family", None) in LINK_FAMILIES
                    and entry.address
                ),
                None,
            )
            break

        if not interface_name:
            for current_name, addresses in psutil.net_if_addrs().items():
                current_ipv4 = next(
                    (
                        entry
                        for entry in addresses
                        if getattr(entry, "family", None) == socket.AF_INET
                        and entry.address
                        and entry.address != "127.0.0.1"
                    ),
                    None,
                )
                if current_ipv4 is None:
                    continue

                interface_name = current_name
                ipv4_info = current_ipv4
                mac_address = next(
                    (
                        entry.address
                        for entry in addresses
                        if getattr(entry, "family", None) in LINK_FAMILIES
                        and entry.address
                    ),
                    None,
                )
                break

        stats = interface_stats.get(interface_name) if interface_name else None
        return {
            "interface_name": interface_name or "Unknown",
            "connection_type": self._guess_connection_type(interface_name),
            "connection_state": self._format_connection_state(stats, ip_address),
            "mac_address": mac_address or "Unknown",
            "subnet_mask": getattr(ipv4_info, "netmask", None) or "Unknown",
            "broadcast_ip": getattr(ipv4_info, "broadcast", None) or "Unknown",
            "link_speed_mbps": stats.speed if stats and stats.speed > 0 else None,
            "mtu": stats.mtu if stats else None,
            "duplex": self._format_duplex(stats.duplex if stats else None),
            "is_up": bool(stats.isup) if stats else False,
        }

    def _collect_cpu_temperature(self) -> float | None:
        if not hasattr(psutil, "sensors_temperatures"):
            return None

        try:
            sensors = psutil.sensors_temperatures()
        except (AttributeError, NotImplementedError, OSError):
            return None

        for entries in sensors.values():
            for entry in entries:
                current = getattr(entry, "current", None)
                if current is not None:
                    return round(float(current), 1)

        return None

    def _is_online(self, ip_address: str) -> bool:
        if ip_address == "127.0.0.1":
            return False
        return any(stats.isup for stats in psutil.net_if_stats().values())

    def _guess_connection_type(self, interface_name: str) -> str:
        name = interface_name.lower()

        if any(keyword in name for keyword in ("wi-fi", "wifi", "wireless", "wlan")):
            return "Wi-Fi"
        if any(keyword in name for keyword in ("ethernet", "eth", "lan")):
            return "Ethernet"
        if any(keyword in name for keyword in ("virtual", "vmware", "hyper-v", "vethernet")):
            return "Virtual"
        if "bluetooth" in name:
            return "Bluetooth"
        if "loopback" in name:
            return "Loopback"
        return "Unknown"

    def _format_connection_state(self, stats: Any, ip_address: str) -> str:
        if ip_address == "127.0.0.1":
            return "No LAN address"
        if not stats:
            return "Adapter not detected"
        if stats.isup:
            return "Connected"
        return "Link down"

    def _format_duplex(self, duplex: Any) -> str:
        if duplex == psutil.NIC_DUPLEX_FULL:
            return "Full duplex"
        if duplex == psutil.NIC_DUPLEX_HALF:
            return "Half duplex"
        return "Unknown"

    def _format_uptime(self, total_seconds: float) -> str:
        minutes = int(total_seconds // 60)
        days, minutes = divmod(minutes, 60 * 24)
        hours, minutes = divmod(minutes, 60)

        parts = []
        if days:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        return " ".join(parts)
