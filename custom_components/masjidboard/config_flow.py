"""Config flow for MasjidBoard."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    MasjidBoardApiClient,
    MasjidBoardApiClientCommunicationError,
    MasjidBoardApiClientError,
)
from .const import (
    CONF_ANNOUNCEMENTS_ENABLED,
    CONF_DEVICE_TRACKER,
    CONF_FRIENDLY_NAME,
    CONF_MASJID_ID,
    CONF_PREFERRED_MASJID,
    CONF_TRAVEL_TIME,
    CONF_TTS_NAME,
    DEFAULT_TRAVEL_TIME,
    DEFAULT_TTS_PRAYERS,
    DOMAIN,
    LOGGER,
    PRAYER_SCHEDULE,
    PREF_DISABLED,
    PREF_EARLIEST,
    PREF_LATEST,
    PREF_PREFERRED,
)


def _is_masjid_entry(entry: config_entries.ConfigEntry) -> bool:
    return CONF_MASJID_ID in entry.data


def _is_preferences_entry(entry: config_entries.ConfigEntry) -> bool:
    return CONF_MASJID_ID not in entry.data


class MasjidBoardFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for MasjidBoard."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> MasjidBoardMasjidOptionsFlow | MasjidBoardPreferencesOptionsFlow:
        """Get the options flow handler."""
        if _is_masjid_entry(config_entry):
            return MasjidBoardMasjidOptionsFlow()
        return MasjidBoardPreferencesOptionsFlow()

    async def async_step_user(
        self,
        user_input: dict | None = None,  # noqa: ARG002
    ) -> config_entries.ConfigFlowResult:
        """Show the menu."""
        return self.async_show_menu(
            step_id="user",
            menu_options=["add_masjid", "preferences"],
        )

    async def async_step_add_masjid(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle adding a masjid."""
        _errors: dict[str, str] = {}
        if user_input is not None:
            masjid_id = self._normalize_masjid_id(user_input[CONF_MASJID_ID])

            try:
                response = await self._test_masjid(masjid_id)
            except MasjidBoardApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except MasjidBoardApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                if not response.get("ok") or "data" not in response:
                    _errors["base"] = "not_found"
                else:
                    meta = response["data"].get("meta", {})
                    masjid_name = meta.get("masjid", masjid_id)

                    await self.async_set_unique_id(masjid_id)
                    self._abort_if_unique_id_configured()

                    return self.async_create_entry(
                        title=masjid_name,
                        data={CONF_MASJID_ID: masjid_id},
                    )

        return self.async_show_form(
            step_id="add_masjid",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MASJID_ID,
                        default=(user_input or {}).get(CONF_MASJID_ID, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.URL,
                        ),
                    ),
                },
            ),
            description_placeholders={
                "masjidboardlive_url": "masjidboardlive.com",
                "find_masjid_url": "https://masjidboardlive.com/findmasjid",
            },
            errors=_errors,
        )

    async def async_step_preferences(
        self,
        user_input: dict | None = None,  # noqa: ARG002
    ) -> config_entries.ConfigFlowResult:
        """Create the preferences entry."""
        # Only allow one preferences entry
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if _is_preferences_entry(entry):
                return self.async_abort(reason="preferences_already_configured")

        await self.async_set_unique_id(f"{DOMAIN}_preferences")
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title="MasjidBoard Preferences",
            data={},
        )

    @staticmethod
    def _normalize_masjid_id(raw_input: str) -> str:
        """Extract the masjid slug from user input."""
        value = raw_input.strip()
        if "masjidboardlive.com" in value:
            if "id=" in value:
                value = value.split("id=")[-1].split("&")[0]
            elif "boards?" in value:
                value = value.split("boards?")[-1].split("&")[0]
        return value.strip().lower()

    async def _test_masjid(self, masjid_id: str) -> dict:
        """Validate that the masjid ID exists by fetching its data."""
        client = MasjidBoardApiClient(
            masjid_id=masjid_id,
            session=async_create_clientsession(self.hass),
        )
        return await client.async_get_data()


