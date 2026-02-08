from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, SENSOR_PLATFORM, CONF_BASE_URL, CONF_USE_ADDON_INTERVAL, CONF_UPDATE_INTERVAL
from .coordinator import ZohoCalendarCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    base_url = entry.data.get(CONF_BASE_URL)
    use_addon_interval = entry.options.get(CONF_USE_ADDON_INTERVAL, True)
    interval = entry.options.get(CONF_UPDATE_INTERVAL, 60)

    coordinator = ZohoCalendarCoordinator(hass, base_url, use_addon_interval, interval)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, [SENSOR_PLATFORM])
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, [SENSOR_PLATFORM])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
