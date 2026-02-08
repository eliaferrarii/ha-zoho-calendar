# Changelog

## 1.0.17

- Aggiunta custom integration (sensori senza MQTT)
- API /api/config/status include update_interval per sincronizzare la frequenza

## 1.0.16

- Formato date/ora per Zoho Creator corretto: `DD/MM/YYYY` e `DD/MM/YYYY HH:MM`

## 1.0.15

- Date/ora create in formato Zoho (DD-MMM-YYYY) per evitare errori "Enter a valid date format"

## 1.0.14

- Fix creazione eventi: formato date/ora compatibile con Zoho + retry su errore formato
- Errori di creazione ora restituiti correttamente

## 1.0.13

- Filtra gli eventi solo per i tecnici configurati (ID o nome)

## 1.0.12

- Controlli calendario forzati su una riga (no wrap)

## 1.0.11

- Gestione ID tecnico: campo in UI + validazione prima di creare eventi
- Creazione eventi usa ID tecnico (lookup Zoho), non il nome
- Documentazione aggiornata su ID tecnico

## 1.0.10

- Documentazione resa piu generica (campi Zoho personalizzati come esempio)
- ID Attivita Interna tornato opzionale in UI

## 1.0.9

- Documentazione installazione e OAuth aggiornata (redirect URI + flusso corretto)
- ID Attivita Interna segnato come obbligatorio e validato in UI

## 1.0.8

- Controlli calendario disposti in orizzontale
- Altezza righe timeline fissa per evitare ridimensionamenti verticali casuali

## 1.0.7

- Redirect URI OAuth aggiornato a `http://localhost:3000/auth/callback` (configurabile via `ZOHO_REDIRECT_URI`)

## 1.0.6

- Rimosso `CMD ["/init"]` per evitare doppio avvio di s6 (PID 1)

## 1.0.5

- Disabilitato `init` di Docker per evitare conflitto con s6-overlay (PID 1)

## 1.0.4

- Pulita struttura `rootfs/` (rimossi file duplicati e directory annidate)

## 1.0.3

- Repo reso valido per Home Assistant Add-on Store: add-on spostato in `zoho-calendar/`
- Aggiornato shebang del servizio s6 a `/command/with-contenv`

## 1.0.2

- Fix avvio: usa s6 (`/init`) e servizio dedicato per evitare errore `s6-overlay-suexec: fatal: can only run as pid 1`
- Logica di startup spostata nel servizio s6 (rimosso `run.sh`)

## 1.0.0

- Prima release
- Integrazione calendario Zoho Creator (CalendarioPianificazione)
- Sensori MQTT Discovery per ogni tecnico
- Dashboard web con vista timeline giornaliera (7:00-21:00)
- API REST per CRUD eventi
- Auto-refresh ogni 30 secondi (dashboard) e 60 secondi (MQTT)
- Supporto 9 tecnici predefiniti
- Tema scuro compatibile con Home Assistant ingress
