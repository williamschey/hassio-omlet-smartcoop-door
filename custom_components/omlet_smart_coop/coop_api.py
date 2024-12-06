from smartcoop import SmartCoop

class SmartCoopAPI:
    def __init__(self, api_key):
        self.api = SmartCoop(api_key)

    def get_devices(self):
        """Retrieve all devices from the API."""
        return self.api.get_all_devices()

    def get_device_state(self, device, key):
        """Get a specific state of a device."""
        return device.get_state(key)

    def set_device_state(self, device, key, value):
        """Set a specific state for a device."""
        device.set_state(key, value)
