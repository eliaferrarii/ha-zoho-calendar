# Changelog

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
