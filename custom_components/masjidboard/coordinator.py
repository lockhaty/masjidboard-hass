"""DataUpdateCoordinator for masjidboard."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    MasjidBoardApiClientCommunicationError,
    MasjidBoardApiClientError,
)

if TYPE_CHECKING:
    from .data import MasjidBoardConfigEntry


class MasjidBoardCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Manage fetching prayer time data from MasjidBoard Live."""

    config_entry: MasjidBoardConfigEntry

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the API."""
        try:
            response = await self.config_entry.runtime_data.client.async_get_data()
        except MasjidBoardApiClientCommunicationError as exception:
            raise UpdateFailed(exception) from exception
        except MasjidBoardApiClientError as exception:
            raise UpdateFailed(exception) from exception

        if not response.get("ok"):
            msg = "MasjidBoard API returned an error response"
            raise UpdateFailed(msg)

        return response.get("data", {})
