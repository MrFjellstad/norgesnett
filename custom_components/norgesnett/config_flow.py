"""Adds config flow for Norgesnett."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import NorgesnettApiClient
from .const import CONF_CUSTOMER_ID, CONF_METERINGPOINT_ID, DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


class NorgesnettFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for norgesnett."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    # def __init__(self):
    #     """Initialize."""
    #     # super().__init__(hass, config)
    #     self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}
        try:
            # Uncomment the next 2 lines if only a single instance of the integration is allowed:
            # if self._async_current_entries():
            #     return self.async_abort(reason="single_instance_allowed")

            if user_input is not None:
                valid = await self._test_credentials(
                    user_input[CONF_CUSTOMER_ID], user_input[CONF_METERINGPOINT_ID]
                )
                if valid:
                    try:
                        return self.async_create_entry(
                            title=user_input[CONF_METERINGPOINT_ID], data=user_input
                        )
                    except Exception as err:
                        _LOGGER.exception("Feil i async_create_entry %s", err)
                        self._errors["base"] = "unknown"
                        return await self._show_config_form(user_input)
                else:
                    self._errors["base"] = "auth"

                return await self._show_config_form(user_input)

            user_input = {}
            # Provide defaults for form
            user_input[CONF_CUSTOMER_ID] = ""
            user_input[CONF_METERINGPOINT_ID] = ""
            return await self._show_config_form(user_input)
        except Exception:
            _LOGGER.exception("Uventet feil i config flow")
            # Møter UI-feilmedingen: gir grunnleggende tilbakemelding
            self._errors["base"] = "unknown"
            return await self._show_config_form(user_input)

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return NorgesnettOptionsFlowHandler(config_entry)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_CUSTOMER_ID): str,
                    vol.Required(CONF_METERINGPOINT_ID): str,
                }
            ),
            errors=self._errors,
        )

    async def _test_credentials(self, customer_id, meteringpoint_id):
        """Return true if credentials is valid."""
        _LOGGER.debug("Tester credentials")
        try:
            session = async_create_clientsession(self.hass)
            client = NorgesnettApiClient(customer_id, meteringpoint_id, session)
            retval = await client.async_get_auth()
            _LOGGER.debug("Auth OK: %s", retval)
            return True
        except Exception:  # pylint: disable=broad-except
            _LOGGER.debug("Auth Fail")
            pass
        return False


class NorgesnettOptionsFlowHandler(config_entries.OptionsFlow):
    """Config flow options handler for norgesnett."""

    def __init__(self, config_entry):
        """Initialize HACS options flow."""
        super().__init__()
        self.options = {}

    async def async_step_init(self, user_input=None):  # pylint: disable=unused-argument
        """Manage the options."""
        self.options = dict(self.config_entry.options)
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}
        if user_input is not None:
            self.options.update(user_input)
            return await self._update_options()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(x, default=self.options.get(x, True)): bool
                    for x in sorted(PLATFORMS)
                }
            ),
        )

    async def _update_options(self):
        """Update config entry options."""
        return self.async_create_entry(
            title=self.config_entry.data.get(CONF_CUSTOMER_ID), data=self.options
        )
