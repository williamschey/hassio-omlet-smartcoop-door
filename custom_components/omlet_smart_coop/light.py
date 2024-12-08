from homeassistant.components.light import LightEntity

from .coop_api import SmartCoopAPI
from .coordinator import CoopCoordinator
from .const import DOMAIN, API, DEVICES, COORDINATOR
from .entity import OmletBaseEntity

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Omlet Smart Coop light."""
    api = hass.data[DOMAIN][API]
    devices = hass.data[DOMAIN][DEVICES]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    lights = [CoopLight(api, coordinator, device) for device in devices]
    async_add_entities(lights)


class CoopLight(OmletBaseEntity, LightEntity):
    """Representation of the coop light."""

    def __init__(self, api: SmartCoopAPI, coordinator: CoopCoordinator, device):
        self._attr_name = f"{device.name} Light"
        self._attr_color_mode = None
        super().__init__(api, coordinator, device, "light")

    @property
    def color_mode(self):
        return self._attr_color_mode
    
    @property
    def is_on(self):
        self.update()
        return self._attr_is_on
    
    async def async_turn_on(self, **kwargs):
        self.api.perform_action(self.device, "on")
        # Update the data
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        self.api.perform_action(self.device, "off")
        # Update the data
        await self.coordinator.async_request_refresh()

    def update(self):
        self.device = self.api.get_device(self.device)
        self._attr_is_on = self.api.get_device_state(self.device, "light").state == 'on'