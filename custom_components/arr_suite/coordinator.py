"""DataUpdateCoordinator for arr_suite."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    DEFAULT_SCAN_INTERVAL,
    REQUEST_TIMEOUT,
    API_PATHS,
)

_LOGGER = logging.getLogger(__name__)


class ArrCoordinator(DataUpdateCoordinator):
    """Fetches data from a single arr instance."""

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        host: str,
        port: int,
        api_key: str,
        arr_type: str,
    ) -> None:
        self.arr_type = arr_type
        self._base_url = f"http://{host}:{port}"
        self._headers = {"X-Api-Key": api_key}
        self._api_base = API_PATHS[arr_type]["base"]
        self._calendar_path = API_PATHS[arr_type]["calendar"]

        super().__init__(
            hass,
            _LOGGER,
            name=f"arr_suite_{name}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        try:
            async with aiohttp.ClientSession(
                headers=self._headers,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as session:
                return await self._fetch_all(session)
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Connection error: {err}") from err
        except TimeoutError as err:
            raise UpdateFailed(f"Timeout: {err}") from err

    async def _fetch_all(self, session: aiohttp.ClientSession) -> dict:
        base = self._api_base

        status, queue, wanted, cutoff, health = await asyncio.gather(
            self._get(session, f"{base}/system/status"),
            self._get(session, f"{base}/queue"),
            self._get(session, f"{base}/wanted/missing"),
            self._get(session, f"{base}/wanted/cutoff"),
            self._get(session, f"{base}/health"),
        )
        calendar = await self._fetch_calendar(session)

        health_issues = [
            {"type": h["type"], "message": h["message"]}
            for h in (health or [])
            if h.get("type") in ("error", "warning")
        ]

        return {
            "status": status.get("appName", "unknown"),
            "version": status.get("version", ""),
            "queue_count": queue.get("totalRecords", 0) if isinstance(queue, dict) else 0,
            "wanted_count": wanted.get("totalRecords", 0) if isinstance(wanted, dict) else 0,
            "missing_count": cutoff.get("totalRecords", 0) if isinstance(cutoff, dict) else 0,
            "health_ok": len(health_issues) == 0,
            "health_issues": health_issues,
            "calendar": calendar,
        }

    async def _fetch_calendar(self, session: aiohttp.ClientSession) -> list:
        if not self._calendar_path:
            return []
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=14)
        params = {
            "start": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "end": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
        result = await self._get(session, self._calendar_path, params=params)
        return result if isinstance(result, list) else []

    async def _get(
        self,
        session: aiohttp.ClientSession,
        path: str,
        params: dict | None = None,
    ) -> Any:
        url = f"{self._base_url}{path}"
        async with session.get(url, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()
