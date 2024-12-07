
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import API_KEY, DOMAIN, PLATFORMS, COORDINATOR, API, DEVICES
from .coop_api import SmartCoopAPI
from .coordinator import CoopCoordinator

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Omlet Smart Coop from a config entry."""
    api_key = entry.data[API_KEY]
    api = SmartCoopAPI(api_key, hass)
    coordinator = CoopCoordinator(hass, api)

    devices = await hass.async_add_executor_job(api.get_devices)
    hass.data[DOMAIN] = {API: api, DEVICES: devices, COORDINATOR: coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.pop(DOMAIN)
    return unload_ok