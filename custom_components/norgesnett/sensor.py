"""Sensor platform for Norgesnett."""

import json
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.event import async_track_time_change
from homeassistant.util.dt import now

from .const import DEFAULT_NAME, DOMAIN, ICON
from .entity import NorgesnettEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    data = coordinator.data or {}

    collections = data.get("gridTariffCollections") or []

    if not collections:
        _LOGGER.error(
            "Norgesnett: Ingen gridTariffCollections i data, hopper over sensor-setup"
        )
        return None

    mp_list = data["gridTariffCollections"][0]["meteringPointsAndPriceLevels"]

    if not mp_list:
        _LOGGER.error(
            "Norgesnett: Ingen gridTariff, hopper over sensor-setup for prisnivå"
        )
        # return None

    if len(mp_list) > 0:
        mp = mp_list[0]
        currentPriceLevel = mp["currentFixedPriceLevel"]["id"]
    else:
        currentPriceLevel = "Effektnivå er ikke satt"

    fixedPrices_list = data["gridTariffCollections"][0]["gridTariff"]["tariffPrice"][
        "priceInfo"
    ]["fixedPrices"]
    fixedPrices = fixedPrices_list[0]

    items = {
        "currentFixedPriceLevel": currentPriceLevel,
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
    def icon(self):
        return ICON

    @property
    def device_class(self):
        # Monetary values per kWh
        return "monetary"

    @property
    def state_class(self):
        # Measurement for graphing
        return "measurement"

    @property
    def state(self):
        # Du kan for eksempel returnere antall perioder:
        collections = self.coordinator.data.get("gridTariffCollections") or []

        if not collections:
            return None

        hours = (
            collections[0].get("gridTariff", {}).get("tariffPrice", {}).get("hours", [])
        )
        # Bygg opp dict som før
        result = {
            entry.get("shortName"): {
                "total": entry.get("energyPrice", {}).get("total"),
                "totalExVat": entry.get("energyPrice", {}).get("totalExVat"),
            }
            for entry in hours
            if entry.get("shortName") and entry.get("energyPrice")
        }
        # Returner som kompakt JSON
        return json.dumps(result)

    def name(self):
        return f"{DEFAULT_NAME} Hourly Prices (JSON)"


class NorgesnettCurrentPriceSensor(NorgesnettEntity, SensorEntity):
    """Sensor som viser dagens pris for gjeldende time."""

    @property
    def device_class(self):
        return "monetary"

    @property
    def state_class(self):
        return "measurement"

    def __init__(self, coordinator, config_entry):
        super().__init__(coordinator, config_entry)
        self._attr_name = f"{DEFAULT_NAME} Current Hour Price"
        self._attr_unique_id = f"{config_entry.entry_id}_current_price"
        self._attr_unit_of_measurement = "NOK"
        self._unsub_time_listener = None

    async def async_added_to_hass(self):
        """Når sensoren legges til, schedule oppdatering på hver hel time."""
        # Kall _update_state klokken H:00:00 hvert minutt
        self._unsub_time_listener = async_track_time_change(
            self.hass, self._update_state, second=0
        )

    async def async_will_remove_from_hass(self):
        """Rydd opp når sensoren fjernes."""
        if self._unsub_time_listener:
            self._unsub_time_listener()
            self._unsub_time_listener = None

    def _update_state(self, now_time):
        """Tving HA til å oppdatere state, uten å hente ny data fra API."""
        # force_refresh=False: vi bruker fremdeles gammel coordinator.data
        self.hass.loop.call_soon_threadsafe(
            self.async_schedule_update_ha_state, False  # force_refresh=False
        )

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
        current = now()
        current_hour = current.hour
        next_hour = (current_hour + 1) % 24
        short_name = f"{current_hour:02d}-{next_hour:02d}"

        # Let opp elementet med matching shortName
        for hour in hours:
            if hour.get("shortName") == short_name:
                energy = hour.get("energyPrice") or {}
                return energy.get("total")

        # Returner None dersom ikke funnet
        return None
