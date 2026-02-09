## Zoho Calendar – Add-on per Home Assistant

Integrazione tra Zoho Creator (Service Management) e Home Assistant per gestire la pianificazione dei tecnici, visualizzare eventi e creare o modificare attività direttamente da Home Assistant.

## Cosa fa l’add-on

- Legge le attività pianificate dal report CalendarioPianificazione di Zoho Creator  
- Crea sensori MQTT per ogni tecnico (stato, eventi, prossimo intervento)  
- Espone una dashboard web integrata in Home Assistant (Ingress) con timeline giornaliera  
- Permette di creare, modificare ed eliminare eventi tramite API REST  
- Sincronizza automaticamente a intervalli configurabili  

## Requisiti

- Account Zoho con accesso a Zoho Creator  
- App Zoho Creator (es. service-management) con form Pianificazione  
- Credenziali OAuth2 Zoho (Client ID, Client Secret, Refresh Token)  
- Broker MQTT configurato in Home Assistant (es. Mosquitto add-on)

## Installazione

1. Vai in Home Assistant → Impostazioni → Add-on → Store  
2. Apri il menu in alto a destra → Repository  
3. Aggiungi:  
   https://github.com/eliaferrarii/ha-zoho-calendar  
4. Installa l’add-on Zoho Calendar  
5. Avvia l’add-on  
6. Apri l’interfaccia web dell’add-on dal pannello laterale

## Configurazione add-on

Le opzioni principali dell’add-on sono:

update_interval  
Intervallo di aggiornamento in secondi (default 60)

mqtt_topic_prefix  
Prefisso dei topic MQTT (default zoho_calendar)

La configurazione dettagliata di Zoho (client ID, secret, refresh token, nomi app, form, report, tecnici, ecc.) viene gestita dalla procedura guidata nell’interfaccia web dell’add-on.

## OAuth2 Zoho – Ottenere le credenziali

1. Vai su https://api-console.zoho.eu  
2. Crea un nuovo client OAuth di tipo Server-based  
3. Imposta la Redirect URI a:  
   http://localhost:3000/auth/callback  
4. Salva Client ID e Client Secret  

## Ottenere il refresh token tramite add-on

1. Apri l’interfaccia dell’add-on  
2. Vai alla sezione Autorizzazione  
3. Clicca Autorizza con Zoho  
4. Completa login e consenso  
5. Copia il parametro code dalla URL di callback  
6. Incollalo nell’add-on e clicca Scambia codice  
7. Il refresh token viene salvato automaticamente  

## Scope consigliati

ZohoCreator.report.READ,ZohoCreator.form.CREATE,ZohoCreator.report.UPDATE,ZohoCreator.report.DELETE

## Struttura dati Zoho Creator

L’add-on lavora tipicamente con:

App: service-management  
Form: Pianificazione  
Report: CalendarioPianificazione  

Campi usati (esempio tipico):

ID  
LkpTecnico.Nominativo  
Titolo  
DescrizioneAttivita  
Data  
DataInizio  
DataFine  
Tipologia  
OrePianificate  
Reparto  

Attenzione: il campo tecnico (lookup) richiede l’ID record Zoho del tecnico, non il nome.

## Dashboard web

Dal menu laterale di Home Assistant trovi la voce Zoho Calendario.

La dashboard mostra una timeline giornaliera con:

- Tutti i tecnici configurati  
- Eventi per fascia oraria  
- Stato occupato o libero  

## API REST dell’add-on

Accessibili tramite Ingress.

## Eventi

GET /api/events → eventi di oggi  
GET /api/events/YYYY-MM-DD → eventi per data  
POST /api/events → crea evento  
PUT /api/events/{id} → aggiorna evento  
DELETE /api/events/{id} → elimina evento  

## Tecnici

GET /api/technicians → lista tecnici e stato  

## Sistema

POST /api/sync → forza sincronizzazione  
GET /api/health → stato servizio  

## Esempio creazione evento

{
  "titolo": "Manutenzione server",
  "tecnico_id": "123456789",
  "data": "2025-01-15",
  "ora_inizio": "09:00",
  "ora_fine": "12:00",
  "descrizione": "Manutenzione programmata"
}

## Sensori MQTT creati

Per ogni tecnico:

sensor.zoho_calendar_{nome}_prossimo_evento  
sensor.zoho_calendar_{nome}_eventi_oggi  
sensor.zoho_calendar_{nome}_stato  
sensor.zoho_calendar_{nome}_orario_prossimo  

Sensori globali:

sensor.zoho_calendar_eventi_totali_oggi  
sensor.zoho_calendar_ultimo_aggiornamento  

## Integrazione custom senza MQTT

Se vuoi sensori nativi in Home Assistant:

1. Copia custom_components/zoho_calendar in  
   config/custom_components/zoho_calendar  
2. Riavvia Home Assistant  
3. Aggiungi integrazione Zoho Calendar Add-on  
4. Inserisci il Base URL dell’add-on  
   default: http://addon_zoho-calendar:8099  

## Risoluzione problemi

Sensori non visibili  
- Verifica che MQTT sia attivo  
- Controlla i log dell’add-on  
- Attendi almeno un ciclo di aggiornamento  

Errore refresh token non configurato  
- Completa la procedura OAuth  
- Inserisci correttamente il token  

Errore invalid_grant  
- Il refresh token è stato revocato  
- Rigeneralo tramite la procedura di autorizzazione  
