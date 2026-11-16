"""Setup, errors, webhook and device registry."""

import time as time_mod
from unittest.mock import AsyncMock, patch

import pytest
import requests

from homeassistant.config_entries import SOURCE_REAUTH, ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from custom_components.omlet_smart_coop.const import DOMAIN, WEBHOOK_TOKEN

from .conftest import load_device
from .helpers import http_error

WEBHOOK_URL = f"/api/webhook/{DOMAIN}"


async def _setup(hass: HomeAssistant, entry) -> None:
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


async def test_setup_and_unload(hass: HomeAssistant, mock_omlet, config_entry) -> None:
    """The entry loads, creates entities and unloads."""
    await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.LOADED
    assert er.async_get(hass).async_get_entity_id("cover", DOMAIN, "door-id_cover")

    assert await hass.config_entries.async_unload(config_entry.entry_id)
    assert config_entry.state is ConfigEntryState.NOT_LOADED


async def test_rejected_key_starts_reauth(
    hass: HomeAssistant, mock_omlet, config_entry
) -> None:
    """A 401 is an auth failure, which starts reauth, not a retry loop."""
    mock_omlet.get_devices.side_effect = http_error(401)
    await _setup(hass, config_entry)

    assert config_entry.state is ConfigEntryState.SETUP_ERROR
    flows = hass.config_entries.flow.async_progress_by_handler(DOMAIN)
    assert [f["context"]["source"] for f in flows] == [SOURCE_REAUTH]


@pytest.mark.parametrize(
    "error", [http_error(500), requests.ConnectionError("down"), requests.Timeout("slow")]
)
async def test_connection_errors_retry(
    hass: HomeAssistant, mock_omlet, config_entry, error
) -> None:
    """A server or network error retries setup later."""
    mock_omlet.get_devices.side_effect = error
    await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_hung_api_call_times_out(
    hass: HomeAssistant, mock_omlet, config_entry
) -> None:
    """The SDK sets no timeout, so the integration bounds the wait."""
    mock_omlet.get_devices.side_effect = lambda: time_mod.sleep(1)
    with patch("custom_components.omlet_smart_coop.coop_api.API_TIMEOUT", 0.05):
        await _setup(hass, config_entry)
    assert config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_webhook_survives_reload(
    hass: HomeAssistant, mock_omlet, config_entry, hass_client_no_auth
) -> None:
    """Fixed: reloading the entry used to leave the webhook unregistered."""
    await _setup(hass, config_entry)
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    coordinator.async_request_refresh = AsyncMock()
    client = await hass_client_no_auth()
    resp = await client.post(WEBHOOK_URL, json={"token": "anything"})
    assert resp.status == 200
    coordinator.async_request_refresh.assert_awaited_once()


async def test_webhook_removed_with_last_entry(
    hass: HomeAssistant, mock_omlet, config_entry, hass_client_no_auth
) -> None:
    """Unloading the last entry removes the webhook."""
    await _setup(hass, config_entry)
    assert await hass.config_entries.async_unload(config_entry.entry_id)

    client = await hass_client_no_auth()
    resp = await client.post(WEBHOOK_URL, json={"token": "anything"})
    # An unknown webhook is answered 200 so callers learn nothing, but nothing runs.
    assert resp.status == 200
    assert DOMAIN not in hass.data or hass.data[DOMAIN] == {}


@pytest.mark.parametrize(
    "config_entry_data", [{"api_key": "test-api-key", WEBHOOK_TOKEN: "s3cret"}]
)
@pytest.mark.parametrize(
    ("body", "refreshes"),
    [
        ({"token": "s3cret"}, True),
        ({"token": "wrong"}, False),
        ({}, False),
        (["not", "an", "object"], False),
    ],
)
async def test_webhook_token_checked(
    hass: HomeAssistant, mock_omlet, config_entry, hass_client_no_auth, body, refreshes
) -> None:
    """With a token set, only requests carrying it refresh."""
    await _setup(hass, config_entry)
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    coordinator.async_request_refresh = AsyncMock()

    client = await hass_client_no_auth()
    resp = await client.post(WEBHOOK_URL, json=body)
    assert resp.status == 200
    assert coordinator.async_request_refresh.await_count == int(refreshes)


async def test_webhook_token_from_options(
    hass: HomeAssistant, mock_omlet, config_entry, hass_client_no_auth
) -> None:
    """A token set in the options is checked too."""
    hass.config_entries.async_update_entry(config_entry, options={WEBHOOK_TOKEN: "opt"})
    await _setup(hass, config_entry)
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    coordinator.async_request_refresh = AsyncMock()

    client = await hass_client_no_auth()
    await client.post(WEBHOOK_URL, json={"token": "nope"})
    coordinator.async_request_refresh.assert_not_awaited()
    await client.post(WEBHOOK_URL, json={"token": "opt"})
    coordinator.async_request_refresh.assert_awaited_once()


async def test_webhook_without_token_accepts_any(
    hass: HomeAssistant, mock_omlet, config_entry, hass_client_no_auth
) -> None:
    """Without a token set, behaviour is unchanged: any request refreshes."""
    await _setup(hass, config_entry)
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    coordinator.async_request_refresh = AsyncMock()

    client = await hass_client_no_auth()
    await client.post(WEBHOOK_URL, json={})
    coordinator.async_request_refresh.assert_awaited_once()


async def test_webhook_non_json_body(
    hass: HomeAssistant, mock_omlet, config_entry, hass_client_no_auth
) -> None:
    """A body that is not JSON is ignored, not an unhandled error."""
    await _setup(hass, config_entry)
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    coordinator.async_request_refresh = AsyncMock()

    client = await hass_client_no_auth()
    resp = await client.post(WEBHOOK_URL, data=b"not json")
    assert resp.status == 200
    coordinator.async_request_refresh.assert_not_awaited()


async def test_device_keyed_by_device_id(
    hass: HomeAssistant, mock_omlet, config_entry, device_registry: dr.DeviceRegistry
) -> None:
    """Devices are identified by Omlet's device ID, not their name."""
    await _setup(hass, config_entry)
    [device] = dr.async_entries_for_config_entry(device_registry, config_entry.entry_id)
    assert device.identifiers == {(DOMAIN, "door-id")}
    assert device.name == "Chicken Coop"


async def test_device_migrated_from_name(
    hass: HomeAssistant, mock_omlet, config_entry, device_registry: dr.DeviceRegistry
) -> None:
    """A device registered by name up to 1.0.10 keeps its registry entry."""
    old = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "Chicken Coop")},
        name="Chicken Coop",
    )
    await _setup(hass, config_entry)

    migrated = device_registry.async_get(old.id)
    assert migrated.identifiers == {(DOMAIN, "door-id")}
    assert len(dr.async_entries_for_config_entry(device_registry, config_entry.entry_id)) == 1


@pytest.mark.parametrize("devices", [[load_device("door")]])
async def test_renamed_device_keeps_identity(
    hass: HomeAssistant, mock_omlet, config_entry, devices, device_registry: dr.DeviceRegistry
) -> None:
    """Renaming a device in the Omlet app no longer creates a second device."""
    await _setup(hass, config_entry)
    devices[0].name = "Renamed Coop"
    assert await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    assert len(dr.async_entries_for_config_entry(device_registry, config_entry.entry_id)) == 1
