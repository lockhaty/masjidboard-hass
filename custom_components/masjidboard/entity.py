"""MasjidBoardEntity class."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, CONF_FRIENDLY_NAME, DOMAIN
from .coordinator import MasjidBoardCoordinator


class MasjidBoardEntity(CoordinatorEntity[MasjidBoardCoordinator]):
    """Base entity for MasjidBoard."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(self, coordinator: MasjidBoardCoordinator) -> None:
        """Initialize."""
        super().__init__(coordinator)
        meta = coordinator.data.get("meta", {})
        friendly = (
            coordinator.config_entry.options.get(CONF_FRIENDLY_NAME, "") or ""
        ).strip()
        name = friendly if friendly else meta.get("masjid", "Unknown Masjid")
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.config_entry.entry_id)},
            name=name,
            manufacturer="MasjidBoard Live",
            model=coordinator.data.get("mbl_number"),
            configuration_url=(
                f"https://masjidboardlive.com/boards?{meta.get('web_url', '')}"
            ),
        )
