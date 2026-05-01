"""Binary sensor platform for arr_suite."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ArrCoordinator
from .sensor import _device_info


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ArrCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ArrHealthBinarySensor(coordinator, entry, entry.data["name"])])


class ArrHealthBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """True when there are health problems (problem device class convention)."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:heart-pulse"

    def __init__(self, coordinator: ArrCoordinator, entry: ConfigEntry, name: str):
        super().__init__(coordinator)
        self._attr_name = f"{name} Health"
        self._attr_unique_id = f"{entry.entry_id}_health"
        self._attr_device_info = _device_info(entry, name)

    @property
    def is_on(self) -> bool | None:
        """True = problems detected."""
        if not self.coordinator.data:
            return None
        return not self.coordinator.data.get("health_ok", True)
