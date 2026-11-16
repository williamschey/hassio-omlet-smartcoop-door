"""Fixtures for the Omlet Smart Coop tests."""

from collections.abc import Generator
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from smartcoop.api.models import Device

from custom_components.omlet_smart_coop.const import API_KEY, DOMAIN

pytest_plugins = "pytest_homeassistant_custom_component"

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"
API_KEY_VALUE = "test-api-key"


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Load custom_components/ in every test."""
    return


def load_device(example: str, device_id: str | None = None) -> Device:
    """Load an example device. The examples all share one redacted ID."""
    raw = json.loads((EXAMPLES / f"{example}.json").read_text(encoding="utf-8"))
    raw["deviceId"] = device_id or f"{example}-id"
    return Device.from_json(raw)


@pytest.fixture
def devices() -> list[Device]:
    """The devices the mocked API returns: one door by default."""
    return [load_device("door")]


@pytest.fixture
def mock_omlet(devices) -> Generator[MagicMock]:
    """Mock the SDK's Omlet class wherever the integration uses it."""
    omlet = MagicMock()
    omlet.get_devices.side_effect = lambda: deepcopy(devices)
    with patch(
        "custom_components.omlet_smart_coop.coop_api.Omlet", return_value=omlet
    ):
        yield omlet


@pytest.fixture
def no_action_sleep() -> Generator[None]:
    """Skip the 10 seconds the coordinator waits after an action."""
    with patch("custom_components.omlet_smart_coop.coordinator.asyncio.sleep"):
        yield


@pytest.fixture
def config_entry_data() -> dict:
    """Config entry data."""
    return {API_KEY: API_KEY_VALUE}


@pytest.fixture
def config_entry(hass, config_entry_data):
    """A config entry added to hass, not yet set up."""
    from pytest_homeassistant_custom_component.common import MockConfigEntry

    entry = MockConfigEntry(domain=DOMAIN, data=config_entry_data, title="Omlet Smart Coop")
    entry.add_to_hass(hass)
    return entry
