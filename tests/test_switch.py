"""Test Norgesnett switch."""

import pytest


async def test_switch_services(hass, bypass_get_data):
    """Test switch services - switch platform ikke aktivert i integrasjonen ennå."""
    # Switch er kommentert ut i PLATFORMS, så denne testen kan ikke kjøre
    # TODO: Aktiver switch platform i const.py PLATFORMS liste
    pytest.skip("Switch platform er ikke aktivert i integrasjonen")
