"""Platform for light switch integration."""
from . import DOMAIN, OmletAPI, OmletCoopEntity

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the light platform."""
    api_key = hass.data[DOMAIN]["api_key"]
    host = hass.data[DOMAIN]["host"]
    session = hass.data[DOMAIN]["session"]
    device_id = hass.data[DOMAIN]["device_id"]
    async_add_entities([
        OmletLightSwitch(api_key, host, session, device_id),
    ])

class OmletLightSwitch(OmletCoopEntity):
    """Representation of a Light Switch for the coop light."""

    def __init__(self, api_key, host, session, device_id):
        """Initialize the light switch."""
        super().__init__(api_key, host, session)
        self.device_id = device_id
        self._is_on = False

    @property
    def is_on(self):
        """Return the state of the light."""
        return self._is_on

    async def async_turn_on(self):
        """Turn on the light."""
        api = OmletAPI(self.api_key, self.host, self.session)
        if await api.control_device(self.device_id, 'on'):
            self._is_on = True
            self.async_write_ha_state()

    async def async_turn_off(self):
        """Turn off the light."""
        api = OmletAPI(self.api_key, self.host, self.session)
        if await api.control_device(self.device_id, 'off'):
            self._is_on = False
            self.async_write_ha_state()

    async def async_update(self):
        """Update the state of the light."""
        api = OmletAPI(self.api_key, self.host, self.session)
        data = await api.fetch_device_info(self.device_id)
        if data:
            self._is_on = data[0]['state']['light']['state'] == 'on'
