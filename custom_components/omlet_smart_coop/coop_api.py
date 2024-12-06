from smartcoop.client import SmartCoopClient
from smartcoop.api.omlet import Omlet
import datetime

class SmartCoopAPI:
    def __init__(self, api_key):
        client = SmartCoopClient(client_secret=api_key)
        self.omlet = Omlet(client)
        self.devices = self.omlet.get_devices()
        self.last_update = datetime.datetime.now()

    def get_devices(self):
        """Retrieve all devices from the API."""
        self.refresh(self)
        return self.devices
    
    def refresh(self):
        newNow = datetime.datetime.now()
        if abs((self.last_update - newNow).seconds) > 10:
            self.devices = self.omlet.get_devices()
            self.last_update = datetime.datetime.now()


    def get_device_state(self, device, key):
        """Get a specific state of a device."""
        self.refresh(self)
        mydevice = next((updateddevice for updateddevice in self.devices if updateddevice.deviceId == device.deviceId), None)
        return getattr(mydevice.state, key)

    def perform_action(self, device, key, value):
        """Set a specific state for a device."""
        mydevice = next((updateddevice for updateddevice in self.devices if updateddevice.deviceId == device.deviceId), None)
        omlet_action = next((action for action in mydevice.actions if action.name == key), None)
        self.hass.async_add_executor_job(self.omlet.perform_action, omlet_action)    
        
