"""Binary sensor platform for homelab_infra."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import InfraCoordinator
from .sensor import _device_info


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: InfraCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([InfraOnlineSensor(coordinator, entry, entry.data["name"])])


class InfraOnlineSensor(CoordinatorEntity, BinarySensorEntity):
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_icon = "mdi:server-network"

    def __init__(self, coordinator: InfraCoordinator, entry: ConfigEntry, name: str):
        super().__init__(coordinator)
        self._attr_name = f"{name} Online"
        self._attr_unique_id = f"{entry.entry_id}_online"
        self._attr_device_info = _device_info(entry)

    @property
    def is_on(self) -> bool | None:
        if not self.coordinator.data:
            return None
        return self.coordinator.data.get("online", False)
