from __future__ import annotations

import asyncio
import logging

from aiohttp import ClientError

_LOGGER = logging.getLogger(__name__)


class ZohoCalendarApi:
    def __init__(self, session, base_url: str) -> None:
        self._session = session
        self._base_url = base_url.rstrip("/")

    async def get_config_status(self) -> dict:
        return await self._get_json("/api/config/status")

    async def get_technicians(self) -> dict:
        return await self._get_json("/api/technicians")

    async def get_events_today(self) -> dict:
        return await self._get_json("/api/events")

    async def _get_json(self, path: str) -> dict:
        url = f"{self._base_url}{path}"
        try:
            async with self._session.get(url, timeout=30) as resp:
                resp.raise_for_status()
                return await resp.json()
        except (ClientError, asyncio.TimeoutError) as err:
            _LOGGER.error("Errore chiamata API %s: %s", url, err)
            raise
