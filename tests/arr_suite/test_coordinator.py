import re
import aiohttp
import pytest
from aioresponses import aioresponses
from custom_components.arr_suite.coordinator import ArrCoordinator
from custom_components.arr_suite.const import DOMAIN
from tests.arr_suite.conftest import (
    SONARR_STATUS, SONARR_QUEUE, SONARR_WANTED,
    SONARR_CUTOFF, SONARR_HEALTH, SONARR_CALENDAR,
)


@pytest.mark.asyncio
async def test_sonarr_coordinator_fetches_all_data(hass):
    coordinator = ArrCoordinator(
        hass=hass,
        name="Sonarr",
        host="192.168.68.2",
        port=8989,
        api_key="testkey123",
        arr_type="sonarr",
    )

    with aioresponses() as m:
        base = "http://192.168.68.2:8989"
        m.get(f"{base}/api/v3/system/status", payload=SONARR_STATUS)
        m.get(f"{base}/api/v3/queue", payload=SONARR_QUEUE)
        m.get(f"{base}/api/v3/wanted/missing", payload=SONARR_WANTED)
        m.get(f"{base}/api/v3/wanted/cutoff", payload=SONARR_CUTOFF)
        m.get(f"{base}/api/v3/health", payload=SONARR_HEALTH)
        m.get(re.compile(r".*/api/v3/calendar.*"), payload=SONARR_CALENDAR)

        data = await coordinator._async_update_data()

    assert data["status"] == "Sonarr"
    assert data["queue_count"] == 3
    assert data["wanted_count"] == 12
    assert data["missing_count"] == 5
    assert data["health_ok"] is True
    assert data["health_issues"] == []
    assert len(data["calendar"]) == 1
    assert data["calendar"][0]["title"] == "Severance"


@pytest.mark.asyncio
async def test_coordinator_raises_update_failed_on_connection_error(hass):
    coordinator = ArrCoordinator(
        hass=hass,
        name="Sonarr",
        host="192.168.68.99",
        port=8989,
        api_key="testkey123",
        arr_type="sonarr",
    )

    with aioresponses() as m:
        m.get("http://192.168.68.99:8989/api/v3/system/status", exception=aiohttp.ClientConnectionError())

        from homeassistant.helpers.update_coordinator import UpdateFailed
        with pytest.raises(UpdateFailed):
            await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_health_issues_parsed(hass):
    coordinator = ArrCoordinator(
        hass=hass, name="Sonarr", host="192.168.68.2",
        port=8989, api_key="key", arr_type="sonarr",
    )
    health_response = [
        {"type": "error", "message": "Root folder /shows missing"},
        {"type": "warning", "message": "Indexer unavailable"},
    ]

    with aioresponses() as m:
        base = "http://192.168.68.2:8989/api/v3"
        for path in ["system/status", "queue", "wanted/missing", "wanted/cutoff"]:
            m.get(f"{base}/{path}", payload={"totalRecords": 0, "appName": "Sonarr"})
        m.get(f"{base}/health", payload=health_response)
        m.get(re.compile(r".*/api/v3/calendar.*"), payload=[])

        data = await coordinator._async_update_data()

    assert data["health_ok"] is False
    assert len(data["health_issues"]) == 2
    assert data["health_issues"][0]["message"] == "Root folder /shows missing"
