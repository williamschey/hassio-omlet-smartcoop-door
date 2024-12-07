from custom_components.omlet_smart_coop.coop_api import SmartCoopAPI
from .const import DOMAIN, API, DEVICES, COORDINATOR
from homeassistant.core import callback
from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Omlet Smart Coop cover."""
    api = hass.data[DOMAIN][API]
    devices = hass.data[DOMAIN][DEVICES]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    lights = [CoopCover(api, coordinator, device) for device in devices]
    async_add_entities(lights)


class CoopCover(CoordinatorEntity, CoverEntity):
    """Representation of the coop door."""

    _attr_device_class = CoverDeviceClass.DOOR
    _attr_supported_features: CoverEntityFeature = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE 
    )

    def __init__(self, api: SmartCoopAPI, coordinator, device):
        super().__init__
        self.api = api
        self.device = device
        self._name = f"{device.name} Door"
        self._attr_unique_id = f"{device.deviceId}_cover"
        super().__init__(coordinator)

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return self._attr_unique_id
    
    @property
    def name(self):
        return self._name
    
    @property
    def last_updated(self):
        return self.api.last_updated()

    @property
    def is_closed(self) -> bool:
        self._attr_is_closed = self.api.get_device_state(self.device, "door").state == "closed"
        return super().is_closed()

    

    @property
    def is_closing(self) -> bool:
        self._attr_is_closing = self.api.get_device_state(self.device, "door").state == "closing"
        return super().is_closing()

    @property
    def is_opening(self) -> bool:
        self._attr_is_opening = self.api.get_device_state(self.device, "door").state == "opening"
        return super().is_opening()
    
    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.update()
        self.async_write_ha_state()

    async def async_open_cover(self, **kwargs):
        await self.api.perform_action(self.device, "open")
        # Update the data
        await self.coordinator.async_request_refresh()

    async def async_close_cover(self, **kwargs):
        await self.api.perform_action(self.device, "close")
        # Update the data
        await self.coordinator.async_request_refresh()

    def update(self):
        self.device = self.api.get_device(self.device)
        self._attr_is_closed = self.api.get_device_state(self.device, "door").state == "closed"
        self._attr_is_closing = self.api.get_device_state(self.device, "door").state == "closing"
        self._attr_is_opening = self.api.get_device_state(self.device, "door").state == "opening"
