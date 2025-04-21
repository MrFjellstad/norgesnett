"""Constants for Norgesnett."""
# Base component constants
NAME = "Norgesnett"
DOMAIN = "norgesnett"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.0.0"

ATTRIBUTION = "Data provided by http://jsonplaceholder.typicode.com/"
ISSUE_URL = "https://github.com/MrFjellstad/norgesnett/issues"

# Icons
ICON = "mdi:format-quote-close"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Platforms
BINARY_SENSOR = "binary_sensor"
SENSOR = "sensor"
SWITCH = "switch"
PLATFORMS = [BINARY_SENSOR, SENSOR, SWITCH]


# Configuration and options
CONF_ENABLED = "enabled"
CONF_CUSTOMER_ID = "customer_id"
CONF_METERINGPOINT_ID = "meteringpoint_id"

# Defaults
DEFAULT_NAME = DOMAIN

API_AUTH_URL = "https://gridtariff-api.norgesnett.no/api/v1.01/Auth/Generate"
API_TARIFFS_URL = "https://gridtariff-api.norgesnett.no/api/v1.01/TariffQuery/MeteringPointsGridTariffs"

STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
