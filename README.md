# Coway Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Integration-41BDF5.svg)](https://hacs.xyz/)
[![GitHub manifest version](https://img.shields.io/github/manifest-json/v/Antonio112009/ha-coway?filename=custom_components%2Fha_coway%2Fmanifest.json)](https://github.com/Antonio112009/ha-coway/releases)
[![GitHub License](https://img.shields.io/github/license/Antonio112009/ha-coway)](LICENSE)

Custom [Home Assistant](https://www.home-assistant.io/) integration for [Coway](https://www.coway.com/) air purifiers connected through the IoCare+ cloud service.

This integration adds your Coway purifiers as Home Assistant devices, with support for fan control, preset modes, filter-life sensors, air-quality metrics, timer controls, and model-specific features such as light modes and button lock.

> [!IMPORTANT]
> Your purifiers must be registered with the **IoCare+** app before they can be used with this integration.

## Highlights

- Native Home Assistant config flow
- HACS support
- Multiple purifiers supported under one Coway account
- Configurable cloud polling interval from 30 to 600 seconds
- Model-aware entities so unsupported controls are not created

## Requirements

- A Coway account that can sign in to the IoCare+ app
- At least one purifier already registered in IoCare+
- Home Assistant with access to HACS for the recommended install method

> [!NOTE]
> This is a cloud-polling integration. Commands are sent immediately, then the integration refreshes device state from Coway shortly after.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=Antonio112009&repository=ha-coway&category=integration)

> [!TIP]
> If the button above doesn't work, manually add this repository as a custom repository in HACS:
> 1. Open HACS in Home Assistant.
> 2. Click the three dots in the top right, then choose **Custom repositories**.
> 3. Add `https://github.com/Antonio112009/ha-coway` with category **Integration**.
> 4. Install **Coway** from HACS.
> 5. Restart Home Assistant.

### Manual

1. Download and copy `custom_components/ha_coway` into your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

> [!WARNING]
> Manual installations don't receive update notifications. You can watch this repository or subscribe to [releases](https://github.com/Antonio112009/ha-coway/releases) to stay informed.

## Setup

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=ha_coway)

Or manually: go to **Settings** > **Devices & Services** > **Add Integration** and search for **Coway**.

During setup, you will be asked for:

- Your Coway username
- Your Coway password
- Whether to enable **Skip password change prompt** (enabled by default)

> [!CAUTION]
> Coway may prompt you to change your password if it hasn't been updated in a while. During setup, you can select **Skip password change** to bypass this. If you don't skip, you'll need to update your password in the IoCare+ app first, then re-authenticate the integration in Home Assistant.

After setup, you can adjust the polling interval from **Settings** > **Devices & Services** > **Coway** > **Configure**. The default is `60` seconds, and the allowed range is `30` to `600` seconds.

## Entities

Each purifier is exposed as a device in Home Assistant. The exact entity set depends on the model and on which values the Coway API reports for that device.

| Category | Entities |
|----------|----------|
| `Fan` | `Purifier` with power, speed control, and preset modes |
| `Select` | `Off timer`, `Smart mode sensitivity`, `Pre-filter wash frequency`, `Light mode` |
| `Switch` | `Light`, `Button lock` |
| `Sensor` | `Indoor air quality`, `Air quality index`, `PM2.5`, `PM10`, `CO2`, `VOC`, `Illuminance`, filter-life sensors, `Timer remaining` |
| `Binary sensor` | `Network` |

### Model-specific notes

- `Airmega 250S` and `Airmega IconS` use a `Light mode` select instead of a simple `Light` switch.
- `Airmega 250S` also exposes a `Button lock` switch.
- `AP-1512HHS` UK/EU variants expose `Charcoal filter` and `HEPA filter` sensors instead of `Pre-filter` and `MAX2 filter`.
- `AP-1512HHS` UK/EU variants do not expose the `Pre-filter wash frequency` select.
- Preset modes vary by model. For example, `AP-1512HHS` uses `Auto` and `Eco`, while `Airmega 250S` can expose `Auto`, `Night`, `Rapid`, and `Auto (Eco)` when applicable.

> [!NOTE]
> Only supported entities are created. If the Coway API does not provide a value for a given sensor or control, that entity is omitted automatically.

## Troubleshooting

### Authentication fails

- Confirm the same username and password work in the IoCare+ app.
- If Coway is forcing a password rotation, enable **Skip password change prompt** during setup or update the password in the app first.
- If authentication stops working later, remove and re-add the integration.

### Some entities are missing

- This is usually model-specific behavior rather than an error.
- Reload the integration after pairing if your purifier was newly added to your Coway account.
- Check whether the missing control is one of the model-specific differences listed above.

### Updates feel slow

- Lower the polling interval in the integration options.
- Keep in mind that lower intervals create more API traffic to Coway.

## Support

If you find a bug or a device-specific incompatibility, open an issue on [GitHub](https://github.com/Antonio112009/ha-coway/issues).

If possible, attach Home Assistant diagnostics for the Coway integration with the report. This integration supports diagnostics export, and sensitive fields such as your username, password, and device identifiers are redacted automatically.

To download diagnostics in Home Assistant, open `Settings > Devices & Services > Coway`, then use the integration menu to download diagnostics before filing the issue.

You do not need to enable anything extra in Home Assistant to make diagnostics available. The Diagnostics integration is built in and enabled by default. If you do not see **Download diagnostics**, make sure you are opening the menu for the Coway integration entry in **Settings** > **Devices & Services**.

## License

This project is licensed under the MIT License. See `LICENSE`.

## Acknowledgements

This integration was developed independently from scratch, but was inspired by the work of **Dr. Drinovac** ([@RobertD502](https://github.com/RobertD502)) and his [IoCare Home Assistant integration](https://github.com/RobertD502/home-assistant-iocare). While both integrations share the same idea of bringing Coway purifiers to Home Assistant, they are built on different libraries — this one uses [pycoway](https://github.com/Antonio112009/pycoway), while the original uses [cowayaio](https://github.com/RobertD502/cowayaio).

Robert collects donations for a local animal rescue. If you'd like to support his work:

<a href="https://www.buymeacoffee.com/RobertD502" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="100" width="424"></a>
<a href="https://liberapay.com/RobertD502/donate"><img alt="Donate using Liberapay" src="https://liberapay.com/assets/widgets/donate.svg" height="100" width="300"></a>
