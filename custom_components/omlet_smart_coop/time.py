"""Define the Omlet Smart Coop time entities."""

from abc import abstractmethod

from smartcoop.api.models import Device

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity, EntityCategory

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
                
    async_add_entities(timeInputs)


class CoopTimeInput(OmletBaseEntity, Entity):
    """Representation of a Smart Coop time input entity."""

    @callback
    def _update_attr(self, device: Device):
        self._attr_state = device.configuration.door.openTime

    async def async_set_value(self, value: str):
        """Set a new time value."""
        device = self.coordinator.data[self.device_id]

        str_value = value.strftime("%H:%M")
        self._patch_config(device, str_value)
        await self.coordinator.patch_config(device)

        self._attr_state = value
        self.async_write_ha_state()

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

    @callback
    def _update_attr(self, device: Device):
        self._attr_state = device.configuration.door.openTime

    def _patch_config(self, device: Device, strTime):
        device.configuration.door.openTime = strTime


class CoopCloseTimeInput(CoopTimeInput):
    """Representation of a Smart Coop Close time input entity."""
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device, coordinator) -> None:
        """Initialize the device."""

        self._attr_name = f"{device.name} Close Time"
        super().__init__(device, coordinator, "close_time")

    @callback
    def _update_attr(self, device: Device):
        self._attr_state = device.configuration.door.closeTime

    def _patch_config(self, device: Device, strTime):
        device.configuration.door.closeTime = strTime


class CoopOvernightSleepStartInput(CoopTimeInput):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device: Device, coordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Overnight Sleep Start Time"
        super().__init__(device, coordinator, "overnight_sleep_start_time")

    @callback
    def _update_attr(self, device: Device):
        self._attr_state = device.configuration.general.overnightSleepStart

    def _patch_config(self, device: Device, strTime):
        device.configuration.general.overnightSleepStart = strTime


class CoopOvernightSleepEndInput(CoopTimeInput):
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, device: Device, coordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Overnight Sleep End Time"
        super().__init__(device, coordinator, "overnight_sleep_end_time")

    @callback
    def _update_attr(self, device: Device):
        self._attr_state = device.configuration.general.overnightSleepEnd

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

    @callback
    def _update_attr(self, device: Device):
        type_str = "On" if self._is_on_time else "Off"
        attr_name = f"time{type_str}{self._index}"
        self._attr_state = getattr(device.configuration.fan, attr_name)

    def _patch_config(self, device: Device, strTime):
        type_str = "On" if self._is_on_time else "Off"
        attr_name = f"time{type_str}{self._index}"
        setattr(device.configuration.fan, attr_name, strTime)