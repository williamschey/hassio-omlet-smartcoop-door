from homeassistant.components.binary_sensor import BinarySensorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Omlet Smart Coop binary sensors."""
    api = hass.data[DOMAIN]["api"]
    devices = hass.data[DOMAIN]["devices"]

    binary_sensors = [CoopDoorState(api, device) for device in devices]
    async_add_entities(binary_sensors)


class CoopDoorState(BinarySensorEntity):
    """Representation of the coop door state."""

    def __init__(self, api, device):
        self.api = api
        self.device = device
        self._name = f"{device.name} Door State"

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self.api.get_device_state(self.device, "door").state == "open"
