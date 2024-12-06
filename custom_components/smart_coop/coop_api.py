from smartcoop import SmartCoop

class SmartCoopAPI:
    def __init__(self, api_key):
        self.api = SmartCoop(api_key)

    def get_devices(self):
        """Retrieve all devices associated with the account."""
        return self.api.get_all_devices()

    def get_device_state(self, device, key):
        """Get the state of a specific attribute for a device."""
        return device.get_state(key)

    def set_door_state(self, device, open):
        """Open or close the door."""
        return device.set_door_open(open)
