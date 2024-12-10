"""Support for Omlet Smart Coop sensors."""

from datetime import datetime, date, timedelta

from smartcoop.api.models import Device

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    LIGHT_LUX,
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import CoopCoordinator
from .entity import OmletBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Omlet Smart Coop sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = []
    for device in coordinator.data.values():
        sensors.append(CoopBatterySensor(device, coordinator))
        sensors.append(CoopWifiStrength(device, coordinator))
        sensors.append(CoopUpdateTime(device, coordinator))
        sensors.append(CoopPollingInterval(device, coordinator))
        sensors.append(CoopLightLevel(device, coordinator))
        sensors.append(CoopOpenTime(device, coordinator))
        sensors.append(CoopCloseTime(device, coordinator))
        sensors.append(CoopNextUpdateTime(device, coordinator))
    async_add_entities(sensors)


class CoopBatterySensor(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop battery sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Battery Level"
        super().__init__(device, coordinator, "battery")

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_native_value = device.state.general.batteryLevel


class CoopWifiStrength(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop wifi sensor."""

    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Wi-Fi Strength"
        super().__init__(device, coordinator, "wifi")

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_native_value = device.state.connectivity.wifiStrength


class CoopUpdateTime(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop last update time."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer"

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Last Updated"
        super().__init__(device, coordinator, "last_updated")

    @callback
    def _update_attr(self, device: Device) -> None:
        last_time = device.configuration.general.datetime
        if isinstance(last_time, str):
            strippedTime = datetime.strptime(last_time[:-6], "%Y-%m-%dT%H:%M:%S")
            self._attr_native_value = dt_util.as_local(strippedTime)


class CoopPollingInterval(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop last update time."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer-sync"

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Polling Interval"
        super().__init__(device, coordinator, "polling_interval")

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_native_value = device.configuration.general.pollFreq


class CoopNextUpdateTime(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop next update time."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer"

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Next Update"
        super().__init__(device, coordinator, "next_update")

    @callback
    def _update_attr(self, device: Device) -> None:
        strippedTime = datetime.strptime(
            device.configuration.general.datetime[:-6], "%Y-%m-%dT%H:%M:%S"
        ) + timedelta(seconds=device.configuration.general.pollFreq)   
        if not device.configuration.general.overnightSleepEnable: 
            self._attr_native_value = dt_util.as_local(strippedTime)
            return
    
        sleep_start = datetime.combine(date.today(), datetime.strptime(
            device.configuration.general.overnightSleepStart, "%H:%M"
        ).time())
        sleep_end = datetime.combine(date.today(), datetime.strptime(
            device.configuration.general.overnightSleepEnd, "%H:%M"
        ).time())

        if (sleep_end < sleep_start):
            sleep_end = sleep_end + timedelta(days=1)
        
        if sleep_start < datetime.now() < sleep_end:
            self._attr_native_value = dt_util.as_local(sleep_end)
            return
        
        self._attr_native_value = dt_util.as_local(strippedTime)
        return


class CoopLightLevel(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop last update time."""

    _attr_device_class = SensorDeviceClass.ILLUMINANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = LIGHT_LUX

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Light Level"
        super().__init__(device, coordinator, "light_level")

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_native_value = device.state.door.lightLevel


class CoopOpenTime(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop last open time."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer"

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Last Open Time"
        super().__init__(device, coordinator, "last_open_time")

    @callback
    def _update_attr(self, device: Device) -> None:
        last_time = device.state.door.lastOpenTime
        if isinstance(last_time, str):
            strippedTime = datetime.strptime(last_time[:-6], "%Y-%m-%dT%H:%M:%S")
            self._attr_native_value = dt_util.as_local(strippedTime)


class CoopCloseTime(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop last close time."""

    _attr_device_class = SensorDeviceClass.TIMESTAMP
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:timer"

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Last Close Time"
        super().__init__(device, coordinator, "last_close_time")

    @callback
    def _update_attr(self, device: Device) -> None:
        # self.device = device
        last_time = device.state.door.lastCloseTime
        if isinstance(last_time, str):
            strippedTime = datetime.strptime(last_time[:-6], "%Y-%m-%dT%H:%M:%S")
            self._attr_native_value = dt_util.as_local(strippedTime)
