"""Config flow for arr_suite."""
from __future__ import annotations

import aiohttp
import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN, ARR_TYPES, REQUEST_TIMEOUT, API_PATHS

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required("name"): str,
        vol.Required("host"): str,
        vol.Required("port"): int,
        vol.Required("api_key"): str,
        vol.Required("arr_type"): vol.In(ARR_TYPES),
    }
)


class ArrConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for arr_suite."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            if await self._test_connection(user_input):
                return self.async_create_entry(
                    title=user_input["name"],
                    data=user_input,
                )
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def _test_connection(self, data: dict) -> bool:
        base_path = API_PATHS[data["arr_type"]]["base"]
        url = f"http://{data['host']}:{data['port']}{base_path}/system/status"
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            ) as session:
                async with session.get(
                    url, headers={"X-Api-Key": data["api_key"]}
                ) as resp:
                    return resp.status == 200
        except Exception:
            return False
