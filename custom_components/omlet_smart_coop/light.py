from homeassistant.components.light import LightEntity
from .const import DOMAIN
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

async def async_setup_entry(hass, coordinator, async_add_entities):
    """Set up Omlet Smart Coop light."""
    api = hass.data[DOMAIN]["api"]
    devices = hass.data[DOMAIN]["devices"]

    lights = [CoopLight(api, coordinator, device) for device in devices]
    async_add_entities(lights)


class CoopLight(CoordinatorEntity, LightEntity):
    """Representation of the coop light."""

    def __init__(self, api, coordinator, device):
        self.api = api
        self.device = device
        self._name = f"{device.name} Light"
        self._attr_unique_id = f"{device.deviceId}_light"
        super().__init__(coordinator)

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def color_mode(self):
        return None
    
    @property
    def name(self):
        return self._name
    
    @property
    def last_updated(self):
        return self.api.last_updated()

    @property
    def is_on(self):
        return self.api.get_device_state(self.device, "light").state == 'on'

    async def async_turn_on(self, **kwargs):
        self.api.perform_action(self.device, "on", True)

    async def async_turn_off(self, **kwargs):
        self.api.perform_action(self.device, "off", False)

    def update(self):
        self.device = self.api.get_device(self.device)