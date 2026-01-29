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

# =============================================================================
# Device Detection
# =============================================================================

# Try to load device config, default to STD10
try:
    with open("/config.json", "r") as f:
        _cfg = json.load(f)
        DEVICE_TYPE = _cfg.get("device", "std10").lower()
except:
    DEVICE_TYPE = "std10"

print(f"Device type: {DEVICE_TYPE}")

if DEVICE_TYPE == "mini6":
    from devices.mini6 import (
        LED_PIN, LED_COUNT, SWITCH_PINS, switch_to_led,
        TFT_DC_PIN, TFT_CS_PIN, TFT_SCK_PIN, TFT_MOSI_PIN,
        DISPLAY_WIDTH, DISPLAY_HEIGHT, DISPLAY_ROWSTART, DISPLAY_ROTATION,
        ENCODER_A_PIN, ENCODER_B_PIN, EXP1_PIN, EXP2_PIN, BATTERY_PIN
    )
    BUTTON_COUNT = 6
    HAS_ENCODER = False
    HAS_EXPRESSION = False
else:
    # Default to STD10
    from devices.std10 import (
        LED_PIN, LED_COUNT, SWITCH_PINS, switch_to_led,
        TFT_DC_PIN, TFT_CS_PIN, TFT_SCK_PIN, TFT_MOSI_PIN,
        DISPLAY_WIDTH, DISPLAY_HEIGHT, DISPLAY_ROWSTART, DISPLAY_ROTATION,
        ENCODER_A_PIN, ENCODER_B_PIN, EXP1_PIN, EXP2_PIN, BATTERY_PIN
    )
    BUTTON_COUNT = 10
    HAS_ENCODER = True
    HAS_EXPRESSION = True

# =============================================================================
# Version
# =============================================================================

VERSION = "1.0.0-alpha.3"
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
                for i in range(BUTTON_COUNT)
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


# Initialize switches
switches = [Switch(pin) for pin in SWITCH_PINS]
print(f"Initialized {len(switches)} switches")

# Encoder (STD10 only)
if HAS_ENCODER:
    encoder = rotaryio.IncrementalEncoder(ENCODER_A_PIN, ENCODER_B_PIN, divisor=2)
    encoder_last_pos = 0
else:
    encoder = None
    encoder_last_pos = 0

# Will be set after config is loaded
encoder_value = 0
encoder_push_state = False  # For toggle mode

# Expression pedals (STD10 only)
if HAS_EXPRESSION:
    exp1 = AnalogIn(EXP1_PIN)
    exp2 = AnalogIn(EXP2_PIN)
    battery = AnalogIn(BATTERY_PIN)
    # Expression pedal calibration (auto-calibrates during use)
    exp1_min, exp1_max = 2048, 63488
    exp2_min, exp2_max = 2048, 63488
    exp1_last, exp2_last = 0, 0
else:
    exp1 = exp2 = battery = None
    exp1_min = exp1_max = exp1_last = 0
    exp2_min = exp2_max = exp2_last = 0

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

# Encoder config (from config.json or defaults)
enc_config = config.get("encoder", {"enabled": True, "cc": 11, "label": "ENC", "min": 0, "max": 127, "initial": 64})
enc_push_config = enc_config.get("push", {"enabled": True, "cc": 14, "label": "PUSH", "mode": "momentary"})

CC_ENCODER = enc_config.get("cc", 11)
CC_ENCODER_PUSH = enc_push_config.get("cc", 14)
ENC_MIN = enc_config.get("min", 0)
ENC_MAX = enc_config.get("max", 127)
ENC_INITIAL = enc_config.get("initial", 64)
ENC_ENABLED = enc_config.get("enabled", True) and HAS_ENCODER
ENC_PUSH_ENABLED = enc_push_config.get("enabled", True) and HAS_ENCODER
ENC_PUSH_MODE = enc_push_config.get("mode", "momentary")

# Stepped mode: steps = number of discrete output values (slots)
# e.g., steps=5 means output CC values 0,1,2,3,4
# Internal encoder tracks 0-127, output only changes at slot boundaries
ENC_STEPS = enc_config.get("steps", None)

# Expression pedal config (from config.json or defaults)
exp_config = config.get("expression", {})
exp1_config = exp_config.get("exp1", {"enabled": True, "cc": 12, "label": "EXP1", "min": 0, "max": 127, "polarity": "normal", "threshold": 2})
exp2_config = exp_config.get("exp2", {"enabled": True, "cc": 13, "label": "EXP2", "min": 0, "max": 127, "polarity": "normal", "threshold": 2})

