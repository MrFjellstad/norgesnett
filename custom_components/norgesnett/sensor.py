"""Sensor platform for Norgesnett."""

import logging

from .const import DEFAULT_NAME, DOMAIN, ICON
from .entity import NorgesnettEntity

_LOGGER = logging.getLogger(__name__)

# PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
#     {
#         # This is only needed if you want the some area but want the prices in a non local currency
#         vol.Optional("currentFixedPriceLevel", default=""): cv.string,
#         vol.Optional("monthlyTotal", default=0): cv.positive_float,
#         vol.Optional("monthlyTotalExVat", default=0): cv.positive_float,
#         vol.Optional("monthlyExTaxes", default=0): cv.positive_float,
#         vol.Optional("monthlyTaxes", default=0): cv.positive_float,
#         vol.Optional("monthlyUnitOfMeasure", default="Kr/month"): cv.string,
#     }
# )


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data  # antatt å være dict fra ditt API

    mp_list = data["gridTariffCollections"][0]["meteringPointsAndPriceLevels"]
    mp = mp_list[0]

    fixedPrices_list = data["gridTariffCollections"][0]["gridTariff"]["tariffPrice"][
        "priceInfo"
    ]["fixedPrices"]
    fixedPrices = fixedPrices_list[0]

    items = {
        "currentFixedPriceLevel": mp["currentFixedPriceLevel"]["id"],
        "monthlyTotal": fixedPrices["priceLevels"][0]["monthlyTotal"],
        "monthlyTotalExVat": fixedPrices["priceLevels"][0]["monthlyTotalExVat"],
        "monthlyExTaxes": fixedPrices["priceLevels"][0]["monthlyExTaxes"],
        "monthlyTaxes": fixedPrices["priceLevels"][0]["monthlyTaxes"],
        "monthlyUnitOfMeasure": fixedPrices["priceLevels"][0]["monthlyUnitOfMeasure"],
    }

    entities = [
        NorgesnettSensor(coordinator, entry, key, value) for key, value in items.items()
    ]

    async_add_entities(entities, update_before_add=True)

    # async_add_devices([NorgesnettSensor(coordinator, entry)])


class NorgesnettSensor(NorgesnettEntity):
    """norgesnett Sensor class."""

    def __init__(self, coordinator, config_entry, key: str, initial_value):
        super().__init__(coordinator, config_entry)
        # self.coordinator = coordinator
        # self._entry_id = entry_id
        self._key = key
        self._attr_unique_id = f"{config_entry.entry_id}_{key}"
        self._attr_native_value = initial_value

    @property
    def state(self):
        # Returner siste verdi fra koordinator, evt. fallback til init
        return self.coordinator.data.get(self._key, self._attr_native_value)

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{DEFAULT_NAME}_{self._key}"

    # @property
    # def state(self):
    #     """Return the state of the sensor."""
    #     return self.coordinator.data.get("body")

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return "norgesnett__custom_device_class"
