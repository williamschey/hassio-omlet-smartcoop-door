from .coop_api import SmartCoopAPI
from .coordinator import CoopCoordinator
from .entity import OmletBaseEntity
from .const import DOMAIN, API, DEVICES, COORDINATOR
from homeassistant.components.cover import (
    CoverDeviceClass,
    CoverEntity,
    CoverEntityFeature,
)

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up Omlet Smart Coop cover."""
    api = hass.data[DOMAIN][API]
    devices = hass.data[DOMAIN][DEVICES]
    coordinator = hass.data[DOMAIN][COORDINATOR]

    lights = [CoopCover(api, coordinator, device) for device in devices]
    async_add_entities(lights)


class CoopCover(OmletBaseEntity, CoverEntity):
    """Representation of the coop door."""

    _attr_device_class = CoverDeviceClass.DOOR
    _attr_supported_features: CoverEntityFeature = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE 
    )

    def __init__(self, api: SmartCoopAPI, coordinator: CoopCoordinator, device):
        self._attr_name = f"{device.name} Door"
        super().__init__(api, coordinator, device, "cover")

    @property
    def is_closed(self) -> bool:
        self.update()
        return self._attr_is_closed

    @property
    def is_closing(self) -> bool:
        self.update()
        return self._attr_is_closing

    @property
    def is_opening(self) -> bool:
        self.update()
        return self._attr_is_opening
    
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
