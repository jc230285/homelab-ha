"""Calendar platform for arr_suite."""
from __future__ import annotations

from datetime import datetime, timezone

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
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
    arr_type = entry.data["arr_type"]
    if arr_type == "prowlarr":
        return  # Prowlarr has no calendar
    async_add_entities([ArrCalendar(coordinator, entry, entry.data["name"])])


class ArrCalendar(CoordinatorEntity, CalendarEntity):
    def __init__(self, coordinator: ArrCoordinator, entry: ConfigEntry, name: str):
        super().__init__(coordinator)
        self._attr_name = f"{name} Upcoming"
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_device_info = _device_info(entry, name)

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        events = self._build_events()
        return events[0] if events else None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        return [
            e for e in self._build_events()
            if start_date <= e.start <= end_date
        ]

    def _build_events(self) -> list[CalendarEvent]:
        if not self.coordinator.data:
            return []
        events = []
        for item in self.coordinator.data.get("calendar", []):
            air_str = item.get("airDateUtc") or item.get("releaseDate")
            if not air_str:
                continue
            try:
                start = datetime.fromisoformat(air_str.replace("Z", "+00:00"))
            except ValueError:
                continue
            title = item.get("title", "Unknown")
            season = item.get("seasonNumber")
            episode = item.get("episodeNumber")
            if season is not None and episode is not None:
                summary = f"{title} S{season:02d}E{episode:02d}"
            else:
                summary = title
            events.append(
                CalendarEvent(
                    start=start,
                    end=start,
                    summary=summary,
                    description=f"Has file: {item.get('hasFile', False)}",
                )
            )
        events.sort(key=lambda e: e.start)
        return events
