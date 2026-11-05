# Contributing

Thanks for your interest! This is an educational, **passive** research project on a
RØDECaster Pro II, plus non-invasive integration tooling. Contributions that help other
owners of the device are very welcome.

## Good contributions
- **Real MIDI mappings** for your unit — run `midi-ha-bridge/rodecaster_bridge.py --log`,
  press pads/buttons/faders, and share the `key` values (pad numbers, record, mute, banks…).
- **Test reports** on other OSes (Linux, macOS) or other Stream Deck models.
- **Home Assistant** blueprints, automations, or dashboard examples built on the bridge.
- **Corrections / additions** to the firmware and application-layer analysis.
- **Documentation** improvements (keep docs in English).

## Scope & ground rules (please respect these)
This project stays strictly on the legal, interoperability side:

- ✅ Passive analysis of the official firmware and of a device **you own**.
- ✅ Integration over the **documented MIDI** surface, or exploration of the device's own
  interfaces for interoperability.
- ❌ **Do not** submit anything that bypasses signature/MD5 checks, injects SSH keys, roots
  the device, or flashes modified firmware.
- ❌ **Do not** upload RØDE firmware, binaries, or other copyrighted material to the repo.
- ❌ **Do not** include personal data, serial numbers, private keys, or MAC addresses in
  issues, PRs, or logs — redact them first.

## How to contribute
1. Open an **Issue** to discuss (or a **Discussion** for open-ended ideas).
2. For changes, fork and open a **Pull Request** against `main` with a clear description.
3. Keep commits focused; English for code comments and docs.

By contributing you agree your work is released under the repository's [MIT License](LICENSE).
