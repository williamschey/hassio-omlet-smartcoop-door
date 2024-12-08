from custom_components.omlet_smart_coop.coop_api import SmartCoopAPI
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

from .coordinator import CoopCoordinator


class OmletBaseEntity(CoordinatorEntity[CoopCoordinator]):
    """Representation of a Omlet Autodoor."""

    _attr_has_entity_name = True

    def __init__(self, api: SmartCoopAPI, coordinator, device, key):
        """Initialize the device."""
        self.api = api
        self.device = device
        super().__init__(coordinator)
        self._attr_unique_id = f"{device.deviceId}_{key}"

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return self._attr_unique_id

    @property
    def name(self):
        return self._attr_name

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.update()
        self.async_write_ha_state()

    @property
    def device_info(self) -> DeviceInfo:
        swversion = None
        if hasattr(self.device.state.general, "firmwareVersionCurrent"):
            swversion = self.device.state.general.firmwareVersionCurrent

        device_name = self.device.name
        device_id = self.device.deviceId

        device_type = self.device.deviceType

        return DeviceInfo(
            identifiers={(DOMAIN, device_name)},
            manufacturer="Omlet",
            serial_number=device_id,
            model_id=device_type,
            name=device_name,
            sw_version=swversion,
            model=device_type,
            suggested_area="Garden",
        )

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return (
            self.device is not None
        )