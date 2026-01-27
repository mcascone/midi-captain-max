# MIDI Captain Hardware Reference

> **Last Updated:** January 26, 2026  
> **Verified On:** STD10 hardware with CircuitPython 7.3.1

This document contains verified hardware specifications for Paint Audio MIDI Captain devices.
For historical context on how these were discovered, see [midicaptain_reverse_engineering_handoff.txt](midicaptain_reverse_engineering_handoff.txt).

---

## Platform

All MIDI Captain variants use:
- **MCU:** RP2040 (Raspberry Pi Pico platform)
- **CircuitPython:** 7.3.1 (verified)
- **Board ID:** `raspberry_pi_pico`

---

## STD10 (10-Switch)

### Physical Layout

```
┌─────────────────────────────────────────────────────────┐
│                      [DISPLAY]                          │
│                       240×240                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐               │
│   │ 1 │   │ 2 │   │ 3 │   │ 4 │   │ ▼ │   [ENCODER]   │
│   └───┘   └───┘   └───┘   └───┘   └───┘               │
│   LED 0   LED 1   LED 2   LED 3   LED 4               │
│                                                         │
│   ┌───┐   ┌───┐   ┌───┐   ┌───┐   ┌───┐               │
│   │ A │   │ B │   │ C │   │ D │   │ ▲ │               │
│   └───┘   └───┘   └───┘   └───┘   └───┘               │
│   LED 5   LED 6   LED 7   LED 8   LED 9               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Switch Mapping

| Index | Label | GPIO Pin | CC Number | LED Index |
|-------|-------|----------|-----------|-----------|
| 0 | Encoder Push | GP0 | CC14 | None |
| 1 | 1 | GP1 | CC20 | 0 |
| 2 | 2 | GP25 | CC21 | 1 |
| 3 | 3 | GP24 | CC22 | 2 |
| 4 | 4 | GP23 | CC23 | 3 |
| 5 | Down (▼) | GP20 | CC24 | 4 |
| 6 | A | GP9 | CC25 | 5 |
| 7 | B | GP10 | CC26 | 6 |
| 8 | C | GP11 | CC27 | 7 |
| 9 | D | GP18 | CC28 | 8 |
| 10 | Up (▲) | GP19 | CC29 | 9 |

**Note:** Switch index 0 (encoder push) has no LED. Switch-to-LED conversion: `led_idx = switch_idx - 1` for indices 1-10.

### NeoPixels

- **Pin:** GP7
- **Count:** 30 (3 LEDs per switch × 10 switches)
- **Chain Order:** LEDs 0-4 = top row, LEDs 5-9 = bottom row
- **Per-Switch:** 3 consecutive pixels (e.g., switch 1 = pixels 0-2)

### Rotary Encoder

- **Pin A:** GP2
- **Pin B:** GP3
- **Push:** GP0 (same as switch index 0)

### Expression Pedals

- **EXP1:** A1 (analog input)
- **EXP2:** A2 (analog input)
- **Battery:** A3 (analog input, for voltage monitoring)

### Display

- **Controller:** ST7789
- **Resolution:** 240 × 240 pixels
- **Interface:** SPI

| Signal | GPIO Pin |
|--------|----------|
| DC | GP12 |
| CS | GP13 |
| SCK/CLK | GP14 |
| MOSI | GP15 |
| PWM (backlight) | GP8 (declared, not used in code) |
| Reset | None (not connected) |

**ST7789 Parameters:**
```python
ST7789(spi, width=240, height=240, rowstart=80, rotation=180)
```

### Serial MIDI

- **TX:** GP16
- **RX:** GP17
- **Baud:** 31250
- **Timeout:** 0.003s

---

## Mini6 (6-Switch)

### Physical Layout

```
┌─────────────────────────────────────┐
│            [DISPLAY]                │
│             240×240                 │
├─────────────────────────────────────┤
│                                     │
│   ┌───┐       ┌───┐       ┌───┐    │
│   │TL │       │TM │       │TR │    │
│   └───┘       └───┘       └───┘    │
│                                     │
│   ┌───┐       ┌───┐       ┌───┐    │
│   │BL │       │BM │       │BR │    │
│   └───┘       └───┘       └───┘    │
│                                     │
└─────────────────────────────────────┘
```

### Switch Mapping

| Position | GPIO Pin | Notes |
|----------|----------|-------|
| Top-Left (TL) | GP1 | Also used as boot mode pin |
| Top-Middle (TM) | board.LED | Repurposed as input |
| Top-Right (TR) | board.VBUS_SENSE | Repurposed as input |
| Bottom-Left (BL) | GP9 | — |
| Bottom-Middle (BM) | GP10 | — |
| Bottom-Right (BR) | GP11 | — |

**Note:** `board.LED` and `board.VBUS_SENSE` are unusual pin assignments — the hardware intentionally repurposes these as footswitch inputs.

### NeoPixels

- **Pin:** GP7 (same as STD10)
- **Count:** 18 (3 LEDs per switch × 6 switches)

### Display

Same parameters as STD10:
- ST7789, 240×240, rowstart=80, rotation=180
- Same SPI pins (GP12-15)

### Not Present

- No rotary encoder
- No expression pedal inputs (TBD — may need probing)

---

## Boot Behavior

All devices use `boot.py` with GP1 as a mode pin:

```python
# If GP1 is True at boot: disable USB drive, remount RW
# If GP1 is False: enable USB drive as MIDICAPTAIN, remount RO
```

- **Volume Label:** `CIRCUITPY` (changed from MIDICAPTAIN for extension compatibility)
- **Autoreload:** Disabled by default for performance
- GP1 is read at boot but can be used as a switch afterward

---

## CircuitPython Notes

### Version Compatibility

- **Target:** CircuitPython 7.x (7.3.1 verified)
- **Display API:** Use `display.show(group)` not `display.root_group` (7.x compatibility)
- **USB CDC:** Disconnects on reset — use auto-reconnect serial workflows

### Required Libraries

Install via `circup install -r requirements-circuitpython.txt`:
- `adafruit_midi`
- `adafruit_display_text`
- `adafruit_st7789`
- `neopixel`

---

## MIDI Protocol

### USB MIDI

- Device appears as USB MIDI device
- Uses `adafruit_midi` library
- Ports: `usb_midi.ports[0]` (in), `usb_midi.ports[1]` (out)

### CC Assignments (Current Demo)

| CC | Direction | Purpose |
|----|-----------|---------|
| 20-29 | TX/RX | Switches 1-10 (bidirectional) |

**TX (device → host):** 127 on press, 0 on release  
**RX (host → device):** >63 = LED on, ≤63 = LED dim/off

### Helmut's Original CC Mapping (Reference)

| CC | Purpose |
|----|---------|
| 11 | Rotary encoder |
| 12-13 | Expression pedals |
| 14 | Encoder push |
| 15-24 | Footswitches |
| 25 | Tuner mode toggle |

---

## Device Abstraction

Hardware constants are defined in `firmware/dev/devices/`:

```python
# firmware/dev/devices/std10.py
from devices.std10 import (
    LED_PIN, LED_COUNT,
    SWITCH_PINS,
    switch_to_led,
    DISPLAY_WIDTH, DISPLAY_HEIGHT,
    # ... etc
)
```

See [std10.py](../firmware/dev/devices/std10.py) for complete definitions.
