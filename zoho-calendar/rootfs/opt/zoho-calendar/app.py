"""
Flask Application - Zoho Calendar Add-on per Home Assistant

Fornisce:
- Dashboard web (ingress) per il calendario
- Pagina di setup/configurazione dalla web UI
- API REST per operazioni CRUD sugli eventi
- API per configurazione e OAuth
- Thread scheduler per polling periodico e aggiornamento MQTT
"""

import logging
import os
import sys
import threading

from flask import Flask, jsonify, render_template, request

from calendar_manager import CalendarManager
from config_manager import ConfigManager
from zoho_api import ZohoAPI, ZohoAPIError

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger("zoho-calendar")

app = Flask(__name__)

# Ingress base path
INGRESS_ENTRY = os.environ.get("INGRESS_ENTRY", "")

# Config manager (singleton)
config_mgr = ConfigManager()

# Calendar manager (singleton)
manager = CalendarManager()


# ======================================================================
# Ingress: dashboard HTML
# ======================================================================

@app.route("/")
def index():
    return render_template("index.html", ingress_entry=INGRESS_ENTRY)


# ======================================================================
# API Configurazione
# ======================================================================

@app.route("/api/config/status")
def api_config_status():
    """Restituisce se l'add-on e' configurato o no."""
    return jsonify({
        "configured": config_mgr.is_configured(),
    })


@app.route("/api/config")
def api_config_get():
    """Restituisce config corrente (senza segreti completi)."""
    return jsonify(config_mgr.get_safe_config())


@app.route("/api/config", methods=["POST"])
def api_config_save():
    """Salva configurazione."""
    body = request.get_json(force=True)
    try:
        # Aggiorna solo i campi forniti
        allowed_keys = [
            "zoho_dc", "zoho_client_id", "zoho_client_secret",
            "zoho_owner", "zoho_app", "zoho_form", "zoho_report",
            "technicians", "tipologia", "ore_pianificate",
            "reparto", "attivita_interna_id",
        ]
        updates = {k: v for k, v in body.items() if k in allowed_keys}
        config_mgr.update(updates)

        # Riconfigura il calendar manager
        manager.reconfigure()

        return jsonify({"ok": True})
    except Exception as e:
        logger.exception("Errore salvataggio configurazione")
        return jsonify({"error": str(e)}), 500


@app.route("/api/auth/url")
def api_auth_url():
    """Restituisce URL di consenso Zoho per aprire in nuova tab."""
    client_id = request.args.get("client_id") or config_mgr.get("zoho_client_id", "")
    dc = request.args.get("dc") or config_mgr.get("zoho_dc", "eu")
    redirect_uri = os.environ.get("ZOHO_REDIRECT_URI", "http://localhost:3000/auth/callback")

    if not client_id:
        return jsonify({"error": "Client ID non configurato"}), 400

    scope = "ZohoCreator.report.READ,ZohoCreator.report.CREATE,ZohoCreator.report.UPDATE,ZohoCreator.report.DELETE,ZohoCreator.form.CREATE"
    auth_url = (
        f"https://accounts.zoho.{dc}/oauth/v2/auth"
        f"?scope={scope}"
        f"&client_id={client_id}"
        f"&response_type=code"
        f"&access_type=offline"
        f"&redirect_uri={redirect_uri}"
        f"&prompt=consent"
    )
    return jsonify({"url": auth_url})


