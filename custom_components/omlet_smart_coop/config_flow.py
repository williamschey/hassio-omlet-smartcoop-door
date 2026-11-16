"""Config flow for Omlet Smart Coop integration."""

from collections.abc import Mapping
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant

from .const import API_KEY, DOMAIN, WEBHOOK_TOKEN
from .coop_api import OmletAuthError, OmletConnectionError, SmartCoopAPI

_LOGGER = logging.getLogger(__name__)


async def _async_validate_api_key(hass: HomeAssistant, api_key: str) -> dict[str, str]:
    """Return config flow errors for an API key: empty if Omlet accepts it."""
    try:
        await SmartCoopAPI(api_key, hass).get_devices()
    except OmletAuthError:
        return {"base": "invalid_api_key"}
    except OmletConnectionError:
        return {"base": "cannot_connect"}
    except Exception:  # noqa: BLE001 - shown to the user as "unknown"
        _LOGGER.exception("Unexpected error validating the Omlet API key")
        return {"base": "unknown"}
    return {}


class OmletSmartCoopConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Omlet Smart Coop."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OmletSmartCoopOptionsFlow()

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        if user_input is not None:
            api_key = user_input[API_KEY].strip()
            self._async_abort_entries_match({API_KEY: api_key})

            errors = await _async_validate_api_key(self.hass, api_key)
            if not errors:
                data = {API_KEY: api_key}
                if token := user_input.get(WEBHOOK_TOKEN, "").strip():
                    data[WEBHOOK_TOKEN] = token
                return self.async_create_entry(title="Omlet Smart Coop", data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(API_KEY): str,
                    vol.Optional(WEBHOOK_TOKEN): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]):
        """Start re-authentication after Omlet rejected the API key."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(self, user_input=None):
        """Ask for a new API key."""
        errors = {}
        if user_input is not None:
            api_key = user_input[API_KEY].strip()
            errors = await _async_validate_api_key(self.hass, api_key)
            if not errors:
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(), data_updates={API_KEY: api_key}
                )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema({vol.Required(API_KEY): str}),
            errors=errors,
        )


class OmletSmartCoopOptionsFlow(config_entries.OptionsFlow):
    """Options: the webhook token checked on incoming Omlet webhooks."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        if user_input is not None:
            token = user_input.get(WEBHOOK_TOKEN, "").strip()
            return self.async_create_entry(data={WEBHOOK_TOKEN: token} if token else {})

        current = self.config_entry.options.get(
            WEBHOOK_TOKEN, self.config_entry.data.get(WEBHOOK_TOKEN, "")
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        WEBHOOK_TOKEN, description={"suggested_value": current}
                    ): str,
                }
            ),
        )
