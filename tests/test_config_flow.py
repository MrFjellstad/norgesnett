"""Tests for config_flow of Norgesnett integration."""

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import RESULT_TYPE_CREATE_ENTRY, RESULT_TYPE_FORM

import custom_components.norgesnett.config_flow as config_flow
from custom_components.norgesnett.const import (
    CONF_CUSTOMER_ID,
    CONF_METERINGPOINT_ID,
    DOMAIN,
)


class DummyFlow(config_flow.NorgesnettFlowHandler):
    """Subclass to override credentials test and entry creation."""

    def __init__(self):
        super().__init__()
        self._errors = {}
        self.created = False

    async def _test_credentials(self, customer_id, meteringpoint_id):
        # Return based on test input
        if customer_id == "valid" and meteringpoint_id == "valid":
            return True
        return False

    def async_create_entry(self, title, data):
        self.created = True
        return {"type": RESULT_TYPE_CREATE_ENTRY, "title": title, "data": data}


@pytest.fixture
def flow_handler(hass: HomeAssistant):
    """Return a fresh FlowHandler."""
    flow = DummyFlow()
    flow.hass = hass
    return flow


async def test_show_form_initial(flow_handler):
    """Test that initial form is shown."""
    result = await flow_handler.async_step_user()
    assert result["type"] == RESULT_TYPE_FORM
    # Form schema keys
    schema = result["data_schema"]
    assert CONF_CUSTOMER_ID in schema.schema
    assert CONF_METERINGPOINT_ID in schema.schema


@pytest.mark.parametrize(
    "cust, meter, expect_errors",
    [
        ("invalid", "invalid", True),
        ("valid", "valid", False),
    ],
)
async def test_user_step_credentials(flow_handler, cust, meter, expect_errors):
    """Test credentials handling in user step."""
    # Step with user_input
    result = await flow_handler.async_step_user(
        {CONF_CUSTOMER_ID: cust, CONF_METERINGPOINT_ID: meter}
    )
    if expect_errors:
        assert result["type"] == RESULT_TYPE_FORM
        assert flow_handler._errors.get("base") == "auth"
    else:
        assert result["type"] == RESULT_TYPE_CREATE_ENTRY
        assert flow_handler.created
        assert result["title"] == meter
        assert result["data"] == {CONF_CUSTOMER_ID: cust, CONF_METERINGPOINT_ID: meter}


async def test_create_entry_exception(flow_handler, caplog):
    """Simulate exception in create_entry branch."""

    # Monkeypatch create_entry to raise
    async def raise_exc(*args, **kwargs):
        raise Exception("creation failed")

    flow_handler.async_create_entry = raise_exc

    result = await flow_handler.async_step_user(
        {CONF_CUSTOMER_ID: "valid", CONF_METERINGPOINT_ID: "valid"}
    )
    assert result["type"] == RESULT_TYPE_FORM
    assert flow_handler._errors.get("base") == "unknown"
    assert "Feil i async_create_entry" in caplog.text


async def test_unexpected_exception(flow_handler, caplog, monkeypatch):
    """Simulate unexpected exception in step."""

    # Monkeypatch _show_config_form to raise
    async def bad_show(*args, **kwargs):
        raise RuntimeError("bad form")

    monkeypatch.setattr(flow_handler, "_show_config_form", bad_show)

    result = await flow_handler.async_step_user(None)
    assert result["type"] == RESULT_TYPE_FORM
    assert flow_handler._errors.get("base") == "unknown"
    assert "Uventet feil i config flow" in caplog.text


async def test_options_flow(hass: HomeAssistant):
    """Test options flow returns form and create entry."""
    # Create dummy entry with empty options
    entry = config_entries.ConfigEntry(
        version=1,
        domain=DOMAIN,
        title="t",
        data={CONF_CUSTOMER_ID: "c", CONF_METERINGPOINT_ID: "m"},
        options={},
        entry_id="testid",
        source="test",
        connection_class=config_flow.config_entries.CONN_CLASS_CLOUD_POLL,
        system_options={},
    )
    options_handler = config_flow.NorgesnettOptionsFlowHandler(entry)

    # Initial step
    result = await options_handler.async_step_init()
    assert result["type"] == RESULT_TYPE_FORM

    # Submit options
    user_input = {p: False for p in config_flow.PLATFORMS}
    result2 = await options_handler.async_step_user(user_input)
    # Should create entry with updated options
    assert result2["type"] == RESULT_TYPE_CREATE_ENTRY
    assert result2["data"] == user_input
    assert result2["title"] == entry.data[CONF_CUSTOMER_ID]
