"""Sensor platform for arr_suite."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ArrCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ArrCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data["name"]
    arr_type = entry.data["arr_type"]

    entities: list[SensorEntity] = [
        ArrStatusSensor(coordinator, entry, name),
        ArrHealthMessageSensor(coordinator, entry, name),
    ]

    if arr_type in ("sonarr", "radarr", "lidarr"):
        entities += [
            ArrCountSensor(coordinator, entry, name, "queue_count", "Queue", "mdi:download"),
            ArrCountSensor(coordinator, entry, name, "wanted_count", "Wanted", "mdi:alert-circle"),
            ArrCountSensor(coordinator, entry, name, "missing_count", "Missing (cutoff)", "mdi:movie-remove"),
        ]
    elif arr_type == "prowlarr":
        entities += [
            ArrCountSensor(coordinator, entry, name, "indexer_count", "Indexers", "mdi:magnify"),
            ArrCountSensor(coordinator, entry, name, "history_total", "History Total", "mdi:history"),
        ]

    async_add_entities(entities)


def _device_info(entry: ConfigEntry, name: str) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=name,
        manufacturer="Arr Suite",
        model=entry.data["arr_type"].capitalize(),
    )


class ArrStatusSensor(CoordinatorEntity, SensorEntity):
    _attr_icon = "mdi:check-circle"

    def __init__(self, coordinator: ArrCoordinator, entry: ConfigEntry, name: str):
        super().__init__(coordinator)
        self._attr_name = f"{name} Status"
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_device_info = _device_info(entry, name)

    @property
    def native_value(self):
        return self.coordinator.data.get("status") if self.coordinator.data else None


class ArrCountSensor(CoordinatorEntity, SensorEntity):
    _attr_native_unit_of_measurement = "items"

    def __init__(
        self,
        coordinator: ArrCoordinator,
        entry: ConfigEntry,
        name: str,
        data_key: str,
        label: str,
        icon: str,
    ):
        super().__init__(coordinator)
        self._data_key = data_key
        self._attr_name = f"{name} {label}"
        self._attr_unique_id = f"{entry.entry_id}_{data_key}"
        self._attr_icon = icon
        self._attr_device_info = _device_info(entry, name)

    @property
    def native_value(self):
        return self.coordinator.data.get(self._data_key) if self.coordinator.data else None


class ArrHealthMessageSensor(CoordinatorEntity, SensorEntity):
    _attr_icon = "mdi:stethoscope"

    def __init__(self, coordinator: ArrCoordinator, entry: ConfigEntry, name: str):
        super().__init__(coordinator)
        self._attr_name = f"{name} Health Message"
        self._attr_unique_id = f"{entry.entry_id}_health_message"
        self._attr_device_info = _device_info(entry, name)

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        issues = self.coordinator.data.get("health_issues", [])
        if not issues:
            return "OK"
        return issues[0]["message"]

    @property
    def extra_state_attributes(self):
        if not self.coordinator.data:
            return {}
        return {"issues": self.coordinator.data.get("health_issues", [])}
