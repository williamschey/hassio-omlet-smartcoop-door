"""Base entity for Omlet Smart Coop integration."""

from abc import abstractmethod

from smartcoop.api.models import Device

from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import CoopCoordinator


class OmletBaseEntity(CoordinatorEntity[CoopCoordinator]):
    """Representation of a Omlet Autodoor."""

    _attr_has_entity_name = True

    def __init__(self, device, coordinator, key) -> None:
        """Initialize the device."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{device.deviceId}_{key}"
        self._update_attr(coordinator.data[device.deviceId])

        self.device_id = device.deviceId

        self._attr_device_info = self._device_info(device)

    @staticmethod
    def _device_info(device) -> DeviceInfo:
        """Return device info."""
        swversion = None
        if hasattr(device.state.general, "firmwareVersionCurrent"):
            swversion = device.state.general.firmwareVersionCurrent

        return DeviceInfo(
            identifiers={(DOMAIN, device.name)},
            manufacturer="Omlet",
            serial_number=device.deviceId,
            model_id=device.deviceType,
            name=device.name,
            sw_version=swversion,
            model=device.deviceType,
            suggested_area="Garden",
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_attr(self.coordinator.data[self.device_id])
        self.async_write_ha_state()

    @abstractmethod
    @callback
    def _update_attr(self, device: Device) -> None:
        """Update the state and attributes."""
