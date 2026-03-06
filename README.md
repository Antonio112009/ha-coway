# Coway Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Integration-41BDF5.svg)](https://hacs.xyz/)

Custom [Home Assistant](https://www.home-assistant.io/) integration for [Coway](https://www.coway.com/) devices.

## HACS

This repository is structured as a HACS custom integration:

1. Open HACS in Home Assistant.
2. Go to **Custom repositories**.
3. Add this repository URL.
4. Select **Integration** as the category.
5. Download the repository and restart Home Assistant.

## Manual installation

1. Copy `custom_components/ha_coway` to your Home Assistant `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings** -> **Devices & Services**.
2. Select **Add Integration**.
3. Search for **Coway**.
4. Enter your Coway account credentials.

## Status

The repository is ready for HACS custom repository installation. Functional device support is still under development.

## Development

The repository includes:

- HACS validation workflow
- Hassfest validation workflow
- Home Assistant config-flow scaffolding

## License

This project is licensed under the MIT License. See `LICENSE`.
