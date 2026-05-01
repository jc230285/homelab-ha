"""DataUpdateCoordinator for homelab_infra."""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, DEFAULT_METRICS_INTERVAL, REQUEST_TIMEOUT
from .prometheus_parser import parse_prometheus_text

_LOGGER = logging.getLogger(__name__)

_OFFLINE_DATA: dict[str, Any] = {
    "online": False,
    "cpu_percent": None,
    "ram_percent": None,
    "disk_percent": None,
    "network_in_bytes": None,
    "network_out_bytes": None,
    "uptime_seconds": None,
    "load_avg": None,
    "docker_running": None,
    "docker_stopped": None,
    "containers": [],
}


class InfraCoordinator(DataUpdateCoordinator):
    """Polls Node Exporter and optionally Coolify for one machine."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        host: str,
        node_exporter_port: int,
        machine_type: str,
        coolify_url: str | None,
        coolify_api_key: str | None,
    ) -> None:
        self._host = host
        self._exporter_url = f"http://{host}:{node_exporter_port}/metrics"
        self._machine_type = machine_type
        self._coolify_url = coolify_url.rstrip("/") if coolify_url else None
        self._coolify_headers = (
            {"Authorization": f"Bearer {coolify_api_key}"} if coolify_api_key else {}
        )
        self._prev_cpu_idle: float | None = None
        self._prev_cpu_total: float | None = None
        self._prev_cpu_time: float = 0.0

        super().__init__(
            hass,
            _LOGGER,
            name=f"homelab_infra_{name}",
            update_interval=timedelta(seconds=DEFAULT_METRICS_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
        ) as session:
            metrics = await self._fetch_node_exporter(session)
            if metrics is None:
                return dict(_OFFLINE_DATA)

            data: dict[str, Any] = {"online": True, **self._extract_metrics(metrics)}

            if self._coolify_url:
                containers = await self._fetch_coolify_containers(session)
                running = sum(1 for c in containers if c["status"] == "running")
                data.update({
                    "docker_running": running,
                    "docker_stopped": len(containers) - running,
                    "containers": containers,
                })
            else:
                data.update({"docker_running": None, "docker_stopped": None, "containers": []})

            return data

    async def _fetch_node_exporter(self, session: aiohttp.ClientSession) -> dict | None:
        try:
            async with session.get(self._exporter_url) as resp:
                if resp.status != 200:
                    return None
                return parse_prometheus_text(await resp.text())
        except Exception:
            return None

    def _extract_metrics(self, m: dict) -> dict:
        mem_total = m.get("node_memory_MemTotal_bytes", 1)
        mem_avail = m.get("node_memory_MemAvailable_bytes", 0)
        ram_percent = round((1 - mem_avail / mem_total) * 100, 1) if mem_total else 0

        disk_avail = m.get("node_filesystem_avail_bytes", 0)
        disk_total = m.get("node_filesystem_size_bytes", 1)
        disk_percent = round((1 - disk_avail / disk_total) * 100, 1) if disk_total else 0

        net_in = m.get("node_network_receive_bytes_total", 0)
        net_out = m.get("node_network_transmit_bytes_total", 0)

        boot_time = m.get("node_boot_time_seconds")
        uptime = round(time.time() - boot_time) if boot_time else None

        load = m.get("node_load1")

        cpu_percent = self._calc_cpu(m)

        return {
            "ram_percent": ram_percent,
            "disk_percent": disk_percent,
            "cpu_percent": cpu_percent,
            "network_in_bytes": net_in,
            "network_out_bytes": net_out,
            "uptime_seconds": uptime,
            "load_avg": load,
        }

    def _calc_cpu(self, m: dict) -> float:
        """Calculate CPU % from windows or node exporter counters."""
        # windows_exporter: use processor utility if available
        util = m.get("windows_cpu_time_total")
        if util is not None:
            # rough: complement of idle fraction
            pass

        idle = m.get("node_cpu_seconds_total")
        if idle is None:
            return 0.0

        now = time.monotonic()
        prev_idle = self._prev_cpu_idle
        prev_time = self._prev_cpu_time

        self._prev_cpu_idle = idle
        self._prev_cpu_time = now

        if prev_idle is None or (now - prev_time) < 1:
            return self.data.get("cpu_percent", 0.0) if self.data else 0.0

        elapsed = now - prev_time
        idle_delta = idle - prev_idle
        busy_frac = max(0.0, 1.0 - (idle_delta / elapsed))
        return round(min(busy_frac * 100, 100.0), 1)

    async def _fetch_coolify_containers(self, session: aiohttp.ClientSession) -> list[dict]:
        try:
            url = f"{self._coolify_url}/api/v1/applications"
            async with session.get(url, headers=self._coolify_headers) as resp:
                if resp.status != 200:
                    return []
                apps = await resp.json()
                if not isinstance(apps, list):
                    apps = apps.get("data", [])
                return [
                    {
                        "name": a.get("name", "unknown"),
                        "status": a.get("status", "unknown"),
                        "image": a.get("docker_image", ""),
                    }
                    for a in apps
                ]
        except Exception:
            return []
