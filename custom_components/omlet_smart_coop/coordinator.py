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
from .coop_api import OmletAuthError, OmletConnectionError, SmartCoopAPI, find_action

_LOGGER = logging.getLogger(__name__)

NORMAL_UPDATE_INTERVAL = timedelta(seconds=60)
FAST_UPDATE_INTERVAL = timedelta(seconds=10)

# Door and feeder states while they move, and the actions that start a move.
MOVING_STATES = frozenset({"opening", "closing", "openpending", "closepending"})
MOVE_ACTIONS = frozenset({"open", "close"})


def is_moving(device: Device) -> bool:
    """Return True if the device's door or feeder hatch is moving."""
    state = getattr(device, "state", None)
    for part in ("door", "feeder"):
        if getattr(getattr(state, part, None), "state", None) in MOVING_STATES:
            return True
    return False


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

    async def _async_update_data(self) -> dict[str, Device]:
        try:
            devices = await self._api.get_devices()
        except OmletAuthError as err:
            raise ConfigEntryAuthFailed(str(err)) from err
        except OmletConnectionError as err:
            raise UpdateFailed(str(err)) from err
        data = {d.deviceId: d for d in devices if d.deviceType in ("Autodoor", "Fan", "Feeder")}
        # Poll every 10 secs while anything is moving, otherwise every 60 secs.
        # The next refresh is scheduled after this returns, at this interval.
        self.update_interval = (
            FAST_UPDATE_INTERVAL
            if any(is_moving(d) for d in data.values())
            else NORMAL_UPDATE_INTERVAL
        )
        return data

    @callback
    def check_action(self, device_id, key) -> None:
        """Raise HomeAssistantError if the device doesn't offer this action."""
        find_action(self.data[device_id], key)

    async def perform_action(self, device_id, key):
        """Perform an action on a device."""
        await self._api.perform_action(self.data[device_id], key)
        if key in MOVE_ACTIONS:
            self.update_interval = FAST_UPDATE_INTERVAL
        await asyncio.sleep(10)
        # Allow time for API to communicate with device.
        await self.async_request_refresh()

    async def patch_config(self, device):
        """Patch the configuration of a device."""
        await self._api.patch_config(device)
        await self.async_request_refresh()
