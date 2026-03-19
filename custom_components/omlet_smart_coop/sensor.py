"""Support for Omlet Smart Coop sensors."""

from datetime import date, datetime, timedelta

from smartcoop.api.models import Device

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    SIGNAL_STRENGTH_DECIBELS_MILLIWATT,
    STATE_UNAVAILABLE,
    UnitOfTime,
    UnitOfTemperature,
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
        sensors.append(CoopWifiStrength(device, coordinator))
        sensors.append(CoopUpdateTime(device, coordinator))
        sensors.append(CoopNextUpdateTime(device, coordinator))
        
        if device.deviceType == "Autodoor":
            sensors.append(CoopPollingInterval(device, coordinator))
            sensors.append(CoopBatterySensor(device, coordinator))
            sensors.append(CoopLightLevel(device, coordinator))
            sensors.append(CoopOpenTime(device, coordinator))
            sensors.append(CoopCloseTime(device, coordinator))
            sensors.append(CoopDoorFault(device, coordinator))
        
        if device.deviceType == "Fan":
            sensors.append(CoopFanSpeed(device, coordinator))
            sensors.append(CoopFanTemperature(device, coordinator))
            sensors.append(CoopFanHumidity(device, coordinator))

        if device.deviceType == "Feeder":
            sensors.append(FeederFeedLevel(device, coordinator))
            sensors.append(FeederLightLevel(device, coordinator))
            sensors.append(FeederLastOpenTime(device, coordinator))
            sensors.append(FeederLastCloseTime(device, coordinator))
            sensors.append(FeederFault(device, coordinator))
            
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
        if device.state.general.powerSource == "external":
            self._attr_state = STATE_UNAVAILABLE
            self._attr_native_value = None
            return

        strippedTime = datetime.strptime(
            device.configuration.general.datetime[:-6], "%Y-%m-%dT%H:%M:%S"
        ) + timedelta(seconds=device.configuration.general.pollFreq)
        if not device.configuration.general.overnightSleepEnable:
            self._attr_native_value = dt_util.as_local(strippedTime)
            return

        sleep_start = datetime.combine(
            date.today(),
            datetime.strptime(
                device.configuration.general.overnightSleepStart, "%H:%M"
            ).time(),
        )
        sleep_end = datetime.combine(
            date.today(),
            datetime.strptime(
                device.configuration.general.overnightSleepEnd, "%H:%M"
            ).time(),
        )

        if sleep_end < sleep_start:
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
    _attr_native_unit_of_measurement = PERCENTAGE

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


class CoopDoorFault(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop door fault state."""

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Door Fault"
        super().__init__(device, coordinator, "door_fault")

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_native_value = device.state.door.fault

class CoopFanSpeed(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop Fan speed sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:fan"

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Fan Speed"
        super().__init__(device, coordinator, "fan_speed")

    @callback
    def _update_attr(self, device: Device) -> None:
        # Re-use logic from fan entity or just calculate similarly?
        # Ideally we should use the same logic. 
        # But we can't easily access the FanEntity instance from here.
        # We will duplicate the simple logic for now or read from the same config.
        # The user said "Using @[examples/fan.json] for reference... the current Fan Speed can assumed to be..."
        # So we should implement the same logic here.
        
        config = device.configuration.fan
        state = device.state.fan.state # "on" or "off"
        
        if state != "on":
            self._attr_native_value = 0
            return

        mode = config.mode
        
        if mode == "manual":
            self._attr_native_value = config.manualSpeed
            return
        
        if mode == "temperature":
            self._attr_native_value = config.tempSpeed
            return
            
        if mode == "time":
            import datetime
            now = datetime.datetime.now().time()
            
            def parse_time(t_str):
                try:
                    return datetime.datetime.strptime(t_str, "%H:%M").time()
                except (ValueError, TypeError):
                    return None

            for i in range(1, 5):
                on_str = getattr(config, f"timeOn{i}", None)
                off_str = getattr(config, f"timeOff{i}", None)
                speed = getattr(config, f"timeSpeed{i}", 100)
                
                start = parse_time(on_str)
                end = parse_time(off_str)
                
                if start and end and start != end:
                    if start < end:
                        if start <= now < end:
                            self._attr_native_value = speed
                            return
                    else: 
                        if start <= now or now < end:
                            self._attr_native_value = speed
                            return
                            
            self._attr_native_value = 100
            return
            
        self._attr_native_value = None


class CoopFanTemperature(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop Fan temperature sensor."""

    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Temperature"
        super().__init__(device, coordinator, "temperature")

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_native_value = device.state.fan.temperature


class CoopFanHumidity(OmletBaseEntity, SensorEntity):
    """Representation of a Smart Coop Fan humidity sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Humidity"
        super().__init__(device, coordinator, "humidity")

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_native_value = device.state.fan.humidity
