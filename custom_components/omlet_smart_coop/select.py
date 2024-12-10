
from smartcoop.api.models import Device

from homeassistant.components.select import SelectEntity, SelectEntityDescription
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
    _attr_options = [e.value for e in DOOR_MODES]        

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Open Mode"
        super().__init__(device, coordinator, "open_mode")

    @callback
    def _update_attr(self, device: Device) -> None:        
        self._attr_current_option = device.configuration.door.openMode

class CoopCloseMode(OmletBaseEntity, SelectEntity):
    _attr_options = [e.value for e in DOOR_MODES]        

    def __init__(self, device, coordinator: CoopCoordinator) -> None:
        """Initialize the device."""
        self._attr_name = f"{device.name} Close Mode"
        super().__init__(device, coordinator, "close_mode")

    @callback
    def _update_attr(self, device: Device) -> None:        
        self._attr_current_option = device.configuration.door.closeMode