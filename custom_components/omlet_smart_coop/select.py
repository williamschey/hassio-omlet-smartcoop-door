"""Define the Omlet Smart Coop select entities."""

from smartcoop.api.models import Device

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, DOOR_MODES, FAN_MODES, FAN_SPEEDS
from .coordinator import CoopCoordinator
from .entity import OmletBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Omlet Smart Coop sensors."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    selects = []
    for device in coordinator.data.values():
        if hasattr(device.configuration, "door") and device.configuration.door:
            selects.append(CoopOpenMode(device, coordinator))
            selects.append(CoopCloseMode(device, coordinator))

        if hasattr(device.configuration, "fan") and device.configuration.fan:
            selects.append(CoopFanMode(device, coordinator))
            selects.append(CoopFanManualSpeed(device, coordinator))
            selects.append(CoopFanTempSpeed(device, coordinator))
            for i in range(1, 5):
                selects.append(CoopFanTimeSpeed(device, coordinator, i))
    async_add_entities(selects)


class CoopOpenMode(OmletBaseEntity, SelectEntity):
    """Representation of a Smart Coop open mode select entity."""
    _attr_entity_category = EntityCategory.CONFIG

    _attr_options = [e.value for e in DOOR_MODES]

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Open Mode"
        super().__init__(device, coordinator, "open_mode")

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_current_option = device.configuration.door.openMode

    async def async_select_option(self, option: str) -> None:
        """Handle the selection of a new option."""
        if option in self._attr_options:
            # Retrieve the latest device data
            device = self.coordinator.data[self.device_id]

            # Update the device configuration
            device.configuration.door.openMode = option
            await self.coordinator.patch_config(device)

            self._attr_current_option = option
            self.async_write_ha_state()


class CoopCloseMode(OmletBaseEntity, SelectEntity):
    """Representation of a Smart Coop close mode select."""
    _attr_entity_category = EntityCategory.CONFIG

    _attr_options = [e.value for e in DOOR_MODES]

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Close Mode"
        super().__init__(device, coordinator, "close_mode")

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_current_option = device.configuration.door.closeMode

    async def async_select_option(self, option: str) -> None:
        """Handle the selection of a new option."""
        if option in self._attr_options:
            # Retrieve the latest device data
            device = self.coordinator.data[self.device_id]

            # Update the device configuration
            device.configuration.door.closeMode = option
            await self.coordinator.patch_config(device)

            self._attr_current_option = option
            self.async_write_ha_state()


class CoopFanMode(OmletBaseEntity, SelectEntity):
    """Representation of a Smart Coop fan mode select entity."""
    _attr_entity_category = EntityCategory.CONFIG

    _attr_options = [e.value for e in FAN_MODES]

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Fan Mode"
        super().__init__(device, coordinator, "fan_mode")

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_current_option = device.configuration.fan.mode

    async def async_select_option(self, option: str) -> None:
        """Handle the selection of a new option."""
        if option in self._attr_options:
            device = self.coordinator.data[self.device_id]
            device.configuration.fan.mode = option
            await self.coordinator.patch_config(device)
            self._attr_current_option = option
            self.async_write_ha_state()


class CoopFanSpeed(OmletBaseEntity, SelectEntity):
    """Base class for Fan Speed selects."""
    _attr_entity_category = EntityCategory.CONFIG
    _attr_options = [e.name.title() for e in FAN_SPEEDS]

    def _get_speed_value(self, option: str) -> int:
        return FAN_SPEEDS[option.upper()].value

    def _get_speed_name(self, value: int) -> str:
        try:
            return FAN_SPEEDS(value).name.title()
        except ValueError:
            return "Unknown"


class CoopFanManualSpeed(CoopFanSpeed):
    """Representation of a Smart Coop fan manual speed select."""

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Manual Speed"
        super().__init__(device, coordinator, "manual_speed")

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_current_option = self._get_speed_name(device.configuration.fan.manualSpeed)

    async def async_select_option(self, option: str) -> None:
        """Handle the selection of a new option."""
        if option in self._attr_options:
            device = self.coordinator.data[self.device_id]
            device.configuration.fan.manualSpeed = self._get_speed_value(option)
            await self.coordinator.patch_config(device)
            self._attr_current_option = option
            self.async_write_ha_state()


class CoopFanTempSpeed(CoopFanSpeed):
    """Representation of a Smart Coop fan temperature speed select."""

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Temperature Speed"
        super().__init__(device, coordinator, "temp_speed")

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_current_option = self._get_speed_name(device.configuration.fan.tempSpeed)

    async def async_select_option(self, option: str) -> None:
        """Handle the selection of a new option."""
        if option in self._attr_options:
            device = self.coordinator.data[self.device_id]
            device.configuration.fan.tempSpeed = self._get_speed_value(option)
            await self.coordinator.patch_config(device)
            self._attr_current_option = option
            self.async_write_ha_state()


class CoopFanTimeSpeed(CoopFanSpeed):
    """Representation of a Smart Coop fan time speed select."""

    def __init__(self, device, coordinator: CoopCoordinator, index: int) -> None:
        """Initialize the device."""
        self._index = index
        self._attr_name = f"{device.name} Time Speed {index}"
        super().__init__(device, coordinator, f"time_speed_{index}")

    @callback
    def _update_attr(self, device: Device) -> None:
        speed = getattr(device.configuration.fan, f"timeSpeed{self._index}")
        self._attr_current_option = self._get_speed_name(speed)

    async def async_select_option(self, option: str) -> None:
        """Handle the selection of a new option."""
        if option in self._attr_options:
            device = self.coordinator.data[self.device_id]
            setattr(device.configuration.fan, f"timeSpeed{self._index}", self._get_speed_value(option))
            await self.coordinator.patch_config(device)
            self._attr_current_option = option
            self.async_write_ha_state()
