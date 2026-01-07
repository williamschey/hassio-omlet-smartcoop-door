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

    @property
    def percentage(self) -> int | None:
        """Return the current speed percentage."""
        device = self.coordinator.data[self.device_id]
        config = device.configuration.fan
        
        # If fan is off, percentage is None (or 0, but HA prefers None for off)
        if not self._attr_is_on:
            return None

        mode = config.mode
        
        if mode == "manual":
            return config.manualSpeed
        
        if mode == "temperature":
            # In app called "Thermostatic"
            return config.tempSpeed
            
        if mode == "time":
            # Check schedules
            # Structure: timeOn1 (HH:MM), timeOff1 (HH:MM), timeSpeed1 (int)
            # Default behavior if no schedule matches: 100 per user request logic?
            # User said: "defaults .. timeSpeed = 100"
            # And "IF state=on AND mode=time AND current time is between timeOn and timeOff ... THEN timeSpeedX"
            
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
        
        if preset_mode:
             await self.async_set_preset_mode(preset_mode)

        # If percentage is provided, we can't really set slightly arbitrary speed 
        # because the device uses modes. 
        # But if the user sets speed, logic suggests we might want to switch to Manual 
        # and set manualSpeed? 
        # The user req didn't specify "Setting speed" logic, only "Reading speed".
        # For now, I will just turn it on.
        
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
        # Attributes are updated via properties usage of self.coordinator.data
        # trigger update of state

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        return {"raw_state": self.raw_state}
