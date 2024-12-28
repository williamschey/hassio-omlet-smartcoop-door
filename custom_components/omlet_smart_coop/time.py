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
        timeInputs.append(CoopOpenTimeInput(device, coordinator))
        timeInputs.append(CoopCloseTimeInput(device, coordinator))
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
