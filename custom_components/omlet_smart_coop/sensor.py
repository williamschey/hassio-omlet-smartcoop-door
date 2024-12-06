from homeassistant.helpers.entity import SensorEntity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Omlet Smart Coop sensors."""
    api = hass.data[DOMAIN]["api"]
    devices = hass.data[DOMAIN]["devices"]

    sensors = []
    for device in devices:
        sensors.append(CoopSensor(api, device, "battery", "Battery Level"))
        sensors.append(CoopSensor(api, device, "wifi_strength", "Wi-Fi Strength"))
    async_add_entities(sensors)


class CoopSensor(SensorEntity):
    """Representation of a Smart Coop sensor."""

    def __init__(self, api, device, key, name):
        self.api = api
        self.device = device
        self.key = key
        self._name = f"{device.name} {name}"

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self.api.get_device_state(self.device, self.key)
