from smartcoop.client import SmartCoopClient
from smartcoop.api.omlet import Omlet
from homeassistant.core import HomeAssistant
import datetime

class SmartCoopAPI:
    def __init__(self, api_key, hass: HomeAssistant):
        self.hass = hass
        client = SmartCoopClient(client_secret=api_key)
        self.omlet = Omlet(client)

    def get_devices(self):
        """Retrieve all devices from the API."""
        if not hasattr(self, 'last_update'):
            self.devices = self.omlet.get_devices()
            self.last_update = datetime.datetime.now()
        return self.devices
    
    def refresh(self):
        newNow = datetime.datetime.now()
        if abs((self.last_update - newNow).seconds) > 10:
            result = self.omlet.get_devices              
                
            self.devices = self.omlet.get_devices()
            self.last_update = datetime.datetime.now()

    def last_updated(self):
        return self.last_update

    def get_device_state(self, device, key):
        """Get a specific state of a device."""
        self.hass.async_add_executor_job(self.refresh)
        mydevice = next((updateddevice for updateddevice in self.devices if updateddevice.deviceId == device.deviceId), None)
        return getattr(mydevice.state, key)

    def perform_action(self, device, key, value):
        """Set a specific state for a device."""
        mydevice = next((updateddevice for updateddevice in self.devices if updateddevice.deviceId == device.deviceId), None)
        omlet_action = next((action for action in mydevice.actions if action.name == key), None)
        self.hass.async_add_executor_job(self.omlet.perform_action, omlet_action)    
        
