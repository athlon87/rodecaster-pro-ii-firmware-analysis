#!/usr/bin/env python3
"""
RODECaster Pro II  <->  Home Assistant  bridge (via MIDI + MQTT discovery).

Usa SOLO la superficie MIDI ufficiale del dispositivo (quella documentata da RODE
per il plugin Elgato Stream Deck). Non modifica il mixer, non tocca il firmware,
non usa l'interfaccia OSC/DBus interna.

Modi d'uso:
  1) Scoprire le porte MIDI:        python rodecaster_bridge.py --list
  2) Imparare i comandi del device: python rodecaster_bridge.py --log --port "RODECaster"
  3) Avviare il bridge verso HA:    python rodecaster_bridge.py --config config.yaml

Il mapping comando<->entita HA e' interamente nel file di config: lo popoli tu
con i numeri reali che vedi in modo --log sul TUO dispositivo.

Dipendenze: mido, python-rtmidi, paho-mqtt, pyyaml  (vedi requirements.txt)
"""
import argparse, json, sys, time

def _need(mod):
    try:
        return __import__(mod)
    except ImportError:
        sys.exit("Manca il modulo '%s'. Esegui:  pip install -r requirements.txt" % mod)

def list_ports():
    mido = _need("mido")
    print("== Porte MIDI in INGRESSO (dal dispositivo al PC) ==")
    for n in mido.get_input_names():
        print("  ", n)
    print("== Porte MIDI in USCITA (dal PC al dispositivo) ==")
    for n in mido.get_output_names():
        print("  ", n)
    print("\nSuggerimento: la porta del mixer contiene di solito 'RODECaster'.")

def _match_port(names, needle):
    for n in names:
        if needle.lower() in n.lower():
            return n
    return None

def log_mode(port_substr):
    mido = _need("mido")
    name = _match_port(mido.get_input_names(), port_substr)
    if not name:
        sys.exit("Nessuna porta di ingresso contiene '%s'. Usa --list." % port_substr)
    print("Ascolto '%s'. Premi pad/fader/pulsanti sul RODECaster; Ctrl+C per uscire.\n" % name)
    with mido.open_input(name) as inport:
        for msg in inport:
            d = msg.dict()
            # riga compatta utile a costruire il mapping di config
            key = _msg_key(msg)
            print("%-22s  key=%s  raw=%s" % (msg.type, key, d))

def _msg_key(msg):
    """Chiave stabile per identificare un controllo nel config."""
    if msg.type in ("note_on", "note_off"):
        return "note:%d:%d" % (msg.channel, msg.note)
    if msg.type == "control_change":
        return "cc:%d:%d" % (msg.channel, msg.control)
    if msg.type == "program_change":
        return "pc:%d:%d" % (msg.channel, msg.program)
    return msg.type

# ---------------------------------------------------------------- bridge ----

