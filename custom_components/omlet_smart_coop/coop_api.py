"""API for interacting with SmartCoop devices."""

from requests.exceptions import JSONDecodeError
from smartcoop.api.models import Device
from smartcoop.api.omlet import Omlet
from smartcoop.client import SmartCoopClient

from homeassistant.core import HomeAssistant


class SmartCoopAPI:
    """API for interacting with SmartCoop devices."""

    def __init__(self, api_key, hass: HomeAssistant) -> None:
        """Initialize the SmartCoopAPI."""
        self.hass = hass
        client = SmartCoopClient(client_secret=api_key)
        self.omlet = Omlet(client)

    async def get_devices(self) -> list[Device]:
        """Get all devices."""
        return await self.hass.async_add_executor_job(self.omlet.get_devices)

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
        return await self.hass.async_add_executor_job(
            self._wrap_perform_action, omlet_action
        )
