from __future__ import annotations

from datetime import datetime, date
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import ZohoCalendarCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator: ZohoCalendarCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []

    # General sensors
    entities.append(ZohoGeneralSensor(coordinator, "totale_eventi_oggi", "Eventi Oggi", "events_total"))
    entities.append(ZohoGeneralSensor(coordinator, "ultimo_sync", "Ultimo Sync", "last_sync", icon="mdi:clock-outline"))

    # Technician sensors
    for tech in coordinator.data.get("technicians", []):
        name = tech.get("name", "Sconosciuto")
        entities.append(ZohoTechnicianSensor(coordinator, name, "stato", "Stato", "status"))
        entities.append(ZohoTechnicianSensor(coordinator, name, "eventi_oggi", "Eventi Oggi", "events_count"))
        entities.append(ZohoTechnicianSensor(coordinator, name, "prossimo_evento", "Prossimo Evento", "next_title"))
        entities.append(ZohoTechnicianSensor(coordinator, name, "orario_prossimo", "Orario Prossimo", "next_time"))

    async_add_entities(entities)


class ZohoBaseSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: ZohoCalendarCoordinator, name: str, unique_id: str):
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = unique_id


class ZohoGeneralSensor(ZohoBaseSensor):
    def __init__(self, coordinator: ZohoCalendarCoordinator, suffix: str, label: str, key: str, icon=None):
        super().__init__(coordinator, f"Zoho {label}", f"zoho_calendar_{suffix}")
        self._key = key
        if icon:
            self._attr_icon = icon
        self._attr_entity_category = EntityCategory.DIAGNOSTIC if key == "last_sync" else None

    @property
    def native_value(self):
        data = self.coordinator.data or {}
        if self._key == "events_total":
            return len(data.get("events", []))
        if self._key == "last_sync":
            return data.get("last_sync")
        return None


class ZohoTechnicianSensor(ZohoBaseSensor):
    def __init__(self, coordinator: ZohoCalendarCoordinator, tech_name: str, suffix: str, label: str, key: str):
        name = f"Zoho {tech_name} {label}"
        uid = f"zoho_calendar_{tech_name}_{suffix}".lower().replace(" ", "_")
        super().__init__(coordinator, name, uid)
        self._tech_name = tech_name
        self._key = key

    @property
    def native_value(self):
        tech = self._find_tech()
        if not tech:
            return None
        if self._key == "status":
            return tech.get("status")
        if self._key == "events_count":
            return tech.get("events_count")
        if self._key in ("next_title", "next_time"):
            next_ev = _find_next_event(self.coordinator.data.get("events", []), self._tech_name)
            if not next_ev:
                return None
            if self._key == "next_title":
                return next_ev.get("title")
            return next_ev.get("start_time")
        return None

    def _find_tech(self):
        data = self.coordinator.data or {}
        for tech in data.get("technicians", []):
            if tech.get("name") == self._tech_name:
                return tech
        return None


def _find_next_event(events, tech_name: str):
    if not events:
        return None
    now = dt_util.now()
    today_str = date.today().isoformat()
    candidates = []
    for ev in events:
        if ev.get("technician") != tech_name:
            continue
        if ev.get("date") != today_str:
            continue
        start = _parse_time(ev.get("start_time"), now)
        if start and start >= now:
            candidates.append((start, ev))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def _parse_time(time_str, ref):
    if not time_str:
        return None
    try:
        parts = time_str.split(":")
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        return ref.replace(hour=hour, minute=minute, second=0, microsecond=0)
    except (ValueError, IndexError):
        return None
