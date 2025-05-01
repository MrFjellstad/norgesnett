"""
Custom integration to integrate Norgesnett with Home Assistant.

For more details about this integration, please refer to
https://github.com/MrFjellstad/norgesnett
"""

import asyncio
import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.core_config import Config
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import NorgesnettApiClient
from .const import (
    CONF_CUSTOMER_ID,
    CONF_METERINGPOINT_ID,
    DOMAIN,
    PLATFORMS,
    STARTUP_MESSAGE,
)

SCAN_INTERVAL = timedelta(days=1)

_LOGGER: logging.Logger = logging.getLogger(__package__)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: Config):
    """Set up this integration using YAML is not supported."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up this integration using UI."""
    if hass.data.get(DOMAIN) is None:
        hass.data.setdefault(DOMAIN, {})
        _LOGGER.info(STARTUP_MESSAGE)

    customer_id = entry.data.get(CONF_CUSTOMER_ID)
    meteringpoint_id = entry.data.get(CONF_METERINGPOINT_ID)

    session = async_get_clientsession(hass)
    client = NorgesnettApiClient(customer_id, meteringpoint_id, session)

    coordinator = NorgesnettDataUpdateCoordinator(hass, client=client)
    coordinator.entry_id = entry.entry_id
    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data[DOMAIN][entry.entry_id] = coordinator

    platforms = [
        platform for platform in PLATFORMS if entry.options.get(platform, True)
    ]
    await hass.config_entries.async_forward_entry_setups(entry, platforms)

    entry.add_update_listener(async_reload_entry)
    return True


class NorgesnettDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    def __init__(
        self,
        hass: HomeAssistant,
        client: NorgesnettApiClient,
    ) -> None:
        """Initialize."""
        self.api = client
        self.platforms = []

        super().__init__(hass, _LOGGER, name=DOMAIN, update_interval=SCAN_INTERVAL)

    async def _async_update_data(self):
        """Update data via library."""

        try:
            result = await self.api.async_get_data()
            if result is None:
                raise UpdateFailed("No data received from API")
            _LOGGER.debug("Norgesnett _async_update_data, incoming result = %s", result)

            collections = result.get("gridTariffCollections") or []
            if not collections:
                raise UpdateFailed("Ingen gridTariffCollections i respons")
            return result
        except Exception as exception:
            self.logger.error(exception)
            raise UpdateFailed() from exception


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle removal of an entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    unloaded = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, platform)
                for platform in PLATFORMS
                if platform in coordinator.platforms
            ]
        )
    )
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)
