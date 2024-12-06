from smartcoop.client import SmartCoopClient
from smartcoop.api.omlet import Omlet

class SmartCoopAPI:
    def __init__(self, api_key):
        client = SmartCoopClient(client_secret=api_key)
        self.omlet = Omlet(client)

    def get_devices(self):
        """Retrieve all devices from the API."""
        return self.omlet.get_devices()

    def get_device_state(self, device, key):
        """Get a specific state of a device."""
        return getattr(device.state, "light")

    def perform_action(self, device, key, value):
        """Set a specific state for a device."""
        open_action = next((action for action in device.actions if action.name == key), None)
        self.omlet.perform_action(open_action)