class MasjidBoardMasjidOptionsFlow(config_entries.OptionsFlow):
    """Handle per-masjid options."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage masjid options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_FRIENDLY_NAME,
                        default=self.config_entry.options.get(
                            CONF_FRIENDLY_NAME, ""
                        ),
                    ): selector.TextSelector(),
                    vol.Optional(
                        CONF_TTS_NAME,
                        default=self.config_entry.options.get(
                            CONF_TTS_NAME, ""
                        ),
                    ): selector.TextSelector(),
                    vol.Optional(
                        CONF_TRAVEL_TIME,
                        default=self.config_entry.options.get(
                            CONF_TRAVEL_TIME, DEFAULT_TRAVEL_TIME
                        ),
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=120,
                            step=1,
                            unit_of_measurement="minutes",
                            mode=selector.NumberSelectorMode.BOX,
                        ),
                    ),
                    vol.Optional(
                        CONF_ANNOUNCEMENTS_ENABLED,
                        default=self.config_entry.options.get(
                            CONF_ANNOUNCEMENTS_ENABLED, True
                        ),
                    ): selector.BooleanSelector(),
                },
            ),
        )


class MasjidBoardPreferencesOptionsFlow(config_entries.OptionsFlow):
    """Handle global preferences options."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Manage preferences."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        # Build masjid dropdown options from configured entries
        masjid_options = [
            selector.SelectOptionDict(
                value=entry.entry_id,
                label=entry.title,
            )
            for entry in self.hass.config_entries.async_entries(DOMAIN)
            if _is_masjid_entry(entry)
        ]

        pref_options = [
            selector.SelectOptionDict(value=PREF_PREFERRED, label="Preferred masjid"),
            selector.SelectOptionDict(value=PREF_EARLIEST, label="Earliest"),
            selector.SelectOptionDict(value=PREF_LATEST, label="Latest"),
            selector.SelectOptionDict(value=PREF_DISABLED, label="Disabled"),
        ]

        # Add individual masjids so users can pick a specific masjid per salaah
        for entry in self.hass.config_entries.async_entries(DOMAIN):
            if _is_masjid_entry(entry):
                pref_options.append(
                    selector.SelectOptionDict(
                        value=entry.entry_id, label=entry.title
                    ),
                )

        schema_dict: dict[vol.Marker, Any] = {}

        if masjid_options:
            schema_dict[
                vol.Optional(
                    CONF_PREFERRED_MASJID,
                    default=self.config_entry.options.get(CONF_PREFERRED_MASJID),
                )
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=masjid_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                ),
            )

        for prayer_name, _api_key, pref_key in PRAYER_SCHEDULE:
            schema_dict[
                vol.Optional(
                    pref_key,
                    default=self.config_entry.options.get(pref_key, PREF_PREFERRED),
                )
            ] = selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=pref_options,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key=f"{prayer_name.lower()}_preference",
                ),
            )

        # Device tracker for fallback reminders
        device_tracker_val = self.config_entry.options.get(CONF_DEVICE_TRACKER)
        device_tracker_marker = (
            vol.Optional(CONF_DEVICE_TRACKER, default=device_tracker_val)
            if device_tracker_val
            else vol.Optional(CONF_DEVICE_TRACKER)
        )
        schema_dict[device_tracker_marker] = selector.EntitySelector(
            selector.EntitySelectorConfig(domain="device_tracker"),
        )

        # TTS pronunciations for prayer names
        for prayer_name, _api_key, _pref_key in PRAYER_SCHEDULE:
            tts_key = f"tts_{prayer_name.lower()}"
            schema_dict[
                vol.Optional(
                    tts_key,
                    default=self.config_entry.options.get(
                        tts_key, DEFAULT_TTS_PRAYERS[prayer_name]
                    ),
                )
            ] = selector.TextSelector()

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema_dict),
        )
