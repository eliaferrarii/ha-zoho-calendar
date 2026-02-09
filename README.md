## \# Home Assistant Add-on: Zoho Calendar

## 

## Integrazione tra Zoho Creator e Home Assistant per la gestione della pianificazione dei tecnici, la visualizzazione degli interventi e la creazione o modifica delle attività direttamente da Home Assistant.

## 

## \## About

## 

## Questo add-on collega Zoho Creator (Service Management) a Home Assistant.

## 

## Permette di sincronizzare la pianificazione dei tecnici, visualizzare gli interventi su una dashboard dedicata e creare o modificare attività tramite API REST o interfaccia web integrata.

## 

## L’add-on espone anche sensori MQTT e un’API locale per l’integrazione con automazioni e dashboard di Home Assistant.

## 

## La documentazione completa è disponibile nel file DOCS.md all’interno della cartella dell’add-on.

## 

## \## Features

## 

## \- Sincronizzazione automatica delle attività da Zoho Creator  

## \- Dashboard web integrata in Home Assistant (Ingress)  

## \- Timeline giornaliera per tecnico  

## \- Creazione, modifica ed eliminazione eventi  

## \- Sensori MQTT per ogni tecnico (stato, prossimo intervento, eventi giornalieri)  

## \- API REST per integrazioni personalizzate  

## \- Configurazione guidata OAuth2 per Zoho  

## \- Supporto multi-tecnico  

## \- Aggiornamento automatico a intervalli configurabili  

## 

## \## Warning

## 

## Questo add-on accede ai dati operativi della tua piattaforma Zoho Creator.

## 

## Configurazioni errate (ID tecnici, form, report o permessi API) possono causare errori di sincronizzazione o modifiche dati indesiderate. Usare con attenzione in ambienti di produzione.

## 

## \## Installation

## 

## 1\. Vai in Home Assistant → Impostazioni → Add-on → Store  

## 2\. Apri il menu in alto a destra → Repository  

## 3\. Aggiungi  

## &nbsp;  https://github.com/eliaferrarii/ha-zoho-calendar  

## 4\. Installa Zoho Calendar  

## 5\. Avvia l’add-on  

## 6\. Apri l’interfaccia web dal menu laterale  

## 

## \## Configuration

## 

## Le opzioni principali dell’add-on sono:

## 

## update\_interval  

## Intervallo di sincronizzazione in secondi

## 

## mqtt\_topic\_prefix  

## Prefisso dei topic MQTT usati per i sensori

## 

## La configurazione completa di Zoho (OAuth, app, form, report, tecnici) viene gestita tramite l’interfaccia web dell’add-on.

## 

## \## How it works

## 

## Zoho Creator → Add-on → MQTT / REST → Home Assistant

## 

## L’add-on legge le attività pianificate da Zoho Creator, le elabora e le pubblica come sensori MQTT e tramite API REST per essere usate in Home Assistant.

## 

## \## MQTT Sensors

## 

## Per ogni tecnico vengono creati sensori come:

## 

## sensor.zoho\_calendar\_<tecnico>\_stato  

## sensor.zoho\_calendar\_<tecnico>\_prossimo\_evento  

## sensor.zoho\_calendar\_<tecnico>\_eventi\_oggi  

## 

## Sensori globali:

## 

## sensor.zoho\_calendar\_eventi\_totali\_oggi  

## sensor.zoho\_calendar\_ultimo\_aggiornamento  

## 

## \## REST API

## 

## L’add-on espone API per:

## 

## \- Lettura eventi  

## \- Creazione nuovi interventi  

## \- Modifica eventi  

## \- Eliminazione attività  

## \- Stato tecnici  

## 

## I dettagli completi degli endpoint sono descritti nel file DOCS.md.

## 

## \## Support

## 

## Per problemi o richieste di funzionalità:

## 

## \- Apri una issue su GitHub  

## \- Allega i log dell’add-on  

## \- Non condividere mai credenziali o token Zoho  

## 

## \## Contributing

## 

## Pull request e miglioramenti sono benvenuti. Assicurati che le modifiche non rompano la compatibilità con configurazioni esistenti.

## 

## \## License

## 

## MIT License

## 

## Copyright (c) 2026 Elia Ferrari



