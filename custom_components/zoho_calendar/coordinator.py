from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ZohoCalendarApi
from .const import DEFAULT_UPDATE_INTERVAL

_LOGGER = logging.getLogger(__name__)


class ZohoCalendarCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, base_url: str, use_addon_interval: bool, interval: int) -> None:
        self.hass = hass
        self.base_url = base_url
        self.use_addon_interval = use_addon_interval
        self.interval = interval
        self.api = ZohoCalendarApi(async_get_clientsession(hass), base_url)
        super().__init__(
            hass,
            _LOGGER,
            name="zoho_calendar",
            update_interval=timedelta(seconds=interval or DEFAULT_UPDATE_INTERVAL),
        )

    async def _async_update_data(self) -> dict:
        try:
            status = await self.api.get_config_status()
            if self.use_addon_interval:
                addon_interval = int(status.get("update_interval", self.interval or DEFAULT_UPDATE_INTERVAL))
                if addon_interval > 0 and addon_interval != self.update_interval.total_seconds():
                    self.update_interval = timedelta(seconds=addon_interval)

            technicians = await self.api.get_technicians()
            events = await self.api.get_events_today()
            return {
                "status": status,
                "technicians": technicians.get("data", []),
                "events": events.get("data", []),
                "last_sync": events.get("last_sync"),
            }
        except Exception as err:
            raise UpdateFailed(str(err)) from err
