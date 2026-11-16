"""Define the Omlet Smart Coop time entities."""

from abc import abstractmethod
from datetime import datetime, time

from smartcoop.api.models import Device

from homeassistant.components.time import TimeEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .entity import OmletBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Omlet Smart Coop time input entities."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    timeInputs = []
    for device in coordinator.data.values():
        if device.deviceType == "Autodoor":
            timeInputs.append(CoopOvernightSleepStartInput(device, coordinator))
            timeInputs.append(CoopOvernightSleepEndInput(device, coordinator))
            timeInputs.append(CoopOpenTimeInput(device, coordinator))
            timeInputs.append(CoopCloseTimeInput(device, coordinator))
        
        if device.deviceType == "Fan":
            for i in range(1, 5):
                timeInputs.append(CoopTimeScheduleInput(device, coordinator, i, True)) # On Time
                timeInputs.append(CoopTimeScheduleInput(device, coordinator, i, False)) # Off Time

        if device.deviceType == "Feeder":
            for i in range(1, 5):
                timeInputs.append(FeederTimeScheduleInput(device, coordinator, i, True))  # Open Time
                timeInputs.append(FeederTimeScheduleInput(device, coordinator, i, False))  # Close Time
            timeInputs.append(CoopOvernightSleepStartInput(device, coordinator))
            timeInputs.append(CoopOvernightSleepEndInput(device, coordinator))
                
    async_add_entities(timeInputs)


def _parse_time(value) -> time | None:
    """Parse the API's "HH:MM" time, or return None."""
    if not isinstance(value, str):
        return None
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError:
        return None


class CoopTimeInput(OmletBaseEntity, TimeEntity):
    """Representation of a Smart Coop time input entity."""

    @callback
    def _update_attr(self, device: Device):
        self._attr_native_value = _parse_time(self._get_value(device))

    async def async_set_value(self, value: time) -> None:
        """Set a new time value."""
        device = self.coordinator.data[self.device_id]

        str_value = value.strftime("%H:%M")
        current = self._attr_native_value
        if current is not None and current.strftime("%H:%M") == str_value:
            return

        self._patch_config(device, str_value)
        await self.coordinator.patch_config(device)

        self._attr_native_value = _parse_time(str_value)
        self.async_write_ha_state()

    @abstractmethod
    def _get_value(self, device: Device) -> str | None:
        """Return the configured "HH:MM" time."""

    @abstractmethod
    def _patch_config(self, device: Device, strTime):
        """Update the device configuration."""


class CoopOpenTimeInput(CoopTimeInput):
    """Representation of a Smart Coop Open time input entity."""
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device: Device, coordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Open Time"
        super().__init__(device, coordinator, "open_time")

    def _get_value(self, device: Device):
        return device.configuration.door.openTime

    def _patch_config(self, device: Device, strTime):
        device.configuration.door.openTime = strTime


class CoopCloseTimeInput(CoopTimeInput):
    """Representation of a Smart Coop Close time input entity."""
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device, coordinator) -> None:
        """Initialize the device."""

        self._attr_name = f"{device.name} Close Time"
        super().__init__(device, coordinator, "close_time")

    def _get_value(self, device: Device):
        return device.configuration.door.closeTime

    def _patch_config(self, device: Device, strTime):
        device.configuration.door.closeTime = strTime


class CoopOvernightSleepStartInput(CoopTimeInput):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device: Device, coordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Overnight Sleep Start Time"
        super().__init__(device, coordinator, "overnight_sleep_start_time")

    def _get_value(self, device: Device):
        return device.configuration.general.overnightSleepStart

    def _patch_config(self, device: Device, strTime):
        device.configuration.general.overnightSleepStart = strTime


class CoopOvernightSleepEndInput(CoopTimeInput):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device: Device, coordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Overnight Sleep End Time"
        super().__init__(device, coordinator, "overnight_sleep_end_time")

    def _get_value(self, device: Device):
        return device.configuration.general.overnightSleepEnd

    def _patch_config(self, device: Device, strTime):
        device.configuration.general.overnightSleepEnd = strTime


class CoopTimeScheduleInput(CoopTimeInput):
    """Representation of a Smart Coop Schedule Time input entity."""
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device: Device, coordinator, index: int, is_on_time: bool) -> None:
        """Initialize the device."""
        self._index = index
        self._is_on_time = is_on_time
        
        type_str = "On" if is_on_time else "Off"
        self._attr_name = f"{device.name} Time {type_str} {index}"
        key = f"time_{type_str.lower()}_{index}"
        super().__init__(device, coordinator, key)

    def _get_value(self, device: Device):
        type_str = "On" if self._is_on_time else "Off"
        attr_name = f"time{type_str}{self._index}"
        return getattr(device.configuration.fan, attr_name)

    def _patch_config(self, device: Device, strTime):
        type_str = "On" if self._is_on_time else "Off"
        attr_name = f"time{type_str}{self._index}"
        setattr(device.configuration.fan, attr_name, strTime)
class FeederTimeScheduleInput(CoopTimeInput):
    """Representation of a Feeder time schedule input entity."""
    _attr_entity_category = EntityCategory.CONFIG
    def __init__(self, device, coordinator, index: int, is_open_time: bool) -> None:
        self._index = index
        self._is_open_time = is_open_time
        type_str = "Open" if is_open_time else "Close"
        self._attr_name = f"{device.name} {type_str} Time {index}"
        key = f"feeder_{type_str.lower()}_time_{index}"
        super().__init__(device, coordinator, key)
    def _get_value(self, device: Device):
        attr_name = f"{'open' if self._is_open_time else 'close'}Time{self._index}"
        return getattr(device.configuration.feeder, attr_name)
    def _patch_config(self, device: Device, strTime):
        attr_name = f"{'open' if self._is_open_time else 'close'}Time{self._index}"
        setattr(device.configuration.feeder, attr_name, strTime)
