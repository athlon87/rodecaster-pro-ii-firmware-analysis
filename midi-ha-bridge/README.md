# RODECaster Pro II — Bridge MIDI → Home Assistant + Stream Deck

Integrazione **esterna e non invasiva** del RØDECaster Pro II, basata unicamente
sulla superficie **MIDI** del dispositivo (quella che RØDE documenta per il plugin
Elgato Stream Deck). Non modifica il mixer, non tocca il firmware, non usa le
interfacce interne OSC/DBus.

## Componenti
- `rodecaster_bridge.py` — ponte MIDI ↔ MQTT per Home Assistant (con MQTT discovery).
- `rodecaster_streamdeck.py` — pannello Elgato Stream Deck: i tasti inviano comandi
  MIDI al mixer e riflettono lo stato in arrivo.
- `config.example.yaml` — configurazione (mappings, comandi, tasti Stream Deck).
- `requirements.txt` — dipendenze Python.

## Installazione
```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## 1. Scoprire porte e comandi del TUO device
I numeri MIDI variano: vanno letti dal proprio dispositivo, non indovinati.

```bash
python rodecaster_bridge.py --list                      # elenca le porte MIDI
python rodecaster_bridge.py --log --port "RODECaster"   # stampa i messaggi MIDI
```
Premi pad, fader e pulsanti: ogni riga mostra una `key` (es. `note:0:36`, `cc:0:20`).
Copia quelle chiavi nel file di config.

## 2. Configurare
Copia `config.example.yaml` in `config.yaml` e inserisci: porta MIDI, broker MQTT,
e le `key`/`midi` reali ricavate al passo 1.

## 3. Avviare
```bash
python rodecaster_bridge.py --config config.yaml        # bridge verso Home Assistant
python rodecaster_streamdeck.py --config config.yaml    # pannello Stream Deck
```

## Come funziona
- **Device → HA:** il bridge ascolta i messaggi MIDI del mixer e pubblica lo stato
  su MQTT con *discovery* automatico (le entità compaiono da sole in Home Assistant).
- **HA → Device:** HA pubblica su un `command_topic` e il bridge invia il MIDI al mixer.
- **Stream Deck:** ogni tasto invia un comando MIDI; un messaggio MIDI in arrivo può
  accendere il tasto corrispondente (`reflect_key`).

## Note
- Lo Stream Deck è pilotato via USB-HID con la libreria `StreamDeck` (abcminiuser).
- Perché HA scopra le entità serve l'integrazione **MQTT** attiva (es. add-on Mosquitto).
- Nessuna operazione scrive sul mixer oltre ai messaggi MIDI che invii volontariamente.
