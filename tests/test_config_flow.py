"""Config, reauth and options flows."""

import pytest
import requests

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.omlet_smart_coop.const import API_KEY, DOMAIN, WEBHOOK_TOKEN

from .conftest import API_KEY_VALUE
from .helpers import http_error


async def _start(hass: HomeAssistant):
    return await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )


async def test_user_flow_creates_entry(hass: HomeAssistant, mock_omlet) -> None:
    """A key Omlet accepts creates the entry; the webhook token is optional."""
    result = await _start(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {API_KEY: f"  {API_KEY_VALUE} ", WEBHOOK_TOKEN: " secret "}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {API_KEY: API_KEY_VALUE, WEBHOOK_TOKEN: "secret"}


async def test_user_flow_without_webhook_token(hass: HomeAssistant, mock_omlet) -> None:
    """No webhook token stores none."""
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {API_KEY: API_KEY_VALUE}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {API_KEY: API_KEY_VALUE}


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        # Fixed: the SDK raises requests.HTTPError, which was not caught.
        (http_error(401), "invalid_api_key"),
        (http_error(403), "invalid_api_key"),
        (http_error(500), "cannot_connect"),
        (requests.ConnectionError("down"), "cannot_connect"),
        (requests.Timeout("slow"), "cannot_connect"),
        (RuntimeError("boom"), "unknown"),
    ],
)
async def test_user_flow_errors(
    hass: HomeAssistant, mock_omlet, error, expected
) -> None:
    """Errors are shown on the form, and the user can then retry."""
    mock_omlet.get_devices.side_effect = error
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {API_KEY: "bad"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected}

    mock_omlet.get_devices.side_effect = None
    mock_omlet.get_devices.return_value = []
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {API_KEY: API_KEY_VALUE}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_user_flow_rejects_duplicate_key(
    hass: HomeAssistant, mock_omlet, config_entry
) -> None:
    """The same API key cannot be added twice."""
    result = await _start(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {API_KEY: API_KEY_VALUE}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_reauth_updates_key(hass: HomeAssistant, mock_omlet, config_entry) -> None:
    """Reauth stores the new key and reloads the entry."""
    result = await config_entry.start_reauth_flow(hass)
    assert result["step_id"] == "reauth_confirm"

    mock_omlet.get_devices.side_effect = http_error(401)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {API_KEY: "still-bad"}
    )
    assert result["errors"] == {"base": "invalid_api_key"}

    mock_omlet.get_devices.side_effect = None
    mock_omlet.get_devices.return_value = []
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {API_KEY: "new-key"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert config_entry.data[API_KEY] == "new-key"


async def test_options_flow_sets_and_clears_token(
    hass: HomeAssistant, mock_omlet, config_entry
) -> None:
    """The webhook token can be set after setup, and cleared."""
    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {WEBHOOK_TOKEN: " later "}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert config_entry.options == {WEBHOOK_TOKEN: "later"}

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {WEBHOOK_TOKEN: ""}
    )
    assert config_entry.options == {}
