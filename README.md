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

## Prayer Times Card

The integration includes a custom Lovelace card for displaying salaah times visually.

### Setup

Add the card as a Lovelace resource:

1. Go to **Settings** > **Dashboards** > **Resources** (three-dot menu).
2. Click **Add Resource**.
3. Enter URL: `/masjidboard/masjidboard-prayer-times-card.js`
4. Select **JavaScript Module** and click **Create**.

### Usage

Add the card to your dashboard:

```yaml
type: custom:masjidboard-prayer-times-card
entity: sensor.<your_masjid>_next_prayer
```

You can also add it via the visual editor — search for **MasjidBoard Prayer Times** in the card picker.

### Options

| Option | Default | Description |
|---|---|---|
| `entity` | *required* | The `next_prayer` sensor entity for your masjid |
| `show_header` | `true` | Show the masjid name header and next prayer banner |
| `show_athan` | `true` | Show athan times alongside jamaah times |
| `show_extra` | `true` | Show extra times (Sehri, Sunrise, Ishraaq, Sunset) |
| `highlight_next` | `true` | Highlight the next upcoming prayer row |

### Example

```yaml
type: custom:masjidboard-prayer-times-card
entity: sensor.my_local_masjid_next_prayer
show_athan: true
show_extra: true
highlight_next: true
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
