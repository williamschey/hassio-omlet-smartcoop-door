from homeassistant.const import Platform
from enum import Enum

class DOOR_MODES(str, Enum):
    LIGHT = 'light'
    TIME = 'time'
    MANUAL = 'manual'

DOMAIN = "omlet_smart_coop"
API_KEY = "api_key"
PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.COVER,
    Platform.LIGHT,
    Platform.SELECT,
    Platform.SENSOR,
]
WEBHOOK_ID_KEY = "webhook_id"
WEBHOOK_TOKEN = "webhook_token"
WEBHOOK_EVENT = f"{DOMAIN}_webhook_event"
