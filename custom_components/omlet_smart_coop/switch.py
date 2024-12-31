"""Support for Omlet Smart Coop binary sensors."""

from abc import abstractmethod
from typing import Any

from smartcoop.api.models import Device

from homeassistant.components.switch import (
    SwitchDeviceClass,
    SwitchEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .coordinator import CoopCoordinator
from .entity import OmletBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Omlet Smart Coop sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = [
        CoopOvernightSleepEnable(device, coordinator) for device in coordinator.data.values()
    ]
    async_add_entities(sensors)


class CoopSwitch(OmletBaseEntity, SwitchEntity):
    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = SwitchDeviceClass.SWITCH

    async def async_turn_on(self, **kwargs: Any) -> None:
        self.async_set_boolean(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        self.async_set_boolean(False)

    async def async_set_boolean(self, value: bool) -> None:
        """Set a new switch value."""
        device = self.coordinator.data[self.device_id]

        self._patch_config(device, value)
        await self.coordinator.patch_config(device)

        self._attr_is_on = value
        self.async_write_ha_state()

    def is_on(self) -> bool | None:
        device = self.coordinator.data[self.device_id]
        return self.is_on(device)
    
    @abstractmethod
    def is_on(self, device: Device) -> bool | None:
        """Return True if entity is on."""

    @abstractmethod
    def _patch_config(self, device: Device, strTime):
        """Update the device configuration."""


class CoopOvernightSleepEnable(CoopSwitch):

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Overnight Sleep Enabled"
        super().__init__(device, coordinator, "overnight_sleep_enabled")

    def is_on(self, device: Device) -> bool | None:
        """Return True if entity is on."""
        return device.configuration.general.overnightSleepEnable

    def _patch_config(self, device: Device, sleepEnabled):
        device.configuration.general.overnightSleepEnable = sleepEnabled

    @callback
    def _update_attr(self, device: Device) -> None:
        """Intentionally blank."""