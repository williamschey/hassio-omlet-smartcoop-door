"""Define the Omlet Smart Coop number entities."""

from abc import abstractmethod

from smartcoop.api.models import Device

from homeassistant.components.number import NumberEntity
from homeassistant.components.number.const import NumberMode
from homeassistant.const import LIGHT_LUX, UnitOfTime, UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import Entity, EntityCategory

from .const import DOMAIN
from .coordinator import CoopCoordinator
from .entity import OmletBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Omlet Smart Coop time input entities."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    numberInputs = []
    for device in coordinator.data.values():
        if device.deviceType == "Autodoor":
            numberInputs.append(CoopPollTimeInput(device, coordinator))
            numberInputs.append(CoopOpenLightLevelInput(device, coordinator))
            numberInputs.append(CoopCloseLightLevelInput(device, coordinator))
            
        if device.deviceType == "Fan":
            numberInputs.append(CoopFanTemperatureInput(device, coordinator, True)) # Temp On
            numberInputs.append(CoopFanTemperatureInput(device, coordinator, False)) # Temp Off
            
    async_add_entities(numberInputs)

class CoopNumberInput(OmletBaseEntity, NumberEntity):
    """Representation of a Smart Coop time input entity."""

    @callback
    def _update_attr(self, device: Device):
        self._attr_native_value = device.configuration.general.pollFreq

    async def async_set_native_value(self, value: float):
        """Set a new light level value (0-99)."""
        device = self.coordinator.data[self.device_id]
        iVal = int(value)

        self._patch_config(device, value)
        await self.coordinator.patch_config(device)

        self._attr_native_value = value
        self.async_write_ha_state()

    @abstractmethod
    def _patch_config(self, device: Device, value):
        """Update the device configuration."""

class CoopLightLevelInput(CoopNumberInput):
    """Representation of a Smart Coop light level input entity."""

    _attr_unit_of_measurement = LIGHT_LUX
    _attr_native_min_value = 0
    _attr_native_max_value = 99  # This matches what the app permits
    _attr_native_step = 1

class CoopOpenLightLevelInput(CoopLightLevelInput):
    """Representation of a Smart Coop time input entity."""
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Open Light Level"
        super().__init__(device, coordinator, "open_light_level")

    @callback
    def _update_attr(self, device: Device):
        self._attr_native_value = device.configuration.door.openLightLevel
        
    def _patch_config(self, device: Device, lightLevel: int):
        if lightLevel <= device.configuration.door.closeLightLevel:
            raise ValueError("Close light level must be less than open light level")

        device.configuration.door.openLightLevel = lightLevel


class CoopCloseLightLevelInput(CoopLightLevelInput):
    """Representation of a Smart Coop time input entity."""
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Close Light Level"
        super().__init__(device, coordinator, "close_light_level")

    @callback
    def _update_attr(self, device: Device):
        self._attr_native_value = device.configuration.door.closeLightLevel

    def _patch_config(self, device: Device, lightLevel: int):
        if lightLevel >= device.configuration.door.openLightLevel:
            raise ValueError("Close light level must be less than open light level")

        device.configuration.door.closeLightLevel = lightLevel


class CoopPollTimeInput(CoopNumberInput):
    """Representation of a Smart Coop time input entity."""
    _attr_unit_of_measurement = UnitOfTime.SECONDS
    _attr_native_min_value = 0
    _attr_native_max_value = 1800  # No idea what the app permits
    _attr_native_step = 1
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Poll Time"
        super().__init__(device, coordinator, "poll_time")

    @callback
    def _update_attr(self, device: Device):
        self._attr_native_value = device.configuration.general.pollFreq

    def _patch_config(self, device: Device, pollTime: int):
        device.configuration.general.pollFreq = pollTime


class CoopFanTemperatureInput(CoopNumberInput):
    """Representation of a Smart Coop fan temperature input."""
    _attr_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = NumberMode.BOX
    _attr_native_min_value = 0
    _attr_native_max_value = 50
    _attr_native_step = 1

    def __init__(self, device: Device, coordinator, is_on_temp: bool) -> None:
        """Initialize the device."""
        self._is_on_temp = is_on_temp
        type_str = "On" if is_on_temp else "Off"
        self._attr_name = f"{device.name} Temperature {type_str}"
        key = f"temp_{type_str.lower()}"
        super().__init__(device, coordinator, key)

    @callback
    def _update_attr(self, device: Device):
        if self._is_on_temp:
            self._attr_native_value = device.configuration.fan.tempOn
        else:
            self._attr_native_value = device.configuration.fan.tempOff

    def _patch_config(self, device: Device, value: int):
        if self._is_on_temp:
            device.configuration.fan.tempOn = value
        else:
            device.configuration.fan.tempOff = value