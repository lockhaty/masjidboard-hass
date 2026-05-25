"""Sensor platform for masjidboard."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.helpers.device_registry import DeviceInfo

from .const import (
    CONF_MASJID_ID,
    CONF_PREFERRED_MASJID,
    CONF_TRAVEL_TIME,
    DEFAULT_TRAVEL_TIME,
    DOMAIN,
    LOGGER,
    PRAYER_SCHEDULE,
    PREF_DISABLED,
    PREF_PREFERRED,
)
from .entity import MasjidBoardEntity
from .scheduler import get_masjid_name, resolve_masjid_for_prayer

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import MasjidBoardCoordinator
    from .data import MasjidBoardConfigEntry

SENSOR_DESCRIPTIONS: tuple[SensorEntityDescription, ...] = (
    # Fajr
    SensorEntityDescription(
        key="sehriEnds",
        name="Sehri Ends",
        translation_key="sehri_ends",
        icon="mdi:food-halal",
    ),
    SensorEntityDescription(
        key="fajrAthan",
        name="Fajr Athan",
        translation_key="fajr_athan",
        icon="mdi:mosque",
    ),
    SensorEntityDescription(
        key="fajrJamaah",
        name="Fajr Jamaah",
        translation_key="fajr_jamaah",
        icon="mdi:mosque",
    ),
    # Morning
    SensorEntityDescription(
        key="sunrise",
        name="Sunrise",
        translation_key="sunrise",
        icon="mdi:weather-sunny",
    ),
    SensorEntityDescription(
        key="ishraaq",
        name="Ishraaq",
        translation_key="ishraaq",
        icon="mdi:weather-sunny",
    ),
    # Dhuhr
    SensorEntityDescription(
        key="dhuhrAthan",
        name="Dhuhr Athan",
        translation_key="dhuhr_athan",
        icon="mdi:mosque",
    ),
    SensorEntityDescription(
        key="dhuhrJamaah",
        name="Dhuhr Jamaah",
        translation_key="dhuhr_jamaah",
        icon="mdi:mosque",
    ),
    # Jumuah
    SensorEntityDescription(
        key="jumuahTime1",
        name="Jumuah 1",
        translation_key="jumuah_time_1",
        icon="mdi:mosque",
    ),
    SensorEntityDescription(
        key="jumuahTime2",
        name="Jumuah 2",
        translation_key="jumuah_time_2",
        icon="mdi:mosque",
    ),
    SensorEntityDescription(
        key="jumuahTime3",
        name="Jumuah 3",
        translation_key="jumuah_time_3",
        icon="mdi:mosque",
    ),
    # Asr
    SensorEntityDescription(
        key="asrShafi",
        name="Asr Start (Shafi)",
        translation_key="asr_shafi",
        icon="mdi:weather-sunset-down",
    ),
    SensorEntityDescription(
        key="asrHanafi",
        name="Asr Start (Hanafi)",
        translation_key="asr_hanafi",
        icon="mdi:weather-sunset-down",
    ),
    SensorEntityDescription(
        key="asrAthan",
        name="Asr Athan",
        translation_key="asr_athan",
        icon="mdi:mosque",
    ),
    SensorEntityDescription(
        key="asrJamaah",
        name="Asr Jamaah",
        translation_key="asr_jamaah",
        icon="mdi:mosque",
    ),
    # Maghrib
    SensorEntityDescription(
        key="sunset",
        name="Sunset",
        translation_key="sunset",
        icon="mdi:weather-sunset",
    ),
    SensorEntityDescription(
        key="maghribAthan",
        name="Maghrib Athan",
        translation_key="maghrib_athan",
        icon="mdi:mosque",
    ),
    SensorEntityDescription(
        key="maghribJamaah",
        name="Maghrib Jamaah",
        translation_key="maghrib_jamaah",
        icon="mdi:mosque",
    ),
    # Esha
    SensorEntityDescription(
        key="eshaAthan",
        name="Esha Athan",
        translation_key="esha_athan",
        icon="mdi:mosque",
    ),
    SensorEntityDescription(
        key="eshaJamaah",
        name="Esha Jamaah",
        translation_key="esha_jamaah",
        icon="mdi:mosque",
    ),
)


def _get_next_prayer(data: dict[str, Any]) -> tuple[str, str] | None:
    """Return (prayer_name, time_str) for the next upcoming prayer, or None."""
    now_time = datetime.now().strftime("%H:%M")  # noqa: DTZ005
    for prayer_name, key, _pref_key in PRAYER_SCHEDULE:
        value = data.get(key)
        if not isinstance(value, str) or value.strip() in ("", "&nbsp;"):
            continue
        if value > now_time:
            return (prayer_name, value)
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MasjidBoardConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MasjidBoard sensors."""
    if CONF_MASJID_ID not in entry.data:
        # Preferences entry — add recommended mosque sensor + scheduled reminders
        async_add_entities([
            RecommendedMosqueSensor(hass, entry),
            ScheduledRemindersSensor(hass, entry),
        ])
        return

    # Masjid entry — add prayer time sensors + next prayer
    coordinator = entry.runtime_data.coordinator
    entities: list[MasjidBoardEntity] = [
        MasjidBoardSensor(
            coordinator=coordinator,
            entity_description=description,
        )
        for description in SENSOR_DESCRIPTIONS
    ]
    entities.append(MasjidBoardNextPrayerSensor(coordinator=coordinator))
    async_add_entities(entities)


