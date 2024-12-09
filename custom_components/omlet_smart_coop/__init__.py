"""The Omlet Smart Coop integration."""

import logging

from homeassistant.components.webhook import async_register, async_unregister
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, PLATFORMS, WEBHOOK_EVENT, WEBHOOK_ID_KEY, WEBHOOK_TOKEN
from .coordinator import CoopCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Omlet Smart Coop from a config entry."""

    coordinator = CoopCoordinator(hass, entry)

    # devices = await hass.async_add_executor_job(api.get_devices)

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    if WEBHOOK_ID_KEY not in hass.data[DOMAIN]:
        webhook_id = DOMAIN
        # Register the webhook handler
        async_register(
            hass,
            DOMAIN,
            "Omlet Webhook",
            webhook_id,
            async_handle_webhook,
        )

        hass.data[DOMAIN][WEBHOOK_ID_KEY] = webhook_id

    # initial refresh
    await coordinator.async_config_entry_first_refresh()

    # Forward entry to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    async_unregister(hass, DOMAIN)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_handle_webhook(hass: HomeAssistant, webhook_id: str, request):
    """Handle incoming webhook requests."""
    try:
        data = await request.json()
        _LOGGER.debug("Received webhook data: %s", data)
        token = data["token"]

        for config_entry in hass.config_entries.async_entries(DOMAIN):
            coordinator = hass.data[DOMAIN][config_entry.entry_id]
            config_token = config_entry.data.get(WEBHOOK_TOKEN)
            if config_token and token != config_token:
                continue
            await coordinator.async_request_refresh()

        # Dispatch the event to entities
        async_dispatcher_send(hass, WEBHOOK_EVENT, data)

    except Exception as e:
        _LOGGER.error("Error handling webhook: %s", e)
        raise
