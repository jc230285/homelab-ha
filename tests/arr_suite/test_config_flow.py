import pytest
from unittest.mock import patch
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResultType
from custom_components.arr_suite.const import DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.mark.asyncio
async def test_config_flow_creates_entry_for_sonarr(hass, enable_custom_integrations):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "custom_components.arr_suite.config_flow.ArrConfigFlow._test_connection",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "Sonarr",
                "host": "192.168.68.2",
                "port": 8989,
                "api_key": "testkey",
                "arr_type": "sonarr",
            },
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Sonarr"
    assert result["data"]["host"] == "192.168.68.2"
    assert result["data"]["arr_type"] == "sonarr"


@pytest.mark.asyncio
async def test_config_flow_shows_error_on_cannot_connect(hass, enable_custom_integrations):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "custom_components.arr_suite.config_flow.ArrConfigFlow._test_connection",
        return_value=False,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "Sonarr",
                "host": "192.168.68.99",
                "port": 8989,
                "api_key": "badkey",
                "arr_type": "sonarr",
            },
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"
