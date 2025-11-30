"""Support for Omlet Smart Coop Door."""
from datetime import timedelta

from smartcoop.api.models import Device

from typing import Any

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

    lights = []
    for device in coordinator.data.values():
        if hasattr(device.state, "light") and device.state.light:
            lights.append(CoopCover(device, coordinator))
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
        self._attr_is_opening = True 
        self._attr_is_closing = False       
        self.async_write_ha_state()
        self.coordinator.update_interval = timedelta(seconds=10)
        await self.coordinator.perform_action(self.device_id, "open")

    async def async_close_cover(self):
        """Close the door."""
        self._attr_is_opening = False 
        self._attr_is_closing = True  
        self.async_write_ha_state()
        self.coordinator.update_interval = timedelta(seconds=10)
        await self.coordinator.perform_action(self.device_id, "close")


    async def async_stop_cover(self):
        """Stop the door."""
        self._attr_is_opening = False 
        self._attr_is_closing = False  
        self.async_write_ha_state()
        await self.coordinator.perform_action(self.device_id, "stop")

    @callback
    def _update_attr(self, device: Device) -> None:
        self.raw_state = device.state.door.state
        if self.raw_state == "stopping":
            return
        self._attr_is_closed = self.raw_state == "closed"
        self._attr_is_closing = self.raw_state in ("closing", "closepending")
        self._attr_is_opening = self.raw_state in ("opening", "openpending")
        # if opening or closing, poll ever 10 secs, otherwise poll every 60 secs
        if (not self._attr_is_closing and not self._attr_is_opening):
            if (timedelta(seconds=60).__ne__(self.coordinator.update_interval)):
                self.coordinator.update_interval = timedelta(seconds=60)

    
    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return {"raw_state": self.raw_state}
