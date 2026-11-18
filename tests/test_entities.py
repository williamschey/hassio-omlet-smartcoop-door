"""Entity behaviour: switch, cover, number, time and the Next Update sensor."""

from datetime import datetime
from unittest.mock import AsyncMock

from freezegun.api import FrozenDateTimeFactory
import pytest
import requests

from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util

from custom_components.omlet_smart_coop.coordinator import (
    FAST_UPDATE_INTERVAL,
    NORMAL_UPDATE_INTERVAL,
    CoopCoordinator,
)
from custom_components.omlet_smart_coop.sensor import CoopNextUpdateTime

from .conftest import load_device

from custom_components.omlet_smart_coop.const import DOMAIN


def eid(hass: HomeAssistant, platform: str, key: str) -> str:
    """The entity ID of the door's entity with this unique ID key."""
    entity_id = er.async_get(hass).async_get_entity_id(platform, DOMAIN, f"door-id_{key}")
    assert entity_id, f"no {platform} entity door-id_{key}"
    return entity_id


async def _setup(hass: HomeAssistant, entry) -> None:
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


def _patched_config(mock_omlet):
    """The configuration sent by the last update_configuration call."""
    return mock_omlet.update_configuration.call_args.args[1]


# --- switch ---------------------------------------------------------------


@pytest.mark.parametrize("enabled", [True, False])
async def test_switch_state_follows_config(
    hass: HomeAssistant, mock_omlet, config_entry, devices, enabled
) -> None:
    """Fixed: is_on was a method, so the switch always read as on."""
    devices[0].configuration.general.overnightSleepEnable = enabled
    await _setup(hass, config_entry)
    assert hass.states.get(eid(hass, "switch", "overnight_sleep_enabled")).state == (STATE_ON if enabled else STATE_OFF)


@pytest.mark.parametrize(
    ("service", "start", "sent"),
    [("turn_off", True, False), ("turn_on", False, True)],
)
async def test_switch_sends_config(
    hass: HomeAssistant, mock_omlet, config_entry, devices, service, start, sent
) -> None:
    """Fixed: turning the switch on or off never sent anything."""
    devices[0].configuration.general.overnightSleepEnable = start
    await _setup(hass, config_entry)

    await hass.services.async_call(
        "switch", service, {ATTR_ENTITY_ID: eid(hass, "switch", "overnight_sleep_enabled")}, blocking=True
    )

    mock_omlet.update_configuration.assert_called_once()
    assert mock_omlet.update_configuration.call_args.args[0] == "door-id"
    assert _patched_config(mock_omlet).general.overnightSleepEnable is sent


# --- cover ----------------------------------------------------------------


async def test_cover_action_sent(
    hass: HomeAssistant, mock_omlet, config_entry, no_action_sleep
) -> None:
    """Opening the door posts the door's open action."""
    await _setup(hass, config_entry)
    await hass.services.async_call(
        "cover", "open_cover", {ATTR_ENTITY_ID: eid(hass, "cover", "cover")}, blocking=True
    )
    action = mock_omlet.perform_action.call_args.args[0]
    assert action.name == "open"


async def test_missing_action_is_a_clear_error(
    hass: HomeAssistant, mock_omlet, config_entry, devices, no_action_sleep
) -> None:
    """Fixed: a missing action passed None to the SDK and crashed."""
    devices[0].actions = [a for a in devices[0].actions if a.name != "stop"]
    await _setup(hass, config_entry)

    with pytest.raises(HomeAssistantError, match="'stop' action"):
        await hass.services.async_call(
            "cover", "stop_cover", {ATTR_ENTITY_ID: eid(hass, "cover", "cover")}, blocking=True
        )
    mock_omlet.perform_action.assert_not_called()


def _coordinator_with(hass, config_entry, *devices) -> CoopCoordinator:
    coordinator = CoopCoordinator(hass, config_entry)
    coordinator.data = {d.deviceId: d for d in devices}
    return coordinator


async def _refresh(hass: HomeAssistant, config_entry) -> CoopCoordinator:
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    await coordinator.async_refresh()
    await hass.async_block_till_done()
    return coordinator


