"""Support for Omlet Smart Coop light."""

from smartcoop.api.models import Device

from homeassistant.components.light import ColorMode, LightEntity
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN
from .coordinator import CoopCoordinator
from .entity import OmletBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Omlet Smart Coop light."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    lights = [CoopLight(device, coordinator) for device in coordinator.data.values()]
    async_add_entities(lights)


class CoopLight(OmletBaseEntity, LightEntity):
    """Representation of the coop light."""

    _attr_color_mode = ColorMode.ONOFF
    _attr_supported_color_modes = {ColorMode.ONOFF}

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Light"
        super().__init__(device, coordinator, "light")

    async def async_turn_on(self):
        """Turn on the light."""
        await self.coordinator.perform_action(self.device_id, "on")

    async def async_turn_off(self):
        """Turn off the light."""
        await self.coordinator.perform_action(self.device_id, "off")

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_is_on = device.state.light.state in ("on", "onpending")
