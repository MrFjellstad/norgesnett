"""Unit tests for Norgesnett entity platforms."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.norgesnett.binary_sensor import NorgesnettBinarySensor
from custom_components.norgesnett.binary_sensor import (
    async_setup_entry as async_setup_binary_sensor_entry,
)
from custom_components.norgesnett.const import (
    BINARY_SENSOR,
    BINARY_SENSOR_DEVICE_CLASS,
    DEFAULT_NAME,
    DOMAIN,
    ICON,
    SWITCH,
)
from custom_components.norgesnett.sensor import (
    NorgesnettCurrentPriceSensor,
    NorgesnettHourlyPricesSensor,
    NorgesnettSensor,
)
from custom_components.norgesnett.sensor import (
    async_setup_entry as async_setup_sensor_entry,
)
from custom_components.norgesnett.switch import NorgesnettBinarySwitch
from custom_components.norgesnett.switch import (
    async_setup_entry as async_setup_switch_entry,
)


@pytest.fixture
def config_entry():
    """Provide a reusable config entry."""
    return MockConfigEntry(domain=DOMAIN, data={}, entry_id="test_entry")


@pytest.fixture
def coordinator():
    """Provide a lightweight coordinator-like object."""
    return SimpleNamespace(
        data={"title": "foo"},
        api=SimpleNamespace(async_set_title=AsyncMock()),
        async_request_refresh=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_binary_sensor_properties_and_setup(config_entry, coordinator):
    """Test binary sensor name, class, state and setup callback."""
    entity = NorgesnettBinarySensor(coordinator, config_entry)

    assert entity.name == f"{DEFAULT_NAME}_{BINARY_SENSOR}"
    assert entity.device_class == BINARY_SENSOR_DEVICE_CLASS
    assert entity.is_on is True

    coordinator.data["title"] = "something_else"
    assert entity.is_on is False

    hass = SimpleNamespace(data={DOMAIN: {config_entry.entry_id: coordinator}})
    added = []

    def add_devices(devices):
        added.extend(devices)

    await async_setup_binary_sensor_entry(hass, config_entry, add_devices)
    assert len(added) == 1
    assert isinstance(added[0], NorgesnettBinarySensor)


@pytest.mark.asyncio
async def test_switch_turn_on_off_properties_and_setup(config_entry, coordinator):
    """Test switch state/properties and turn on/off behavior."""
    entity = NorgesnettBinarySwitch(coordinator, config_entry)

    assert entity.name == f"{DEFAULT_NAME}_{SWITCH}"
    assert entity.icon == ICON
    assert entity.is_on is True

    coordinator.data["title"] = "not_foo"
    assert entity.is_on is False

    await entity.async_turn_on()
    coordinator.api.async_set_title.assert_awaited_with("bar")
    coordinator.async_request_refresh.assert_awaited()

    coordinator.api.async_set_title.reset_mock()
    coordinator.async_request_refresh.reset_mock()

    await entity.async_turn_off()
    coordinator.api.async_set_title.assert_awaited_with("foo")
    coordinator.async_request_refresh.assert_awaited()

    hass = SimpleNamespace(data={DOMAIN: {config_entry.entry_id: coordinator}})
    added = []

    def add_devices(devices):
        added.extend(devices)

    await async_setup_switch_entry(hass, config_entry, add_devices)
    assert len(added) == 1
    assert isinstance(added[0], NorgesnettBinarySwitch)


@pytest.mark.asyncio
async def test_sensor_async_setup_entry_adds_expected_entities(config_entry):
    """Test sensor platform setup creates expected entities from data."""
    coordinator = SimpleNamespace(
        data={
            "gridTariffCollections": [
                {
                    "meteringPointsAndPriceLevels": [
                        {"currentFixedPriceLevel": {"id": "L1"}}
                    ],
                    "gridTariff": {
                        "tariffPrice": {
                            "priceInfo": {
                                "fixedPrices": [
                                    {
                                        "priceLevels": [
                                            {
                                                "monthlyTotal": 10,
                                                "monthlyTotalExVat": 8,
                                                "monthlyExTaxes": 7,
                                                "monthlyTaxes": 3,
                                                "monthlyUnitOfMeasure": "NOK",
                                            }
                                        ]
                                    }
                                ]
                            },
                            "hours": [],
                        }
                    },
                }
            ]
        }
    )

    hass = SimpleNamespace(data={DOMAIN: {config_entry.entry_id: coordinator}})
    captured = {}

    def add_entities(entities, update_before_add=True):
        captured["entities"] = entities
        captured["update_before_add"] = update_before_add

    await async_setup_sensor_entry(hass, config_entry, add_entities)

    assert captured["update_before_add"] is True
    entities = captured["entities"]
    assert len(entities) == 8
    assert any(isinstance(entity, NorgesnettHourlyPricesSensor) for entity in entities)
    assert any(isinstance(entity, NorgesnettCurrentPriceSensor) for entity in entities)


@pytest.mark.asyncio
async def test_sensor_async_setup_entry_handles_missing_collections(
    config_entry, caplog
):
    """Test setup returns early when tariff collections are missing."""
    coordinator = SimpleNamespace(data={})
    hass = SimpleNamespace(data={DOMAIN: {config_entry.entry_id: coordinator}})

    def add_entities(entities, update_before_add=True):  # pragma: no cover
        raise AssertionError("Should not add entities when data is missing")

    result = await async_setup_sensor_entry(hass, config_entry, add_entities)

    assert result is None
    assert "Ingen gridTariffCollections" in caplog.text


@pytest.mark.asyncio
async def test_sensor_async_setup_entry_empty_mp_list_uses_fallback(
    config_entry, caplog
):
    """Test setup handles empty price-level list and uses fallback text."""
    coordinator = SimpleNamespace(
        data={
            "gridTariffCollections": [
                {
                    "meteringPointsAndPriceLevels": [],
                    "gridTariff": {
                        "tariffPrice": {
                            "priceInfo": {
                                "fixedPrices": [
                                    {
                                        "priceLevels": [
                                            {
                                                "monthlyTotal": 10,
                                                "monthlyTotalExVat": 8,
                                                "monthlyExTaxes": 7,
                                                "monthlyTaxes": 3,
                                                "monthlyUnitOfMeasure": "NOK",
                                            }
                                        ]
                                    }
                                ]
                            },
                            "hours": [],
                        }
                    },
                }
            ]
        }
    )

    hass = SimpleNamespace(data={DOMAIN: {config_entry.entry_id: coordinator}})
    captured = {}

    def add_entities(entities, update_before_add=True):
        captured["entities"] = entities

    await async_setup_sensor_entry(hass, config_entry, add_entities)

    current_level_entities = [
        entity
        for entity in captured["entities"]
        if isinstance(entity, NorgesnettSensor)
        and entity._key == "currentFixedPriceLevel"
    ]
    assert len(current_level_entities) == 1
    assert current_level_entities[0].state == "Effektnivå er ikke satt"
    assert "Ingen gridTariff" in caplog.text


def test_norgesnett_sensor_state_name_icon_and_device_class(config_entry):
    """Test generic Norgesnett sensor attributes and state fallback."""
    coordinator = SimpleNamespace(data={"my_key": 123})
    entity = NorgesnettSensor(coordinator, config_entry, "my_key", 42)

    assert entity.state == 123
    assert entity.name == f"{DEFAULT_NAME}_my_key"
    assert entity.icon == ICON
    assert entity.device_class == "monetary"

    coordinator.data = {}
    assert entity.state == 42

    coordinator.data = None
    assert entity.state == 42


def test_hourly_prices_sensor_state_and_name(config_entry):
    """Test hourly prices sensor state derivation and metadata."""
    coordinator = SimpleNamespace(
        data={
            "gridTariffCollections": [
                {
                    "gridTariff": {
                        "tariffPrice": {
                            "hours": [
                                {"shortName": "00-01"},
                                {"shortName": "01-02"},
                            ]
                        }
                    }
                }
            ]
        }
    )
    entity = NorgesnettHourlyPricesSensor(coordinator, config_entry)

    assert entity.state == 2
    assert entity.name == f"{DEFAULT_NAME} Hourly Prices (JSON)"
    assert entity.icon == ICON
    assert entity.device_class == "monetary"
    assert entity.state_class == "measurement"

    coordinator.data = {"gridTariffCollections": []}
    assert entity.state is None


def test_hourly_prices_sensor_state_handles_exception(config_entry):
    """Test hourly prices sensor returns None if coordinator data access fails."""
    coordinator = SimpleNamespace(data=None)
    entity = NorgesnettHourlyPricesSensor(coordinator, config_entry)

    assert entity.state is None


@pytest.mark.asyncio
async def test_current_price_sensor_lifecycle_and_state(config_entry):
    """Test current price sensor scheduler hooks and current-hour lookup."""
    coordinator = SimpleNamespace(
        data={
            "gridTariffCollections": [
                {
                    "gridTariff": {
                        "tariffPrice": {
                            "hours": [
                                {"shortName": "09-10", "energyPrice": {"total": 1.23}},
                                {"shortName": "10-11", "energyPrice": {"total": 2.34}},
                            ]
                        }
                    }
                }
            ]
        }
    )

    entity = NorgesnettCurrentPriceSensor(coordinator, config_entry)
    fake_hass = MagicMock()
    fake_hass.loop = MagicMock()

    unsubscribe = MagicMock()
    with patch(
        "custom_components.norgesnett.sensor.async_track_time_change",
        return_value=unsubscribe,
    ) as track_time_change:
        await entity.async_added_to_hass()
        track_time_change.assert_called_once()

    mock_now = SimpleNamespace(hour=10)
    with patch("custom_components.norgesnett.sensor.now", return_value=mock_now):
        assert entity.state == 2.34

    with patch.object(
        NorgesnettCurrentPriceSensor,
        "hass",
        new_callable=PropertyMock,
        return_value=fake_hass,
    ):
        entity._update_state(now_time=None)
    fake_hass.loop.call_soon_threadsafe.assert_called_once_with(
        entity.async_schedule_update_ha_state,
        False,
    )

    await entity.async_will_remove_from_hass()
    unsubscribe.assert_called_once()

    coordinator.data = {"gridTariffCollections": []}
    assert entity.state is None


def test_current_price_sensor_state_no_match_and_exception(config_entry):
    """Test current price sensor when no hour matches and on malformed data."""
    coordinator = SimpleNamespace(
        data={
            "gridTariffCollections": [
                {
                    "gridTariff": {
                        "tariffPrice": {
                            "hours": [
                                {"shortName": "08-09", "energyPrice": {"total": 1.11}},
                            ]
                        }
                    }
                }
            ]
        }
    )
    entity = NorgesnettCurrentPriceSensor(coordinator, config_entry)

    mock_now = SimpleNamespace(hour=10)
    with patch("custom_components.norgesnett.sensor.now", return_value=mock_now):
        assert entity.state is None

    coordinator.data = None
    assert entity.state is None
