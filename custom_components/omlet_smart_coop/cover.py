"""Support for Omlet Smart Coop Door."""

from smartcoop.api.models import Device

from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .coordinator import CoopCoordinator
from .entity import OmletBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Omlet Smart Coop cover."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    lights = [CoopCover(device, coordinator) for device in coordinator.data.values()]
    async_add_entities(lights)


class CoopCover(OmletBaseEntity, CoverEntity):
    """Representation of the coop door."""

    _attr_device_class = CoverDeviceClass.DOOR
    _attr_supported_features: CoverEntityFeature = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Door"
        super().__init__(device, coordinator, "cover")

    async def async_open_cover(self):
        """Open the door."""
        await self.coordinator.perform_action(self.device_id, "open")

    async def async_close_cover(self):
        """Close the door."""
        await self.coordinator.perform_action(self.device_id, "close")

    async def async_stop_cover(self):
        """Stop the door."""
        await self.coordinator.perform_action(self.device_id, "stop")

    @callback
    def _update_attr(self, device: Device) -> None:
        state = device.state.door.state
        if state == "stopping":
            return
        self._attr_is_closed = state == "closed"
        self._attr_is_closing = state == "closepending"
        self._attr_is_opening = state == "openpending"
