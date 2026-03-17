"""Constants for masjidboard."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "masjidboard"
ATTRIBUTION = "Data provided by masjidboardlive.com"
API_BASE_URL = "https://masjidboardlive.com/boards/api/board.php"

# Config keys
CONF_MASJID_ID = "masjid_id"

# Per-masjid options
CONF_TRAVEL_TIME = "travel_time"
CONF_ANNOUNCEMENTS_ENABLED = "announcements_enabled"
CONF_FRIENDLY_NAME = "friendly_name"
CONF_TTS_NAME = "tts_name"
DEFAULT_TRAVEL_TIME = 10

# Preferences options
CONF_PREFERRED_MASJID = "preferred_masjid"
CONF_DEVICE_TRACKER = "device_tracker"

# Per-salaah preference values
PREF_PREFERRED = "preferred"
PREF_EARLIEST = "earliest"
PREF_LATEST = "latest"
PREF_DISABLED = "disabled"

# Default TTS pronunciations for prayer names
DEFAULT_TTS_PRAYERS = {
    "Fajr": "Fajr",
    "Dhuhr": "Duhr",
    "Asr": "Asr",
    "Maghrib": "Mughrib",
    "Esha": "Esha",
}

# Prayer schedule: (display_name, api_key, preference_config_key)
PRAYER_SCHEDULE = (
    ("Fajr", "fajrJamaah", "fajr_preference"),
    ("Dhuhr", "dhuhrJamaah", "dhuhr_preference"),
    ("Asr", "asrJamaah", "asr_preference"),
    ("Maghrib", "maghribAthan", "maghrib_preference"),
    ("Esha", "eshaJamaah", "esha_preference"),
)
