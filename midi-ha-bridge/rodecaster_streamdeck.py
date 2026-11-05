#!/usr/bin/env python3
"""
Stream Deck panel for the RODECaster Pro II (via MIDI).

Turns an Elgato Stream Deck into a control surface for the mixer:
- pressing a key -> sends a MIDI command to the RODECaster;
- (optional) an incoming MIDI message from the mixer lights up the matching key.

Uses the official 'StreamDeck' library (abcminiuser), which talks to the
hardware directly over USB-HID. No change to the mixer or the firmware.

  List connected Stream Decks:  python rodecaster_streamdeck.py --list
  Start the panel:              python rodecaster_streamdeck.py --config config.yaml
"""
import argparse, sys, threading

def _need(mod):
    try:
        return __import__(mod, fromlist=["x"])
    except ImportError:
        sys.exit("A module is missing ('%s'). Run:  pip install -r requirements.txt" % mod)

def _msg_key(msg):
    if msg.type in ("note_on", "note_off"):
        return "note:%d:%d" % (msg.channel, msg.note)
    if msg.type == "control_change":
        return "cc:%d:%d" % (msg.channel, msg.control)
    if msg.type == "program_change":
        return "pc:%d:%d" % (msg.channel, msg.program)
    return msg.type

def _render(deck, label, on=False):
    from StreamDeck.ImageHelpers import PILHelper
    from PIL import Image, ImageDraw, ImageFont
    img = PILHelper.create_key_image(deck)
    d = ImageDraw.Draw(img)
    bg = (0, 90, 40) if on else (20, 20, 20)
    d.rectangle([0, 0, img.width, img.height], fill=bg)
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except Exception:
        font = ImageFont.load_default()
    d.text((img.width / 2, img.height / 2), label, anchor="mm", fill=(255, 255, 255), font=font)
    return PILHelper.to_native_key_format(deck, img)

def list_decks():
    DeviceManager = _need("StreamDeck.DeviceManager").DeviceManager
    decks = DeviceManager().enumerate()
    if not decks:
        print("No Stream Deck found.")
        return
    for d in decks:
        d.open(); d.reset()
        print("  %s  (%d keys)" % (d.deck_type(), d.key_count()))
        d.close()

def send_midi(mido, outname, spec):
    kind, ch, n = spec.split(":")[0], int(spec.split(":")[1]), int(spec.split(":")[2])
    if kind == "note":
        m = mido.Message("note_on", channel=ch, note=n, velocity=127)
    elif kind == "cc":
        m = mido.Message("control_change", channel=ch, control=n, value=127)
    elif kind == "pc":
        m = mido.Message("program_change", channel=ch, program=n)
    else:
        print("Invalid MIDI spec: %s" % spec); return
    with mido.open_output(outname) as o:
        o.send(m)

def run(path):
    yaml = _need("yaml")
    mido = _need("mido")
    DeviceManager = _need("StreamDeck.DeviceManager").DeviceManager
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    sd = cfg.get("streamdeck", {})
    keys = sd.get("keys", [])
    by_index = {k["index"]: k for k in keys}
    by_reflect = {k["reflect_key"]: k for k in keys if k.get("reflect_key")}

    def match(names, needle):
        return next((n for n in names if needle.lower() in n.lower()), None)
    outname = match(mido.get_output_names(), cfg["midi_port"])
    inname = match(mido.get_input_names(), cfg["midi_port"])

    decks = DeviceManager().enumerate()
    if not decks:
        sys.exit("No Stream Deck found (use --list).")
    deck = decks[0]
    deck.open(); deck.reset()
    deck.set_brightness(sd.get("brightness", 60))
    for idx, k in by_index.items():
        deck.set_key_image(idx, _render(deck, k.get("label", str(idx))))

    def on_press(d, key, pressed):
        if not pressed or key not in by_index:
            return
        k = by_index[key]
        if outname and k.get("midi"):
            send_midi(mido, outname, k["midi"])
            print("Key %d -> MIDI %s" % (key, k["midi"]))
        else:
            print("Key %d pressed (no MIDI out port or 'midi' not set)" % key)
    deck.set_key_callback(on_press)

    # feedback from the mixer -> light up the keys
    def midi_listener():
        if not inname:
            return
        with mido.open_input(inname) as inport:
            for msg in inport:
                k = by_reflect.get(_msg_key(msg))
                if not k:
                    continue
                on = not (msg.type == "note_off" or (msg.type == "note_on" and getattr(msg, "velocity", 0) == 0))
                deck.set_key_image(k["index"], _render(deck, k.get("label", ""), on=on))
    if inname:
        threading.Thread(target=midi_listener, daemon=True).start()

    print("Stream Deck panel running. Ctrl+C to exit.")
    try:
        while True:
            threading.Event().wait(1)
    except KeyboardInterrupt:
        pass
    finally:
        deck.reset(); deck.close()

def main():
    ap = argparse.ArgumentParser(description="Stream Deck panel for RODECaster Pro II via MIDI")
    ap.add_argument("--list", action="store_true", help="list connected Stream Decks")
    ap.add_argument("--config", help="YAML configuration file")
    a = ap.parse_args()
    if a.list:
        list_decks()
    elif a.config:
        run(a.config)
    else:
        ap.print_help()

if __name__ == "__main__":
    main()
