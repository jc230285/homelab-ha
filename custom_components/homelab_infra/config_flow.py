"""Config flow for homelab_infra."""
from __future__ import annotations

import aiohttp
import voluptuous as vol
from homeassistant import config_entries

from .const import (
    DOMAIN, MACHINE_TYPES, REQUEST_TIMEOUT,
    DEFAULT_NODE_EXPORTER_PORT_LINUX, DEFAULT_NODE_EXPORTER_PORT_WINDOWS,
)

STEP_SCHEMA = vol.Schema({
    vol.Required("name"): str,
    vol.Required("host"): str,
    vol.Required("machine_type"): vol.In(MACHINE_TYPES),
    vol.Required("node_exporter_port", default=DEFAULT_NODE_EXPORTER_PORT_LINUX): int,
    vol.Optional("coolify_url", default=""): str,
    vol.Optional("coolify_api_key", default=""): str,
})


class InfraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            if await self._test_node_exporter(user_input):
                return self.async_create_entry(title=user_input["name"], data=user_input)
            errors["base"] = "cannot_connect"

        return self.async_show_form(step_id="user", data_schema=STEP_SCHEMA, errors=errors)

    async def _test_node_exporter(self, data: dict) -> bool:
        url = f"http://{data['host']}:{data['node_exporter_port']}/metrics"
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT)
            ) as session:
                async with session.get(url) as resp:
                    return resp.status == 200
        except Exception:
            return False
