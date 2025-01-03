"""Config flow for Omlet Smart Coop integration."""

from urllib.error import HTTPError

from smartcoop.api.omlet import Omlet
from smartcoop.client import SmartCoopClient
import voluptuous as vol

from homeassistant import config_entries

from .const import API_KEY, DOMAIN


class OmletSmartCoopConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Omlet Smart Coop."""

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            api_key = user_input.get(API_KEY)

            try:
                client = SmartCoopClient(client_secret=api_key)
                api = Omlet(client)
                await self.hass.async_add_executor_job(api.get_devices)
                return self.async_create_entry(
                    title="Omlet Smart Coop", data=user_input
                )
            except HTTPError:
                errors["base"] = "invalid_api_key"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(API_KEY): str}),
            errors=errors,
        )
