"""Define the Omlet Smart Coop select entities."""

from smartcoop.api.models import Device

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN, DOOR_MODES
from .coordinator import CoopCoordinator
from .entity import OmletBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Omlet Smart Coop sensors."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    selects = []
    for device in coordinator.data.values():
        if device.deviceType == "Autodoor":
            selects.append(CoopOpenMode(device, coordinator))
            selects.append(CoopCloseMode(device, coordinator))
            
        if device.deviceType == "Fan":
            selects.append(CoopManualSpeedSelect(device, coordinator))
            selects.append(CoopTempSpeedSelect(device, coordinator))
            for i in range(1, 5):
                selects.append(CoopTimeSpeedSelect(device, coordinator, i))
                
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
            if option == self._attr_current_option:
                return

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
            if option == self._attr_current_option:
                return

            # Retrieve the latest device data
            device = self.coordinator.data[self.device_id]

            # Update the device configuration
            device.configuration.door.closeMode = option
            await self.coordinator.patch_config(device)

            self._attr_current_option = option
            self.async_write_ha_state()


class CoopFanSpeedSelect(OmletBaseEntity, SelectEntity):
    """Representation of a Smart Coop fan speed select."""
    _attr_entity_category = EntityCategory.CONFIG
    
    # Mapping logic
    SPEED_MAP = {"Low": 60, "Medium": 80, "High": 100}
    REVERSE_MAP = {60: "Low", 80: "Medium", 100: "High"}
    
    _attr_options = ["Low", "Medium", "High"]

    def _get_speed_from_config(self, device: Device) -> int | None:
        """Get the speed value from config."""
        raise NotImplementedError

    def _set_speed_in_config(self, device: Device, speed: int) -> None:
        """Set the speed value in config."""
        raise NotImplementedError

    @callback
    def _update_attr(self, device: Device) -> None:
        val = self._get_speed_from_config(device)
        self._attr_current_option = self.REVERSE_MAP.get(val)

    async def async_select_option(self, option: str) -> None:
        """Handle the selection of a new option."""
        if option in self._attr_options:
            if option == self._attr_current_option:
                return

            device = self.coordinator.data[self.device_id]
            speed = self.SPEED_MAP[option]
            
            self._set_speed_in_config(device, speed)
            await self.coordinator.patch_config(device)

            self._attr_current_option = option
            self.async_write_ha_state()


class CoopManualSpeedSelect(CoopFanSpeedSelect):
    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        self._attr_name = f"{device.name} Manual Speed"
        super().__init__(device, coordinator, "manual_speed")

    def _get_speed_from_config(self, device: Device):
        return device.configuration.fan.manualSpeed

    def _set_speed_in_config(self, device: Device, speed: int):
        device.configuration.fan.manualSpeed = speed


class CoopTempSpeedSelect(CoopFanSpeedSelect):
    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        self._attr_name = f"{device.name} Temperature Speed"
        super().__init__(device, coordinator, "temp_speed")

    def _get_speed_from_config(self, device: Device):
        return device.configuration.fan.tempSpeed

    def _set_speed_in_config(self, device: Device, speed: int):
        device.configuration.fan.tempSpeed = speed


class CoopTimeSpeedSelect(CoopFanSpeedSelect):
    def __init__(self, device, coordinator: CoopCoordinator, index: int) -> None:
        self._index = index
        self._attr_name = f"{device.name} Time Speed {index}"
        super().__init__(device, coordinator, f"time_speed_{index}")

    def _get_speed_from_config(self, device: Device):
        return getattr(device.configuration.fan, f"timeSpeed{self._index}")

    def _set_speed_in_config(self, device: Device, speed: int):
        setattr(device.configuration.fan, f"timeSpeed{self._index}", speed)
