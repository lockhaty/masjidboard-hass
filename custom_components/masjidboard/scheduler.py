"""Prayer reminder scheduler for MasjidBoard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.core import callback
from homeassistant.helpers.event import async_track_point_in_time
from homeassistant.util import dt as dt_util

from .const import (
    CONF_ANNOUNCEMENTS_ENABLED,
    CONF_DEVICE_TRACKER,
    CONF_FRIENDLY_NAME,
    CONF_MASJID_ID,
    CONF_PREFERRED_MASJID,
    CONF_TRAVEL_TIME,
    CONF_TTS_NAME,
    DEFAULT_TRAVEL_TIME,
    DEFAULT_TTS_PRAYERS,
    DOMAIN,
    LOGGER,
    PRAYER_SCHEDULE,
    PREF_DISABLED,
    PREF_EARLIEST,
    PREF_LATEST,
    PREF_PREFERRED,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant

EVENT_PRAYER_REMINDER = "masjidboard_prayer_reminder"


@dataclass
class ResolvedPrayer:
    """Result of resolving which masjid to use for a prayer."""

    entry: ConfigEntry
    time_str: str
    travel_time: int


def _get_masjid_entries(hass: HomeAssistant) -> list[ConfigEntry]:
    """Get all masjid config entries with loaded runtime data."""
    return [
        entry
        for entry in hass.config_entries.async_entries(DOMAIN)
        if CONF_MASJID_ID in entry.data and hasattr(entry, "runtime_data")
    ]


def _get_prayer_time(entry: ConfigEntry, api_key: str) -> str | None:
    """Get a prayer time string from a masjid entry's coordinator data."""
    value = entry.runtime_data.coordinator.data.get(api_key)
    if isinstance(value, str) and value.strip() not in ("", "&nbsp;"):
        return value
    return None


def get_masjid_name(entry: ConfigEntry) -> str:
    """Get the masjid display name, preferring the user-set friendly name."""
    friendly = (entry.options.get(CONF_FRIENDLY_NAME, "") or "").strip()
    if friendly:
        return friendly
    meta = entry.runtime_data.coordinator.data.get("meta", {})
    return meta.get("masjid", entry.title)


def get_masjid_tts_name(entry: ConfigEntry) -> str:
    """Get the masjid TTS name, falling back to friendly name then API name."""
    tts = (entry.options.get(CONF_TTS_NAME, "") or "").strip()
    if tts:
        return tts
    return get_masjid_name(entry)


def _get_tts_prayer_name(prefs_entry: ConfigEntry | None, prayer_name: str) -> str:
    """Get the TTS pronunciation for a prayer name from preferences."""
    if prefs_entry:
        key = f"tts_{prayer_name.lower()}"
        val = (prefs_entry.options.get(key, "") or "").strip()
        if val:
            return val
    return DEFAULT_TTS_PRAYERS.get(prayer_name, prayer_name)


def resolve_masjid_for_prayer(
    hass: HomeAssistant,
    api_key: str,
    preference: str,
    preferred_entry_id: str | None,
) -> ResolvedPrayer | None:
    """Resolve which masjid to use for a prayer based on preference."""
    masjid_entries = _get_masjid_entries(hass)

    if preference == PREF_DISABLED:
        return None

    if preference == PREF_PREFERRED:
        return _resolve_preferred(masjid_entries, api_key, preferred_entry_id)

    if preference in (PREF_EARLIEST, PREF_LATEST):
        return _resolve_earliest_or_latest(masjid_entries, api_key, preference)

    # Specific masjid entry ID — use it directly as the preferred
    return _resolve_preferred(masjid_entries, api_key, preference)


def _resolve_preferred(
    entries: list[ConfigEntry],
    api_key: str,
    preferred_entry_id: str | None,
) -> ResolvedPrayer | None:
    """Resolve using the preferred masjid."""
    for entry in entries:
        if entry.entry_id != preferred_entry_id:
            continue
        if not entry.options.get(CONF_ANNOUNCEMENTS_ENABLED, True):
            return None
        time_val = _get_prayer_time(entry, api_key)
        if time_val is None:
            return None
        travel = int(entry.options.get(CONF_TRAVEL_TIME, DEFAULT_TRAVEL_TIME))
        return ResolvedPrayer(entry=entry, time_str=time_val, travel_time=travel)
    return None


