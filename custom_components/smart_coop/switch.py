from homeassistant.components.switch import SwitchEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    api = hass.data[DOMAIN]["api"]
    devices = hass.data[DOMAIN]["devices"]

    switches = [CoopDoorSwitch(api, device) for device in devices]
    async_add_entities(switches)


class CoopDoorSwitch(SwitchEntity):
    def __init__(self, api, device):
        self.api = api
        self.device = device
        self._name = f"{device.name} Door Control"

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self.api.get_device_state(self.device, "door_state") == "open"

    async def async_turn_on(self, **kwargs):
        await self.api.set_door_state(self.device, True)

    async def async_turn_off(self, **kwargs):
        await self.api.set_door_state(self.device, False)
