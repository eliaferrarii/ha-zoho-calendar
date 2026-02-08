# Zoho Calendar - Home Assistant Add-on

Integrazione del calendario di Zoho Service Management (Zoho Creator) con Home Assistant.

## Funzionalita

- Lettura attivita pianificate dal report `CalendarioPianificazione` di Zoho Creator
- Sensori MQTT per ogni tecnico (prossimo evento, eventi oggi, stato)
- Dashboard web (ingress) con vista timeline giornaliera
- Creazione e modifica eventi direttamente da Home Assistant
- Aggiornamento automatico ogni 60 secondi (configurabile)

## Installazione

1. Aggiungere questo repository come add-on repository in Home Assistant
2. Installare l'add-on "Zoho Calendar"
3. Configurare le credenziali Zoho nella tab Configurazione
4. Avviare l'add-on

## Configurazione

| Parametro | Descrizione | Default |
|-----------|-------------|---------|
| `zoho_dc` | Datacenter Zoho | `eu` |
| `zoho_client_id` | Client ID OAuth2 | |
| `zoho_client_secret` | Client Secret OAuth2 | |
| `zoho_refresh_token` | Refresh Token OAuth2 | |
| `zoho_owner` | Owner dell'app Zoho Creator | `emironet` |
| `zoho_app` | Nome app Zoho Creator | `service-management` |
| `zoho_form` | Nome form | `Pianificazione` |
| `zoho_report` | Nome report | `CalendarioPianificazione` |
| `technicians` | Lista tecnici (id + nome) | 9 tecnici predefiniti |
| `update_interval` | Intervallo polling (secondi) | `60` |
| `mqtt_topic_prefix` | Prefisso topic MQTT | `zoho_calendar` |

## Sensori MQTT

Per ogni tecnico vengono creati 4 sensori:
- `sensor.zoho_calendar_{nome}_prossimo_evento` - Titolo prossimo evento
- `sensor.zoho_calendar_{nome}_eventi_oggi` - Conteggio eventi
- `sensor.zoho_calendar_{nome}_stato` - Stato (libero/occupato/ferie)
- `sensor.zoho_calendar_{nome}_orario_prossimo` - Orario prossimo evento

Sensori generali:
- `sensor.zoho_calendar_eventi_totali_oggi` - Totale eventi
- `sensor.zoho_calendar_ultimo_aggiornamento` - Timestamp ultimo sync

## Dashboard

La dashboard web e accessibile dal pannello laterale di Home Assistant (Zoho Calendario).
Mostra una vista timeline giornaliera con tutti i tecnici e i loro eventi.
