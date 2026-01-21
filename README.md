# hassio-omlet-smartcoop-door
Home Assistant integration to monitor and control Omlet's [Smart Automatic Chicken Coop Door](https://www.omlet.co.uk/smart-automatic-chicken-coop-door-opener/)

The Omlet server is **polled**, using their official API, to get the latest status of your devices. Also supports **cloud push** using Omlet's webhooks. Home Assistant can be notified in real-time of any changes without needing to wait for a poll.


## Supported Devices

- [x] Smart Automatic Chicken Coop Door
- [x] Smart Automatic Chicken Coop Fan

## Installation

1. Install HACS - [Instructions](https://www.hacs.xyz/docs/use/download/download/)
2. Add the custom repo to your HACS Store - [Instructions](https://www.hacs.xyz/docs/faq/custom_repositories/)
3. Add the integration to Home Assistant by searching for "Omlet Smart Coop" in the HACS Store
4. Configure the integration by going to Settings -> Devices and Services -> Add integration
5. Enter your [API Key](#api-key)
6. Enjoy


## Configuration

### API Key

Accessing the Omlet API requires an API Key. These are free and limitless:

1. Login to your Omlet Account at https://smart.omlet.com/developers/login
2. Under [API Keys](https://smart.omlet.com/developers/my/api-keys), generate a new key. Copy the newly generated token, that's your API Key that'll you'll need to enter during setup.

### Webhooks

If your HA instance is accessible via the internet, then you can be notified of events in real-time rather than relying on polling.

Create a webhook

1. Visit [Manage Webhooks](https://smart.omlet.com/developers/my/webhooks) in the Omlet Developer Portal.
2. The URL will be [your hostname]**/api/webhook/omlet_smart_coop**
3. Select all the events you want to track.
4. Webhook token is mandatory but not used, any value will suffice.

Enjoy!