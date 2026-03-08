"""Support for Omlet Smart Coop binary sensors."""

from smartcoop.api.models import Device

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory

from .const import DOMAIN
from .coordinator import CoopCoordinator
from .entity import OmletBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Omlet Smart Coop sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    sensors = []
    for device in coordinator.data.values():
        sensors.append(CoopPowerConnection(device, coordinator))
        sensors.append(CoopConnectivity(device, coordinator))
    
    async_add_entities(sensors)


class CoopPowerConnection(OmletBaseEntity, BinarySensorEntity):
    """Representation of a Smart Coop power connection."""

    _attr_device_class = BinarySensorDeviceClass.PLUG

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Power Connection"
        super().__init__(device, coordinator, "battery")

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_is_on = device.state.general.powerSource == "external"


class CoopConnectivity(OmletBaseEntity, BinarySensorEntity):
    """Representation of a Smart Coop connectivity status."""

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Connected"
        super().__init__(device, coordinator, "connected")

    @callback
    def _update_attr(self, device: Device) -> None:
        self._attr_is_on = device.state.connectivity.connected
