"""Test Norgesnett setup process."""

import importlib
import sys
import types
from unittest.mock import AsyncMock, patch

import pytest
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

import custom_components.norgesnett as norgesnett_module
from custom_components.norgesnett import (
    NorgesnettDataUpdateCoordinator,
    async_reload_entry,
    async_setup_entry,
    async_unload_entry,
)
from custom_components.norgesnett.const import DOMAIN

from .const import MOCK_CONFIG


# We can pass fixtures as defined in conftest.py to tell pytest to use the fixture
# for a given test. We can also leverage fixtures and mocks that are available in
# Home Assistant using the pytest_homeassistant_custom_component plugin.
# Assertions allow you to verify that the return value of whatever is on the left
# side of the assertion matches with the right side.
async def test_setup_unload_and_reload_entry(hass, bypass_get_data):
    """Test entry setup and unload."""
    # Create a mock entry so we don't have to go through config flow
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")
    config_entry.add_to_hass(hass)

    # Set up the entry and assert that the values set during setup are where we expect
    # them to be. Because we have patched the NorgesnettDataUpdateCoordinator.async_get_data
    # call, no code from custom_components/norgesnett/api.py actually runs.
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
    assert (
        type(hass.data[DOMAIN][config_entry.entry_id])
        is NorgesnettDataUpdateCoordinator
    )

    # Reload the entry and assert that the data from above is still there
    assert await async_reload_entry(hass, config_entry) is None
    assert DOMAIN in hass.data and config_entry.entry_id in hass.data[DOMAIN]
    assert (
        type(hass.data[DOMAIN][config_entry.entry_id])
        is NorgesnettDataUpdateCoordinator
    )

    # Unload the entry and verify that the data has been removed
    assert await async_unload_entry(hass, config_entry)
    assert config_entry.entry_id not in hass.data[DOMAIN]


async def test_setup_entry_exception(hass, error_on_get_data):
    """Test ConfigEntryNotReady when API raises an exception during entry setup."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=MOCK_CONFIG, entry_id="test")

    # In this case we are testing the condition where async_setup_entry raises
    # ConfigEntryNotReady using the `error_on_get_data` fixture which simulates
    # an error.
    with pytest.raises(ConfigEntryNotReady):
        assert await async_setup_entry(hass, config_entry)


async def test_coordinator_update_data_raises_on_none(hass):
    """Test coordinator raises UpdateFailed when API returns None."""
    client = types.SimpleNamespace(async_get_data=AsyncMock(return_value=None))
    coordinator = NorgesnettDataUpdateCoordinator(hass, client=client)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


async def test_coordinator_update_data_raises_on_missing_collections(hass):
    """Test coordinator raises UpdateFailed on missing collections."""
    client = types.SimpleNamespace(
        async_get_data=AsyncMock(return_value={"gridTariffCollections": []})
    )
    coordinator = NorgesnettDataUpdateCoordinator(hass, client=client)

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


def test_module_reload_config_import_fallback_branch():
    """Test module fallback branch importing Config from homeassistant.core."""
    with patch("importlib.util.find_spec", return_value=None):
        with patch("homeassistant.core.Config", object, create=True):
            reloaded = importlib.reload(norgesnett_module)
            assert reloaded is not None


def test_module_reload_config_import_primary_branch():
    """Test module primary branch importing Config from homeassistant.core_config."""
    fake_core_config = types.ModuleType("homeassistant.core_config")
    fake_core_config.Config = object

    with patch("importlib.util.find_spec", return_value=object()):
        with patch.dict(
            sys.modules,
            {"homeassistant.core_config": fake_core_config},
            clear=False,
        ):
            reloaded = importlib.reload(norgesnett_module)
            assert reloaded is not None

    importlib.reload(norgesnett_module)


def test_module_reload_config_schema_fallback_branch():
    """Test module fallback branch building CONFIG_SCHEMA with vol.Schema."""
    import homeassistant.helpers as ha_helpers

    real_cv = sys.modules["homeassistant.helpers.config_validation"]
    fake_cv = types.ModuleType("homeassistant.helpers.config_validation")

    with patch.object(ha_helpers, "config_validation", fake_cv, create=True):
        with patch.dict(
            sys.modules,
            {"homeassistant.helpers.config_validation": fake_cv},
            clear=False,
        ):
            reloaded = importlib.reload(norgesnett_module)
            assert reloaded.CONFIG_SCHEMA is not None

    with patch.dict(
        sys.modules,
        {"homeassistant.helpers.config_validation": real_cv},
        clear=False,
    ):
        importlib.reload(norgesnett_module)