class MasjidBoardSensor(MasjidBoardEntity, SensorEntity):
    """Sensor for a masjid prayer time."""

    def __init__(
        self,
        coordinator: MasjidBoardCoordinator,
        entity_description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = entity_description
        self._attr_unique_id = (
            f"{coordinator.config_entry.entry_id}_{entity_description.key}"
        )

    @property
    def native_value(self) -> str | None:
        """Return the prayer time value."""
        value = self.coordinator.data.get(self.entity_description.key)
        if not value or not isinstance(value, str) or value.strip() in ("", "&nbsp;"):
            return None
        return value


class MasjidBoardNextPrayerSensor(MasjidBoardEntity, SensorEntity):
    """Sensor showing the next upcoming prayer for this masjid."""

    _attr_name = "Next Prayer"
    _attr_translation_key = "next_prayer"
    _attr_icon = "mdi:mosque"

    def __init__(self, coordinator: MasjidBoardCoordinator) -> None:
        """Initialize the next prayer sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_next_prayer"

    @property
    def native_value(self) -> str | None:
        """Return the name of the next prayer."""
        result = _get_next_prayer(self.coordinator.data)
        if result is None:
            return "Fajr (Tomorrow)"
        return result[0]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        travel_time = self.coordinator.config_entry.options.get(
            CONF_TRAVEL_TIME, DEFAULT_TRAVEL_TIME
        )
        result = _get_next_prayer(self.coordinator.data)
        if result is None:
            fajr_time = self.coordinator.data.get("fajrJamaah")
            return {
                "time": fajr_time if isinstance(fajr_time, str) else None,
                "travel_time": travel_time,
            }
        return {
            "time": result[1],
            "travel_time": travel_time,
        }


class RecommendedMosqueSensor(SensorEntity):
    """Cross-masjid sensor showing the recommended mosque for the next prayer."""

    _attr_name = "Recommended Mosque"
    _attr_translation_key = "recommended"
    _attr_icon = "mdi:mosque"
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: MasjidBoardConfigEntry,
    ) -> None:
        """Initialize the recommended mosque sensor."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_recommended"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="MasjidBoard Preferences",
            manufacturer="MasjidBoard Live",
        )
        self._unsub_listeners: list = []

    async def async_added_to_hass(self) -> None:
        """Subscribe to all masjid coordinator updates."""
        self._subscribe_to_coordinators()

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from coordinator updates."""
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()

    def _subscribe_to_coordinators(self) -> None:
        """Subscribe to all masjid coordinators for updates."""
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()

        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if CONF_MASJID_ID in entry.data and hasattr(entry, "runtime_data"):
                unsub = entry.runtime_data.coordinator.async_add_listener(
                    self.async_write_ha_state
                )
                self._unsub_listeners.append(unsub)

    def _resolve_next(self) -> tuple[str, Any, str, int] | None:
        """Resolve the recommended masjid for the next prayer."""
        preferred_id = self._entry.options.get(CONF_PREFERRED_MASJID)
        now_time = datetime.now().strftime("%H:%M")  # noqa: DTZ005

        for prayer_name, api_key, pref_key in PRAYER_SCHEDULE:
            preference = self._entry.options.get(pref_key, PREF_PREFERRED)
            if preference == PREF_DISABLED:
                continue

            resolved = resolve_masjid_for_prayer(
                self.hass, api_key, preference, preferred_id
            )
            if resolved is None:
                continue

            if resolved.time_str > now_time:
                masjid_name = get_masjid_name(resolved.entry)
                return (
                    prayer_name,
                    masjid_name,
                    resolved.time_str,
                    resolved.travel_time,
                )

        return None

    @property
    def native_value(self) -> str | None:
        """Return the recommended mosque and prayer."""
        result = self._resolve_next()
        if result is None:
            return None
        prayer_name, masjid_name, _time, _travel = result
        return f"{prayer_name} at {masjid_name}"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed attributes."""
        result = self._resolve_next()
        if result is None:
            return {}
        prayer_name, masjid_name, time_str, travel_time = result
        try:
            parts = time_str.strip().split(":")
            hour, minute = int(parts[0]), int(parts[1])
            now = datetime.now()  # noqa: DTZ005
            prayer_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            leave_dt = prayer_dt - timedelta(minutes=travel_time)
            leave_by = leave_dt.strftime("%H:%M")
        except (ValueError, IndexError):
            leave_by = None
        return {
            "prayer": prayer_name,
            "masjid_name": masjid_name,
            "prayer_time": time_str,
            "travel_time": travel_time,
            "leave_by": leave_by,
        }


