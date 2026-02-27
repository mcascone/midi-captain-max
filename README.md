[![CI](https://github.com/MC-Music-Workshop/midi-captain-max/actions/workflows/ci.yml/badge.svg)](https://github.com/MC-Music-Workshop/midi-captain-max/actions/workflows/ci.yml)

# MIDI Captain MAX Custom Firmware

**Bidirectional, config-driven CircuitPython firmware for Paint Audio MIDI Captain foot controllers.**

Includes a **GUI Config Editor**!

<img width="1312" height="912" alt="MCM-config-editor" src="https://github.com/user-attachments/assets/5e4c0b73-074b-4895-8861-d95aea7f1426" />

## What It Does

This firmware transforms your MIDI Captain into a **bidirectional MIDI controller** where your host software (DAW, plugin host) can control the device's LEDs and display, not just receive button presses.

Momentary and toggle modes are currently supported. Many more issues are coming! [See here for all open features and issues](https://github.com/MC-Music-Workshop/midi-captain-max/issues).

## Key Features
- 🔄 **Bidirectional MIDI** — Host can update LEDs/display state
- ⚙️ **Config-driven** — Customize button labels, CC numbers, colors with the GUI Config Editor.
- 🎨 **Visual feedback** — LEDs and LCD reflect actual host state
- 🎛️ **Full input support** — Footswitches, rotary encoder, expression pedals
- 🎸 **Stage-ready** — No unexpected resets, no crashes, no surprises

## Supported Devices

| Device | Status |
|--------|--------|
| MIDI Captain STD10 (10-switch) | ✅ Fully working |
| MIDI Captain Mini6 (6-switch) | ✅ Fully working |
| 4, 2, 1-button variations | ❔ need hardware |

# Installation

1. [Download the latest firmware.zip and appropriate GUI Config Editor](https://github.com/MC-Music-Workshop/midi-captain-max/releases/latest)
3. Connect your MIDI Captain via USB (hold Button 1 while powering on)
4. Copy all files and folders from the zip to the device drive (CIRCUITPY or MIDICAPTAIN)
5. On mini6, rename `config-mini6.json` to `config.json`, overwriting the existing one.
6. Power off/on or unplug and replug USB to restart

## Configuration

### Custom USB Drive Name

If you have multiple MIDI Captain devices, you can give each one a unique name! Edit the `usb_drive_name` field in `config.json`:

```json
{
  "device": "std10",
  "usb_drive_name": "MYCAPTAIN",
  ...
}
```

**Requirements:**
- Maximum 11 characters
- Letters, numbers, and underscores only
- Will be automatically converted to uppercase

The name persists across power cycles and USB disconnects. Change it anytime by editing config.json and restarting the device.

### Config Editor App (Recommended)

The **MIDI Captain MAX Config Editor** is a desktop app that makes configuration easy!

**Download for your platform:**
- **macOS:** `MIDI-Captain-MAX-Config-Editor-[version].dmg`
- **Windows:** `MIDI-Captain-MAX-Config-Editor-[version].msi` or `MIDI-Captain-MAX-Config-Editor-[version]-setup.exe`

Get the latest release from [Releases](https://github.com/MC-Music-Workshop/midi-captain-max/releases/latest)

## Installation

### MacOS
1. Open the DMG and drag the app to your Applications folder

### Windows
1. Run the MSI installer or setup.exe
2. At this time, Windows builds are unsigned. Users will see a Windows SmartScreen warning.
3. To continue installation, click "More Info" --> "Run Anyway".
    - Signing certificates will be obtained in the near future.

## Usage

2. Launch the app and connect your MIDI Captain
3. Edit button labels, CC numbers, and colors using the visual editor
4. Save directly to the device.
5. Power cycle the device to load the new settings.

# Features

- 🖱️ **Visual editing** — No JSON syntax to learn
- ✅ **Real-time validation** — Catch errors before saving
- 🎨 **Color picker** — Visual color selection 
- 🔍 **Device detection** — Automatically detects connected MIDI Captain

## Manual Configuration

You can also edit `config.json` directly on the device:

```json
{
  "buttons": [
    {"label": "DELAY", "cc": 20, "color": [0, 0, 255]},
    {"label": "REVERB", "cc": 21, "color": [0, 255, 0]},
    {"label": "CHORUS", "cc": 22, "color": [255, 0, 255]},
    {"label": "DRIVE", "cc": 23, "color": [255, 128, 0]},
    {"label": "COMP", "cc": 24, "color": [0, 255, 255]},
    {"label": "MOD", "cc": 25, "color": [255, 255, 0]},
    {"label": "LOOP", "cc": 26, "color": [255, 0, 0]},
    {"label": "TUNER", "cc": 27, "color": [255, 255, 255]},
    {"label": "BANK-", "cc": 28, "color": [128, 128, 128]},
    {"label": "BANK+", "cc": 29, "color": [128, 128, 128]}
  ]
}
```

| Field | Description | Default |
|-------|-------------| ---------|
| `label` | Text shown on LCD (max ~6 chars) |
| `cc` | MIDI CC number sent on press (0-127) |
| `color` | RGB color for LED when ON `[R, G, B]` |
| `off_mode` | LED is `off` or `dim` when in OFF state | `off`

## MIDI Protocol

### Device → Host (button presses)
| Input | MIDI Message |
|-------|--------------|
| Encoder wheel | CC 11 (0-127 position) |
| Encoder push | CC 14 (127=press, 0=release) |
| Footswitch 1-10 | CC 20-29 (127=ON, 0=OFF) |
| Expression 1 | CC 12 (0-127) |
| Expression 2 | CC 13 (0-127) |

### Host → Device (LED/state control)
Send CC to the switch on its CC Number with value 0 or 127 to set button state:
- `CC 20, value 127` → Button 1 turns ON (LED lights up)
- `CC 20, value 0` → Button 1 turns OFF (LED off/dim)

## Use Cases

- **Gig Performer / MainStage** — Sync button states with plugin bypass
- **Ableton Live** — Control track mutes/solos with visual feedback
- **Guitar Rig / Helix Native** — Effect on/off with LED confirmation
- **Any MIDI-capable host** — Generic CC control with bidirectional sync

## Repository Layout

| Path | Purpose |
|------|---------|
| `firmware/dev/` | Active firmware (copy to device) |
| `config-editor/` | Desktop config editor app (Tauri + Svelte) |
| `firmware/original_helmut/` | Helmut Keller's original code (reference) |
| `docs/` | Hardware specs, design docs |
| `tools/` | Helper scripts |

## License

Copyright © 2026 Maximilian Cascone. All rights reserved.

You may use this firmware freely for personal or commercial performances. Redistribution of modified versions requires permission. See [LICENSE](LICENSE) for details.

## Attribution

This project builds on work by **Helmut Keller** ([hfrk.de](https://hfrk.de)), whose original firmware demonstrated bidirectional MIDI on the MIDI Captain. His code is preserved in `firmware/original_helmut/` as a reference.

---

## Questions, Comments, Suggestions are welcome

[Open an issue](https://github.com/MC-Music-Workshop/midi-captain-max/issues) or check [AGENTS.md](AGENTS.md) for developer documentation.

