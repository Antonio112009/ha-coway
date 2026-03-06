# Coway Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Integration-41BDF5.svg)](https://hacs.xyz/)
[![GitHub manifest version](https://img.shields.io/github/manifest-json/v/Antonio112009/ha-coway?filename=custom_components%2Fha_coway%2Fmanifest.json)](https://github.com/Antonio112009/ha-coway/releases)
[![GitHub License](https://img.shields.io/github/license/Antonio112009/ha-coway)](LICENSE)

Custom [Home Assistant](https://www.home-assistant.io/) integration for [Coway](https://www.coway.com/) air purifiers using the IoCare+ app.

> [!IMPORTANT]
> Your purifiers must be registered with the **IoCare+** app before they can be used with this integration.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Antonio112009&repository=ha-coway&category=integration)

> [!TIP]
> If the button above doesn't work, manually add this repository as a custom repository in HACS:
> 1. Open HACS in Home Assistant.
> 2. Click the three dots in the top right → **Custom repositories**.
> 3. Add `https://github.com/Antonio112009/ha-coway` with category **Integration**.
> 4. Download and restart Home Assistant.

### Manual

1. Download and copy `custom_components/ha_coway` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

> [!WARNING]
> Manual installations don't receive update notifications. You can watch this repository or subscribe to [releases](https://github.com/Antonio112009/ha-coway/releases) to stay informed.

## Setup

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ha_coway)

Or manually: go to **Settings** → **Devices & Services** → **Add Integration** → search for **Coway**.

> [!CAUTION]
> Coway may prompt you to change your password if it hasn't been updated in a while. During setup, you can select **Skip password change** to bypass this. If you don't skip, you'll need to update your password in the IoCare+ app first, then re-authenticate the integration in Home Assistant.

## Devices

Each purifier is exposed as a device in Home Assistant. Depending on your purifier model, the following entities are available:

| Entity | Type | Description |
|--------|------|-------------|
| `Purifier` | `Fan` | Power, speed, and preset mode control (Auto, Night, Rapid, etc.) |
| `Timer` | `Select` | Set timer to OFF, 1h, 2h, 4h, or 8h. Setting a timer can only be done when the purifier is ON. |
| `Light` | `Switch` | Turn indicator light on/off. Controlling the light can only be done when the purifier is ON. |
| `Pre-filter wash frequency` | `Select` | View and change pre-filter wash frequency setting. |
| `Smart mode sensitivity` | `Select` | View and change smart mode sensitivity setting. |
| `Indoor air quality` | `Sensor` | Air quality grade (Good, Moderate, Unhealthy, Very Unhealthy). |
| `PM10` | `Sensor` | Particulate matter 10 concentration. |
| `Lux` | `Sensor` | Light lux measurement. |
| `Pre-filter` | `Sensor` | Pre-filter life remaining (%). |
| `Max2 filter` | `Sensor` | Max2 filter life remaining (%). |
| `Timer remaining` | `Sensor` | Time left on active timer (hours:minutes). |

> [!NOTE]
> Only entities supported by your purifier model are created. Unsupported sensors are automatically hidden.

## License

This project is licensed under the MIT License. See `LICENSE`.

## Acknowledgements

This integration was developed independently from scratch, but was inspired by the work of **Dr. Drinovac** ([@RobertD502](https://github.com/RobertD502)) and his [IoCare Home Assistant integration](https://github.com/RobertD502/home-assistant-iocare). While both integrations share the same idea of bringing Coway purifiers to Home Assistant, they are built on different libraries — this one uses [pycoway](https://github.com/Antonio112009/pycoway), while the original uses [cowayaio](https://github.com/RobertD502/cowayaio).

Robert collects donations for a local animal rescue. If you'd like to support his work:

<a href="https://www.buymeacoffee.com/RobertD502" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="100" width="424"></a>
<a href="https://liberapay.com/RobertD502/donate"><img alt="Donate using Liberapay" src="https://liberapay.com/assets/widgets/donate.svg" height="100" width="300"></a>
