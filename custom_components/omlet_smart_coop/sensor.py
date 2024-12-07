from .const import DOMAIN, API, DEVICES, COORDINATOR
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Omlet Smart Coop sensors."""
    api = hass.data[DOMAIN][API]
    devices = hass.data[DOMAIN][DEVICES]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    sensors = []
    for device in devices:
        sensors.append(CoopBatterySensor(api, coordinator, device))
        sensors.append(CoopWifiStrength(api, coordinator, device))
    async_add_entities(sensors)


class CoopBatterySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Smart Coop battery sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api, coordinator, device):
        self.api = api
        self.device = device
        self._attr_name = f"{device.name} Battery Level"
        self._attr_unique_id = f"{device.deviceId}_batt"
        super().__init__(coordinator)

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

class CoopWifiStrength(CoordinatorEntity, SensorEntity):
    """Representation of a Smart Coop wifi sensor."""

    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api, coordinator, device):
        self.api = api
        self.device = device
        self._attr_name = f"{device.name} Wi-Fi Strength"
        self._attr_unique_id = f"{device.deviceId}_wifi"
        super().__init__(coordinator)

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