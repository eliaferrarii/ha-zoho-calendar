"""
MQTT Manager per Home Assistant

Pubblica sensori via MQTT Discovery per ogni tecnico e sensori generali.
"""

import json
import logging
import os
import re
import time
from datetime import datetime

import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)


def _slugify(text):
    """Converte un nome in slug HA-compatibile."""
    text = text.lower().strip()
    text = re.sub(r"[àáâãä]", "a", text)
    text = re.sub(r"[èéêë]", "e", text)
    text = re.sub(r"[ìíîï]", "i", text)
    text = re.sub(r"[òóôõö]", "o", text)
    text = re.sub(r"[ùúûü]", "u", text)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_")


class MQTTManager:
    def __init__(self, technicians=None):
        self.host = os.environ.get("MQTT_HOST", "")
        self.port = int(os.environ.get("MQTT_PORT", "1883"))
        self.user = os.environ.get("MQTT_USER", "")
        self.password = os.environ.get("MQTT_PASS", "")
        self.prefix = os.environ.get("MQTT_TOPIC_PREFIX", "zoho_calendar")
        self.technicians = technicians or []

        self._client = None
        self._connected = False

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect(self):
        if not self.host:
            logger.warning("MQTT host non configurato, skip connessione")
            return False

        self._client = mqtt.Client(client_id="zoho_calendar_addon")
        if self.user:
            self._client.username_pw_set(self.user, self.password)

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect

        try:
            logger.info("Connessione MQTT a %s:%s...", self.host, self.port)
            self._client.connect(self.host, self.port, keepalive=60)
            self._client.loop_start()
            # Attendi connessione
            for _ in range(50):
                if self._connected:
                    break
                time.sleep(0.1)
            return self._connected
        except Exception as e:
            logger.error("Errore connessione MQTT: %s", e)
            return False

    def disconnect(self):
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connesso al broker MQTT")
            self._connected = True
            self._publish_discovery()
        else:
            logger.error("Connessione MQTT fallita (rc=%d)", rc)

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc != 0:
            logger.warning("Disconnessione MQTT inattesa (rc=%d)", rc)

    # ------------------------------------------------------------------
    # MQTT Discovery
    # ------------------------------------------------------------------

    def _publish_discovery(self):
        """Pubblica configurazioni MQTT Discovery per tutti i sensori."""
        device_info = {
            "identifiers": ["zoho_calendar"],
            "name": "Zoho Calendario",
            "manufacturer": "Zoho",
            "model": "Service Management",
        }

        # Sensori per ogni tecnico
        for tech in self.technicians:
            slug = _slugify(tech["name"])
            name = tech["name"]

            sensors = [
                {
                    "suffix": "prossimo_evento",
                    "label": f"{name} - Prossimo Evento",
                    "unique_id": f"zoho_cal_{slug}_next",
                    "icon": "mdi:calendar-clock",
                },
                {
                    "suffix": "eventi_oggi",
                    "label": f"{name} - Eventi Oggi",
                    "unique_id": f"zoho_cal_{slug}_count",
                    "icon": "mdi:counter",
                },
                {
                    "suffix": "stato",
                    "label": f"{name} - Stato",
                    "unique_id": f"zoho_cal_{slug}_status",
                    "icon": "mdi:account-clock",
                },
                {
                    "suffix": "orario_prossimo",
                    "label": f"{name} - Orario Prossimo",
                    "unique_id": f"zoho_cal_{slug}_next_time",
                    "icon": "mdi:clock-outline",
                },
            ]

            for sensor in sensors:
                config_topic = (
                    f"homeassistant/sensor/{self.prefix}/"
                    f"{slug}_{sensor['suffix']}/config"
                )
                state_topic = (
                    f"{self.prefix}/{slug}/{sensor['suffix']}"
                )
                payload = {
                    "name": sensor["label"],
                    "unique_id": sensor["unique_id"],
                    "state_topic": state_topic,
                    "json_attributes_topic": f"{state_topic}/attributes",
                    "icon": sensor["icon"],
                    "device": device_info,
                }
                self._publish(config_topic, payload, retain=True)

        # Sensori generali
        general_sensors = [
            {
                "suffix": "eventi_totali_oggi",
                "label": "Zoho - Eventi Totali Oggi",
                "unique_id": "zoho_cal_total_today",
                "icon": "mdi:calendar-multiple",
            },
            {
                "suffix": "ultimo_aggiornamento",
                "label": "Zoho - Ultimo Aggiornamento",
                "unique_id": "zoho_cal_last_update",
                "icon": "mdi:update",
            },
        ]

        for sensor in general_sensors:
            config_topic = (
                f"homeassistant/sensor/{self.prefix}/"
                f"{sensor['suffix']}/config"
            )
            state_topic = f"{self.prefix}/{sensor['suffix']}"
            payload = {
                "name": sensor["label"],
                "unique_id": sensor["unique_id"],
                "state_topic": state_topic,
                "json_attributes_topic": f"{state_topic}/attributes",
                "icon": sensor["icon"],
                "device": device_info,
            }
            self._publish(config_topic, payload, retain=True)

        logger.info(
            "Discovery MQTT pubblicata per %d tecnici + %d sensori generali",
            len(self.technicians), len(general_sensors),
        )

    # ------------------------------------------------------------------
    # State updates
    # ------------------------------------------------------------------

    def update_technician(self, tech_name, events):
        """Aggiorna i sensori di un tecnico con i suoi eventi del giorno."""
        slug = _slugify(tech_name)
        now = datetime.now()

        # Trova prossimo evento
        future_events = [
            e for e in events
            if self._parse_time(e.get("DataFine", "")) > now
        ]
        future_events.sort(key=lambda e: self._parse_time(e.get("DataInizio", "")))

        next_event = future_events[0] if future_events else None

        # Stato attuale
        current_events = [
            e for e in events
            if (self._parse_time(e.get("DataInizio", "")) <= now
                <= self._parse_time(e.get("DataFine", "")))
        ]

        if current_events:
            stato = self._get_status_from_title(
                current_events[0].get("Titolo", "")
            )
        elif not events:
            stato = "libero"
        else:
            stato = "libero"

        # Prossimo evento
        next_title = next_event.get("Titolo", "Nessuno") if next_event else "Nessuno"
        self._publish(
            f"{self.prefix}/{slug}/prossimo_evento",
            next_title,
        )
        if next_event:
            self._publish(
                f"{self.prefix}/{slug}/prossimo_evento/attributes",
                {
                    "descrizione": next_event.get("DescrizioneAttivita", ""),
                    "ora_inizio": next_event.get("DataInizio", ""),
                    "ora_fine": next_event.get("DataFine", ""),
                    "tipologia": next_event.get("Tipologia", ""),
                },
            )
        else:
            self._publish(
                f"{self.prefix}/{slug}/prossimo_evento/attributes", {},
            )

        # Conteggio eventi oggi
        self._publish(
            f"{self.prefix}/{slug}/eventi_oggi",
            str(len(events)),
        )
        self._publish(
            f"{self.prefix}/{slug}/eventi_oggi/attributes",
            {
                "eventi": [
                    {
                        "titolo": e.get("Titolo", ""),
                        "inizio": e.get("DataInizio", ""),
                        "fine": e.get("DataFine", ""),
                    }
                    for e in events
                ],
            },
        )

        # Stato
        self._publish(f"{self.prefix}/{slug}/stato", stato)
        self._publish(
            f"{self.prefix}/{slug}/stato/attributes",
            {"attivita_corrente": current_events[0].get("Titolo", "") if current_events else ""},
        )

        # Orario prossimo
        next_time = next_event.get("DataInizio", "N/A") if next_event else "N/A"
        self._publish(f"{self.prefix}/{slug}/orario_prossimo", next_time)

    def update_general(self, total_events, last_update=None):
        """Aggiorna i sensori generali."""
        self._publish(
            f"{self.prefix}/eventi_totali_oggi",
            str(total_events),
        )
        ts = last_update or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self._publish(
            f"{self.prefix}/ultimo_aggiornamento",
            ts,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _publish(self, topic, payload, retain=False):
        if not self._client or not self._connected:
            return
        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload)
        self._client.publish(topic, payload, retain=retain)

    @staticmethod
    def _parse_time(time_str):
        """Converte orario HH:MM o HH:MM:SS in datetime di oggi."""
        if not time_str:
            return datetime.min
        try:
            parts = time_str.split(":")
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 0
            now = datetime.now()
            return now.replace(hour=h, minute=m, second=0, microsecond=0)
        except (ValueError, IndexError):
            return datetime.min

    @staticmethod
    def _get_status_from_title(title):
        title_lower = title.lower()
        if "ferie" in title_lower or "permesso" in title_lower:
            return "ferie"
        if "malattia" in title_lower:
            return "malattia"
        if "reperibilità" in title_lower:
            return "reperibilita"
        return "occupato"
