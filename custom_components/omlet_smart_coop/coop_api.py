"""API for interacting with SmartCoop devices."""

import asyncio

import requests
from requests.exceptions import HTTPError, JSONDecodeError, RequestException
from smartcoop.api.models import Device
from smartcoop.api.omlet import Omlet
from smartcoop.client import SmartCoopClient

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import API_TIMEOUT

# (connect, read) seconds for each HTTP request. Shorter than API_TIMEOUT, so a
# stalled request frees its executor thread before Home Assistant stops waiting.
REQUEST_TIMEOUT = (10, 15)


class OmletAuthError(HomeAssistantError):
    """The Omlet API rejected the API key."""


class OmletConnectionError(HomeAssistantError):
    """The Omlet API could not be reached, timed out or returned an error."""


def is_auth_error(err: HTTPError) -> bool:
    """Return True if an HTTP error means the API key was rejected."""
    return err.response is not None and err.response.status_code in (401, 403)


class TimeoutSmartCoopClient(SmartCoopClient):
    """The SDK's client, with a timeout on every request.

    smartcoop-python-sdk 1.1.7 calls requests without a timeout, so a stalled
    connection would block its executor thread indefinitely. These methods
    match the SDK's own return values.
    """

    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        response = requests.request(
            method,
            f"{self.base_url}/{endpoint}",
            headers=self._get_headers(),
            timeout=REQUEST_TIMEOUT,
            **kwargs,
        )
        response.raise_for_status()
        return response

    def get(self, endpoint, params=None):
        """GET an endpoint and return its JSON."""
        return self._request("GET", endpoint, params=params).json()

    def post(self, endpoint, json=None):
        """POST to an endpoint and return its JSON, if any."""
        response = self._request("POST", endpoint, json=json)
        if response.status_code != 204:
            return response.json()
        return None

    def patch(self, endpoint, json=None):
        """PATCH an endpoint."""
        self._request("PATCH", endpoint, json=json)

    def delete(self, endpoint):
        """DELETE an endpoint."""
        self._request("DELETE", endpoint)


def find_action(device, key):
    """Return the device's action with this name, or raise if it has none."""
    action = next((action for action in device.actions if action.name == key), None)
    if action is None:
        raise HomeAssistantError(
            f"{device.name} does not offer the '{key}' action right now"
        )
    return action


class SmartCoopAPI:
    """API for interacting with SmartCoop devices."""

    def __init__(self, api_key, hass: HomeAssistant) -> None:
        """Initialize the SmartCoopAPI."""
        self.hass = hass
        client = TimeoutSmartCoopClient(client_secret=api_key)
        self.omlet = Omlet(client)

    async def _call(self, func, *args):
        """Run a blocking SDK call in the executor, bounded and with mapped errors.

        Each request has its own timeout (REQUEST_TIMEOUT); asyncio.timeout is
        a backstop on the whole call.
        """
        try:
            async with asyncio.timeout(API_TIMEOUT):
                return await self.hass.async_add_executor_job(func, *args)
        except HTTPError as err:
            if is_auth_error(err):
                raise OmletAuthError("Omlet rejected the API key") from err
            raise OmletConnectionError(f"Omlet API error: {err}") from err
        except (RequestException, TimeoutError) as err:
            raise OmletConnectionError(
                f"Error communicating with the Omlet API: {err!r}"
            ) from err

    async def get_devices(self) -> list[Device]:
        """Get all devices."""
        return await self._call(self.omlet.get_devices)

    def _wrap_perform_action(self, omlet_action):
        try:
            return self.omlet.perform_action(omlet_action)
        except JSONDecodeError:
            # ignore
            return None

    async def perform_action(self, device, key):
        """Set a specific state for a device."""
        omlet_action = find_action(device, key)
        return await self._call(self._wrap_perform_action, omlet_action)

    async def patch_config(self, device):
        """Patch the configuration of a device."""
        return await self._call(
            self.omlet.update_configuration, device.deviceId, device.configuration
        )
