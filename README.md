# Coway Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Integration-41BDF5.svg)](https://hacs.xyz/)
[![GitHub manifest version](https://img.shields.io/github/manifest-json/v/Antonio112009/ha-coway?filename=custom_components%2Fha_coway%2Fmanifest.json)](https://github.com/Antonio112009/ha-coway/releases)
[![GitHub License](https://img.shields.io/github/license/Antonio112009/ha-coway)](LICENSE)

Custom [Home Assistant](https://www.home-assistant.io/) integration for [Coway](https://www.coway.com/) air purifiers using the IoCare+ app.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Antonio112009&repository=ha-coway&category=integration)

> **Tip:** If the button above doesn't work, manually add this repository as a custom repository in HACS:
> 1. Open HACS in Home Assistant.
> 2. Click the three dots in the top right → **Custom repositories**.
> 3. Add `https://github.com/Antonio112009/ha-coway` with category **Integration**.
> 4. Download and restart Home Assistant.

### Manual

1. Copy the `custom_components/ha_coway` directory to your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

> **Note:** Manual installations won't receive automatic update notifications. Subscribe to [releases](https://github.com/Antonio112009/ha-coway/releases) to stay updated.

## Setup

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ha_coway)

> **Tip:** If the button above doesn't work:
> 1. Go to **Settings** → **Devices & Services**.
> 2. Click **+ Add Integration**.
> 3. Search for **Coway**.
> 4. Enter your IoCare+ account credentials.

> **⚠️ Important:** Your purifiers must be registered with the **IoCare+** app before they can be used with this integration.

## Devices

Each purifier is exposed as a device in Home Assistant. Depending on your purifier model, the following entities are available:

| Entity | Type | Description |
|--------|------|-------------|
| Purifier | Fan | Power, speed, and preset mode control (Auto, Night, Rapid, etc.) |
| Timer | Select | Set timer to OFF, 1h, 2h, 4h, or 8h (purifier must be ON) |
| Light | Switch | Turn indicator light on/off (purifier must be ON) |
| Pre-filter wash frequency | Select | View and change pre-filter wash frequency |
| Smart mode sensitivity | Select | View and change smart mode sensitivity |
| Indoor air quality | Sensor | Air quality grade (Good, Moderate, Unhealthy, Very Unhealthy) |
| PM10 | Sensor | Particulate matter 10 concentration |
| Lux | Sensor | Light lux measurement |
| Pre-filter | Sensor | Pre-filter life remaining (%) |
| Max2 filter | Sensor | Max2 filter life remaining (%) |
| Timer remaining | Sensor | Time left on active timer |

> **Note:** Only entities supported by your purifier model are created. Unsupported sensors are automatically hidden.

## License

This project is licensed under the MIT License. See `LICENSE`.

## Acknowledgements

This integration is built on top of the work by **Dr. Drinovac** ([@RobertD502](https://github.com/RobertD502)), who created the original [cowayaio](https://github.com/RobertD502/cowayaio) Python library and the [IoCare Home Assistant integration](https://github.com/RobertD502/home-assistant-iocare) for Coway air purifiers.

Robert collects donations for a local animal rescue. If you'd like to support his work, you can donate through his repository:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-donate-yellow)](https://www.buymeacoffee.com/RobertD502)
[![Liberapay](https://img.shields.io/badge/Liberapay-donate-F6C915)](https://liberapay.com/RobertD502/donate)
