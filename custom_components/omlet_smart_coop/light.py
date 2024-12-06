from homeassistant.components.light import LightEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Omlet Smart Coop light."""
    api = hass.data[DOMAIN]["api"]
    devices = hass.data[DOMAIN]["devices"]

    lights = [CoopLight(api, device) for device in devices]
    async_add_entities(lights)


class CoopLight(LightEntity):
    """Representation of the coop light."""

    def __init__(self, api, device):
        self.api = api
        self.device = device
        self._name = f"{device.name} Light"

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self.api.get_device_state(self.device, "light").state

    async def async_turn_on(self, **kwargs):
        await self.api.perform_action(self.device, "on", True)

    async def async_turn_off(self, **kwargs):
        await self.api.perform_action(self.device, "off", False)