class ScheduledRemindersSensor(SensorEntity):
    """Sensor exposing currently scheduled prayer reminders."""

    _attr_name = "Scheduled Reminders"
    _attr_icon = "mdi:bell-ring-outline"
    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: MasjidBoardConfigEntry,
    ) -> None:
        """Initialize the scheduled reminders sensor."""
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_scheduled_reminders"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="MasjidBoard Preferences",
            manufacturer="MasjidBoard Live",
        )
        self._unsub_listeners: list = []

    async def async_added_to_hass(self) -> None:
        """Subscribe to all masjid coordinator updates."""
        self._subscribe_to_coordinators()

    async def async_will_remove_from_hass(self) -> None:
        """Unsubscribe from coordinator updates."""
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()

    def _subscribe_to_coordinators(self) -> None:
        """Subscribe to all masjid coordinators for updates."""
        for unsub in self._unsub_listeners:
            unsub()
        self._unsub_listeners.clear()

        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if CONF_MASJID_ID in entry.data and hasattr(entry, "runtime_data"):
                unsub = entry.runtime_data.coordinator.async_add_listener(
                    self.async_write_ha_state
                )
                self._unsub_listeners.append(unsub)

    def _get_scheduler(self):
        """Get the scheduler instance."""
        return self.hass.data.get(DOMAIN, {}).get("scheduler")

    @property
    def native_value(self) -> str | None:
        """Return the count of scheduled reminders."""
        scheduler = self._get_scheduler()
        if scheduler is None:
            return "0"
        return str(len(scheduler.scheduled_reminders))

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the list of scheduled reminders."""
        scheduler = self._get_scheduler()
        if scheduler is None:
            return {"reminders": []}
        return {"reminders": scheduler.scheduled_reminders}