CC_EXP1 = exp1_config.get("cc", 12)
CC_EXP2 = exp2_config.get("cc", 13)

# =============================================================================
# State
# =============================================================================

button_states = [False] * BUTTON_COUNT  # Toggle state for each button
encoder_value = ENC_INITIAL  # Internal value 0-127
encoder_slot = -1  # Current slot (set on first change)

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

# Button labels - layout depends on device
button_labels = []
button_boxes = []
top_row_y = 5
bottom_row_y = 205

if BUTTON_COUNT == 6:
    # Mini6: 3 buttons per row, wider spacing
    button_width = 70
    button_height = 30
    button_spacing = 80
    row_size = 3
else:
    # STD10: 5 buttons per row
    button_width = 46
    button_height = 30
    button_spacing = 48
    row_size = 5

for i in range(BUTTON_COUNT):
    btn_config = buttons[i] if i < len(buttons) else {"label": str(i + 1), "color": "white"}

    if i < row_size:
        x = 1 + i * button_spacing
        y = top_row_y
    else:
        x = 1 + (i - row_size) * button_spacing
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

# Expression pedal display (below status, only if device has expression)
exp1_label = None
exp2_label = None
if HAS_EXPRESSION:
    exp1_lbl_text = exp1_config.get("label", "EXP1")
    exp1_label = label.Label(
        BUTTON_FONT,
        text=f"{exp1_lbl_text}: ---",
        color=0x888888,
        anchor_point=(0.5, 0.5),
        anchored_position=(70, 150),
    )
    main_group.append(exp1_label)
    
    exp2_lbl_text = exp2_config.get("label", "EXP2")
    exp2_label = label.Label(
        BUTTON_FONT,
        text=f"{exp2_lbl_text}: ---",
        color=0x888888,
        anchor_point=(0.5, 0.5),
        anchored_position=(170, 150),
    )
    main_group.append(exp2_label)

display.show(main_group)

# =============================================================================
# LED & Display Helpers
# =============================================================================


def set_button_state(switch_idx, on):
    """Update LED and display for a button (1-indexed)."""
    idx = switch_idx - 1
    if idx < 0 or idx >= BUTTON_COUNT:
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
    """Initialize all LEDs to off/dim state."""
    for i in range(1, BUTTON_COUNT + 1):
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
    # STD10: index 0 is encoder push, 1-10 are footswitches
    # Mini6: indices 0-5 are footswitches (no encoder)
    start_idx = 1 if HAS_ENCODER else 0
    for i in range(start_idx, len(switches)):
        sw = switches[i]
        changed, pressed = sw.changed()

        if changed:
            # Convert to 1-indexed button number
            btn_num = i if HAS_ENCODER else i + 1
            idx = btn_num - 1
            btn_config = buttons[idx] if idx < len(buttons) else {"cc": 20 + idx}
            cc = btn_config.get("cc", 20 + idx)
            mode = btn_config.get("mode", "toggle")  # "toggle" or "momentary"

            if mode == "momentary":
                # Momentary: 127 on press, 0 on release
                val = 127 if pressed else 0
                set_button_state(btn_num, pressed)
                midi.send(ControlChange(cc, val))
                print(f"[MIDI TX] CC{cc}={val} (switch {btn_num}, momentary)")
                status_label.text = f"TX CC{cc}={val}"
            elif pressed:
                # Toggle: only act on press, flip state
                new_state = not button_states[idx]
                set_button_state(btn_num, new_state)
                val = 127 if new_state else 0
                midi.send(ControlChange(cc, val))
                print(f"[MIDI TX] CC{cc}={val} (switch {btn_num}, toggle)")
                status_label.text = f"TX CC{cc}={'ON' if new_state else 'OFF'}"


def handle_encoder_button():
    """Handle encoder push button."""
    global encoder_push_state
    
    if not ENC_PUSH_ENABLED:
        return
    
    sw = switches[0]  # Encoder push is switch index 0
    changed, pressed = sw.changed()
    if changed:
        if ENC_PUSH_MODE == "toggle":
            # Toggle mode: flip state on press only
            if pressed:
                encoder_push_state = not encoder_push_state
                cc_val = 127 if encoder_push_state else 0
                midi.send(ControlChange(CC_ENCODER_PUSH, cc_val))
                status_label.text = f"TX CC{CC_ENCODER_PUSH}={'ON' if encoder_push_state else 'OFF'}"
        else:
            # Momentary mode: send on press and release
            cc_val = 127 if pressed else 0
            midi.send(ControlChange(CC_ENCODER_PUSH, cc_val))
            status_label.text = f"TX CC{CC_ENCODER_PUSH}={cc_val}"


