"""Availability regressions using Home Assistant and the integration's SDK.

With those dependencies installed, run: python -m unittest discover -s tests
"""

from copy import deepcopy
from datetime import timedelta
from itertools import product
import json
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

from homeassistant.components.binary_sensor import BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import Entity, EntityCategory
from smartcoop.api.models import Device

from custom_components.omlet_smart_coop.binary_sensor import (
    CoopConnectivity,
    CoopPowerConnection,
    async_setup_entry,
)
from custom_components.omlet_smart_coop.const import DOMAIN
from custom_components.omlet_smart_coop.coordinator import CoopCoordinator
from custom_components.omlet_smart_coop.cover import CoopCover, FeederCover
from custom_components.omlet_smart_coop.fan import CoopFan
from custom_components.omlet_smart_coop.light import CoopLight
from custom_components.omlet_smart_coop.sensor import (
    CoopPowerSource,
    async_setup_entry as async_setup_sensor_entry,
)

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
OPERATIONAL_ENTITIES = (
    (CoopCover, "door"),
    (CoopLight, "door"),
    (FeederCover, "feeder"),
    (CoopFan, "fan"),
)


def load_device(example: str) -> Device:
    return Device.from_json(
        json.loads((EXAMPLES / f"{example}.json").read_text(encoding="utf-8"))
    )


def make_coordinator(device: Device) -> Mock:
    return Mock(
        spec=CoopCoordinator,
        data={device.deviceId: device},
        last_update_success=True,
        update_interval=timedelta(seconds=60),
    )


class OperationalAvailabilityTests(unittest.TestCase):
    def test_sleeping_feeder_from_api_is_available(self) -> None:
        device = load_device("feeder")
        self.assertEqual(device.state.general.powerSource, "battery")
        self.assertFalse(device.state.connectivity.connected)

        entity = FeederCover(device, make_coordinator(device))
        self.assertTrue(entity.available)

    def test_availability_by_power_connection_and_update_status(self) -> None:
        for (entity_type, example), power, connected, update_success in product(
            OPERATIONAL_ENTITIES,
            ("battery", "external", "unknown"),
            (False, True),
            (False, True),
        ):
            with self.subTest(
                entity=entity_type.__name__,
                power=power,
                connected=connected,
                update_success=update_success,
            ):
                device = load_device(example)
                device.state.general.powerSource = power
                device.state.connectivity.connected = connected
                coordinator = make_coordinator(device)
                coordinator.last_update_success = update_success
                entity = entity_type(device, coordinator)

                self.assertIs(
                    entity.available,
                    update_success and (power == "battery" or connected),
                )

    def test_availability_follows_updated_power_source(self) -> None:
        for entity_type, example in OPERATIONAL_ENTITIES:
            with self.subTest(entity=entity_type.__name__):
                device = load_device(example)
                device.state.connectivity.connected = False
                coordinator = make_coordinator(device)
                entity = entity_type(device, coordinator)

                for power in ("external", "battery", "external"):
                    updated_device = deepcopy(device)
                    updated_device.state.general.powerSource = power
                    coordinator.data[device.deviceId] = updated_device
                    self.assertIs(entity.available, power == "battery")

    def test_battery_does_not_bypass_missing_device_or_state(self) -> None:
        for entity_type, example in OPERATIONAL_ENTITIES:
            with self.subTest(entity=entity_type.__name__):
                device = load_device(example)
                device.state.general.powerSource = "battery"
                coordinator = make_coordinator(device)
                entity = entity_type(device, coordinator)

                coordinator.data = {}
                self.assertFalse(entity.available)
                coordinator.data = {device.deviceId: Mock(spec=Device, state=None)}
                self.assertFalse(entity.available)

    def test_missing_connectivity_preserves_existing_fallback(self) -> None:
        for entity_type, example in OPERATIONAL_ENTITIES:
            with self.subTest(entity=entity_type.__name__):
                device = load_device(example)
                device.state.general.powerSource = "external"
                entity = entity_type(device, make_coordinator(device))
                del device.state.connectivity

                self.assertTrue(entity.available)


class ConnectivitySensorTests(unittest.IsolatedAsyncioTestCase):
    async def test_connected_sensor_for_every_device_type(self) -> None:
        for example, connected in product(("door", "feeder", "fan"), (False, True)):
            with self.subTest(example=example, connected=connected):
                device = load_device(example)
                device.state.connectivity.connected = connected
                coordinator = make_coordinator(device)
                entry = Mock(spec=ConfigEntry, entry_id="test-entry")
                hass = Mock(
                    spec=HomeAssistant,
                    data={DOMAIN: {entry.entry_id: coordinator}},
                )
                async_add_entities = Mock()

                await async_setup_entry(hass, entry, async_add_entities)

                async_add_entities.assert_called_once()
                sensors = async_add_entities.call_args.args[0]
                expected_types = [CoopConnectivity]
                if device.deviceType != "Feeder":
                    expected_types.append(CoopPowerConnection)
                self.assertCountEqual(map(type, sensors), expected_types)

                sensor = next(s for s in sensors if isinstance(s, CoopConnectivity))
                self.assertEqual(sensor.unique_id, f"{device.deviceId}_connected")
                self.assertEqual(sensor.name, f"{device.name} Connected")
                self.assertEqual(
                    sensor.device_class, BinarySensorDeviceClass.CONNECTIVITY
                )
                self.assertTrue(sensor.available)
                self.assertIs(sensor.is_on, connected)

                device.state.connectivity.connected = not connected
                with patch.object(Entity, "async_write_ha_state"):
                    sensor._handle_coordinator_update()
                self.assertIs(sensor.is_on, not connected)

                coordinator.last_update_success = False
                self.assertFalse(sensor.available)


class PowerSourceSensorTests(unittest.IsolatedAsyncioTestCase):
    async def test_power_source_sensor_for_every_device_type(self) -> None:
        for example, connected in product(("door", "feeder", "fan"), (False, True)):
            with self.subTest(example=example, connected=connected):
                device = load_device(example)
                device.state.connectivity.connected = connected
                coordinator = make_coordinator(device)
                entry = Mock(spec=ConfigEntry, entry_id="test-entry")
                hass = Mock(
                    spec=HomeAssistant,
                    data={DOMAIN: {entry.entry_id: coordinator}},
                )
                async_add_entities = Mock()

                await async_setup_sensor_entry(hass, entry, async_add_entities)

                async_add_entities.assert_called_once()
                sensors = [
                    sensor
                    for sensor in async_add_entities.call_args.args[0]
                    if isinstance(sensor, CoopPowerSource)
                ]
                self.assertEqual(len(sensors), 1)
                sensor = sensors[0]
                self.assertEqual(sensor.unique_id, f"{device.deviceId}_power_source")
                self.assertEqual(sensor.name, f"{device.name} Power Source")
                self.assertEqual(sensor.entity_category, EntityCategory.DIAGNOSTIC)
                self.assertEqual(sensor.native_value, device.state.general.powerSource)
                self.assertTrue(sensor.available)

                for power in ("battery", "external", "unexpected"):
                    updated_device = deepcopy(device)
                    updated_device.state.general.powerSource = power
                    coordinator.data[device.deviceId] = updated_device
                    with patch.object(Entity, "async_write_ha_state"):
                        sensor._handle_coordinator_update()
                    self.assertEqual(sensor.native_value, power)
                    self.assertTrue(sensor.available)

                coordinator.last_update_success = False
                self.assertFalse(sensor.available)
                coordinator.last_update_success = True
                self.assertTrue(sensor.available)
