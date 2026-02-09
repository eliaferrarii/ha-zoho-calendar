\## Zoho Calendar – Home Assistant Add-on

Integration between Zoho Creator (Service Management) and Home Assistant to manage staff scheduling, view events, and create or modify tasks directly from Home Assistant.



\## What the add-on does

Reads scheduled tasks from the CalendarioPianificazione report in Zoho Creator

Creates MQTT sensors for each person (status, events, next job)

Provides a web dashboard integrated into Home Assistant (Ingress) with a daily timeline

Allows creating, editing, and deleting events via REST API

Automatically syncs at configurable intervals



\## Requirements

Zoho account with access to Zoho Creator

Zoho Creator app (e.g. service-management) with a Pianificazione form

Zoho OAuth2 credentials (Client ID, Client Secret, Refresh Token)

MQTT broker configured in Home Assistant (e.g. Mosquitto add-on)



\## Installation

Go to Home Assistant → Settings → Add-ons → Store

Open the menu at the top right → Repositories

Add:

https://github.com/eliaferrarii/ha-zoho-calendar



Install the Zoho Calendar add-on

Start the add-on

Open the add-on web interface from the sidebar



Add-on configuration

Main add-on options:



update\_interval

Update interval in seconds (default 60)



mqtt\_topic\_prefix

MQTT topic prefix (default zoho\_calendar)



Detailed Zoho configuration (client ID, secret, refresh token, app names, forms, reports, technicians, etc.) is handled through the setup wizard in the add-on web interface.



Zoho OAuth2 – Getting credentials

Go to https://api-console.zoho.eu



Create a new OAuth client of type Server-based

Set the Redirect URI to:

http://localhost:3000/auth/callback



Save the Client ID and Client Secret



Getting the refresh token via the add-on

Open the add-on interface

Go to the Authorization section

Click Authorize with Zoho

Complete login and consent

Copy the code parameter from the callback URL

Paste it into the add-on and click Exchange code

The refresh token is saved automatically



\## Recommended scopes

ZohoCreator.report.READ,ZohoCreator.form.CREATE,ZohoCreator.report.UPDATE,ZohoCreator.report.DELETE



\## Zoho Creator data structure

\## The add-on typically works with:



App: service-management

Form: Pianificazione

Report: CalendarioPianificazione



Fields used (typical example):

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



Note: the person field (lookup) requires the Zoho record ID of the person, not the name.



\## Web dashboard

From the Home Assistant sidebar, you will find Zoho Calendario.

The dashboard shows a daily timeline with:

All configured people

Events by time slot

Busy or free status



Add-on REST API

Accessible via Ingress.



\## Events

GET /api/events → today’s events

GET /api/events/YYYY-MM-DD → events by date

POST /api/events → create event

PUT /api/events/{id} → update event

DELETE /api/events/{id} → delete event



\## People

GET /api/technicians → list of people and status



\## System

POST /api/sync → force synchronization

GET /api/health → service status



\## Event creation example

{

"titolo": "Server maintenance",

"tecnico\_id": "123456789",

"data": "2025-01-15",

"ora\_inizio": "09:00",

"ora\_fine": "12:00",

"descrizione": "Scheduled maintenance"

}



\## MQTT sensors created

\## For each person:

sensor.zoho\_calendar\_{name}next\_event

sensor.zoho\_calendar{name}events\_today

sensor.zoho\_calendar{name}status

sensor.zoho\_calendar{name}\_next\_time



\## Global sensors:

sensor.zoho\_calendar\_total\_events\_today

sensor.zoho\_calendar\_last\_update



\## Troubleshooting



\## Sensors not visible

Check that MQTT is running

Check the add-on logs

Wait at least one update cycle



\## Error: refresh token not configured

Complete the OAuth procedure

Enter the token correctly



\## Error: invalid\_grant

The refresh token has been revoked

Generate a new one through the authorization process

