from .const import DOMAIN, API, DEVICES, COORDINATOR
from .entity import OmletBaseEntity
from .coop_api import SmartCoopAPI
from .coordinator import CoopCoordinator
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Omlet Smart Coop sensors."""
    api = hass.data[DOMAIN][API]
    devices = hass.data[DOMAIN][DEVICES]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    sensors = []
    for device in devices:
        sensors.append(CoopPowerConnection(api, coordinator, device))
    async_add_entities(sensors)


class CoopPowerConnection(OmletBaseEntity, BinarySensorEntity):
    """Representation of a Smart Coop power connection."""

    _attr_device_class = BinarySensorDeviceClass.PLUG
    
    def __init__(self, api: SmartCoopAPI, coordinator: CoopCoordinator, device):
        self._attr_name = f"{device.name} Power Connection"
        super().__init__(self, api, coordinator, device, "battery")

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def name(self):
        return self._attr_name

    @property
    def state(self):
        state = self.api.get_device_state(self.device, "general")
        self._attr_native_value = getattr(state, "batteryLevel")
        return self._attr_native_value
    
    @property
    def last_updated(self):
        return self.api.last_updated()
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.update()
        self.async_write_ha_state()
    
    def update(self):
        self.device = self.api.get_device(self.device)
        state = self.api.get_device_state(self.device, "general")
        self._attr_native_value = getattr(state, "batteryLevel")
