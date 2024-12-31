"""Constants for the Omlet Smart Coop integration."""

from enum import Enum

from homeassistant.const import Platform


class DOOR_MODES(str, Enum):
    """Enumeration of door modes."""

    LIGHT = "light"
    TIME = "time"
    MANUAL = "manual"


DOMAIN = "omlet_smart_coop"
API_KEY = "api_key"
PLATFORMS = [
    Platform.BINARY_SENSOR,
    Platform.COVER,
    Platform.LIGHT,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
    Platform.TIME,
]
WEBHOOK_ID_KEY = "webhook_id"
WEBHOOK_TOKEN = "webhook_token"
WEBHOOK_EVENT = f"{DOMAIN}_webhook_event"
