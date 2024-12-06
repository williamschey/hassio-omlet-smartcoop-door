import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN
from smartcoop import SmartCoop, SmartCoopError

class OmletSmartCoopConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Omlet Smart Coop."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            api_key = user_input["api_key"]

            try:
                api = SmartCoop(api_key)
                await self.hass.async_add_executor_job(api.get_all_devices)
                return self.async_create_entry(title="Omlet Smart Coop", data=user_input)
            except SmartCoopError:
                errors["base"] = "invalid_api_key"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("api_key"): str}),
            errors=errors,
        )
