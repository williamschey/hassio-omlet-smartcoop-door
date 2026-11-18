"""Support for Omlet Smart Coop Door and Feeder."""
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
from .entity import OmletOperationalEntity
async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Omlet Smart Coop cover."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    covers = []
    for device in coordinator.data.values():
        if device.deviceType == "Autodoor":
            covers.append(CoopCover(device, coordinator))
        if device.deviceType == "Feeder":
            covers.append(FeederCover(device, coordinator))
    async_add_entities(covers)
class OmletCoverEntity(OmletOperationalEntity, CoverEntity):
    """A door or feeder hatch that opens and closes on command."""

    async def _async_command(self, key: str, *, opening: bool, closing: bool) -> None:
        """Send an action, showing the move optimistically until it reports back."""
        # Check first, so a device without the action keeps its state.
        self.coordinator.check_action(self.device_id, key)
        self._attr_is_opening = opening
        self._attr_is_closing = closing
        self.async_write_ha_state()
        try:
            await self.coordinator.perform_action(self.device_id, key)
        except Exception:
            # Back to the last state the device reported.
            self._update_attr(self.coordinator.data[self.device_id])
            self.async_write_ha_state()
            raise


class CoopCover(OmletCoverEntity):
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
        await self._async_command("open", opening=True, closing=False)
    async def async_close_cover(self):
        """Close the door."""
        await self._async_command("close", opening=False, closing=True)
    async def async_stop_cover(self):
        """Stop the door."""
        await self._async_command("stop", opening=False, closing=False)
    @callback
    def _update_attr(self, device: Device) -> None:
        self.raw_state = device.state.door.state
        if self.raw_state == "stopping":
            return
        self._attr_is_closed = self.raw_state == "closed"
        self._attr_is_closing = self.raw_state in ("closing", "closepending")
        self._attr_is_opening = self.raw_state in ("opening", "openpending")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return {"raw_state": self.raw_state}
class FeederCover(OmletCoverEntity):
    """Representation of the feeder hatch."""
    _attr_device_class = CoverDeviceClass.DOOR
    _attr_supported_features: CoverEntityFeature = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE
    )
    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Feeder"
        super().__init__(device, coordinator, "feeder_cover")
    async def async_open_cover(self):
        """Open the feeder."""
        await self._async_command("open", opening=True, closing=False)
    async def async_close_cover(self):
        """Close the feeder."""
        await self._async_command("close", opening=False, closing=True)
    @callback
    def _update_attr(self, device: Device) -> None:
        self.raw_state = device.state.feeder.state
        self._attr_is_closed = self.raw_state == "closed"
        self._attr_is_closing = self.raw_state in ("closing", "closepending")
        self._attr_is_opening = self.raw_state in ("opening", "openpending")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return {"raw_state": self.raw_state}
