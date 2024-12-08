from .const import DOMAIN, API, DEVICES, COORDINATOR
from .entity import OmletBaseEntity
from .coop_api import SmartCoopAPI
from .coordinator import CoopCoordinator
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
        super().__init__(api, coordinator, device, "battery")

    @property
    def is_on(self):
        self.update()
        return self._attr_is_on
    
    def update(self):
        self.device = self.api.get_device(self.device)
        state = self.api.get_device_state(self.device, "general")
        self._attr_native_value = getattr(state, "powerSource") == "external"
