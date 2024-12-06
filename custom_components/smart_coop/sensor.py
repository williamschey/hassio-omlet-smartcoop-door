from homeassistant.helpers.entity import Entity
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    api = hass.data[DOMAIN]["api"]
    devices = hass.data[DOMAIN]["devices"]

    sensors = []
    for device in devices:
        sensors.append(CoobSensor(api, device, "door_state", "Door State"))
        sensors.append(CoobSensor(api, device, "battery", "Battery Level"))
        sensors.append(CoobSensor(api, device, "wifi_strength", "Wi-Fi Strength"))
        sensors.append(CoobSensor(api, device, "light", "Light State"))
    async_add_entities(sensors)


class CoobSensor(Entity):
    def __init__(self, api, device, sensor_type, name):
        self.api = api
        self.device = device
        self.type = sensor_type
        self._name = f"{device.name} {name}"

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self.api.get_device_state(self.device, self.type)
