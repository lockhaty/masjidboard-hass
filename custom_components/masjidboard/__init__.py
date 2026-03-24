"""Custom integration for MasjidBoard Live prayer times."""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import TYPE_CHECKING

from homeassistant.const import Platform
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MasjidBoardApiClient
from .const import CONF_MASJID_ID, DOMAIN, LOGGER
from .coordinator import MasjidBoardCoordinator
from .data import MasjidBoardData
from .scheduler import MasjidBoardScheduler

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import MasjidBoardConfigEntry

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
]

CARD_URL = "/masjidboard/masjidboard-prayer-times-card.js"
CARD_DIR = Path(__file__).parent / "www"


def _get_scheduler(hass: HomeAssistant) -> MasjidBoardScheduler:
    """Get or create the shared scheduler instance."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if "scheduler" not in domain_data:
        domain_data["scheduler"] = MasjidBoardScheduler(hass)
    return domain_data["scheduler"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MasjidBoardConfigEntry,
) -> bool:
    """Set up MasjidBoard from a config entry."""
    # Register the prayer times card frontend resource
    _register_card(hass)

    if CONF_MASJID_ID not in entry.data:
        # Preferences entry — no coordinator needed, just set up sensors
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
        entry.async_on_unload(entry.add_update_listener(_async_preferences_updated))
        # Reschedule reminders now that preferences exist
        _get_scheduler(hass).async_schedule()
        return True

    # Masjid entry
    coordinator = MasjidBoardCoordinator(
        hass=hass,
        logger=LOGGER,
        name=DOMAIN,
        update_interval=timedelta(hours=1),
    )
    entry.runtime_data = MasjidBoardData(
        client=MasjidBoardApiClient(
            masjid_id=entry.data[CONF_MASJID_ID],
            session=async_get_clientsession(hass),
        ),
        coordinator=coordinator,
    )

    await coordinator.async_config_entry_first_refresh()

    # Reschedule reminders whenever this coordinator updates
    coordinator.async_add_listener(lambda: _get_scheduler(hass).async_schedule())

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    # Schedule reminders with this new masjid's data
    _get_scheduler(hass).async_schedule()

    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: MasjidBoardConfigEntry,
) -> bool:
    """Handle removal of an entry."""
    result = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if CONF_MASJID_ID not in entry.data:
        # Preferences entry removed — cancel all reminders
        scheduler = hass.data.get(DOMAIN, {}).get("scheduler")
        if scheduler:
            scheduler.cancel()
    else:
        # Masjid entry removed — reschedule without it
        _get_scheduler(hass).async_schedule()

    return result


async def async_reload_entry(
    hass: HomeAssistant,
    entry: MasjidBoardConfigEntry,
) -> None:
    """Reload config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


def _register_card(hass: HomeAssistant) -> None:
    """Register the prayer times card static path."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get("card_registered"):
        return
    domain_data["card_registered"] = True

    hass.http.register_static_path(
        CARD_URL,
        str(CARD_DIR / "masjidboard-prayer-times-card.js"),
        cache_headers=True,
    )
    LOGGER.debug("Registered MasjidBoard prayer times card at %s", CARD_URL)


async def _async_preferences_updated(
    hass: HomeAssistant,
    entry: MasjidBoardConfigEntry,  # noqa: ARG001
) -> None:
    """Handle preferences options update."""
    _get_scheduler(hass).async_schedule()
