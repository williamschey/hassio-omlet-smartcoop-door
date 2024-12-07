from .const import DOMAIN
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.helpers.entity import generate_entity_id

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Omlet Smart Coop sensors."""
    api = hass.data[DOMAIN]["api"]
    devices = hass.data[DOMAIN]["devices"]

    sensors = []
    for device in devices:
        sensors.append(CoopBatterySensor(api, device))
        sensors.append(CoopWifiStrength(api, device))
    async_add_entities(sensors)


class CoopBatterySensor(SensorEntity):
    """Representation of a Smart Coop battery sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api, device):
        self.api = api
        self.device = device
        self._attr_name = f"{device.name} Battery Level"
        self._attr_unique_id = f"{device.deviceId}_batt"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def name(self):
        return self._attr_name

    @property
    def state(self):
        state = self.api.get_device_state(self.device, "general")
        return getattr(state, "batteryLevel")
    
    @property
    def last_updated(self):
        return self.api.last_updated()
    
    def update(self):
        self.device = self.api.get_device(self.device)

class CoopWifiStrength(SensorEntity):
    """Representation of a Smart Coop wifi sensor."""

    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api, device):
        self.api = api
        self.device = device
        self._attr_name = f"{device.name} Wi-Fi Strength"
        self._attr_unique_id = f"{device.deviceId}_wifi"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def name(self):
        return self._attr_name

    @property
    def state(self):
        state = self.api.get_device_state(self.device, "connectivity")
        return getattr(state, "wifiStrength")
    
    @property
    def last_updated(self):
        return self.api.last_updated()
    
    def update(self):
        self.device = self.api.get_device(self.device)