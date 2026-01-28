"""
MIDI Captain Custom Firmware - MVP

Config-driven, bidirectional MIDI firmware for Paint Audio MIDI Captain controllers.

Features:
- JSON configuration for button labels, CC numbers, and colors
- Bidirectional MIDI: host controls LED/display state, device sends switch/encoder events
- Toggle mode: local state for instant feedback, host override when it speaks
- Asyncio-based concurrent handling of MIDI, switches, encoder, expression pedals

Hardware: STD10 (10 switches, encoder, 2 expression inputs, ST7789 display, 30 NeoPixels)

Author: Max Cascone (based on work by Helmut Keller)
Date: 2026-01-27
"""

print("\n=== MIDI CAPTAIN CUSTOM FIRMWARE ===\n")

import board
import neopixel
import time
import displayio
import digitalio
import usb_midi
import busio
import rotaryio
import json
from analogio import AnalogIn
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
import terminalio
from adafruit_st7789 import ST7789
import adafruit_midi
from adafruit_midi.control_change import ControlChange

# Import device constants
from devices.std10 import (
    LED_PIN, LED_COUNT, SWITCH_PINS, switch_to_led,
    TFT_DC_PIN, TFT_CS_PIN, TFT_SCK_PIN, TFT_MOSI_PIN,
    DISPLAY_WIDTH, DISPLAY_HEIGHT, DISPLAY_ROWSTART, DISPLAY_ROTATION,
    ENCODER_A_PIN, ENCODER_B_PIN, EXP1_PIN, EXP2_PIN, BATTERY_PIN
)

# =============================================================================
# Version
# =============================================================================

VERSION = "1.0.0-alpha.2"
print(f"Version: {VERSION}")

# =============================================================================
# Color Palette
# =============================================================================

