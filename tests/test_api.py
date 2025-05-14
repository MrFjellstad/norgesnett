"""Tests for Norgesnett api."""

import asyncio
import logging

import aiohttp
import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession

import custom_components.norgesnett.api as api_module
from custom_components.norgesnett.api import NorgesnettApiClient

# Monkeypatch API URLs to use JSONPlaceholder for testing
api_module.API_AUTH_URL = "https://jsonplaceholder.typicode.com/auth"
api_module.API_TARIFFS_URL = "https://jsonplaceholder.typicode.com/tariffs"

_LOGGER = logging.getLogger(__name__)


async def test_async_get_auth(hass, aioclient_mock, caplog):
    """Test the async_get_auth method."""
    caplog.set_level(logging.DEBUG)
    api = NorgesnettApiClient(
        "test_customer", "test_meteringpoint", async_get_clientsession(hass)
    )

    # Mock the authentication response
    aioclient_mock.post(
        api_module.API_AUTH_URL,
        json={"apiKey": "test_api_key"},
    )

    auth_info = await api.async_get_auth()
    assert auth_info == {"apiKey": "test_api_key"}

    # Test logging of the apiKey
    assert "apiKey:" in caplog.text
    assert "test_api_key" in caplog.text


async def test_async_get_data(hass, aioclient_mock, caplog):
    """Test the async_get_data method."""
    caplog.set_level(logging.DEBUG)
    api = NorgesnettApiClient(
        "test_customer", "test_meteringpoint", async_get_clientsession(hass)
    )

    # Mock authentication
    aioclient_mock.post(
        api_module.API_AUTH_URL,
        json={"apiKey": "test_api_key"},
    )

    # Mock tariff data
    aioclient_mock.post(
        api_module.API_TARIFFS_URL,
        json={"tariffs": "test_tariff_data"},
    )

    tariffs = await api.async_get_data()
    assert tariffs == {"tariffs": "test_tariff_data"}

    # Test logging of the api_wrapper calls
    assert f"api_wrapper: post {api_module.API_AUTH_URL}" in caplog.text
    assert f"api_wrapper: post {api_module.API_TARIFFS_URL}" in caplog.text


@pytest.mark.asyncio
async def test_api_wrapper_get(hass, aioclient_mock):
    """Test api_wrapper with GET method."""
    api = NorgesnettApiClient(
        "test_customer", "test_meteringpoint", async_get_clientsession(hass)
    )

    aioclient_mock.get(
        "https://jsonplaceholder.typicode.com/posts/1", json={"test": "test"}
    )
    result = await api.api_wrapper(
        "get", "https://jsonplaceholder.typicode.com/posts/1"
    )
    assert result == {"test": "test"}


async def test_api_wrapper_put_and_patch(hass, aioclient_mock):
    """Test api_wrapper PUT and PATCH methods returning JSON."""
    api = NorgesnettApiClient(
        "test_customer", "test_meteringpoint", async_get_clientsession(hass)
    )

    # Mock PUT
    aioclient_mock.put(
        "https://jsonplaceholder.typicode.com/posts/2", json={"foo": "bar"}
    )
    result_put = await api.api_wrapper(
        "put", "https://jsonplaceholder.typicode.com/posts/2"
    )
    assert result_put == {"foo": "bar"}

    # Mock PATCH
    aioclient_mock.patch(
        "https://jsonplaceholder.typicode.com/posts/3", json={"baz": 123}
    )
    result_patch = await api.api_wrapper(
        "patch", "https://jsonplaceholder.typicode.com/posts/3"
    )
    assert result_patch == {"baz": 123}


async def test_api_wrapper_invalid_method(hass, caplog):
    """Test api_wrapper with an invalid HTTP method."""
    caplog.set_level(logging.ERROR)
    api = NorgesnettApiClient(
        "test_customer", "test_meteringpoint", async_get_clientsession(hass)
    )

    result = await api.api_wrapper(
        "invalid_method", "https://jsonplaceholder.typicode.com/invalid"
    )
    assert result is None
    assert "Something really wrong happened!" in caplog.text


async def test_api_set_and_exceptions(hass, aioclient_mock, caplog):
    """Test async_set_title and exception logging in api_wrapper."""
    caplog.set_level(logging.ERROR)
    api = NorgesnettApiClient("test", "test", async_get_clientsession(hass))

    # Test async_set_title (PATCH)
    aioclient_mock.patch("https://jsonplaceholder.typicode.com/posts/1")
    assert await api.async_set_title("test") is None

    # TimeoutError on PUT
    caplog.clear()
    aioclient_mock.put(
        "https://jsonplaceholder.typicode.com/posts/1", exc=asyncio.TimeoutError
    )
    result = await api.api_wrapper(
        "put", "https://jsonplaceholder.typicode.com/posts/1"
    )
    assert result is None
    assert any(
        "Timeout error fetching information" in rec.message for rec in caplog.records
    )

    # ClientError on POST
    caplog.clear()
    aioclient_mock.post(
        "https://jsonplaceholder.typicode.com/posts/1", exc=aiohttp.ClientError
    )
    result = await api.api_wrapper(
        "post", "https://jsonplaceholder.typicode.com/posts/1"
    )
    assert result is None
    assert any("Error fetching information" in rec.message for rec in caplog.records)

    # Generic Exception on POST
    caplog.clear()
    aioclient_mock.post("https://jsonplaceholder.typicode.com/posts/2", exc=Exception)
    result = await api.api_wrapper(
        "post", "https://jsonplaceholder.typicode.com/posts/2"
    )
    assert result is None
    assert any(
        "Something really wrong happened!" in rec.message for rec in caplog.records
    )

    # TypeError on POST (parsing error)
    caplog.clear()
    aioclient_mock.post("https://jsonplaceholder.typicode.com/posts/3", exc=TypeError)
    result = await api.api_wrapper(
        "post", "https://jsonplaceholder.typicode.com/posts/3"
    )
    assert result is None
    assert any(
        "Error parsing information from" in rec.message for rec in caplog.records
    )
