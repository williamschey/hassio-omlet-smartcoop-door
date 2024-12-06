from homeassistant.components.cover import CoverEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Omlet Smart Coop light."""
    api = hass.data[DOMAIN]["api"]
    devices = hass.data[DOMAIN]["devices"]

    lights = [CoopCover(api, device) for device in devices]
    async_add_entities(lights)


class CoopCover(CoverEntity):
    """Representation of the coop door."""

    def __init__(self, api, device):
        self.api = api
        self.device = device
        self._name = f"{device.name} Door"
    
    @property
    def name(self):
        return self._name

    @property
    def is_closed(self) -> bool:
        return self.api.get_device_state(self.device, "door").state == "closed"
    

    @property
    def is_closing(self) -> bool:
        return self.api.get_device_state(self.device, "door").state == "closing"

    @property
    def is_opening(self) -> bool:
        return self.api.get_device_state(self.device, "door").state == "opening"

    async def async_open_cover(self, **kwargs):
        await self.api.perform_action(self.device, "open")

    async def async_close_cover(self, **kwargs):
        await self.api.perform_action(self.device, "close")
