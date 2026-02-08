"""
Calendar Manager

Orchestrazione tra Zoho API e MQTT Manager.
Gestisce il polling periodico e le operazioni sul calendario.
"""

import logging
import os
import threading
import time
from datetime import date, datetime

import schedule

from config_manager import ConfigManager
from zoho_api import ZohoAPI, ZohoAPIError
from mqtt_manager import MQTTManager

logger = logging.getLogger(__name__)

# Utenti esclusi dal calendario
EXCLUDED_USERS = ["Nicola Grassi", "Francesco Brunelli"]


class CalendarManager:
    def __init__(self):
        self.config_manager = ConfigManager()

        # Inizializza Zoho API con config (se disponibile)
        zoho_config = self.config_manager.get_zoho_config()
        self.zoho = ZohoAPI(config=zoho_config)

        # Carica lista tecnici dal config_manager
        self.technicians = self.config_manager.get_technicians()

        self.mqtt = MQTTManager(technicians=self.technicians)
        self.update_interval = int(os.environ.get("UPDATE_INTERVAL", "60"))

        # Cache eventi correnti
        self._events = []
        self._events_by_tech = {}
        self._last_sync = None
        self._scheduler_thread = None
        self._running = False

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def start(self):
        """Avvia il manager: connette MQTT e avvia lo scheduler."""
        if not self.config_manager.is_configured():
            logger.warning("Add-on non configurato, in attesa di configurazione dalla web UI...")
            # Avvia comunque lo scheduler che controllera' periodicamente
            self._start_scheduler()
            return

        self.mqtt.connect()
        self.sync_calendar()
        self._start_scheduler()

    def stop(self):
        """Ferma lo scheduler e disconnette MQTT."""
        self._running = False
        schedule.clear()
        self.mqtt.disconnect()

    def reconfigure(self):
        """Ricarica la configurazione e riapplica senza riavvio."""
        self.config_manager.load()

        # Aggiorna Zoho API
        zoho_config = self.config_manager.get_zoho_config()
        self.zoho.reconfigure(zoho_config)

        # Aggiorna tecnici
        self.technicians = self.config_manager.get_technicians()
        self.mqtt.technicians = self.technicians

        # Connetti MQTT se non gia' connesso
        if not self.mqtt._connected:
            self.mqtt.connect()

        # Forza sync
        if self.config_manager.is_configured():
            self.sync_calendar()

        logger.info("CalendarManager riconfigurato")

    def _start_scheduler(self):
        """Avvia il thread scheduler per il polling periodico."""
        self._running = True

        schedule.every(self.update_interval).seconds.do(self._scheduled_sync)

        def _run():
            while self._running:
                schedule.run_pending()
                time.sleep(1)

        self._scheduler_thread = threading.Thread(
            target=_run, daemon=True, name="calendar-scheduler"
        )
        self._scheduler_thread.start()
        logger.info(
            "Scheduler avviato (intervallo: %ds)", self.update_interval
        )

    def _scheduled_sync(self):
        """Sync schedulata: esegue solo se configurato."""
        if self.config_manager.is_configured():
            self.sync_calendar()

    # ------------------------------------------------------------------
    # Sync
    # ------------------------------------------------------------------

    def sync_calendar(self):
        """Polling: legge eventi da Zoho e aggiorna sensori MQTT."""
        if not self.config_manager.is_configured():
            logger.debug("Skip sync: non configurato")
            return

        logger.info("Sincronizzazione calendario...")
        try:
            raw_events = self.zoho.get_today_events()

            # Filtra utenti esclusi
            events = [
                e for e in raw_events
                if e.get("LkpTecnico", {}).get("Nominativo", "")
                not in EXCLUDED_USERS
            ]

            self._events = events
            self._last_sync = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # Raggruppa per tecnico
            self._events_by_tech = {}
            for ev in events:
                tech_name = ev.get("LkpTecnico", {}).get("Nominativo", "Sconosciuto")
                self._events_by_tech.setdefault(tech_name, []).append(ev)

            # Aggiorna sensori MQTT per ogni tecnico configurato
            for tech in self.technicians:
                name = tech["name"]
                tech_events = self._events_by_tech.get(name, [])
                self.mqtt.update_technician(name, tech_events)

            # Sensori generali
            self.mqtt.update_general(len(events), self._last_sync)

            logger.info(
                "Sync completata: %d eventi, %d tecnici attivi",
                len(events), len(self._events_by_tech),
            )
        except ZohoAPIError as e:
            logger.error("Errore sync Zoho: %s", e)
        except Exception as e:
            logger.exception("Errore sync imprevisto: %s", e)

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def get_events(self, target_date=None):
        """Restituisce eventi per una data (default: oggi, dalla cache)."""
        if target_date is None or target_date == date.today().isoformat():
            return self._transform_events(self._events)
        # Per date diverse, richiedi a Zoho
        try:
            raw = self.zoho.get_events_by_date(target_date)
            filtered = [
                e for e in raw
                if e.get("LkpTecnico", {}).get("Nominativo", "")
                not in EXCLUDED_USERS
            ]
            return self._transform_events(filtered)
        except ZohoAPIError as e:
            logger.error("Errore lettura eventi: %s", e)
            return []

    def get_technicians_status(self):
        """Restituisce lo stato di ogni tecnico configurato."""
        result = []
        for tech in self.technicians:
            name = tech["name"]
            events = self._events_by_tech.get(name, [])
            status = self._get_technician_status(name, events)
            result.append({
                "id": tech.get("id", ""),
                "name": name,
                "status": status,
                "events_count": len(events),
            })
        return result

    @property
    def last_sync(self):
        return self._last_sync

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def create_event(self, titolo, tecnico_id, data_str, ora_inizio,
                     ora_fine, descrizione=""):
        """Crea un nuovo evento su Zoho Creator."""
        defaults = self.config_manager.get_event_defaults()

        tecnico_id = self._resolve_technician_id(tecnico_id)
        if not tecnico_id:
            raise ValueError("ID tecnico mancante: inserisci l'ID del record Zoho per il tecnico")

        event_data = {
            "Titolo": titolo,
            "LkpTecnico": tecnico_id,
            "Data": data_str,
            "DataInizio": ora_inizio,
            "DataFine": ora_fine,
            "DescrizioneAttivita": descrizione,
            "Tipologia": defaults["tipologia"],
            "OrePianificate": defaults["ore_pianificate"],
        }
        if defaults["attivita_interna_id"]:
            event_data["LkpAttivitaInterna"] = defaults["attivita_interna_id"]
        if defaults["reparto"]:
            event_data["Reparto"] = defaults["reparto"]

        result = self.zoho.create_event(event_data)
        # Risincronizza
        self.sync_calendar()
        return result

    def update_event(self, record_id, fields):
        """Aggiorna un evento esistente su Zoho Creator."""
        result = self.zoho.update_event(record_id, fields)
        self.sync_calendar()
        return result

    def delete_event(self, record_id):
        """Elimina un evento su Zoho Creator."""
        result = self.zoho.delete_event(record_id)
        self.sync_calendar()
        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _transform_events(self, raw_events):
        """Trasforma eventi Zoho Creator nel formato API."""
        transformed = []
        for ev in raw_events:
            tech_name = ev.get("LkpTecnico", {}).get("Nominativo", "Sconosciuto")
            transformed.append({
                "id": ev.get("ID", ""),
                "title": ev.get("Titolo", ""),
                "description": ev.get("DescrizioneAttivita", ""),
                "technician": tech_name,
                "date": ev.get("Data", ""),
                "start_time": ev.get("DataInizio", ""),
                "end_time": ev.get("DataFine", ""),
                "type": ev.get("Tipologia", ""),
                "hours": ev.get("OrePianificate", ""),
                "department": ev.get("Reparto", ""),
            })
        return transformed

    def _resolve_technician_id(self, tecnico_id):
        """Risolve l'ID tecnico se e' stato passato il nome."""
        if not tecnico_id:
            return ""
        # Se sembra un ID numerico, usalo direttamente
        if str(tecnico_id).isdigit():
            return tecnico_id
        # Altrimenti prova a mappare da nome -> id
        for tech in self.technicians:
            if tech.get("name") == tecnico_id and tech.get("id"):
                return tech["id"]
        return ""

    @staticmethod
    def _get_technician_status(name, events):
        """Calcola lo stato attuale di un tecnico."""
        if not events:
            return "libero"

        now = datetime.now()
        for ev in events:
            title = ev.get("Titolo", "").lower()
            if "ferie" in title or "permesso" in title:
                return "ferie"
            if "malattia" in title:
                return "malattia"

            start_str = ev.get("DataInizio", "")
            end_str = ev.get("DataFine", "")
            try:
                parts_s = start_str.split(":")
                parts_e = end_str.split(":")
                start = now.replace(
                    hour=int(parts_s[0]), minute=int(parts_s[1]),
                    second=0, microsecond=0,
                )
                end = now.replace(
                    hour=int(parts_e[0]), minute=int(parts_e[1]),
                    second=0, microsecond=0,
                )
                if start <= now <= end:
                    return "occupato"
            except (ValueError, IndexError):
                pass

        return "libero"
