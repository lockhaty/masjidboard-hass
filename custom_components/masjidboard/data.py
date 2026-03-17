"""Custom types for masjidboard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .api import MasjidBoardApiClient
    from .coordinator import MasjidBoardCoordinator


type MasjidBoardConfigEntry = ConfigEntry[MasjidBoardData]


@dataclass
class MasjidBoardData:
    """Data for the MasjidBoard integration."""

    client: MasjidBoardApiClient
    coordinator: MasjidBoardCoordinator
