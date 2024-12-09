"""Define the Omlet Smart Coop data coordinator."""

from datetime import timedelta
import logging

from smartcoop.api.models import Device

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import API_KEY
from .coop_api import SmartCoopAPI

_LOGGER = logging.getLogger(__name__)


class CoopCoordinator(DataUpdateCoordinator[dict[str, Device]]):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize my coordinator."""

        super().__init__(
            hass,
            _LOGGER,
            name="omlet_data",
            update_method=self._async_update_data,
            update_interval=timedelta(seconds=120),
        )

        self._api = SmartCoopAPI(entry.data[API_KEY], hass)

    async def _async_update_data(self) -> dict[str, Device]:
        devices = await self._api.get_devices()
        return {d.deviceId: d for d in devices if d.deviceType == "Autodoor"}

    async def perform_action(self, device_id, key):
        """Perform an action on a device."""
        await self._api.perform_action(self.data[device_id], key)
        await self.async_request_refresh()
