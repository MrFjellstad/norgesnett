"""Sample API Client."""

import asyncio
import logging
import socket
from datetime import datetime

import aiohttp
import async_timeout

from .const import API_AUTH_URL, API_TARIFFS_URL

TIMEOUT = 10

_LOGGER: logging.Logger = logging.getLogger(__package__)

HEADERS = {"Content-type": "application/json; charset=UTF-8"}


class NorgesnettApiClient:
    def __init__(
        self, customer_id: str, meteringpoint_id: str, session: aiohttp.ClientSession
    ) -> None:
        """Sample API Client."""
        self._customer_id = customer_id
        self._meteringpoint_id = meteringpoint_id
        self._session = session

    async def async_get_auth(self) -> dict:
        """Get data from the API."""
        url = API_AUTH_URL
        auth_info = await self.api_wrapper(
            "post",
            url,
            {
                "customerId": self._customer_id,
                "meteringPointId": self._meteringpoint_id,
            },
        )
        apiKey = auth_info["apiKey"]
        _LOGGER.debug("apiKey:", apiKey)
        return auth_info

    async def async_get_data(self) -> dict:
        """Get data from the API."""
        url = API_AUTH_URL
        auth_info = await self.api_wrapper(
            "post",
            url,
            data={
                "customerId": self._customer_id,
                "meteringPointId": self._meteringpoint_id,
            },
            headers=HEADERS,
        )
        apiKey = auth_info["apiKey"]
        headers = {
            "X-API-Key": apiKey,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        now = datetime.now()
        iso_string = now.replace(microsecond=0).isoformat()
        # Get the tariff data
        request = {
            "range": "today",
            "startTime": iso_string,
            "endTime": iso_string,
            "meteringPointIds": [self._meteringpoint_id],
        }
        url = API_TARIFFS_URL
        tariffs = await self.api_wrapper("post", url, data=request, headers=headers)
        return tariffs

    # async def async_set_title(self, value: str) -> None:
    #     """Get data from the API."""
    #     url = "https://jsonplaceholder.typicode.com/posts/1"
    #     await self.api_wrapper("patch", url, data={"title": value}, headers=HEADERS)

    async def api_wrapper(
        self, method: str, url: str, data: dict = {}, headers: dict = {}
    ) -> dict:
        """Get information from the API."""
        _LOGGER.info("api_wrapper: %s %s", method, url)
        data = {} if data is None else data
        headers = {} if headers is None else headers
        try:
            async with async_timeout.timeout(TIMEOUT):
                if method == "get":
                    response = await self._session.get(url, headers=headers)
                    response.raise_for_status()
                    return await response.json()

                elif method == "put":
                    response = await self._session.put(url, headers=headers, json=data)
                    response.raise_for_status()
                    return await response.json()

                elif method == "patch":
                    response = await self._session.patch(
                        url, headers=headers, json=data
                    )
                    response.raise_for_status()
                    return await response.json()

                elif method == "post":
                    response = await self._session.post(url, headers=headers, json=data)
                    response.raise_for_status()
                    return await response.json()

        except asyncio.TimeoutError as exception:
            _LOGGER.error(
                "Timeout error fetching information from %s - %s",
                url,
                exception,
            )

        except (KeyError, TypeError) as exception:
            _LOGGER.error(
                "Error parsing information from %s - %s",
                url,
                exception,
            )
        except (aiohttp.ClientError, socket.gaierror) as exception:
            _LOGGER.error(
                "Error fetching information from %s - %s",
                url,
                exception,
            )
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error("Something really wrong happened! - %s", exception)
