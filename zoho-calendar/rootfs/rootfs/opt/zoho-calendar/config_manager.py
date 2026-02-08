"""
Config Manager

Gestione configurazione persistente su /config/zoho_calendar_config.json.
Permette di configurare l'add-on interamente dalla dashboard web.
"""

import json
import logging
import os
import threading

logger = logging.getLogger(__name__)

CONFIG_FILE = "/config/zoho_calendar_config.json"

DEFAULT_TECHNICIANS = [
    {"id": "", "name": "Daniele Ciccarese"},
    {"id": "", "name": "Andrea Scaltriti"},
    {"id": "", "name": "Francesco Rosi"},
    {"id": "", "name": "Hakan Fida"},
    {"id": "", "name": "Kenneth Agapito"},
    {"id": "", "name": "Elia Ferrari"},
    {"id": "", "name": "Antonio Calcagno"},
    {"id": "", "name": "Marco Albertelli"},
    {"id": "", "name": "Luca Marinelli"},
]

DEFAULTS = {
    "zoho_dc": "eu",
    "zoho_client_id": "",
    "zoho_client_secret": "",
    "zoho_refresh_token": "",
    "zoho_owner": "emironet",
    "zoho_app": "service-management",
    "zoho_form": "Pianificazione",
    "zoho_report": "CalendarioPianificazione",
    "technicians": DEFAULT_TECHNICIANS,
    "tipologia": "Altre attivit\u00e0",
    "ore_pianificate": "8",
    "reparto": "",
    "attivita_interna_id": "",
}


class ConfigManager:
    """Gestione configurazione persistente."""

    def __init__(self, config_file=None):
        self._config_file = config_file or CONFIG_FILE
        self._config = {}
        self._lock = threading.Lock()
        self.load()

    def load(self):
        """Carica configurazione da disco."""
        with self._lock:
            if os.path.exists(self._config_file):
                try:
                    with open(self._config_file, "r") as f:
                        self._config = json.load(f)
                    logger.info("Configurazione caricata da %s", self._config_file)
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning("Errore lettura config: %s", e)
                    self._config = {}
            else:
                logger.info("File config non trovato, uso defaults")
                self._config = {}
        return self._config

    def save(self, config=None):
        """Salva configurazione su disco."""
        with self._lock:
            if config is not None:
                self._config = config
            try:
                os.makedirs(os.path.dirname(self._config_file), exist_ok=True)
                with open(self._config_file, "w") as f:
                    json.dump(self._config, f, indent=2, ensure_ascii=False)
                logger.info("Configurazione salvata in %s", self._config_file)
            except OSError as e:
                logger.error("Errore salvataggio config: %s", e)
                raise

    def get(self, key, default=None):
        """Legge un valore dalla config, con fallback ai defaults."""
        with self._lock:
            val = self._config.get(key)
            if val is not None:
                return val
            if default is not None:
                return default
            return DEFAULTS.get(key, None)

    def set(self, key, value):
        """Imposta un valore nella config e salva."""
        with self._lock:
            self._config[key] = value
        self.save()

    def update(self, data):
        """Aggiorna piu' valori nella config e salva."""
        with self._lock:
            self._config.update(data)
        self.save()

    def is_configured(self):
        """Verifica che client_id, client_secret e refresh_token siano presenti."""
        return bool(
            self.get("zoho_client_id")
            and self.get("zoho_client_secret")
            and self.get("zoho_refresh_token")
        )

    def get_technicians(self):
        """Restituisce la lista dei tecnici configurati."""
        return self.get("technicians", DEFAULT_TECHNICIANS)

    def set_technicians(self, technicians):
        """Imposta la lista dei tecnici."""
        self.set("technicians", technicians)

    def get_zoho_config(self):
        """Restituisce la configurazione Zoho completa."""
        return {
            "dc": self.get("zoho_dc", "eu"),
            "client_id": self.get("zoho_client_id", ""),
            "client_secret": self.get("zoho_client_secret", ""),
            "refresh_token": self.get("zoho_refresh_token", ""),
            "owner": self.get("zoho_owner", "emironet"),
            "app": self.get("zoho_app", "service-management"),
            "form": self.get("zoho_form", "Pianificazione"),
            "report": self.get("zoho_report", "CalendarioPianificazione"),
        }

    def get_event_defaults(self):
        """Restituisce i default per la creazione eventi."""
        return {
            "tipologia": self.get("tipologia", "Altre attivit\u00e0"),
            "ore_pianificate": self.get("ore_pianificate", "8"),
            "reparto": self.get("reparto", ""),
            "attivita_interna_id": self.get("attivita_interna_id", ""),
        }

    def get_safe_config(self):
        """Restituisce la config senza segreti completi (per API)."""
        zoho = self.get_zoho_config()
        return {
            "zoho_dc": zoho["dc"],
            "zoho_client_id": self._mask(zoho["client_id"]),
            "zoho_client_secret": self._mask(zoho["client_secret"]),
            "zoho_refresh_token": self._mask(zoho["refresh_token"]),
            "zoho_owner": zoho["owner"],
            "zoho_app": zoho["app"],
            "zoho_form": zoho["form"],
            "zoho_report": zoho["report"],
            "technicians": self.get_technicians(),
            "tipologia": self.get("tipologia", "Altre attivit\u00e0"),
            "ore_pianificate": self.get("ore_pianificate", "8"),
            "reparto": self.get("reparto", ""),
            "attivita_interna_id": self.get("attivita_interna_id", ""),
            "configured": self.is_configured(),
        }

    @staticmethod
    def _mask(value):
        """Maschera un valore segreto mostrando solo gli ultimi 4 caratteri."""
        if not value or len(value) <= 4:
            return "*" * len(value) if value else ""
        return "*" * (len(value) - 4) + value[-4:]
