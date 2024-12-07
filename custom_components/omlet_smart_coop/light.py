from homeassistant.components.light import LightEntity

from custom_components.omlet_smart_coop.coop_api import SmartCoopAPI
from .const import DOMAIN, API, DEVICES, COORDINATOR
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Omlet Smart Coop light."""
    api = hass.data[DOMAIN][API]
    devices = hass.data[DOMAIN][DEVICES]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    lights = [CoopLight(api, coordinator, device) for device in devices]
    async_add_entities(lights)


class CoopLight(CoordinatorEntity, LightEntity):
    """Representation of the coop light."""

    def __init__(self, api: SmartCoopAPI, coordinator, device):
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
        self._attr_is_on = self.api.get_device_state(self.device, "light").state == 'on'
        return self._attr_is_on
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.update()
        self.async_write_ha_state()

    async def async_turn_on(self, **kwargs):
        self.api.perform_action(self.device, "on")
        # Update the data
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs):
        self.api.perform_action(self.device, "off")
        # Update the data
        await self.coordinator.async_request_refresh()

    def update(self):
        self.device = self.api.get_device(self.device)
        self._attr_is_on = self.api.get_device_state(self.device, "light").state == 'on'