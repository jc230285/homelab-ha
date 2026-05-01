import pytest
from aioresponses import aioresponses
from custom_components.homelab_infra.coordinator import InfraCoordinator

NODE_EXPORTER_RESPONSE = """
node_memory_MemAvailable_bytes 8589934592
node_memory_MemTotal_bytes 17179869184
node_filesystem_avail_bytes{mountpoint="/"} 107374182400
node_filesystem_size_bytes{mountpoint="/"} 214748364800
node_network_receive_bytes_total 1048576000
node_network_transmit_bytes_total 524288000
node_boot_time_seconds 1746100000
node_load1 0.42
node_cpu_seconds_total{mode="idle"} 50000
"""


@pytest.mark.asyncio
async def test_coordinator_parses_node_exporter_metrics(hass):
    coordinator = InfraCoordinator(
        hass=hass, name="hom1", host="192.168.68.222",
        node_exporter_port=9100, machine_type="linux",
        coolify_url=None, coolify_api_key=None,
    )
    with aioresponses() as m:
        m.get("http://192.168.68.222:9100/metrics", body=NODE_EXPORTER_RESPONSE, content_type="text/plain")
        data = await coordinator._async_update_data()

    assert data["online"] is True
    assert 40.0 <= data["ram_percent"] <= 60.0
    assert 0.0 <= data["disk_percent"] <= 100.0
    assert "network_in_bytes" in data
    assert data["load_avg"] == pytest.approx(0.42)


@pytest.mark.asyncio
async def test_coordinator_marks_offline_on_connection_error(hass):
    import aiohttp as _aiohttp
    coordinator = InfraCoordinator(
        hass=hass, name="hom1", host="192.168.68.99",
        node_exporter_port=9100, machine_type="linux",
        coolify_url=None, coolify_api_key=None,
    )
    with aioresponses() as m:
        m.get("http://192.168.68.99:9100/metrics", exception=_aiohttp.ClientConnectionError())
        data = await coordinator._async_update_data()

    assert data["online"] is False