class Bridge:
    def __init__(self, cfg):
        self.mido = _need("mido")
        mqtt = _need("paho.mqtt.client")
        self.cfg = cfg
        self.mappings = cfg.get("mappings", [])       # device -> HA
        self.commands = cfg.get("commands", [])        # HA -> device
        disc = cfg.get("discovery_prefix", "homeassistant")
        self.disc = disc
        self.node = cfg.get("node_id", "rodecaster")
        b = cfg["mqtt"]
        self.cli = mqtt.Client(client_id="rodecaster-bridge")
        if b.get("username"):
            self.cli.username_pw_set(b["username"], b.get("password", ""))
        self.cli.on_connect = self._on_connect
        self.cli.on_message = self._on_message
        self._broker = (b["host"], int(b.get("port", 1883)))
        self.inname = _match_port(self.mido.get_input_names(), cfg["midi_port"])
        self.outname = _match_port(self.mido.get_output_names(), cfg["midi_port"])
        if not self.inname:
            sys.exit("Porta MIDI in ingresso '%s' non trovata (usa --list)." % cfg["midi_port"])

    # ---- Home Assistant MQTT discovery -------------------------------------
    def _publish_discovery(self):
        for m in self.mappings:
            uid = "%s_%s" % (self.node, m["id"])
            comp = m.get("ha_type", "binary_sensor")
            topic = "%s/%s/%s/%s/config" % (self.disc, comp, self.node, m["id"])
            payload = {
                "name": m.get("name", m["id"]),
                "unique_id": uid,
                "state_topic": "%s/%s/%s/state" % (self.node, comp, m["id"]),
                "device": {"identifiers": [self.node],
                           "name": "RODECaster Pro II",
                           "manufacturer": "RODE"},
            }
            payload.update(m.get("extra", {}))
            self.cli.publish(topic, json.dumps(payload), retain=True)
        print("Discovery pubblicato per %d entita'." % len(self.mappings))

    def _on_connect(self, c, u, flags, rc):
        print("MQTT connesso (rc=%s)." % rc)
        self._publish_discovery()
        # ascolta i comandi da HA verso il device
        for cmd in self.commands:
            c.subscribe(cmd["command_topic"])

    def _on_message(self, c, u, msg):
        text = msg.payload.decode("utf-8", "replace")
        for cmd in self.commands:
            if cmd["command_topic"] == msg.topic and text == cmd.get("payload", text):
                self._send_midi(cmd["midi"])

    def _send_midi(self, spec):
        if not self.outname:
            print("Nessuna porta MIDI in uscita: comando ignorato.")
            return
        kind, ch, n = spec.split(":")[0], int(spec.split(":")[1]), int(spec.split(":")[2])
        if kind == "note":
            m = self.mido.Message("note_on", channel=ch, note=n, velocity=127)
        elif kind == "cc":
            m = self.mido.Message("control_change", channel=ch, control=n, value=127)
        elif kind == "pc":
            m = self.mido.Message("program_change", channel=ch, program=n)
        else:
            print("Spec MIDI non valida: %s" % spec); return
        with self.mido.open_output(self.outname) as o:
            o.send(m)
        print("MIDI inviato: %s" % spec)

    # ---- loop device -> HA --------------------------------------------------
    def run(self):
        self.cli.connect(*self._broker, keepalive=30)
        self.cli.loop_start()
        by_key = {m["key"]: m for m in self.mappings}
        print("Bridge attivo su '%s'. Ctrl+C per fermare." % self.inname)
        try:
            with self.mido.open_input(self.inname) as inport:
                for msg in inport:
                    m = by_key.get(_msg_key(msg))
                    if not m:
                        continue
                    comp = m.get("ha_type", "binary_sensor")
                    state = m.get("on_payload", "ON")
                    if msg.type == "note_off" or (msg.type == "note_on" and getattr(msg, "velocity", 0) == 0):
                        state = m.get("off_payload", "OFF")
                    st = "%s/%s/%s/state" % (self.node, comp, m["id"])
                    self.cli.publish(st, state, retain=False)
                    print("-> HA  %s = %s" % (m["id"], state))
        except KeyboardInterrupt:
            pass
        finally:
            self.cli.loop_stop()

def run_bridge(path):
    yaml = _need("yaml")
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    Bridge(cfg).run()

def main():
    ap = argparse.ArgumentParser(description="Bridge RODECaster Pro II <-> Home Assistant via MIDI")
    ap.add_argument("--list", action="store_true", help="elenca le porte MIDI e termina")
    ap.add_argument("--log", action="store_true", help="stampa i messaggi MIDI in arrivo (per mappare i controlli)")
    ap.add_argument("--port", default="RODECaster", help="sottostringa del nome porta MIDI (default: RODECaster)")
    ap.add_argument("--config", help="file YAML di configurazione per avviare il bridge")
    a = ap.parse_args()
    if a.list:
        list_ports()
    elif a.log:
        log_mode(a.port)
    elif a.config:
        run_bridge(a.config)
    else:
        ap.print_help()

if __name__ == "__main__":
    main()
