"""API for interacting with SmartCoop devices."""

import asyncio

from requests.exceptions import HTTPError, JSONDecodeError, RequestException
from smartcoop.api.models import Device
from smartcoop.api.omlet import Omlet
from smartcoop.client import SmartCoopClient

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import API_TIMEOUT


class OmletAuthError(HomeAssistantError):
    """The Omlet API rejected the API key."""


class OmletConnectionError(HomeAssistantError):
    """The Omlet API could not be reached, timed out or returned an error."""


def is_auth_error(err: HTTPError) -> bool:
    """Return True if an HTTP error means the API key was rejected."""
    return err.response is not None and err.response.status_code in (401, 403)


class SmartCoopAPI:
    """API for interacting with SmartCoop devices."""

    def __init__(self, api_key, hass: HomeAssistant) -> None:
        """Initialize the SmartCoopAPI."""
        self.hass = hass
        client = SmartCoopClient(client_secret=api_key)
        self.omlet = Omlet(client)

    async def _call(self, func, *args):
        """Run a blocking SDK call in the executor, bounded and with mapped errors.

        The SDK sets no timeout on its requests, so asyncio.timeout bounds how
        long Home Assistant waits for an answer.
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
        omlet_action = next(
            (action for action in device.actions if action.name == key), None
        )
        if omlet_action is None:
            raise HomeAssistantError(
                f"{device.name} does not offer the '{key}' action right now"
            )
        return await self._call(self._wrap_perform_action, omlet_action)

    async def patch_config(self, device):
        """Patch the configuration of a device."""
        return await self._call(
            self.omlet.update_configuration, device.deviceId, device.configuration
        )
