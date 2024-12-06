"""Platform for sensor integration."""
from . import DOMAIN, OmletAPI, OmletCoopEntity

async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the sensor platform."""
    api_key = hass.data[DOMAIN]["api_key"]
    host = hass.data[DOMAIN]["host"]
    session = hass.data[DOMAIN]["session"]
    device_id = hass.data[DOMAIN]["device_id"]
    async_add_entities([
        OmletBatterySensor(api_key, host, session, device_id),
        OmletDoorSensor(api_key, host, session, device_id),
    ])

class OmletBatterySensor(OmletCoopEntity):
    """Representation of a Battery Sensor."""

    async def async_update(self):
        """Fetch new state data for the sensor."""
        api = OmletAPI(self.api_key, self.host, self.session)
        data = await api.fetch_device_info(self.device_id)
        if data:
            self.battery_level = data[0]['state']['general']['batteryLevel']

class OmletDoorSensor(OmletCoopEntity):
    """Representation of a Door Sensor."""

    async def async_update(self):
        """Fetch new state data for the sensor."""
        api = OmletAPI(self.api_key, self.host, self.session)
        data = await api.fetch_device_info(self.device_id)
        if data:
            self.door_status = data[0]['state']['door']['state']
