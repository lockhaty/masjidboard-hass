"""MasjidBoard Live API Client."""

from __future__ import annotations

import socket
from typing import Any

import aiohttp
import async_timeout

from .const import API_BASE_URL


class MasjidBoardApiClientError(Exception):
    """Exception to indicate a general API error."""


class MasjidBoardApiClientCommunicationError(MasjidBoardApiClientError):
    """Exception to indicate a communication error."""


class MasjidBoardApiClient:
    """API client for MasjidBoard Live."""

    def __init__(
        self,
        masjid_id: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the API client."""
        self._masjid_id = masjid_id
        self._session = session

    async def async_get_data(self) -> dict[str, Any]:
        """Get prayer time data for the masjid."""
        return await self._api_wrapper(
            method="get",
            url=f"{API_BASE_URL}?id={self._masjid_id}",
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Wrap API requests with error handling."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                response.raise_for_status()
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout fetching data for {self._masjid_id} - {exception}"
            raise MasjidBoardApiClientCommunicationError(msg) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching data for {self._masjid_id} - {exception}"
            raise MasjidBoardApiClientCommunicationError(msg) from exception
        except Exception as exception:
            msg = f"Unexpected error fetching data for {self._masjid_id} - {exception}"
            raise MasjidBoardApiClientError(msg) from exception
