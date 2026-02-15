"""Global fixtures for Norgesnett integration."""

from unittest.mock import patch

import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


# This fixture enables loading custom components.
@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations defined in the test dir."""
    yield


# This fixture is used to prevent HomeAssistant from attempting to create and dismiss persistent
# notifications. These calls would fail without this fixture since the persistent_notification
# integration is never loaded during a test.
@pytest.fixture(name="skip_notifications", autouse=True)
def skip_notifications_fixture():
    """Skip notification calls."""
    with patch("homeassistant.components.persistent_notification.async_create"), patch(
        "homeassistant.components.persistent_notification.async_dismiss"
    ):
        yield


# This fixture, when used, will result in calls to async_get_data to return some mock data.
@pytest.fixture(name="bypass_get_data")
def bypass_get_data_fixture():
    """Skip calls to get data from API."""
    mock_data = {
        "gridTariffCollections": [
            {
                "meteringPointsAndPriceLevels": [
                    {"currentFixedPriceLevel": {"id": "test_level"}}
                ],
                "gridTariff": {
                    "tariffPrice": {
                        "priceInfo": {
                            "fixedPrices": [
                                {
                                    "priceLevels": [
                                        {
                                            "monthlyTotal": 100,
                                            "monthlyTotalExVat": 80,
                                            "monthlyExTaxes": 75,
                                            "monthlyTaxes": 25,
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
    with patch(
        "custom_components.norgesnett.NorgesnettApiClient.async_get_data",
        return_value=mock_data,
    ):
        yield


# In this fixture, we are forcing calls to async_get_data to raise an Exception. This is useful
# for exception handling.
@pytest.fixture(name="error_on_get_data")
def error_get_data_fixture():
    """Simulate error when retrieving data from API."""
    with patch(
        "custom_components.norgesnett.NorgesnettApiClient.async_get_data",
        side_effect=Exception,
    ):
        yield
