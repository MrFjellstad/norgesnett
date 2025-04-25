"""Sensor platform for Norgesnett."""

import logging
from datetime import datetime, timezone

from homeassistant.components.sensor import SensorEntity

from .const import DEFAULT_NAME, DOMAIN, ICON
from .entity import NorgesnettEntity

_LOGGER = logging.getLogger(__name__)


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

    entities = (
        [NorgesnettHourlyPricesSensor(coordinator, entry)]
        + [
            NorgesnettSensor(coordinator, entry, key, value)
            for key, value in items.items()
        ]
        + [NorgesnettCurrentPriceSensor(coordinator, entry)]
    )

    async_add_entities(entities, update_before_add=True)

    # async_add_devices([NorgesnettSensor(coordinator, entry)])


class NorgesnettSensor(NorgesnettEntity):
    """norgesnett Sensor class."""

    def __init__(self, coordinator, config_entry, key: str, initial_value):
        super().__init__(coordinator, config_entry)
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

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return ICON

    @property
    def device_class(self):
        """Return de device class of the sensor."""
        return "norgesnett__custom_device_class"


class NorgesnettHourlyPricesSensor(NorgesnettEntity, SensorEntity):
    """Én sensor som inneholder alle tidsperioder som attributter."""

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry)
        self._attr_name = f"{DEFAULT_NAME} Hourly Prices"
        self._attr_unique_id = f"{config_entry.entry_id}_hourly_prices"

    @property
    def state(self):
        # Du kan for eksempel returnere antall perioder:
        collections = self.coordinator.data.get("gridTariffCollections") or []

        if not collections:
            return None

        hours = (
            collections[0].get("gridTariff", {}).get("tariffPrice", {}).get("hours", [])
        )
        return len(hours)

    @property
    def extra_state_attributes(self):
        """Returner dict med shortName som nøkkel, og total/totalExVat som verdi."""
        result = {}
        for hour in self.coordinator.data.get("hours", []):
            sn = hour.get("shortName")
            ep = hour.get("energyPrice", {})
            if sn and ep:
                result[sn] = {
                    "total": ep.get("total"),
                    "totalExVat": ep.get("totalExVat"),
                }
        return result


class NorgesnettCurrentPriceSensor(NorgesnettEntity, SensorEntity):
    """Sensor som viser dagens pris for gjeldende time."""

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry)
        self._attr_name = f"{DEFAULT_NAME} Current Hour Price"
        self._attr_unique_id = f"{config_entry.entry_id}_current_price"
        self._attr_unit_of_measurement = "NOK"

    @property
    def state(self):
        """Returner total-prisen for gjeldende timeintervall."""
        # Hent listen med timer fra koordinatoren
        collections = self.coordinator.data.get("gridTariffCollections") or []
        if not collections:
            return None

        hours = (
            collections[0].get("gridTariff", {}).get("tariffPrice", {}).get("hours", [])
        )
        if not hours:
            _LOGGER.debug("CurrentPrice: ingen timer i data")
            return None

        # Finn nåværende lokal tid (kan byttes til UTC om API gir UTC-tider)
        now = datetime.now(timezone.utc).astimezone()
        current_hour = now.hour
        next_hour = (current_hour + 1) % 24
        short_name = f"{current_hour:02d}-{next_hour:02d}"

        # Let opp elementet med matching shortName
        for hour in hours:
            if hour.get("shortName") == short_name:
                energy = hour.get("energyPrice") or {}
                return energy.get("total")

        # Returner None dersom ikke funnet
        return None
