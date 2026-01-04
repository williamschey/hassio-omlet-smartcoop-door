"""Support for Omlet Smart Coop fan."""
from typing import Any

from smartcoop.api.models import Device

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .coordinator import CoopCoordinator
from .entity import OmletBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Omlet Smart Coop fan."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # only add fan entity if device type is Fan
    fans = [
        CoopFan(device, coordinator)
        for device in coordinator.data.values()
        if device.deviceType == "Fan"
    ]
    async_add_entities(fans)


class CoopFan(OmletBaseEntity, FanEntity):
    """Representation of the coop fan."""

    _attr_supported_features = FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF

    def __init__(self, device: Device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Fan"
        super().__init__(device, coordinator, "fan")

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        self._attr_is_on = True
        self.async_write_ha_state()
        await self.coordinator.perform_action(self.device_id, "on")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        self._attr_is_on = False
        self.async_write_ha_state()
        await self.coordinator.perform_action(self.device_id, "off")

    @callback
    def _update_attr(self, device: Device) -> None:
        self.raw_state = device.state.fan.state
        self._attr_is_on = self.raw_state in ("on", "onpending")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return {"raw_state": self.raw_state}
