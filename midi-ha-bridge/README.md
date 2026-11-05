# RODECaster Pro II — MIDI → Home Assistant bridge + Stream Deck

**External, non-invasive** integration of the RØDECaster Pro II, based solely on the
device's **MIDI** surface (the one RØDE documents for the Elgato Stream Deck plugin).
It does not modify the mixer, does not touch the firmware, and does not use the
internal OSC/D-Bus interfaces.

## Components
- `rodecaster_bridge.py` — MIDI ↔ MQTT bridge for Home Assistant (with MQTT discovery).
- `rodecaster_streamdeck.py` — Elgato Stream Deck panel: keys send MIDI to the mixer
  and reflect incoming state.
- `config.example.yaml` — configuration (mappings, commands, Stream Deck keys).
- `requirements.txt` — Python dependencies.

## Install
```bash
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## 1. Discover YOUR device's ports and commands
MIDI numbers vary per device: read them from your own unit, don't guess.

```bash
python rodecaster_bridge.py --list                      # list MIDI ports
python rodecaster_bridge.py --log --port "RODECaster"   # print MIDI messages
```
Press pads, faders and buttons: each line shows a `key` (e.g. `note:0:36`, `cc:0:20`).
Copy those keys into the config file.

## 2. Configure
Copy `config.example.yaml` to `config.yaml` and fill in: MIDI port, MQTT broker,
and the real `key`/`midi` values obtained in step 1.

## 3. Run
```bash
python rodecaster_bridge.py --config config.yaml        # bridge to Home Assistant
python rodecaster_streamdeck.py --config config.yaml    # Stream Deck panel
```

## How it works
- **Device → HA:** the bridge listens to the mixer's MIDI messages and publishes state
  over MQTT with automatic *discovery* (entities appear by themselves in Home Assistant).
- **HA → Device:** HA publishes to a `command_topic` and the bridge sends MIDI to the mixer.
- **Stream Deck:** each key sends a MIDI command; an incoming MIDI message can light up
  the matching key (`reflect_key`).

## Notes
- The Stream Deck is driven over USB-HID with the `StreamDeck` library (abcminiuser).
- **Windows — Stream Deck:** `hidapi.dll` must be reachable (next to the scripts or on PATH).
  Download it from [libusb/hidapi releases](https://github.com/libusb/hidapi/releases)
  (`hidapi-win.zip` → use `x64\hidapi.dll`). Without it, `--list` reports "Probe failed … HID backend".
- **MIDI port on Windows:** the mixer may show up as **"MIDI function"** instead of "RODECaster";
  check with `--list`.
- For HA to discover the entities, the **MQTT** integration must be active (e.g. the Mosquitto add-on).
- No operation writes to the mixer other than the MIDI messages you send on purpose.

## Tested (2026-11-05, Windows 11, Python 3.12)
Feasibility checks, without sending commands to the mixer or creating entities in HA:
- mixer MIDI port detected ✔ (shows up as `MIDI function 0/1`)
- `Stream Deck Original` (15 keys) detected ✔ and key-label rendering ✔
- Home Assistant MQTT discovery payloads well-formed (dry-run) ✔
- HA→mixer MIDI messages built correctly (dry-run, nothing sent) ✔
- read-only MIDI port open ✔

*Live* tests (sending MIDI to the mixer, creating entities in HA) not yet performed.
