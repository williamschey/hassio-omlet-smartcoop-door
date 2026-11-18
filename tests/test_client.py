"""The SDK client wrapper: every request has a timeout."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from homeassistant.core import HomeAssistant

from custom_components.omlet_smart_coop.coop_api import (
    REQUEST_TIMEOUT,
    SmartCoopAPI,
    TimeoutSmartCoopClient,
)
from custom_components.omlet_smart_coop.const import API_TIMEOUT

from .helpers import http_error

REQUEST = "custom_components.omlet_smart_coop.coop_api.requests.request"


def _response(status: int = 200, body=None) -> MagicMock:
    response = MagicMock(status_code=status)
    response.json.return_value = body
    if status >= 400:
        response.raise_for_status.side_effect = http_error(status)
    return response


async def test_api_uses_timeout_client(hass: HomeAssistant) -> None:
    """Review point 1: the integration's API uses the client with a timeout."""
    api = SmartCoopAPI("key", hass)
    assert isinstance(api.omlet.client, TimeoutSmartCoopClient)


def test_request_timeout_is_shorter_than_backstop() -> None:
    """A stalled request gives up before Home Assistant stops waiting."""
    assert sum(REQUEST_TIMEOUT) < API_TIMEOUT


@pytest.mark.parametrize(
    ("method", "args", "http_method", "kwargs", "body", "expected"),
    [
        ("get", ("device",), "GET", {"params": None}, [{"a": 1}], [{"a": 1}]),
        ("post", ("device/x/action/open",), "POST", {"json": None}, {"ok": True}, {"ok": True}),
        ("patch", ("device/x/configuration", {"c": 1}), "PATCH", {"json": {"c": 1}}, None, None),
        ("delete", ("group/1",), "DELETE", {}, None, None),
    ],
)
def test_every_request_has_timeout(method, args, http_method, kwargs, body, expected) -> None:
    """Each SDK verb sends the bearer key with a timeout, and matches the SDK's return."""
    client = TimeoutSmartCoopClient(client_secret="the-key")
    with patch(REQUEST, return_value=_response(body=body)) as request:
        assert getattr(client, method)(*args) == expected

    request.assert_called_once()
    assert request.call_args.args == (http_method, f"{client.base_url}/{args[0]}")
    assert request.call_args.kwargs["timeout"] == REQUEST_TIMEOUT
    assert request.call_args.kwargs["headers"]["Authorization"] == "Bearer the-key"
    for key, value in kwargs.items():
        assert request.call_args.kwargs[key] == value


def test_post_204_returns_none() -> None:
    """A 204 from an action has no body, as the SDK expects."""
    client = TimeoutSmartCoopClient(client_secret="k")
    with patch(REQUEST, return_value=_response(status=204)) as request:
        assert client.post("device/x/action/open") is None
    request.return_value.json.assert_not_called()


def test_http_errors_raise() -> None:
    """HTTP errors still raise requests.HTTPError, which the API maps."""
    client = TimeoutSmartCoopClient(client_secret="k")
    with patch(REQUEST, return_value=_response(status=401)), pytest.raises(
        requests.HTTPError
    ):
        client.get("device")


def test_request_timeout_raises() -> None:
    """A stalled request raises requests.Timeout instead of blocking."""
    client = TimeoutSmartCoopClient(client_secret="k")
    with patch(REQUEST, side_effect=requests.Timeout("read timed out")), pytest.raises(
        requests.Timeout
    ):
        client.get("device")
