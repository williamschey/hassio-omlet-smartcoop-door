from homeassistant.const import Platform

DOMAIN = "omlet_smart_coop"
API_KEY = "api_key"
PLATFORMS = [Platform.BINARY_SENSOR, Platform.COVER, Platform.LIGHT, Platform.SENSOR]
WEBHOOK_ID_KEY = "webhook_id"
WEBHOOK_TOKEN = "webhook_token"
WEBHOOK_EVENT = f"{DOMAIN}_webhook_event"
