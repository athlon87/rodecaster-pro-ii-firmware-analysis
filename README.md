# rodecaster-pro-ii-firmware-analysis
Technical analysis and system architecture documentation of the RØDECaster Pro II Linux embedded firmware.
# RØDECaster Pro II — Embedded Linux System Architecture

This repository hosts a technical and educational analysis of the **RØDECaster Pro II** (product `rcp2`) system architecture. The data has been extracted via passive analysis of the official firmware `os.tar.gz` (v1.7.7).

## 📌 Firmware Information
* **Source:** ://rode.com
* **OS Version:** 1.7.7
* **Firmware MD5:** `4476bb557ee4cb444918303bed844f11` (verified)

---

## 🛠️ Hardware & Platform Summary

The device is engineered as a robust, high-reliability audio appliance based on a customized Poky / Yocto Project distribution and a real-time patched Linux kernel.

* **SoC:** Amlogic Meson AXG (A113D Family)
* **Bootloader:** U-Boot 2020.04 (`boot/u-boot-rodecaster-pro-ii-2020.04-r0.bin`)
* **Kernel:** Linux 5.10.17 with `PREEMPT_RT` patches for ultra-low latency audio processing.
* **Storage & Filesystem:** Rootfs resides on eMMC (`/dev/mmcblk1p1`) managed in **Read-Only** mode. Writable areas are mounted as overlays on `tmpfs` (`/var/volatile`, `/run`).
* **Service Access:** UART serial console enabled on `ttyAML0` @ 115200 baud with active getty.

---

## 🚀 SysVinit Daemon Startup Sequence (Runlevel 5)

The system uses a classic SysVinit setup rather than systemd. The following sequence details the chronological boot order of the main daemons extracted from `/etc/rc5.d/`:

1. **S02 `dbus-1`**: System message bus.
2. **S03 `rode-audio-service`**: Launches the core audio engine (`AudioCompressorAlsa`) while isolating CPU cores via `cpuset-init.sh`.
3. **S03 `rode-update-env`**: Prepares the staging environment for firmware updates.
4. **S06 `rode-display-service`**: Spawns the main touchscreen UI built on the **JUCE** framework (`rc_gui_juce`) via `display-start.sh`.
5. **S07 `networking`**: Basic network interface configuration.
6. **S09 `sshd`**: OpenSSH daemon listening on port 22.
7. **S12 `rpcbind`**: RPC Portmapper listening on port 111.
8. **S21 `avahi-daemon`**: mDNS / Zero-conf service for network discovery.
9. **S22 `ofono`**: Telephony stack managing mobile and Bluetooth connections.
10. **S30 `callme-t-service`**: "CallMe-T" SIP / Opus IP audio codec on ports 5060/5061 (depends on `rc_audio_mixer`).
11. **S64 `neard`**: Near Field Communication (NFC) manager.

---

## 📡 Network Port Mapping

This mapping correlates the open ports observed during network scans with the internal daemons running on the system:

| Port / Protocol | Active Daemon | System Role |
| :--- | :--- | :--- |
| **22/tcp (SSH)** | `sshd` | Remote shell access |
| **111/tcp (RPC)** | `rpcbind` | System RPC Portmapper |
| **5060-5061/tcp (SIP)** | `ofono` + `callme-t` | VoIP SIP stack and Opus audio codec |
| **UDP (mDNS)** | `avahi-daemon` | Mixer network discovery |

---

## 🧩 Application Layer & Control Surfaces

Beyond the OS/boot layer above, a passive analysis of the user-space application
binaries (`rc_audio_mixer`, `rc_gui_juce`) documents the device's control surfaces —
an internal **OSC/TCP** property bus, the officially documented **MIDI** interface,
and a **D-Bus** UI interface — plus dynamic dependencies and the update mechanism.

➡️ See **[APPLICATION_LAYER.md](APPLICATION_LAYER.md)**.

---

## 🔗 External Resources & GPL Source Code
The Linux kernel source code patched by RØDE is released publicly under the GPL license and can be retrieved from:
* [RØDE Linux Kernel A113D Source Archive](https://amazonaws.com)
