import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN
from smartcoop import SmartCoop, SmartCoopError

class SmartCoopConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Coop."""

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            api_key = user_input["api_key"]

            try:
                api = SmartCoop(api_key)
                await self.hass.async_add_executor_job(api.get_all_devices)
                return self.async_create_entry(title="Smart Coop", data=user_input)
            except SmartCoopError:
                return self.async_show_form(
                    step_id="user",
                    data_schema=self._get_schema(),
                    errors={"base": "invalid_api_key"},
                )

        return self.async_show_form(step_id="user", data_schema=self._get_schema())

    def _get_schema(self):
        return vol.Schema({vol.Required("api_key"): str})
