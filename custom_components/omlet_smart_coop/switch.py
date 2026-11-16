"""Support for Omlet Smart Coop switches."""

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
    """Set up Omlet Smart Coop switches."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    switches = []
    for device in coordinator.data.values():
        if device.deviceType in ("Autodoor", "Feeder"):
            switches.append(CoopOvernightSleepEnable(device, coordinator))
    async_add_entities(switches)


class CoopSwitch(OmletBaseEntity, SwitchEntity):
    """A switch backed by a boolean in the device's configuration."""

    _attr_entity_category = EntityCategory.CONFIG
    _attr_device_class = SwitchDeviceClass.SWITCH

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        await self.async_set_boolean(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        await self.async_set_boolean(False)

    async def async_set_boolean(self, value: bool) -> None:
        """Set a new switch value."""
        device = self.coordinator.data[self.device_id]

        self._patch_config(device, value)
        await self.coordinator.patch_config(device)

        self._attr_is_on = value
        self.async_write_ha_state()

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_is_on = self._get_value(device)

    @abstractmethod
    def _get_value(self, device: Device) -> bool | None:
        """Return the configuration value."""

    @abstractmethod
    def _patch_config(self, device: Device, value: bool):
        """Update the device configuration."""


class CoopOvernightSleepEnable(CoopSwitch):
    """Whether the device sleeps overnight."""

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Overnight Sleep Enabled"
        super().__init__(device, coordinator, "overnight_sleep_enabled")

    def _get_value(self, device: Device) -> bool | None:
        return device.configuration.general.overnightSleepEnable

    def _patch_config(self, device: Device, value: bool):
        device.configuration.general.overnightSleepEnable = value
