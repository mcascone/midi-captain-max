# MIDI Captain Custom Firmware

**Bidirectional, config-driven CircuitPython firmware for Paint Audio MIDI Captain foot controllers.**

> ⚠️ **Alpha Release** — Core features working, more coming soon.

## What It Does

This firmware transforms your MIDI Captain into a **bidirectional MIDI controller** where your host software (DAW, plugin host) can control the device's LEDs and display, not just receive button presses.

**Key Features:**
- 🔄 **Bidirectional MIDI** — Host sends CC to update LEDs/display state
- ⚙️ **Config-driven** — Customize button labels, CC numbers, colors via JSON
- 🎨 **Visual feedback** — LEDs and LCD reflect actual host state
- 🎛️ **Full input support** — Footswitches, rotary encoder, expression pedals
- 🎸 **Stage-ready** — No unexpected resets, no crashes, no surprises

## Supported Devices

| Device | Status |
|--------|--------|
| MIDI Captain STD10 (10-switch) | ✅ Fully working |
| MIDI Captain Mini6 (6-switch) | 🚧 Planned |

## Quick Start

### Requirements
- Paint Audio MIDI Captain (STD10)
- CircuitPython 7.3.1+ installed on device
- Required libraries in `lib/` folder (see [Installation](#installation))

### Installation

1. **Install CircuitPython** (if not already):
   - Download [CircuitPython for Raspberry Pi Pico](https://circuitpython.org/board/raspberry_pi_pico/)
   - Hold BOOTSEL while plugging in USB
   - Copy `.uf2` file to `RPI-RP2` drive

2. **Install required libraries** via [circup](https://github.com/adafruit/circup):
   ```bash
   pip install circup
   circup install adafruit_midi adafruit_display_text adafruit_st7789 neopixel adafruit_debouncer
   ```

3. **Copy firmware files**:
   ```bash
   cp firmware/dev/code.py /Volumes/CIRCUITPY/
   cp firmware/dev/boot.py /Volumes/CIRCUITPY/
   cp firmware/dev/config.json /Volumes/CIRCUITPY/
   cp -r firmware/dev/devices /Volumes/CIRCUITPY/
   ```

4. **Power cycle** the device (required for boot.py to take effect)

## Configuration

Edit `config.json` on the device to customize your setup:

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

| Field | Description |
|-------|-------------|
| `label` | Text shown on LCD (max ~6 chars) |
| `cc` | MIDI CC number sent on press (0-127) |
| `color` | RGB color for LED when ON `[R, G, B]` |

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
Send CC 20-29 with value 0 or 127 to set button state:
- `CC 20, value 127` → Button 1 turns ON (LED lights up)
- `CC 20, value 0` → Button 1 turns OFF (LED off)

## Use Cases

- **Gig Performer / MainStage** — Sync button states with plugin bypass
- **Ableton Live** — Control track mutes/solos with visual feedback
- **Guitar Rig / Helix Native** — Effect on/off with LED confirmation
- **Any MIDI-capable host** — Generic CC control with bidirectional sync

## Repository Layout

| Path | Purpose |
|------|---------|
| `firmware/dev/` | Active firmware (copy to device) |
| `firmware/original_helmut/` | Helmut Keller's original code (reference) |
| `docs/` | Hardware specs, design docs |
| `tools/` | Helper scripts |

## Attribution

This project builds on work by **Helmut Keller** ([hfrk.de](https://hfrk.de)), whose original firmware demonstrated bidirectional MIDI on the MIDI Captain. His code is preserved in `firmware/original_helmut/` as a reference.

## License

Copyright © 2026 Maximilian Cascone. All rights reserved.

You may use this firmware freely for personal or commercial performances. Redistribution of modified versions requires permission. See [LICENSE](LICENSE) for details.

---

**Questions?** Open an issue or check [AGENTS.md](AGENTS.md) for developer documentation.

