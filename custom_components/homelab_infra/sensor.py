"""Sensor platform for homelab_infra."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfInformation, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import InfraCoordinator


def _device_info(entry: ConfigEntry) -> DeviceInfo:
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.data["name"],
        manufacturer="Homelab Infra",
        model=entry.data["machine_type"],
    )


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: InfraCoordinator = hass.data[DOMAIN][entry.entry_id]
    name = entry.data["name"]
    machine_type = entry.data["machine_type"]

    entities = [
        InfraPercentSensor(coordinator, entry, name, "cpu_percent", "CPU", "mdi:cpu-64-bit"),
        InfraPercentSensor(coordinator, entry, name, "ram_percent", "RAM", "mdi:memory"),
        InfraPercentSensor(coordinator, entry, name, "disk_percent", "Disk", "mdi:harddisk"),
        InfraBytesSensor(coordinator, entry, name, "network_in_bytes", "Network In", "mdi:arrow-down-network"),
        InfraBytesSensor(coordinator, entry, name, "network_out_bytes", "Network Out", "mdi:arrow-up-network"),
        InfraUptimeSensor(coordinator, entry, name),
    ]

    if "linux" in machine_type:
        entities.append(InfraLoadSensor(coordinator, entry, name))

    if "docker" in machine_type:
        entities += [
            InfraCountSensor(coordinator, entry, name, "docker_running", "Docker Running", "mdi:docker"),
            InfraCountSensor(coordinator, entry, name, "docker_stopped", "Docker Stopped", "mdi:docker"),
        ]

    async_add_entities(entities)


class InfraPercentSensor(CoordinatorEntity, SensorEntity):
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry, machine_name, key, label, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"{machine_name} {label}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_icon = icon
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key) if self.coordinator.data else None

    @property
    def available(self):
        return bool(self.coordinator.data and self.coordinator.data.get("online"))


class InfraBytesSensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DATA_SIZE
    _attr_native_unit_of_measurement = UnitOfInformation.BYTES
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, entry, machine_name, key, label, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"{machine_name} {label}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_icon = icon
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key) if self.coordinator.data else None

    @property
    def available(self):
        return bool(self.coordinator.data and self.coordinator.data.get("online"))


class InfraUptimeSensor(CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    def __init__(self, coordinator, entry, machine_name):
        super().__init__(coordinator)
        self._attr_name = f"{machine_name} Uptime"
        self._attr_unique_id = f"{entry.entry_id}_uptime_seconds"
        self._attr_icon = "mdi:clock-outline"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        return self.coordinator.data.get("uptime_seconds") if self.coordinator.data else None

    @property
    def available(self):
        return bool(self.coordinator.data and self.coordinator.data.get("online"))


class InfraLoadSensor(CoordinatorEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry, machine_name):
        super().__init__(coordinator)
        self._attr_name = f"{machine_name} Load Avg"
        self._attr_unique_id = f"{entry.entry_id}_load_avg"
        self._attr_icon = "mdi:gauge"
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        return self.coordinator.data.get("load_avg") if self.coordinator.data else None

    @property
    def available(self):
        return bool(self.coordinator.data and self.coordinator.data.get("online"))


class InfraCountSensor(CoordinatorEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry, machine_name, key, label, icon):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = f"{machine_name} {label}"
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_icon = icon
        self._attr_device_info = _device_info(entry)

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key) if self.coordinator.data else None
