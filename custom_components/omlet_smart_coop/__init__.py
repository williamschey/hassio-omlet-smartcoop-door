"""The Omlet Smart Coop integration."""

import hmac
import logging

from homeassistant.components.webhook import async_register, async_unregister
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, PLATFORMS, WEBHOOK_EVENT, WEBHOOK_ID_KEY, WEBHOOK_TOKEN
from .coordinator import CoopCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Omlet Smart Coop from a config entry."""

    _async_move_webhook_token_to_options(hass, entry)

    coordinator = CoopCoordinator(hass, entry)

    # initial refresh
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    _async_migrate_device_identifiers(hass, coordinator)

    if WEBHOOK_ID_KEY not in hass.data[DOMAIN]:
        webhook_id = DOMAIN
        # Register the webhook handler
        async_register(
            hass,
            DOMAIN,
            "Omlet Webhook",
            webhook_id,
            async_handle_webhook,
            allowed_methods=["POST"],
        )

        hass.data[DOMAIN][WEBHOOK_ID_KEY] = webhook_id

    # Forward entry to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        domain_data = hass.data[DOMAIN]
        domain_data.pop(entry.entry_id)
        # The webhook is shared by every entry: remove it with the last one,
        # so that setting an entry up again registers it again.
        if not any(key != WEBHOOK_ID_KEY for key in domain_data):
            webhook_id = domain_data.pop(WEBHOOK_ID_KEY, None)
            if webhook_id is not None:
                async_unregister(hass, webhook_id)

    return unload_ok


@callback
def _async_migrate_device_identifiers(
    hass: HomeAssistant, coordinator: CoopCoordinator
) -> None:
    """Move devices registered under their name to their Omlet device ID.

    Up to 1.0.10 the device identifier was the device's name, so renaming a
    device in the Omlet app created a new device in Home Assistant.
    """
    dev_reg = dr.async_get(hass)
    by_identifier = {
        identifier: registered
        for registered in dr.async_entries_for_config_entry(
            dev_reg, coordinator.config_entry.entry_id
        )
        for domain, identifier in registered.identifiers
        if domain == DOMAIN
    }
    for device_id, device in coordinator.data.items():
        if device_id in by_identifier:
            continue
        old = by_identifier.get(device.name)
        if old is not None:
            dev_reg.async_update_device(old.id, new_identifiers={(DOMAIN, device_id)})
            by_identifier[device_id] = old


@callback
def _async_move_webhook_token_to_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Keep the webhook token in the options only, so clearing it there works.

    An earlier revision of this change stored a token entered at setup in the
    entry's data.
    """
    if WEBHOOK_TOKEN not in entry.data:
        return
    data = dict(entry.data)
    token = data.pop(WEBHOOK_TOKEN)
    options = dict(entry.options)
    if token and WEBHOOK_TOKEN not in options:
        options[WEBHOOK_TOKEN] = token
    hass.config_entries.async_update_entry(entry, data=data, options=options)


def _entry_webhook_token(entry: ConfigEntry) -> str | None:
    """Return the webhook token set for an entry, if any."""
    return entry.options.get(WEBHOOK_TOKEN) or None


def _tokens_match(received, expected: str) -> bool:
    """Compare tokens in constant time.

    hmac.compare_digest only accepts ASCII str, so compare UTF-8 bytes.
    """
    return isinstance(received, str) and hmac.compare_digest(
        received.encode(), expected.encode()
    )


async def async_handle_webhook(hass: HomeAssistant, webhook_id: str, request):
    """Handle incoming webhook requests.

    An entry with a webhook token set only refreshes for requests carrying
    that token. An entry without one refreshes for any request, as before.
    """
    try:
        data = await request.json()
    except ValueError:
        _LOGGER.warning("Ignoring an Omlet webhook request whose body is not JSON")
        return

    _LOGGER.debug("Received webhook data: %s", data)
    token = data.get("token") if isinstance(data, dict) else None

    matched = False
    for config_entry in hass.config_entries.async_entries(DOMAIN):
        coordinator = hass.data.get(DOMAIN, {}).get(config_entry.entry_id)
        if coordinator is None:
            continue  # not loaded
        config_token = _entry_webhook_token(config_entry)
        if config_token and not _tokens_match(token, config_token):
            continue
        matched = True
        await coordinator.async_request_refresh()

    if not matched:
        _LOGGER.debug("Ignoring an Omlet webhook request that matches no entry")
        return

    # Dispatch the event to entities
    async_dispatcher_send(hass, WEBHOOK_EVENT, data)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry
) -> bool:
    """Remove a config entry from a device."""
    return True