def _resolve_earliest_or_latest(
    entries: list[ConfigEntry],
    api_key: str,
    preference: str,
) -> ResolvedPrayer | None:
    """Resolve using earliest or latest time across enabled masjids."""
    candidates: list[ResolvedPrayer] = []
    for entry in entries:
        if not entry.options.get(CONF_ANNOUNCEMENTS_ENABLED, True):
            continue
        time_val = _get_prayer_time(entry, api_key)
        if time_val is not None:
            travel = int(entry.options.get(CONF_TRAVEL_TIME, DEFAULT_TRAVEL_TIME))
            candidates.append(
                ResolvedPrayer(entry=entry, time_str=time_val, travel_time=travel)
            )

    if not candidates:
        return None

    if preference == PREF_EARLIEST:
        return min(candidates, key=lambda x: x.time_str)
    return max(candidates, key=lambda x: x.time_str)


class MasjidBoardScheduler:
    """Schedule prayer reminder events."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the scheduler."""
        self._hass = hass
        self._cancel_callbacks: list[Callable[[], None]] = []
        self._scheduled_reminders: list[dict[str, Any]] = []

    @property
    def scheduled_reminders(self) -> list[dict[str, Any]]:
        """Return the list of currently scheduled reminders."""
        return list(self._scheduled_reminders)

    def async_schedule(self) -> None:
        """Recalculate and schedule all reminder events for today."""
        self._cancel_all()
        self._scheduled_reminders.clear()

        prefs_entry = self._get_preferences_entry()
        if not prefs_entry:
            return

        preferred_id = prefs_entry.options.get(CONF_PREFERRED_MASJID)
        device_tracker = (
            prefs_entry.options.get(CONF_DEVICE_TRACKER) or ""
        ).strip()
        now = dt_util.now()

        for prayer_name, api_key, pref_key in PRAYER_SCHEDULE:
            preference = prefs_entry.options.get(pref_key, PREF_PREFERRED)
            result = resolve_masjid_for_prayer(
                self._hass, api_key, preference, preferred_id
            )
            if result is None:
                continue

            tts_prayer = _get_tts_prayer_name(prefs_entry, prayer_name)
            reminder_dt = self._parse_reminder_time(
                now, result.time_str, result.travel_time
            )

            # Schedule primary reminder if leave-by time is still in the future
            if reminder_dt is not None and reminder_dt > now:
                self._schedule_event(
                    reminder_dt=reminder_dt,
                    event_data={
                        "prayer": prayer_name,
                        "masjid_name": get_masjid_name(result.entry),
                        "masjid_id": result.entry.data.get(CONF_MASJID_ID, ""),
                        "prayer_time": result.time_str,
                        "travel_time": result.travel_time,
                        "leave_by": reminder_dt.strftime("%H:%M"),
                        "tts_masjid_name": get_masjid_tts_name(result.entry),
                        "tts_prayer": tts_prayer,
                        "is_fallback": False,
                    },
                )

            # Schedule fallback check at prayer time if device tracker is set
            if device_tracker:
                prayer_dt = self._parse_reminder_time(now, result.time_str, 0)
                if prayer_dt is not None and prayer_dt > now:
                    self._schedule_fallback_check(
                        prayer_dt=prayer_dt,
                        prayer_name=prayer_name,
                        api_key=api_key,
                        original_entry_id=result.entry.entry_id,
                        device_tracker=device_tracker,
                        prefs_entry=prefs_entry,
                    )

        LOGGER.debug("Scheduled %d prayer reminders", len(self._cancel_callbacks))

    def cancel(self) -> None:
        """Cancel all scheduled events."""
        self._cancel_all()

    def _cancel_all(self) -> None:
        """Cancel all pending callbacks."""
        for cancel in self._cancel_callbacks:
            cancel()
        self._cancel_callbacks.clear()

    def _get_preferences_entry(self) -> ConfigEntry | None:
        """Find the preferences config entry."""
        for entry in self._hass.config_entries.async_entries(DOMAIN):
            if CONF_MASJID_ID not in entry.data:
                return entry
        return None

    @staticmethod
    def _parse_reminder_time(
        now: datetime,
        time_str: str,
        travel_minutes: int,
    ) -> datetime | None:
        """Parse HH:MM time string and subtract travel time."""
        try:
            parts = time_str.strip().split(":")
            hour, minute = int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            return None
        prayer_dt = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return prayer_dt - timedelta(minutes=travel_minutes)

    def _find_fallback_masjid(
        self,
        api_key: str,
        original_entry_id: str,
        now: datetime,
    ) -> ResolvedPrayer | None:
        """Find the next masjid with a later jamaah for the same prayer."""
        now_time = now.strftime("%H:%M")
        candidates: list[ResolvedPrayer] = []

        for entry in _get_masjid_entries(self._hass):
            if entry.entry_id == original_entry_id:
                continue
            if not entry.options.get(CONF_ANNOUNCEMENTS_ENABLED, True):
                continue
            time_val = _get_prayer_time(entry, api_key)
            if time_val is None or time_val <= now_time:
                continue
            travel = int(entry.options.get(CONF_TRAVEL_TIME, DEFAULT_TRAVEL_TIME))
            candidates.append(
                ResolvedPrayer(entry=entry, time_str=time_val, travel_time=travel)
            )

        if not candidates:
            return None
        return min(candidates, key=lambda x: x.time_str)

    def _schedule_fallback_check(
        self,
        prayer_dt: datetime,
        prayer_name: str,
        api_key: str,
        original_entry_id: str,
        device_tracker: str,
        prefs_entry: ConfigEntry,
    ) -> None:
        """Schedule a device-tracker check at prayer time for fallback."""

        @callback
        def _check_fallback(_now: datetime) -> None:
            state = self._hass.states.get(device_tracker)
            if state is None or state.state != "home":
                return

            fallback = self._find_fallback_masjid(
                api_key, original_entry_id, _now
            )
            if fallback is None:
                return

            leave_dt = self._parse_reminder_time(
                _now, fallback.time_str, fallback.travel_time
            )
            leave_by = (
                leave_dt.strftime("%H:%M") if leave_dt else fallback.time_str
            )

            LOGGER.debug(
                "Device still home — fallback reminder: %s at %s",
                prayer_name,
                get_masjid_name(fallback.entry),
            )
            self._hass.bus.async_fire(
                EVENT_PRAYER_REMINDER,
                {
                    "prayer": prayer_name,
                    "masjid_name": get_masjid_name(fallback.entry),
                    "masjid_id": fallback.entry.data.get(CONF_MASJID_ID, ""),
                    "prayer_time": fallback.time_str,
                    "travel_time": fallback.travel_time,
                    "leave_by": leave_by,
                    "tts_masjid_name": get_masjid_tts_name(fallback.entry),
                    "tts_prayer": _get_tts_prayer_name(prefs_entry, prayer_name),
                    "is_fallback": True,
                },
            )

        cancel = async_track_point_in_time(self._hass, _check_fallback, prayer_dt)
        self._cancel_callbacks.append(cancel)

    def _schedule_event(
        self,
        reminder_dt: datetime,
        event_data: dict[str, Any],
    ) -> None:
        """Schedule a single reminder event."""

        @callback
        def _fire_event(_now: datetime) -> None:
            LOGGER.debug(
                "Firing prayer reminder: %s at %s",
                event_data["prayer"],
                event_data["masjid_name"],
            )
            self._hass.bus.async_fire(EVENT_PRAYER_REMINDER, event_data)

        cancel = async_track_point_in_time(self._hass, _fire_event, reminder_dt)
        self._cancel_callbacks.append(cancel)
        self._scheduled_reminders.append(
            {**event_data, "reminder_at": reminder_dt.isoformat()}
        )
