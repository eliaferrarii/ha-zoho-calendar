# Documentazione - Zoho Calendar Add-on

## Prerequisiti

1. **Account Zoho** con accesso a Zoho Creator
2. **App Zoho Creator** "service-management" con form "Pianificazione"
3. **Credenziali OAuth2** (Client ID, Client Secret, Refresh Token)
4. **Broker MQTT** configurato in Home Assistant (es. Mosquitto)

## Ottenere le credenziali OAuth2

### 1. Creare un client OAuth su Zoho

1. Vai su [Zoho API Console](https://api-console.zoho.eu/)
2. Clicca "Add Client" e crea un **Server-based** client (consigliato)
3. Imposta **Redirect URI** a: `http://localhost:3000/auth/callback`
4. Annota il **Client ID** e **Client Secret**

### 2. Ottenere il Refresh Token (via add-on)

1. Apri l'add-on e vai allo step **Autorizzazione**
2. Clicca **Autorizza con Zoho** e completa il consenso
3. Copia il parametro `code` dalla URL di callback
4. Incolla il codice nell'add-on e clicca **Scambia codice**
5. Il refresh token viene salvato automaticamente

### 3. Configurazione Add-on

Inserisci i valori nella configurazione dell'add-on:
- `zoho_client_id`: Client ID
- `zoho_client_secret`: Client Secret
- `zoho_refresh_token`: Refresh Token ottenuto

### Scopes richiesti

Usa almeno questi scopes:
```
ZohoCreator.report.READ,ZohoCreator.form.CREATE,ZohoCreator.report.UPDATE,ZohoCreator.report.DELETE
```

## API REST

L'add-on espone le seguenti API tramite ingress:

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| GET | `/api/events` | Eventi di oggi |
| GET | `/api/events/{data}` | Eventi per data (YYYY-MM-DD) |
| POST | `/api/events` | Crea evento |
| PUT | `/api/events/{id}` | Aggiorna evento |
| DELETE | `/api/events/{id}` | Elimina evento |
| GET | `/api/technicians` | Lista tecnici con stato |
| POST | `/api/sync` | Forza sincronizzazione |
| GET | `/api/health` | Health check |

### Esempio creazione evento

```json
POST /api/events
{
    "titolo": "Manutenzione server",
    "tecnico_id": "123456789",
    "data": "2025-01-15",
    "ora_inizio": "09:00",
    "ora_fine": "12:00",
    "descrizione": "Manutenzione programmata"
}
```

## Campi Zoho Creator

Nota: i campi possono variare in base alla tua app Zoho Creator. Gli esempi sotto
sono basati su un'implementazione reale e vanno adattati alla tua struttura.

Importante: il campo lookup `LkpTecnico` richiede **l'ID del record Zoho** del tecnico,
non il nome visualizzato. Inserisci gli ID nella lista tecnici dell'add-on.

Il report `CalendarioPianificazione` espone i seguenti campi:

| Campo | Descrizione |
|-------|-------------|
| `ID` | ID record |
| `LkpTecnico.Nominativo` | Nome tecnico |
| `Titolo` | Titolo attivita |
| `DescrizioneAttivita` | Descrizione |
| `Data` | Data (YYYY-MM-DD) |
| `DataInizio` | Ora inizio (HH:MM) |
| `DataFine` | Ora fine (HH:MM) |
| `Tipologia` | Tipo attivita |
| `OrePianificate` | Ore pianificate |
| `LkpAttivitaInterna` | Riferimento attivita interna (campo personalizzato, opzionale) |
| `Reparto` | Reparto |

## Risoluzione problemi

### I sensori non appaiono in HA
- Verificare che il broker MQTT sia attivo e configurato
- Controllare i log dell'add-on per errori di connessione MQTT
- I sensori appaiono dopo il primo ciclo di polling

### Errore "Refresh token non configurato"
- Assicurarsi di aver inserito il refresh token nella configurazione
- Il refresh token non scade, ma puo essere revocato da Zoho

### Errore "invalid_grant"
- Il refresh token e stato revocato o e scaduto
- Generare un nuovo refresh token seguendo la procedura sopra
