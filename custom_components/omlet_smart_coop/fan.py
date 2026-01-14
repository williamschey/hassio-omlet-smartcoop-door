"""Support for Omlet Smart Coop fan."""
from typing import Any

from smartcoop.api.models import Device
import logging

from homeassistant.components.fan import (
    FanEntity,
    FanEntityFeature,
)
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .coordinator import CoopCoordinator
from .entity import OmletBaseEntity


_LOGGER = logging.getLogger(__name__)


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

    def __init__(self, device: Device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Fan"
        super().__init__(device, coordinator, "fan")

    @property
    def supported_features(self) -> FanEntityFeature:
        """Flag supported features."""
        return FanEntityFeature.TURN_ON | FanEntityFeature.TURN_OFF | FanEntityFeature.PRESET_MODE

    @property
    def preset_modes(self) -> list[str] | None:
        """Return a list of available preset modes."""
        return ["manual", "time", "temperature"]

    @property
    def preset_mode(self) -> str | None:
        """Return the current preset mode."""
        return self.coordinator.data[self.device_id].configuration.fan.mode

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set the preset mode of the fan."""
        if preset_mode not in self.preset_modes:
            raise ValueError(f"Invalid preset mode: {preset_mode}")
            
        device = self.coordinator.data[self.device_id]
        device.configuration.fan.mode = preset_mode
        await self.coordinator.patch_config(device)
        self.async_write_ha_state()

    def _calculate_percentage(self, device: Device) -> int | None:
        """Calculate the current speed percentage based on mode and state."""
        config = device.configuration.fan
        mode = config.mode
        
        if mode == "manual":
            return config.manualSpeed
        
        if mode == "temperature":
            # In app called "Thermostatic"
            return config.tempSpeed
            
        if mode == "time":
            # Check schedules
            # Structure: timeOn1 (HH:MM), timeOff1 (HH:MM), timeSpeed1 (int)
            import datetime
            now = datetime.datetime.now().time()
            
            # Helper to parse time string "HH:MM"
            def parse_time(t_str):
                try:
                    return datetime.datetime.strptime(t_str, "%H:%M").time()
                except (ValueError, TypeError):
                    return None

            # Check 4 slots
            for i in range(1, 5):
                on_str = getattr(config, f"timeOn{i}", None)
                off_str = getattr(config, f"timeOff{i}", None)
                speed = getattr(config, f"timeSpeed{i}", 100)
                
                start = parse_time(on_str)
                end = parse_time(off_str)
                
                if start and end and start != end:
                    # Handle crossing midnight
                    if start < end:
                        if start <= now < end:
                            return speed
                    else: # Crosses midnight
                        if start <= now or now < end:
                            return speed
                            
            # If no schedule active, return default 100
            return 100
            
        return None

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn on the fan."""
        self._attr_is_on = True
        # Calculate percentage for the on state
        device = self.coordinator.data[self.device_id]
        self._attr_percentage = self._calculate_percentage(device)
        self.async_write_ha_state()
        await self.coordinator.perform_action(self.device_id, "on")

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn off the fan."""
        self._attr_is_on = False
        self._attr_percentage = None  # Explicitly set to None when off
        self.async_write_ha_state()
        await self.coordinator.perform_action(self.device_id, "off")

    @callback
    def _update_attr(self, device: Device) -> None:
        self.raw_state = device.state.fan.state
                
        self._attr_is_on = state_str in ("on", "onpending")
        
        # Set percentage based on state - must be synchronized with is_on
        if self._attr_is_on:
            self._attr_percentage = self._calculate_percentage(device)
        else:
            self._attr_percentage = None
    
    @property
    def is_on(self):
        """Return true if the fan is on."""
        return self.raw_state in ("on", "onpending")

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return {"raw_state": self.raw_state}
