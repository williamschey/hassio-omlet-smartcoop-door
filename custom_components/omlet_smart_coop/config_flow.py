import voluptuous as vol
from homeassistant import config_entries
from custom_components.omlet_smart_coop.coop_api import SmartCoopAPI
from .const import DOMAIN
from smartcoop.client import SmartCoopClient
from smartcoop.api.omlet import Omlet

class OmletSmartCoopConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Omlet Smart Coop."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            api_key = user_input["api_key"]

            try:
                client = SmartCoopClient(client_secret=api_key)
                api = Omlet(client)
                api.get_devices() # This will cause an exception if the api_key is wrong
                return self.async_create_entry(title="Omlet Smart Coop", data=user_input)
            except:
                errors["base"] = "invalid_api_key"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("api_key"): str}),
            errors=errors,
        )
