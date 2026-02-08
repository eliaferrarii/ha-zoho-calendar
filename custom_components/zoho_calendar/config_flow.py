from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries

from .const import DOMAIN, CONF_BASE_URL, DEFAULT_BASE_URL, CONF_USE_ADDON_INTERVAL, CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL


class ZohoCalendarConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="Zoho Calendar Add-on", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_BASE_URL, default=DEFAULT_BASE_URL): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_import(self, user_input):
        return await self.async_step_user(user_input)


class ZohoCalendarOptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema({
            vol.Required(CONF_USE_ADDON_INTERVAL, default=self.entry.options.get(CONF_USE_ADDON_INTERVAL, True)): bool,
            vol.Required(CONF_UPDATE_INTERVAL, default=self.entry.options.get(CONF_UPDATE_INTERVAL, DEFAULT_UPDATE_INTERVAL)): int,
        })
        return self.async_show_form(step_id="init", data_schema=schema)


async def async_get_options_flow(config_entry):
    return ZohoCalendarOptionsFlowHandler(config_entry)
