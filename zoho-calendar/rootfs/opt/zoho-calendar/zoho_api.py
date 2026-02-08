"""
Zoho Creator API Client

Gestisce l'autenticazione OAuth2 e le operazioni CRUD
sul report CalendarioPianificazione di Zoho Creator.
"""

import json
import logging
import os
import time
from datetime import date, datetime

import requests

logger = logging.getLogger(__name__)

TOKEN_CACHE_FILE = "/config/zoho_tokens.json"


class ZohoAPIError(Exception):
    """Errore API Zoho"""
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class ZohoAPI:
    def __init__(self, config=None):
        """Inizializza con config dict o env vars come fallback."""
        config = config or {}
        self.dc = config.get("dc") or os.environ.get("ZOHO_DC", "eu")
        self.client_id = config.get("client_id") or os.environ.get("ZOHO_CLIENT_ID", "")
        self.client_secret = config.get("client_secret") or os.environ.get("ZOHO_CLIENT_SECRET", "")
        self.refresh_token = config.get("refresh_token") or os.environ.get("ZOHO_REFRESH_TOKEN", "")
        self.owner = config.get("owner") or os.environ.get("ZOHO_OWNER", "emironet")
        self.app = config.get("app") or os.environ.get("ZOHO_APP", "service-management")
        self.form = config.get("form") or os.environ.get("ZOHO_FORM", "Pianificazione")
        self.report = config.get("report") or os.environ.get("ZOHO_REPORT", "CalendarioPianificazione")

        self._access_token = None
        self._token_expires_at = 0

        self._load_cached_token()

    def reconfigure(self, config):
        """Aggiorna credenziali senza riavvio."""
        self.dc = config.get("dc", self.dc)
        self.client_id = config.get("client_id", self.client_id)
        self.client_secret = config.get("client_secret", self.client_secret)
        self.refresh_token = config.get("refresh_token", self.refresh_token)
        self.owner = config.get("owner", self.owner)
        self.app = config.get("app", self.app)
        self.form = config.get("form", self.form)
        self.report = config.get("report", self.report)
        # Invalida token corrente per forzare rigenerazione
        self._access_token = None
        self._token_expires_at = 0
        logger.info("ZohoAPI riconfigurato")

    @property
    def _base_url(self):
        return f"https://creator.zoho.{self.dc}/api/v2.1/{self.owner}/{self.app}"

    @property
    def _accounts_url(self):
        return f"https://accounts.zoho.{self.dc}/oauth/v2/token"

    # ------------------------------------------------------------------
    # Token management
    # ------------------------------------------------------------------

    def _load_cached_token(self):
        """Carica token dalla cache su disco."""
        if not os.path.exists(TOKEN_CACHE_FILE):
            return
        try:
            with open(TOKEN_CACHE_FILE, "r") as f:
                data = json.load(f)
            if time.time() < data.get("expires_at", 0):
                self._access_token = data["access_token"]
                self._token_expires_at = data["expires_at"]
                logger.info("Token caricato dalla cache")
        except (json.JSONDecodeError, KeyError):
            pass

    def _save_cached_token(self):
        """Salva token nella cache su disco."""
        try:
            os.makedirs(os.path.dirname(TOKEN_CACHE_FILE), exist_ok=True)
            with open(TOKEN_CACHE_FILE, "w") as f:
                json.dump({
                    "access_token": self._access_token,
                    "expires_at": self._token_expires_at,
                }, f, indent=2)
        except OSError as e:
            logger.warning("Impossibile salvare cache token: %s", e)

    def get_access_token(self):
        """Ottiene un access token valido, rigenerandolo se necessario."""
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        if not self.refresh_token:
            raise ZohoAPIError("Refresh token non configurato")

        logger.info("Rigenerazione access token...")
        try:
            resp = requests.post(self._accounts_url, data={
                "grant_type": "refresh_token",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
            }, timeout=30)

            if resp.status_code >= 400:
                error_data = resp.json() if resp.text else {}
                error_msg = error_data.get("error", resp.text)
                raise ZohoAPIError(
                    f"Errore refresh token: {error_msg}",
                    status_code=resp.status_code,
                )

            data = resp.json()
            self._access_token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            self._token_expires_at = int(time.time()) + expires_in - 60
            self._save_cached_token()
            logger.info("Access token ottenuto (scade in %ds)", expires_in)
            return self._access_token

        except requests.RequestException as e:
            raise ZohoAPIError(f"Errore di rete: {e}")

    def _headers(self):
        token = self.get_access_token()
        return {
            "Authorization": f"Zoho-oauthtoken {token}",
            "Accept": "application/json",
        }

    # ------------------------------------------------------------------
    # OAuth code exchange
    # ------------------------------------------------------------------

    def exchange_code(self, code, redirect_uri=None):
        """Scambia il codice di autorizzazione per un refresh token.

        Chiama accounts.zoho.eu/oauth/v2/token con grant_type=authorization_code
        e restituisce il refresh_token.
        """
        if not redirect_uri:
            redirect_uri = os.environ.get("ZOHO_REDIRECT_URI", "http://localhost:3000/auth/callback")
        logger.info("Scambio codice autorizzazione...")
        try:
            resp = requests.post(self._accounts_url, data={
                "grant_type": "authorization_code",
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            }, timeout=30)

            if resp.status_code >= 400:
                error_data = resp.json() if resp.text else {}
                error_msg = error_data.get("error", resp.text)
                raise ZohoAPIError(
                    f"Errore scambio codice: {error_msg}",
                    status_code=resp.status_code,
                )

            data = resp.json()
            if "error" in data:
                raise ZohoAPIError(f"Errore Zoho: {data['error']}")

            refresh_token = data.get("refresh_token")
            if not refresh_token:
                raise ZohoAPIError("Refresh token non presente nella risposta")

            # Salva anche l'access token ricevuto
            self._access_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            self._token_expires_at = int(time.time()) + expires_in - 60
            self._save_cached_token()

            self.refresh_token = refresh_token
            logger.info("Codice scambiato con successo, refresh token ottenuto")
            return refresh_token

        except requests.RequestException as e:
            raise ZohoAPIError(f"Errore di rete: {e}")

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_events_by_date(self, target_date=None):
        """Legge eventi dal report CalendarioPianificazione per una data."""
        if target_date is None:
            target_date = date.today()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

        date_str = target_date.strftime("%Y-%m-%d")
        url = f"{self._base_url}/report/{self.report}"
        params = {
            "criteria": f'(Data=="{date_str}")',
            "from": 1,
            "limit": 200,
        }

        logger.info("Caricamento eventi per %s...", date_str)
        try:
            resp = requests.get(url, headers=self._headers(),
                                params=params, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                events = data.get("data", [])
                logger.info("Trovati %d eventi per %s", len(events), date_str)
                return events
            elif resp.status_code == 204:
                logger.info("Nessun evento per %s", date_str)
                return []
            else:
                raise ZohoAPIError(
                    f"Errore lettura report: {resp.status_code} {resp.text}",
                    status_code=resp.status_code,
                )
        except requests.RequestException as e:
            raise ZohoAPIError(f"Errore di rete: {e}")

    def get_today_events(self):
        """Scorciatoia per eventi di oggi."""
        return self.get_events_by_date(date.today())

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create_event(self, data):
        """Crea un nuovo evento nel form Pianificazione."""
        url = f"{self._base_url}/form/{self.form}"
        payload = {"data": data}

        logger.info("Creazione evento: %s", data.get("Titolo", "?"))
        try:
            resp = requests.post(url, headers=self._headers(),
                                 json=payload, timeout=15)
            if resp.status_code in (200, 201):
                result = resp.json()
                logger.info("Evento creato: %s", result)
                return result
            else:
                raise ZohoAPIError(
                    f"Errore creazione evento: {resp.status_code} {resp.text}",
                    status_code=resp.status_code,
                )
        except requests.RequestException as e:
            raise ZohoAPIError(f"Errore di rete: {e}")

    def update_event(self, record_id, data):
        """Aggiorna un evento esistente."""
        url = f"{self._base_url}/report/{self.report}/{record_id}"
        payload = {"data": data}

        logger.info("Aggiornamento evento %s", record_id)
        try:
            resp = requests.patch(url, headers=self._headers(),
                                  json=payload, timeout=15)
            if resp.status_code == 200:
                result = resp.json()
                logger.info("Evento aggiornato: %s", result)
                return result
            else:
                raise ZohoAPIError(
                    f"Errore aggiornamento: {resp.status_code} {resp.text}",
                    status_code=resp.status_code,
                )
        except requests.RequestException as e:
            raise ZohoAPIError(f"Errore di rete: {e}")

    def delete_event(self, record_id):
        """Elimina un evento."""
        url = f"{self._base_url}/report/{self.report}/{record_id}"

        logger.info("Eliminazione evento %s", record_id)
        try:
            resp = requests.delete(url, headers=self._headers(), timeout=15)
            if resp.status_code == 200:
                result = resp.json()
                logger.info("Evento eliminato: %s", result)
                return result
            else:
                raise ZohoAPIError(
                    f"Errore eliminazione: {resp.status_code} {resp.text}",
                    status_code=resp.status_code,
                )
        except requests.RequestException as e:
            raise ZohoAPIError(f"Errore di rete: {e}")