@app.route("/api/auth/exchange", methods=["POST"])
def api_auth_exchange():
    """Riceve codice autorizzazione, lo scambia per refresh_token."""
    body = request.get_json(force=True)
    code = body.get("code", "").strip()
    if not code:
        return jsonify({"error": "Codice autorizzazione mancante"}), 400

    client_id = config_mgr.get("zoho_client_id", "")
    client_secret = config_mgr.get("zoho_client_secret", "")
    dc = config_mgr.get("zoho_dc", "eu")

    if not client_id or not client_secret:
        return jsonify({"error": "Client ID e Client Secret devono essere salvati prima"}), 400

    try:
        zoho = ZohoAPI(config={
            "dc": dc,
            "client_id": client_id,
            "client_secret": client_secret,
        })
        redirect_uri = os.environ.get("ZOHO_REDIRECT_URI", "http://localhost:3000/auth/callback")
        refresh_token = zoho.exchange_code(code, redirect_uri=redirect_uri)

        # Salva il refresh token nella config
        config_mgr.set("zoho_refresh_token", refresh_token)

        # Riconfigura il calendar manager
        manager.reconfigure()

        return jsonify({"ok": True, "message": "Refresh token ottenuto e salvato"})
    except ZohoAPIError as e:
        logger.error("Errore scambio codice: %s", e)
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.exception("Errore imprevisto scambio codice")
        return jsonify({"error": str(e)}), 500


# ======================================================================
# API REST Eventi
# ======================================================================

@app.route("/api/events")
def api_events_today():
    """Lista eventi di oggi."""
    if not config_mgr.is_configured():
        return jsonify({"data": [], "last_sync": None, "configured": False})
    events = manager.get_events()
    return jsonify({"data": events, "last_sync": manager.last_sync})


@app.route("/api/events/<date_str>")
def api_events_by_date(date_str):
    """Eventi per una data specifica (YYYY-MM-DD)."""
    if not config_mgr.is_configured():
        return jsonify({"data": [], "configured": False})
    events = manager.get_events(date_str)
    return jsonify({"data": events})


@app.route("/api/events", methods=["POST"])
def api_create_event():
    """Crea un nuovo evento."""
    body = request.get_json(force=True)
    required = ["titolo", "tecnico_id", "data", "ora_inizio", "ora_fine"]
    missing = [f for f in required if f not in body]
    if missing:
        return jsonify({"error": f"Campi mancanti: {', '.join(missing)}"}), 400

    try:
        result = manager.create_event(
            titolo=body["titolo"],
            tecnico_id=body["tecnico_id"],
            data_str=body["data"],
            ora_inizio=body["ora_inizio"],
            ora_fine=body["ora_fine"],
            descrizione=body.get("descrizione", ""),
        )
        return jsonify({"ok": True, "result": result})
    except Exception as e:
        logger.exception("Errore creazione evento")
        return jsonify({"error": str(e)}), 500


@app.route("/api/events/<record_id>", methods=["PUT"])
def api_update_event(record_id):
    """Aggiorna un evento esistente."""
    body = request.get_json(force=True)
    try:
        result = manager.update_event(record_id, body)
        return jsonify({"ok": True, "result": result})
    except Exception as e:
        logger.exception("Errore aggiornamento evento")
        return jsonify({"error": str(e)}), 500


@app.route("/api/events/<record_id>", methods=["DELETE"])
def api_delete_event(record_id):
    """Elimina un evento."""
    try:
        result = manager.delete_event(record_id)
        return jsonify({"ok": True, "result": result})
    except Exception as e:
        logger.exception("Errore eliminazione evento")
        return jsonify({"error": str(e)}), 500


@app.route("/api/technicians")
def api_technicians():
    """Lista tecnici con stato corrente."""
    techs = manager.get_technicians_status()
    return jsonify({"data": techs})


@app.route("/api/sync", methods=["POST"])
def api_sync():
    """Forza sincronizzazione manuale."""
    if not config_mgr.is_configured():
        return jsonify({"error": "Add-on non configurato"}), 400
    manager.sync_calendar()
    return jsonify({"ok": True, "last_sync": manager.last_sync})


@app.route("/api/health")
def api_health():
    """Health check."""
    return jsonify({
        "status": "ok",
        "configured": config_mgr.is_configured(),
        "last_sync": manager.last_sync,
    })


# ======================================================================
# Startup
# ======================================================================

def main():
    port = int(os.environ.get("INGRESS_PORT", "8099"))

    # Avvia calendar manager in background
    bg = threading.Thread(target=manager.start, daemon=True, name="calendar-mgr")
    bg.start()

    logger.info("Avvio server Flask su porta %d", port)
    app.run(host="0.0.0.0", port=port, debug=False)


if __name__ == "__main__":
    main()
