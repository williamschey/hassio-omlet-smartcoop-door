from datetime import datetime, timedelta
from .const import DOMAIN, API, DEVICES, COORDINATOR
from .entity import OmletBaseEntity
from .coop_api import SmartCoopAPI
from .coordinator import CoopCoordinator
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.helpers.entity import EntityCategory
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    LIGHT_LUX,
    UnitOfTime,
) 
from homeassistant.util import dt

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Omlet Smart Coop sensors."""
    api = hass.data[DOMAIN][API]
    devices = hass.data[DOMAIN][DEVICES]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    sensors = []
    for device in devices:
        sensors.append(CoopBatterySensor(api, coordinator, device))
        sensors.append(CoopWifiStrength(api, coordinator, device))
        sensors.append(CoopUpdateTime(api, coordinator, device))
        sensors.append(CoopPollingInterval(api, coordinator, device))
        sensors.append(CoopLightLevel(api, coordinator, device))
        sensors.append(CoopOpenTime(api, coordinator, device))
        sensors.append(CoopCloseTime(api, coordinator, device))
        sensors.append(CoopNextUpdateTime(api, coordinator, device))
    async_add_entities(sensors)


class CoopBatterySensor(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop battery sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api: SmartCoopAPI, coordinator: CoopCoordinator, device):
        self._attr_name = f"{device.name} Battery Level"
        super().__init__(api, coordinator, device, "battery")

    @property
    def state(self):
        self.update()
        return self._attr_native_value
            
    def update(self):
        self.device = self.api.get_device(self.device)
        state = self.api.get_device_state(self.device, "general")
        self._attr_native_value = getattr(state, "batteryLevel")

class CoopWifiStrength(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop wifi sensor."""

    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT
    
    def __init__(self, api: SmartCoopAPI, coordinator: CoopCoordinator, device):
        self._attr_name = f"{device.name} Wi-Fi Strength"
        super().__init__(api, coordinator, device, "wifi")

    @property
    def state(self):
        self.update()
        return self._attr_native_value
            
    def update(self):
        self.device = self.api.get_device(self.device)
        state = self.api.get_device_state(self.device, "connectivity")
        self._attr_native_value = getattr(state, "wifiStrength")

class CoopUpdateTime(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop last update time."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer"
    
    def __init__(self, api: SmartCoopAPI, coordinator: CoopCoordinator, device):
        self._attr_name = f"{device.name} Last Updated"
        super().__init__(api, coordinator, device, "last_updated")

    @property
    def native_value(self) -> datetime:
        self.update()
        return self._attr_native_value
            
    def update(self):
        self.device = self.api.get_device(self.device)
        state = self.api.get_device_config(self.device, "general")
        last_time = getattr(state, "datetime")
        if isinstance(last_time, str):
            strippedTime = datetime.strptime(last_time[:-6], '%Y-%m-%dT%H:%M:%S')
            self._attr_native_value = dt.as_local(strippedTime)

class CoopPollingInterval(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop last update time."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer-sync"
    
    def __init__(self, api: SmartCoopAPI, coordinator: CoopCoordinator, device):
        self._attr_name = f"{device.name} Polling Interval"
        super().__init__(api, coordinator, device, "polling_interval")

    @property
    def native_value(self) -> int:
        self.update()
        return self._attr_native_value
            
    def update(self):
        self.device = self.api.get_device(self.device)
        state = self.api.get_device_config(self.device, "general")
        self._attr_native_value = getattr(state, "pollFreq")

class CoopNextUpdateTime(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop next update time."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer"
    
    def __init__(self, api: SmartCoopAPI, coordinator: CoopCoordinator, device):
        self._attr_name = f"{device.name} Next Update"
        super().__init__(api, coordinator, device, "next_update")

    @property
    def native_value(self) -> datetime:
        self.update()
        return self._attr_native_value
        
    def update(self):
        self.device = self.api.get_device(self.device)
        state = self.api.get_device_config(self.device, "general")
        last_time = getattr(state, "datetime")
        poll_freq = getattr(state, "pollFreq")
        if isinstance(last_time, str):
            strippedTime = datetime.strptime(last_time[:-6], '%Y-%m-%dT%H:%M:%S') + timedelta(seconds=poll_freq)
            self._attr_native_value = dt.as_local(strippedTime)

class CoopLightLevel(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop last update time."""

    _attr_device_class = SensorDeviceClass.ILLUMINANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = LIGHT_LUX
    
    def __init__(self, api: SmartCoopAPI, coordinator: CoopCoordinator, device):
        self._attr_name = f"{device.name} Light Level"
        super().__init__(api, coordinator, device, "light_level")

    @property
    def native_value(self) -> int:
        self.update()
        return self._attr_native_value
            
    def update(self):
        self.device = self.api.get_device(self.device)
        state = self.api.get_device_state(self.device, "door")
        self._attr_native_value = getattr(state, "lightLevel")


class CoopOpenTime(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop last open time."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer"
    
    def __init__(self, api: SmartCoopAPI, coordinator: CoopCoordinator, device):
        self._attr_name = f"{device.name} Last Open Time"
        super().__init__(api, coordinator, device, "last_open_time")

    @property
    def native_value(self) -> datetime:
        self.update()
        return self._attr_native_value
            
    def update(self):
        self.device = self.api.get_device(self.device)
        state = self.api.get_device_state(self.device, "door")
        last_time = getattr(state, "lastOpenTime")
        if isinstance(last_time, str):
            strippedTime = datetime.strptime(last_time[:-6], '%Y-%m-%dT%H:%M:%S')
            self._attr_native_value = dt.as_local(strippedTime)

class CoopCloseTime(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop last close time."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer"
    
    def __init__(self, api: SmartCoopAPI, coordinator: CoopCoordinator, device):
        self._attr_name = f"{device.name} Last Close Time"
        super().__init__(api, coordinator, device, "last_close_time")

    @property
    def native_value(self) -> datetime:
        self.update()
        return self._attr_native_value
            
    def update(self):
        self.device = self.api.get_device(self.device)
        state = self.api.get_device_state(self.device, "door")
        last_time = getattr(state, "lastCloseTime")
        if isinstance(last_time, str):
            strippedTime = datetime.strptime(last_time[:-6], '%Y-%m-%dT%H:%M:%S')
            self._attr_native_value = dt.as_local(strippedTime)