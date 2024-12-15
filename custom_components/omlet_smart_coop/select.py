"""Define the Omlet Smart Coop select entities."""

from smartcoop.api.models import Device

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN, DOOR_MODES
from .coordinator import CoopCoordinator
from .entity import OmletBaseEntity


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Set up Omlet Smart Coop sensors."""

    coordinator = hass.data[DOMAIN][entry.entry_id]

    selects = []
    for device in coordinator.data.values():
        selects.append(CoopOpenMode(device, coordinator))
        selects.append(CoopCloseMode(device, coordinator))
    async_add_entities(selects)


class CoopOpenMode(OmletBaseEntity, SelectEntity):
    """Representation of a Smart Coop open mode select entity."""

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