@pytest.mark.parametrize(
    "devices", [[load_device("door"), load_device("feeder")]]
)
async def test_polling_follows_device_states(
    hass: HomeAssistant, mock_omlet, config_entry, devices
) -> None:
    """Poll fast while any door or hatch moves, whatever the entities are doing."""
    door, feeder = devices
    door.state.door.state = "open"
    feeder.state.feeder.state = "closed"
    await _setup(hass, config_entry)
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    assert coordinator.update_interval == NORMAL_UPDATE_INTERVAL

    door.state.door.state = "closepending"
    assert (await _refresh(hass, config_entry)).update_interval == FAST_UPDATE_INTERVAL

    # An idle feeder doesn't slow polling while the door moves.
    door.state.door.state = "closing"
    assert (await _refresh(hass, config_entry)).update_interval == FAST_UPDATE_INTERVAL

    door.state.door.state = "closed"
    feeder.state.feeder.state = "opening"
    assert (await _refresh(hass, config_entry)).update_interval == FAST_UPDATE_INTERVAL

    feeder.state.feeder.state = "open"
    assert (await _refresh(hass, config_entry)).update_interval == NORMAL_UPDATE_INTERVAL


async def test_disabled_cover_does_not_hold_fast_polling(
    hass: HomeAssistant, mock_omlet, config_entry, devices
) -> None:
    """Review point 4: a disabled cover created mid-move kept polling at 10 s."""
    registry = er.async_get(hass)
    registry.async_get_or_create(
        "cover",
        DOMAIN,
        "door-id_cover",
        config_entry=config_entry,
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    devices[0].state.door.state = "opening"
    await _setup(hass, config_entry)
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    assert registry.async_get(eid(hass, "cover", "cover")).disabled
    assert coordinator.update_interval == FAST_UPDATE_INTERVAL

    devices[0].state.door.state = "open"
    assert (await _refresh(hass, config_entry)).update_interval == NORMAL_UPDATE_INTERVAL


async def test_open_command_polls_fast(
    hass: HomeAssistant, mock_omlet, config_entry, no_action_sleep
) -> None:
    """Right after an open or close command, poll fast until the device reports."""
    await _setup(hass, config_entry)
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    coordinator.async_request_refresh = AsyncMock()
    assert coordinator.update_interval == NORMAL_UPDATE_INTERVAL

    await hass.services.async_call(
        "cover", "close_cover", {ATTR_ENTITY_ID: eid(hass, "cover", "cover")}, blocking=True
    )
    assert coordinator.update_interval == FAST_UPDATE_INTERVAL


async def test_light_command_keeps_normal_polling(
    hass: HomeAssistant, mock_omlet, config_entry, no_action_sleep
) -> None:
    """Only moves speed up polling."""
    await _setup(hass, config_entry)
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    coordinator.async_request_refresh = AsyncMock()

    light = er.async_get(hass).async_get_entity_id("light", DOMAIN, "door-id_light")
    await hass.services.async_call("light", "turn_on", {ATTR_ENTITY_ID: light}, blocking=True)
    assert coordinator.update_interval == NORMAL_UPDATE_INTERVAL


async def test_missing_action_leaves_state_and_polling(
    hass: HomeAssistant, mock_omlet, config_entry, devices, no_action_sleep
) -> None:
    """Review point 5: the optimistic state was set before the action check."""
    devices[0].state.door.state = "open"
    devices[0].actions = [a for a in devices[0].actions if a.name != "close"]
    await _setup(hass, config_entry)
    cover = eid(hass, "cover", "cover")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    states: list[str] = []
    hass.bus.async_listen(
        "state_changed",
        lambda event: states.append(event.data["new_state"].state)
        if event.data["entity_id"] == cover
        else None,
    )

    with pytest.raises(HomeAssistantError, match="'close' action"):
        await hass.services.async_call(
            "cover", "close_cover", {ATTR_ENTITY_ID: cover}, blocking=True
        )
    await hass.async_block_till_done()

    assert hass.states.get(cover).state == "open"
    assert states == []  # never shown as closing
    assert coordinator.update_interval == NORMAL_UPDATE_INTERVAL


async def test_failed_command_restores_state(
    hass: HomeAssistant, mock_omlet, config_entry, devices, no_action_sleep
) -> None:
    """If Omlet can't be reached, the cover goes back to its last reported state."""
    devices[0].state.door.state = "closed"
    await _setup(hass, config_entry)
    cover = eid(hass, "cover", "cover")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    mock_omlet.perform_action.side_effect = requests.ConnectionError("down")

    with pytest.raises(HomeAssistantError, match="Omlet"):
        await hass.services.async_call(
            "cover", "open_cover", {ATTR_ENTITY_ID: cover}, blocking=True
        )
    await hass.async_block_till_done()

    assert hass.states.get(cover).state == "closed"
    assert coordinator.update_interval == NORMAL_UPDATE_INTERVAL


# --- number ---------------------------------------------------------------


async def test_number_sends_int(hass: HomeAssistant, mock_omlet, config_entry) -> None:
    """Fixed: the value was sent as a float (300.0); the API takes an int."""
    await _setup(hass, config_entry)
    state = hass.states.get(eid(hass, "number", "poll_time"))
    assert state.attributes["unit_of_measurement"] == "s"

    await hass.services.async_call(
        "number",
        "set_value",
        {ATTR_ENTITY_ID: eid(hass, "number", "poll_time"), "value": 300},
        blocking=True,
    )
    poll = _patched_config(mock_omlet).general.pollFreq
    assert poll == 300 and isinstance(poll, int)


async def test_light_level_unit(hass: HomeAssistant, mock_omlet, config_entry) -> None:
    """Units are native units, so Home Assistant shows them."""
    await _setup(hass, config_entry)
    state = hass.states.get(eid(hass, "number", "open_light_level"))
    assert state.attributes["unit_of_measurement"] == "%"


# --- time -----------------------------------------------------------------


async def test_time_entity(hass: HomeAssistant, mock_omlet, config_entry, devices) -> None:
    """The time inputs are TimeEntity: state is a time, and set_value sends HH:MM."""
    devices[0].configuration.door.openTime = "07:00"
    await _setup(hass, config_entry)
    assert hass.states.get(eid(hass, "time", "open_time")).state == "07:00:00"

    await hass.services.async_call(
        "time",
        "set_value",
        {ATTR_ENTITY_ID: eid(hass, "time", "open_time"), "time": "06:30:00"},
        blocking=True,
    )
    assert _patched_config(mock_omlet).door.openTime == "06:30"


async def test_time_entity_unset(hass: HomeAssistant, mock_omlet, config_entry, devices) -> None:
    """A schedule slot the API leaves empty is unknown, not an error."""
    devices[0].configuration.door.closeTime = None
    await _setup(hass, config_entry)
    assert hass.states.get(eid(hass, "time", "close_time")).state == "unknown"


# --- Next Update sensor ---------------------------------------------------


@pytest.mark.parametrize(
    ("local_now", "expected_local"),
    [
        # Inside a 21:00-06:00 window before midnight: next update at 06:00 tomorrow.
        ("2026-06-01 23:00", "2026-06-02 06:00"),
        # Fixed: after midnight, the window that started yesterday was missed.
        ("2026-06-02 02:00", "2026-06-02 06:00"),
    ],
)
async def test_next_update_during_overnight_sleep(
    hass: HomeAssistant,
    config_entry,
    freezer: FrozenDateTimeFactory,
    local_now: str,
    expected_local: str,
) -> None:
    """The sleep window is read in Home Assistant's time zone, not the host's."""
    await hass.config.async_set_time_zone("Europe/London")  # BST: UTC+1
    tz = dt_util.get_default_time_zone()
    freezer.move_to(datetime.fromisoformat(local_now).replace(tzinfo=tz))

    device = load_device("door")
    device.state.general.powerSource = "battery"
    device.configuration.general.overnightSleepEnable = True
    device.configuration.general.overnightSleepStart = "21:00"
    device.configuration.general.overnightSleepEnd = "06:00"
    coordinator = _coordinator_with(hass, config_entry, device)

    sensor = CoopNextUpdateTime(device, coordinator)
    assert sensor.native_value == datetime.fromisoformat(expected_local).replace(tzinfo=tz)


async def test_next_update_outside_sleep(
    hass: HomeAssistant, config_entry, freezer: FrozenDateTimeFactory
) -> None:
    """Outside the window: the last check-in plus the poll interval."""
    await hass.config.async_set_time_zone("Europe/London")
    tz = dt_util.get_default_time_zone()
    freezer.move_to(datetime(2026, 6, 2, 12, 0, tzinfo=tz))

    device = load_device("door")
    device.state.general.powerSource = "battery"
    device.configuration.general.datetime = "2026-06-02T11:55:00+01:00"
    device.configuration.general.pollFreq = 600
    coordinator = _coordinator_with(hass, config_entry, device)

    sensor = CoopNextUpdateTime(device, coordinator)
    assert sensor.native_value == datetime(2026, 6, 2, 12, 5, tzinfo=tz)
