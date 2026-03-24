# MasjidBoard Live for Home Assistant

[![HACS Validation](https://github.com/yusuff/masjidboard-hass/actions/workflows/validate.yml/badge.svg)](https://github.com/yusuff/masjidboard-hass/actions/workflows/validate.yml)
[![Lint](https://github.com/yusuff/masjidboard-hass/actions/workflows/lint.yml/badge.svg)](https://github.com/yusuff/masjidboard-hass/actions/workflows/lint.yml)

A Home Assistant custom integration that fetches prayer times from [MasjidBoard Live](https://masjidboardlive.com) for your local masjid.

## Features

- Daily prayer times (Fajr, Dhuhr, Asr, Maghrib, Esha)
- Athan and Jamaah times for each prayer
- Jumuah prayer times
- Additional times: Sehri, Sunrise, Ishraaq, Sunset

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance.
2. Go to **Integrations** and click the three-dot menu.
3. Select **Custom repositories**.
4. Add `https://github.com/lockhaty/masjidboard-hass` with category **Integration**.
5. Search for "MasjidBoard Live" and install it.
6. Restart Home Assistant.

### Manual

1. Copy the `custom_components/masjidboard` directory into your Home Assistant `custom_components` folder.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings** > **Devices & Services** > **Add Integration**.
2. Search for "MasjidBoard Live".
3. Enter your Masjid ID (found on your MasjidBoard Live dashboard).

## Sensors

The integration creates sensors for the following prayer times:

| Sensor | Description |
|---|---|
| Sehri Ends | End of Sehri time |
| Fajr Athan / Jamaah | Fajr athan and congregation times |
| Sunrise | Sunrise time |
| Ishraaq | Ishraaq prayer time |
| Dhuhr Athan / Jamaah | Dhuhr athan and congregation times |
| Jumuah 1 / 2 / 3 | Friday prayer times |
| Asr Start (Shafi / Hanafi) | Asr start times by madhab |
| Asr Athan / Jamaah | Asr athan and congregation times |
| Sunset | Sunset time |
| Maghrib Athan / Jamaah | Maghrib athan and congregation times |
| Esha Athan / Jamaah | Esha athan and congregation times |

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
