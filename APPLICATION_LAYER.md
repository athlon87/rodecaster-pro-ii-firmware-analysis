# RØDECaster Pro II — Application Layer & Control Surfaces

Educational, **passive** static analysis of the application binaries shipped in the
official firmware `app.zip` (v1.7.7). No commands were ever sent to the device, the
image was not modified, and no signature/MD5 check was bypassed. Findings are derived
from ELF metadata and string inventory only — there is no function-level decompilation
of proprietary code here.

> This document complements the OS/boot/network analysis in the main
> [README](README.md) by describing the **user-space application layer**.

## Binary inventory

The real application binaries live in `app.zip` under `usr/bin/`, not in the rootfs.
All are **ELF 64-bit aarch64, PIE, stripped**, built for glibc (Amlogic A113D).

| Binary | Size | Role |
| :--- | :--- | :--- |
| `rc_audio_mixer` | ~31 MB | Audio engine + mixer state + control surfaces (core process) |
| `rc_gui_juce` | ~20 MB | Touchscreen UI (JUCE framework) |
| `rc_rode_rf_compliance` | ~18 KB | RF compliance utility |
| `Application/mcu-images/*.bin` | — | Microcontroller firmware images (fader, digital) |

App version marker: `1.7.7`.

## Dynamic dependencies of `rc_audio_mixer` (17 libraries)

* **Audio / DSP:** `libasound` (ALSA), `libjack`, `libsamplerate`, `libSoundTouch`, `libmp3lame`
* **Network / system:** `libcurl` (HTTP, used for updates), `libglib` / `libgio` / `libgobject` (GLib + D-Bus)
* **Graphics / fonts:** `libdrm`, `libfreetype`
* **C++ runtime:** `libstdc++`, `libgcc_s`, `libpthread`, `librt`, `libm`, `libc`

## Control surfaces

### 1. OSC over TCP — the internal control bus
The mixer embeds a full **OSC** (Open Sound Control) implementation (JUCE OSC classes):
strings such as `OSC TCP Connection Thread`, `[OSC Bundle]`, a complete OSC parser
(int32 / float / blob / colour / bundle), and `Received RCV OSC frame count`.

The key architectural element is an **`OSCPropertyBridge<T>`** template that bridges
internal state properties to OSC addresses. State lives in a **`SyncTree`**, and
`RcSyncMixerDevice::InitSyncTreeListeners` registers dozens of per-parameter listeners
(bool / float / string). In practice, the companion application and the mixer keep a
property tree synchronised over OSC/TCP. This interface is **not publicly documented**
by RØDE; the exact address space and port would have to be confirmed by passively
observing the companion app's own traffic, not guessed.

### 2. MIDI — the officially documented surface
* `RodecasterUartMidi`: MIDI over **UART** toward the fader MCU (internal hardware link).
* `MIDIController` / `RodecasterPadMidi`: smart-pad and bank control over MIDI, including
  SysEx (`RC-MIDI Received SysEx:`), routed via ALSA (`snd_midi_event_*`) and JUCE MIDI I/O.

RØDE publishes MIDI command tables for the Elgato Stream Deck plugin, which makes MIDI
the **sanctioned** path for external integrations (e.g. a MIDI → MQTT / Home Assistant
bridge, or a Stream Deck control panel).

### 3. D-Bus — system IPC
* Exposed interface: **`org.rodemicrophones.rodecaster.rcui`** (UI control).
* RØDE USB microphones are controlled over D-Bus: `com.rode.ai_micro`,
  `com.rode.nt-usb-plus`, `com.rode.podmicusb`, `com.rode.vmgo2`.
* Networking is handled through `org.freedesktop.NetworkManager` (Wi-Fi / AP).

## Firmware update mechanism (observed, not exercised)

Update staging under `/Application/update-staging/`: `usb-update.img`,
`system-config-20XX.bin` with matching `.md5` and `.lock`, `reboot.file`,
`unit-serial.txt`, `eth-mac.txt`. Remote manifests: `update.rode.com/manifest.json`
(and `rcp2-mini-manifest.json` for the Duo). Downloads go through libcurl.

## Tooling note

On Windows, Ghidra (as integrated by common MCP tooling) only accepts native PE targets,
not aarch64 ELF. Function-level disassembly of these binaries therefore requires Rizin
(free, cross-architecture) or Ghidra on Linux/macOS. The analysis above intentionally
stays at the ELF-metadata and string level.

## Practical takeaways for extending the device

* **Safe, sustainable integration:** use **MIDI** (documented) — e.g. a bridge to
  Home Assistant/MQTT, or a Stream Deck panel. No device modification required.
* **More powerful but undocumented:** the mixer's **OSC/TCP** interface. Explorable for
  interoperability with one's own device, but address list and port should be confirmed
  by passive capture of the companion app, not assumed.
* **No public SDK/REST API** from RØDE was found.