def handle_encoder():
    """Handle rotary encoder."""
    global encoder_last_pos, encoder_value, encoder_slot
    
    if not ENC_ENABLED:
        return

    pos = encoder.position
    if pos != encoder_last_pos:
        delta = pos - encoder_last_pos
        encoder_last_pos = pos
        
        # Update internal value (always 0-127)
        encoder_value = max(0, min(127, encoder_value + delta))
        
        if ENC_STEPS and ENC_STEPS > 1:
            # Stepped mode: calculate which slot we're in
            # Slot boundaries: 0-25=slot0, 26-50=slot1, etc. for 5 slots
            slot_size = 128 // ENC_STEPS
            new_slot = min(encoder_value // slot_size, ENC_STEPS - 1)
            
            if new_slot != encoder_slot:
                encoder_slot = new_slot
                # Output CC is the slot number (0 to steps-1)
                midi.send(ControlChange(CC_ENCODER, encoder_slot))
                status_label.text = f"ENC slot {encoder_slot}"
        else:
            # Normal mode: send every change
            midi.send(ControlChange(CC_ENCODER, encoder_value))
            status_label.text = f"ENC={encoder_value}"


def handle_expression():
    """Handle expression pedals."""
    global exp1_min, exp1_max, exp1_last
    global exp2_min, exp2_max, exp2_last

    if not HAS_EXPRESSION:
        return

    # Expression 1
    if exp1_config.get("enabled", True) and exp1 is not None:
        raw1 = exp1.value
        exp1_max = max(raw1, exp1_max)
        exp1_min = min(raw1, exp1_min)
        
        if exp1_max > exp1_min:
            # Map to 0-127, then apply config range
            normalized = (raw1 - exp1_min) / (exp1_max - exp1_min)
            if exp1_config.get("polarity", "normal") == "reverse":
                normalized = 1.0 - normalized
            out_min = exp1_config.get("min", 0)
            out_max = exp1_config.get("max", 127)
            val1 = int(out_min + normalized * (out_max - out_min))
            val1 = max(0, min(127, val1))  # Clamp to valid MIDI range
            
            # Hysteresis: only send if change exceeds threshold
            threshold = exp1_config.get("threshold", 2)
            if abs(val1 - exp1_last) >= threshold:
                exp1_last = val1
                midi.send(ControlChange(CC_EXP1, val1))
                lbl = exp1_config.get("label", "EXP1")
                print(f"[{lbl}] CC{CC_EXP1}={val1}")
                # Update display
                if exp1_label:
                    exp1_label.text = f"{lbl}: {val1:3d}"

    # Expression 2
    if exp2_config.get("enabled", True) and exp2 is not None:
        raw2 = exp2.value
        exp2_max = max(raw2, exp2_max)
        exp2_min = min(raw2, exp2_min)
        
        if exp2_max > exp2_min:
            # Map to 0-127, then apply config range
            normalized = (raw2 - exp2_min) / (exp2_max - exp2_min)
            if exp2_config.get("polarity", "normal") == "reverse":
                normalized = 1.0 - normalized
            out_min = exp2_config.get("min", 0)
            out_max = exp2_config.get("max", 127)
            val2 = int(out_min + normalized * (out_max - out_min))
            val2 = max(0, min(127, val2))  # Clamp to valid MIDI range
            
            # Hysteresis: only send if change exceeds threshold
            threshold = exp2_config.get("threshold", 2)
            if abs(val2 - exp2_last) >= threshold:
                exp2_last = val2
                midi.send(ControlChange(CC_EXP2, val2))
                lbl = exp2_config.get("label", "EXP2")
                print(f"[{lbl}] CC{CC_EXP2}={val2}")
                # Update display
                if exp2_label:
                    exp2_label.text = f"{lbl}: {val2:3d}"


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
if HAS_ENCODER:
    if ENC_STEPS and ENC_STEPS > 1:
        print(f"Encoder: CC{CC_ENCODER} ({ENC_STEPS} slots, outputs 0-{ENC_STEPS-1})")
    else:
        print(f"Encoder: CC{CC_ENCODER} (range {ENC_MIN}-{ENC_MAX}, init={ENC_INITIAL})")
    print(f"Encoder Push: CC{CC_ENCODER_PUSH} ({ENC_PUSH_MODE})")
if HAS_EXPRESSION:
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
    if HAS_ENCODER:
        handle_encoder_button()
        handle_encoder()
    if HAS_EXPRESSION:
        handle_expression()