COLORS = {
    "red": (255, 0, 0),
    "green": (0, 255, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "orange": (255, 128, 0),
    "purple": (128, 0, 255),
    "white": (255, 255, 255),
    "off": (0, 0, 0),
}


def get_color(name):
    """Get RGB tuple from color name, with fallback to white."""
    return COLORS.get(name.lower(), COLORS["white"])


def dim_color(rgb, factor=0.15):
    """Return a dimmed version of an RGB color."""
    return tuple(int(c * factor) for c in rgb)


def rgb_to_hex(rgb):
    """Convert RGB tuple to hex integer for display."""
    return (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]


def get_off_color(color_rgb, off_mode="dim"):
    """Get the color to use when button is off.
    
    Args:
        color_rgb: The button's on-state RGB color
        off_mode: "dim" for dimmed color, "off" for completely off
    """
    if off_mode == "off":
        return (0, 0, 0)
    return dim_color(color_rgb)

# =============================================================================
# Configuration
# =============================================================================


def load_config(path="/config.json"):
    """Load button configuration from JSON file."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Config load error: {e}, using defaults")
        return {
            "buttons": [
                {"label": str(i + 1), "cc": 20 + i, "color": "white"}
                for i in range(10)
            ]
        }


config = load_config()
buttons = config.get("buttons", [])
print(f"Loaded {len(buttons)} button configs")

# =============================================================================
# Fonts
# =============================================================================

try:
    STATUS_FONT = bitmap_font.load_font("/fonts/PTSans-Regular-20.pcf")
    print("Loaded PCF status font")
except Exception as e:
    print(f"Font load failed: {e}")
    STATUS_FONT = terminalio.FONT

BUTTON_FONT = terminalio.FONT  # Built-in works well for narrow button boxes

# =============================================================================
# Hardware Init
# =============================================================================

# NeoPixels
pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=0.3, auto_write=False)

# Display
displayio.release_displays()
spi = busio.SPI(clock=TFT_SCK_PIN, MOSI=TFT_MOSI_PIN)
display_bus = displayio.FourWire(spi, command=TFT_DC_PIN, chip_select=TFT_CS_PIN)
display = ST7789(
    display_bus,
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    rowstart=DISPLAY_ROWSTART,
    rotation=DISPLAY_ROTATION,
)

# =============================================================================
# Switch Class
# =============================================================================


class Switch:
    """Footswitch with state tracking."""

    def __init__(self, pin):
        self.io = digitalio.DigitalInOut(pin)
        self.io.direction = digitalio.Direction.INPUT
        self.io.pull = digitalio.Pull.UP
        self.last_state = True  # Pull-up: True = not pressed

    @property
    def pressed(self):
        return not self.io.value

    def changed(self):
        """Returns (changed, pressed) tuple."""
        current = self.pressed
        changed = current != self.last_state
        self.last_state = current
        return changed, current


# Initialize switches (index 0 = encoder push, 1-10 = footswitches)
switches = [Switch(pin) for pin in SWITCH_PINS]
print(f"Initialized {len(switches)} switches")

# Encoder
encoder = rotaryio.IncrementalEncoder(ENCODER_A_PIN, ENCODER_B_PIN, divisor=2)
encoder_last_pos = 0
encoder_value = 64  # Start at middle

# Expression pedals
exp1 = AnalogIn(EXP1_PIN)
exp2 = AnalogIn(EXP2_PIN)
battery = AnalogIn(BATTERY_PIN)

# Expression pedal calibration (auto-calibrates during use)
exp1_min, exp1_max = 2048, 63488
exp2_min, exp2_max = 2048, 63488
exp1_last, exp2_last = 0, 0

# Battery voltage low-pass filter
vbat_filtered = 0.0
vbat_alpha = 0.01

# =============================================================================
# MIDI Setup
# =============================================================================

midi = adafruit_midi.MIDI(
    midi_in=usb_midi.ports[0],
    midi_out=usb_midi.ports[1],
    in_channel=0,
    out_channel=0,
    in_buf_size=64,
)
print("MIDI initialized")

# CC assignments
CC_ENCODER = 11
CC_EXP1 = 12
CC_EXP2 = 13
CC_ENCODER_PUSH = 14
# Switches 1-10 use CC numbers from config (default 20-29)

# =============================================================================
# State
# =============================================================================

button_states = [False] * 10  # Toggle state for each button

# =============================================================================
# Display Setup
# =============================================================================

main_group = displayio.Group()

# Background
bg_bitmap = displayio.Bitmap(240, 240, 1)
bg_palette = displayio.Palette(1)
bg_palette[0] = 0x000000
bg_sprite = displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette, x=0, y=0)
main_group.append(bg_sprite)

# Button labels - 2 rows matching physical layout
button_labels = []
button_boxes = []
button_width = 46
button_height = 30
button_spacing = 48
top_row_y = 5
bottom_row_y = 205

for i in range(10):
    btn_config = buttons[i] if i < len(buttons) else {"label": str(i + 1), "color": "white"}

    if i < 5:
        x = 1 + i * button_spacing
        y = top_row_y
    else:
        x = 1 + (i - 5) * button_spacing
        y = bottom_row_y

    color_rgb = get_color(btn_config.get("color", "white"))
    off_mode = btn_config.get("off_mode", "dim")  # "dim" or "off"
    off_color = get_off_color(color_rgb, off_mode)

    # Create box background with border
    box_bitmap = displayio.Bitmap(button_width, button_height, 2)
    box_palette = displayio.Palette(2)
    box_palette[0] = 0x000000
    box_palette[1] = rgb_to_hex(off_color)  # Start in off state

    for bx in range(button_width):
        box_bitmap[bx, 0] = 1
        box_bitmap[bx, button_height - 1] = 1
    for by in range(button_height):
        box_bitmap[0, by] = 1
        box_bitmap[button_width - 1, by] = 1

    box_sprite = displayio.TileGrid(box_bitmap, pixel_shader=box_palette, x=x, y=y)
    button_boxes.append((box_sprite, box_palette))
    main_group.append(box_sprite)

    # Label
    lbl = label.Label(
        BUTTON_FONT,
        text=btn_config.get("label", str(i + 1))[:6],
        color=rgb_to_hex(off_color),
        anchor_point=(0.5, 0.5),
        anchored_position=(x + button_width // 2, y + button_height // 2),
    )
    button_labels.append(lbl)
    main_group.append(lbl)

# Status area (center)
status_label = label.Label(
    STATUS_FONT,
    text="Ready",
    color=0xFFFFFF,
    anchor_point=(0.5, 0.5),
    anchored_position=(120, 120),
)
main_group.append(status_label)

display.show(main_group)

# =============================================================================
# LED & Display Helpers
# =============================================================================


def set_button_state(switch_idx, on):
    """Update LED and display for a button (1-indexed)."""
    idx = switch_idx - 1
    if idx < 0 or idx >= 10:
        return

    button_states[idx] = on
    btn_config = buttons[idx] if idx < len(buttons) else {"color": "white"}
    color_rgb = get_color(btn_config.get("color", "white"))
    off_mode = btn_config.get("off_mode", "dim")  # "dim" or "off"

    # Update LED
    led_idx = switch_to_led(switch_idx)
    if led_idx is not None:
        rgb = color_rgb if on else get_off_color(color_rgb, off_mode)
        base = led_idx * 3
        for j in range(3):
            if base + j < LED_COUNT:
                pixels[base + j] = rgb
        pixels.show()

    # Update display
    if idx < len(button_labels):
        color_hex = rgb_to_hex(color_rgb if on else get_off_color(color_rgb, off_mode))
        button_labels[idx].color = color_hex
        if idx < len(button_boxes):
            _, box_palette = button_boxes[idx]
            box_palette[1] = color_hex


def init_leds():
    """Initialize all LEDs to dim state."""
    for i in range(1, 11):
        set_button_state(i, False)


# =============================================================================
# Polling Functions
# =============================================================================


def handle_midi():
    """Handle incoming MIDI messages."""
    msg = midi.receive()
    if msg and isinstance(msg, ControlChange):
        cc = msg.control
        val = msg.value
        print(f"[MIDI RX] CC{cc}={val}")

        # Check if this CC matches any button
        for i, btn_config in enumerate(buttons):
            if btn_config.get("cc") == cc:
                on = val > 63
                set_button_state(i + 1, on)
                status_label.text = f"RX CC{cc}={val}"
                break


def handle_switches():
    """Handle footswitch presses."""
    for i in range(1, 11):  # Footswitches 1-10
        sw = switches[i]
        changed, pressed = sw.changed()

        if changed:
            idx = i - 1
            btn_config = buttons[idx] if idx < len(buttons) else {"cc": 20 + idx}
            cc = btn_config.get("cc", 20 + idx)
            mode = btn_config.get("mode", "toggle")  # "toggle" or "momentary"

            if mode == "momentary":
                # Momentary: 127 on press, 0 on release
                val = 127 if pressed else 0
                set_button_state(i, pressed)
                midi.send(ControlChange(cc, val))
                print(f"[MIDI TX] CC{cc}={val} (switch {i}, momentary)")
                status_label.text = f"TX CC{cc}={val}"
            elif pressed:
                # Toggle: only act on press, flip state
                new_state = not button_states[idx]
                set_button_state(i, new_state)
                val = 127 if new_state else 0
                midi.send(ControlChange(cc, val))
                print(f"[MIDI TX] CC{cc}={val} (switch {i}, toggle)")
                status_label.text = f"TX CC{cc}={'ON' if new_state else 'OFF'}"


def handle_encoder_button():
    """Handle encoder push button."""
    sw = switches[0]  # Encoder push is switch index 0
    changed, pressed = sw.changed()
    if changed:
        cc_val = 127 if pressed else 0
        midi.send(ControlChange(CC_ENCODER_PUSH, cc_val))
        status_label.text = f"TX CC{CC_ENCODER_PUSH}={cc_val}"


def handle_encoder():
    """Handle rotary encoder."""
    global encoder_last_pos, encoder_value

    pos = encoder.position
    if pos != encoder_last_pos:
        delta = pos - encoder_last_pos
        encoder_last_pos = pos
        encoder_value = max(0, min(127, encoder_value + delta))
        midi.send(ControlChange(CC_ENCODER, encoder_value))
        status_label.text = f"ENC={encoder_value}"


def handle_expression():
    """Handle expression pedals."""
    global exp1_min, exp1_max, exp1_last
    global exp2_min, exp2_max, exp2_last

    # Expression 1 with auto-calibration
    raw1 = exp1.value
    exp1_max = max(raw1, exp1_max)
    exp1_min = min(raw1, exp1_min)
    if exp1_max > exp1_min:
        val1 = int((raw1 - exp1_min) / (exp1_max - exp1_min) * 127)
        if val1 != exp1_last and exp1_max > 63488:
            exp1_last = val1
            midi.send(ControlChange(CC_EXP1, val1))

    # Expression 2 with auto-calibration
    raw2 = exp2.value
    exp2_max = max(raw2, exp2_max)
    exp2_min = min(raw2, exp2_min)
    if exp2_max > exp2_min:
        val2 = int((raw2 - exp2_min) / (exp2_max - exp2_min) * 127)
        if val2 != exp2_last and exp2_max > 63488:
            exp2_last = val2
            midi.send(ControlChange(CC_EXP2, val2))


# =============================================================================
# Startup
# =============================================================================

print("Initializing...")
init_leds()

# Startup animation
pixels.fill((0, 255, 0))
pixels.show()
time.sleep(0.5)
init_leds()

# Show CC mapping info
print(f"Encoder: CC{CC_ENCODER}")
print(f"Expression 1: CC{CC_EXP1}")
print(f"Expression 2: CC{CC_EXP2}")
for i, btn in enumerate(buttons):
    print(f"Button {i+1}: CC{btn.get('cc', 20+i)} ({btn.get('label', '')})")

print("\nRunning...")

# =============================================================================
# Main Loop
# =============================================================================

while True:
    handle_midi()
    handle_switches()
    handle_encoder_button()
    handle_encoder()
    handle_expression()
