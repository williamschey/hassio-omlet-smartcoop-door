"""Define the Omlet Smart Coop data coordinator."""

import asyncio
from datetime import timedelta
import logging

from smartcoop.api.models import Device

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import API_KEY
from .coop_api import OmletAuthError, OmletConnectionError, SmartCoopAPI

_LOGGER = logging.getLogger(__name__)

NORMAL_UPDATE_INTERVAL = timedelta(seconds=60)
FAST_UPDATE_INTERVAL = timedelta(seconds=10)


class CoopCoordinator(DataUpdateCoordinator[dict[str, Device]]):
    """My custom coordinator."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize my coordinator."""

        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name="omlet_data",
            update_method=self._async_update_data,
            update_interval=NORMAL_UPDATE_INTERVAL,
        )

        self._api = SmartCoopAPI(entry.data[API_KEY], hass)
        self._moving: set[str] = set()

    async def _async_update_data(self) -> dict[str, Device]:
        try:
            devices = await self._api.get_devices()
        except OmletAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except OmletConnectionError as err:
            raise UpdateFailed(str(err)) from err
        return {d.deviceId: d for d in devices if d.deviceType in ("Autodoor", "Fan", "Feeder")}

    @callback
    def set_moving(self, key: str, moving: bool) -> None:
        """Record whether an entity is moving, and poll faster while any is."""
        if moving:
            self._moving.add(key)
        else:
            self._moving.discard(key)
        self.update_interval = (
            FAST_UPDATE_INTERVAL if self._moving else NORMAL_UPDATE_INTERVAL
        )

    async def perform_action(self, device_id, key):
        """Perform an action on a device."""
        await self._api.perform_action(self.data[device_id], key)
        await asyncio.sleep(10)
        # Allow time for API to communicate with device.
        await self.async_request_refresh()

    async def patch_config(self, device):
        """Patch the configuration of a device."""
        await self._api.patch_config(device)
        await self.async_request_refresh()
