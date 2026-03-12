${NOTES}

## Installation

**Before doing any of this, if you haven't already, please back up your existing config and firmware in a safe place** for recovery or to revert to OEM firmware.

### GUI Config Editor

Download the appropriate **MIDI-Captain-MAX-Config-Editor** installer file from the `Assets` section below.

### Device Firmware

1. Download the firmware zip: [midi-captain-max-latest.zip](https://github.com/MC-Music-Workshop/midi-captain-max/releases/latest/download/midi-captain-max-latest.zip).
1. Extract the zip.
1. Connect your MIDI Captain via USB. Power it on normally.
    - The device will mount as `CIRCUITPY` or `MIDICAPTAIN`.
    - If the drive mounts as read-only, hold switch 1 (top-left footswitch) while plugging in USB to enable write access.

#### macOS / Linux — deploy script (recommended)

Run the included `deploy.sh` script from the extracted zip folder:

```bash
# Quick update (preserves your existing config.json)
./deploy.sh

# First-time install — also installs required CircuitPython libraries
./deploy.sh --install

# Deploy and eject for a clean reload
./deploy.sh --eject

# Overwrite config.json with the default (resets your button mappings)
./deploy.sh --fresh
```

The script auto-detects your device type (STD10 or Mini6) and preserves your `config.json` unless you pass `--fresh`.

#### Windows — manual install

> **Note:** A PowerShell install script and a GUI-based installer are coming soon.

1. Open the extracted zip folder.
1. Copy all files and folders to the device drive (`CIRCUITPY` or `MIDICAPTAIN`), replacing existing files.
    - If you have a custom `config.json` with your own button mappings, keep your existing one.
1. **First-time install on Mini6:** delete `config.json` on the device and rename `config-mini6.json` to `config.json`.

---

Eject and reconnect the device to reload the firmware. If anything goes wrong, it's fully recoverable: mount the device, erase the contents, and copy your backed-up files back.
