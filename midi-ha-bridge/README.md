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
- **Windows — Stream Deck:** serve `hidapi.dll` raggiungibile (accanto agli script o nel PATH).
  Scaricala da [libusb/hidapi releases](https://github.com/libusb/hidapi/releases)
  (`hidapi-win.zip` → usa la `x64\hidapi.dll`). Senza, `--list` dà "Probe failed … HID backend".
- **Porta MIDI su Windows:** il mixer può comparire come **"MIDI function"** invece di "RODECaster";
  controlla con `--list`.
- Perché HA scopra le entità serve l'integrazione **MQTT** attiva (es. add-on Mosquitto).
- Nessuna operazione scrive sul mixer oltre ai messaggi MIDI che invii volontariamente.

## Testato (2026-11-05, Windows 11, Python 3.12)
Verifiche di fattibilità, senza inviare comandi al mixer né creare entità in HA:
- rilevamento porta MIDI del mixer ✔ (compare come `MIDI function 0/1`)
- `Stream Deck Original` (15 tasti) rilevato ✔ e render etichette sui tasti ✔
- payload MQTT discovery per Home Assistant ben formati (dry-run) ✔
- messaggi MIDI HA→mixer costruiti correttamente (dry-run, nessun invio) ✔
- apertura porta MIDI in sola lettura ✔

Test *live* (invio MIDI al mixer, creazione entità in HA) non ancora eseguiti.
