"""
MIDI Captain MAX Custom Firmware - MVP

Config-driven, bidirectional MIDI firmware for Paint Audio MIDI Captain controllers.

Features:
- JSON configuration for button labels, CC numbers, and colors
- Bidirectional MIDI: host controls LED/display state, device sends switch/encoder events
- Toggle mode: local state for instant feedback, host override when it speaks
- Automatic device detection (STD10 vs Mini6 based on hardware probing)

Hardware Variants:
- STD10: 10 switches, encoder, 2 expression inputs, ST7789 display, 30 NeoPixels
- Mini6: 6 switches, ST7789 display, 18 NeoPixels

Author: Max Cascone (based on work by Helmut Keller)
Date: 2026-01-27
"""

print("\n=== MIDI CAPTAIN MAX ===\n")

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
from adafruit_midi.program_change import ProgramChange
from adafruit_midi.note_on import NoteOn
from adafruit_midi.note_off import NoteOff

# Import core modules (testable logic)
from core.colors import COLORS, get_color, dim_color, rgb_to_hex, get_off_color, get_off_color_for_display
from core.config import load_config as _load_config_from_file, validate_config, get_display_config, get_button_state_config
from core.button import Switch, ButtonState

# =============================================================================
# Font Size Configuration
# =============================================================================
#
# Maps descriptive size names to font files and approximate heights.
# - "small": terminalio.FONT (built-in, ~8px) - compact button labels
# - "medium": PTSans-Regular-20.pcf (~20px) - readable status text
# - "large": PTSans-Bold-60.pcf (~60px) - large, bold display
#
FONT_SIZE_MAP = {
    "small": ("terminalio", 8),
    "medium": ("/fonts/PTSans-Regular-20.pcf", 20),
    "large": ("/fonts/PTSans-Bold-60.pcf", 60),
}

# =============================================================================
# Device Detection
# =============================================================================
#
# Two-tier detection strategy:
#   1. Config-based: read "device" field from /config.json (most reliable)
#   2. Hardware probe: check STD10-exclusive switch pins GP0/GP18/GP19/GP20
#
# The old approach (probing board.LED / board.VBUS_SENSE for Mini6) was broken
# because GP25 (board.LED) is also a switch pin on STD10, so both devices
# passed the probe and everything was detected as Mini6.
#
# Config loading priority:
#   1. /config.json if present (user customization - always wins)
#   2. /config-{device}.json (device-specific defaults)
#   3. Built-in fallback defaults
#
# =============================================================================


def _read_device_from_config():
    """Quick config.json read for just the device field.

    Returns "mini6", "std10", or None if not found/invalid.
    """
    try:
        with open("/config.json", "r") as f:
            device = json.load(f).get("device")
            if device in ("mini6", "std10"):
                return device
    except Exception:
        pass
    return None


def _probe_hardware():
    """Detect device type by probing STD10-exclusive switch pins.

    STD10 has physical switches on GP0 (encoder push), GP18 (switch D),
    GP19 (switch Up), GP20 (switch Down). Mini6 does not use these pins.
    With internal pull-ups, connected switches read HIGH when open.

    Returns "std10" if 3+ of 4 pins read HIGH, otherwise "mini6".
    """
    probe_pins = [board.GP0, board.GP18, board.GP19, board.GP20]
    count = 0
    for pin in probe_pins:
        try:
            t = digitalio.DigitalInOut(pin)
            t.direction = digitalio.Direction.INPUT
            t.pull = digitalio.Pull.UP
            if t.value:
                count += 1
            t.deinit()
        except Exception:
            pass
    return "std10" if count >= 3 else "mini6"


def detect_device_type():
    """Auto-detect device type.

    Priority:
      1. Explicit "device" field in /config.json
      2. Hardware pin probing (STD10-exclusive pins)
    """
    device = _read_device_from_config()
    if device:
        print(f"Device type from config: {device}")
        return device

    device = _probe_hardware()
    print(f"Device type from hardware probe: {device}")
    return device


# Detect device first, before loading any config
DETECTED_DEVICE = detect_device_type()
print(f"Hardware detected: {DETECTED_DEVICE}")

# Now load appropriate device module
if DETECTED_DEVICE == "mini6":
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

DEVICE_TYPE = DETECTED_DEVICE  # For compatibility

# =============================================================================
# Version
# =============================================================================


def _read_version():
    try:
        with open("/VERSION", "r") as f:
            return f.read().strip()
    except Exception:
        return "dev"


VERSION = _read_version()
print(f"Version: {VERSION}")

# =============================================================================
# Color Palette - imported from core/colors.py
# =============================================================================
# COLORS, get_color, dim_color, rgb_to_hex, get_off_color imported at top

# =============================================================================
# Configuration
# =============================================================================


def load_config():
    """Load button configuration from JSON file.

    Priority:
      1. /config.json (user customization - always wins)
      2. /config-{device}.json (device-specific defaults)
      3. Built-in fallback defaults
    """
    # Try user config
    cfg = _load_config_from_file("/config.json", button_count=BUTTON_COUNT)
    if "buttons" in cfg and len(cfg["buttons"]) > 0:
        print("Loaded config.json")
        return cfg

    # Try device-specific default
    device_config = f"/config-{DETECTED_DEVICE}.json"
    cfg = _load_config_from_file(device_config, button_count=BUTTON_COUNT)
    if "buttons" in cfg and len(cfg["buttons"]) > 0:
        print(f"Loaded {device_config}")
        return cfg

    # Built-in fallback
    print("No config found, using built-in defaults")
    return {
        "buttons": [
            {"label": str(i + 1), "cc": 20 + i, "color": "white"}
            for i in range(BUTTON_COUNT)
        ]
    }


config = load_config()
buttons = config.get("buttons", [])
print(f"Loaded {len(buttons)} button configs")
# Validate/normalize config so derived fields like `led_mode` are populated
try:
    config = validate_config(config, button_count=BUTTON_COUNT)
    buttons = config.get("buttons", [])
except Exception:
    # Defensive: if validation fails, continue with raw config
    pass
print(f"Validated {len(buttons)} button configs")

# =============================================================================
# Fonts
# =============================================================================

# Font cache to avoid loading the same font multiple times
_font_cache = {}


def load_font(size_name):
    """Load a font based on size name, with fallback to terminalio.

    Uses a cache to avoid loading the same font multiple times, saving RAM.

    Args:
        size_name: One of "small", "medium", "large"

    Returns:
        Tuple of (font_object, approximate_height_px)
    """
    if size_name not in FONT_SIZE_MAP:
        print(f"Invalid font size '{size_name}', using 'small'")
        size_name = "small"

    # Check cache first
    if size_name in _font_cache:
        return _font_cache[size_name]

    font_path, height = FONT_SIZE_MAP[size_name]

    if font_path == "terminalio":
        result = (terminalio.FONT, height)
        _font_cache[size_name] = result
        return result

    try:
        loaded_font = bitmap_font.load_font(font_path)
        print(f"Loaded font: {font_path} (~{height}px)")
        result = (loaded_font, height)
        _font_cache[size_name] = result
        return result
    except Exception as e:
        print(f"Font load failed for '{font_path}': {e}, falling back to terminalio")
        result = (terminalio.FONT, 8)
        _font_cache[size_name] = result
        return result


# Load display config
display_config = get_display_config(config)
button_text_size = display_config["button_text_size"]
status_text_size = display_config["status_text_size"]
expression_text_size = display_config["expression_text_size"]
button_name_text_size = display_config["button_name_text_size"]

print(f"Display config: button={button_text_size}, status={status_text_size}, expression={expression_text_size}, button_name={button_name_text_size}")

# Load fonts based on config (cached to avoid duplicate loads)
BUTTON_FONT, BUTTON_FONT_HEIGHT = load_font(button_text_size)
STATUS_FONT, STATUS_FONT_HEIGHT = load_font(status_text_size)
EXPRESSION_FONT, EXPRESSION_FONT_HEIGHT = load_font(expression_text_size)
BUTTON_NAME_FONT, BUTTON_NAME_FONT_HEIGHT = load_font(button_name_text_size)

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
# Switch Class - imported from core.button
# =============================================================================
# Switch class imported at top from core.button

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

MIDI_TRANSPORT = config.get("midi_transport", "usb")

# USB MIDI — primary transport and the only receive path for host → device sync
# No out_channel specified: allows per-message channel control for multi-command
midi_usb = adafruit_midi.MIDI(
    midi_in=usb_midi.ports[0],
    midi_out=usb_midi.ports[1],
    in_channel=0,
    in_buf_size=64,
)

# TRS / Serial MIDI via UART — GP16 (TX) / GP17 (RX) per hardware-reference.md
# Bidirectional like Helmut's original firmware (some pedals need RX for feedback)
# No out_channel specified: allows per-message channel control for multi-command
midi_uart = busio.UART(tx=board.GP16, rx=board.GP17, baudrate=31250, timeout=0.003,
                       receiver_buffer_size=512)
midi_trs = adafruit_midi.MIDI(
    midi_in=midi_uart,
    midi_out=midi_uart,
    in_buf_size=512,
)

print(f"MIDI initialized: transport={MIDI_TRANSPORT}")


def send_midi_message(msg, channel=0):
    """Send a MIDI message to USB, TRS, or both transports on specified channel.

    Transport is controlled by the 'midi_transport' config key:
      "usb"  - USB MIDI only (default)
      "trs"  - TRS/serial MIDI only
      "both" - send to both transports simultaneously

    RX (host → device) always comes from USB only via midi_usb.receive().

    Args:
        msg: MIDI message object (ControlChange, NoteOn, ProgramChange, etc.)
        channel: MIDI channel 0-15 (wire channels, displayed as 1-16 in UI)

    Note: adafruit_midi doesn't support per-message channels on send - the channel
    parameter on message constructors is for RX only. We temporarily set the
    transport's out_channel before each send.
    """
    if MIDI_TRANSPORT in ("usb", "both"):
        try:
            midi_usb.out_channel = channel
            midi_usb.send(msg)
        except Exception as e:
            print(f"[WARN] USB MIDI send failed: {e}")
    if MIDI_TRANSPORT in ("trs", "both"):
        try:
            midi_trs.out_channel = channel
            midi_trs.send(msg)
        except Exception as e:
            print(f"[WARN] TRS MIDI send failed: {e}")

# Encoder config (from config.json or defaults)
enc_config = config.get("encoder", {"enabled": True, "cc": 11, "label": "ENC", "min": 0, "max": 127, "initial": 64})
enc_push_config = enc_config.get("push", {"enabled": True, "cc": 14, "label": "PUSH", "mode": "momentary"})

CC_ENCODER = enc_config.get("cc", 11)
CC_ENCODER_PUSH = enc_push_config.get("cc", 14)
ENC_LABEL = enc_config.get("label", "ENC")
ENC_PUSH_LABEL = enc_push_config.get("label", "PUSH")
ENC_MIN = enc_config.get("min", 0)
ENC_MAX = enc_config.get("max", 127)
ENC_INITIAL = enc_config.get("initial", 64)
ENC_ENABLED = enc_config.get("enabled", True) and HAS_ENCODER
ENC_PUSH_ENABLED = enc_push_config.get("enabled", True) and HAS_ENCODER
ENC_PUSH_MODE = enc_push_config.get("mode", "momentary")
ENC_CHANNEL = enc_config.get("channel", 0)
ENC_PUSH_CHANNEL = enc_push_config.get("channel", 0)
ENC_PUSH_CC_ON = enc_push_config.get("cc_on", 127)
ENC_PUSH_CC_OFF = enc_push_config.get("cc_off", 0)

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
EXP1_CHANNEL = exp1_config.get("channel", 0)
EXP2_CHANNEL = exp2_config.get("channel", 0)

# =============================================================================
# State
# =============================================================================

# Initialize ButtonState objects for each button with keytimes support
button_states = []
for i in range(BUTTON_COUNT):
    btn_config = buttons[i] if i < len(buttons) else {}
    cc = btn_config.get("cc", 0)  # 0 for non-CC types; ButtonState.cc unused by note/pc dispatch
    mode = btn_config.get("mode", "toggle")
    keytimes = btn_config.get("keytimes", 1)
    # For 'tap' mode we do not keep a persistent logical ON state; visual
    # blinking is driven by recent taps. Initialize as OFF.
    initial_on = False
    button_states.append(ButtonState(cc=cc, mode=mode, initial_state=initial_on, keytimes=keytimes))

    # Long-press support state
    # Per-button: time when press started (monotonic), 0 if not pressed
press_start_times = [0.0] * BUTTON_COUNT
# Whether long-press action was already triggered for this button during current hold
long_press_triggered = [False] * BUTTON_COUNT
# Guard to avoid executing the short-press action more than once per press/release
short_action_executed = [False] * BUTTON_COUNT
# Default threshold (ms) if not provided per-button; can be overridden in config
DEFAULT_LONG_PRESS_MS = config.get("long_press_threshold_ms", 500)

pc_values = [0] * 16                 # Current PC value per MIDI channel (0-15), shared across all pc_inc/pc_dec buttons
pc_flash_timers = [0.0] * BUTTON_COUNT  # Expiry time (monotonic) for PC button flash; 0 = inactive
PC_FLASH_DURATION_MS = 200              # Default PC button flash duration in ms

encoder_value = ENC_INITIAL  # Internal value 0-127
encoder_slot = -1  # Current slot (set on first change)

# Blink/tap mode state (per-button)
blink_state = [False] * BUTTON_COUNT        # Current visual blink state (True=show ON color, False=show OFF color)
blink_next_toggle = [0.0] * BUTTON_COUNT    # Next monotonic time to toggle blink state
blink_rate_ms = [config.get("tap_rate_ms", 500)] * BUTTON_COUNT
for i in range(BUTTON_COUNT):
    try:
        btn_cfg = buttons[i] if i < len(buttons) else {}
        br = btn_cfg.get("tap_rate_ms", config.get("tap_rate_ms", 500))
        if not isinstance(br, int) or br <= 0:
            br = 500
        blink_rate_ms[i] = br
    except Exception:
        blink_rate_ms[i] = config.get("tap_rate_ms", 500)

# Tap-tempo tracking: per-button recent tap timestamps (monotonic seconds)
# We store up to TAP_HISTORY taps and compute average interval to set blink rate.
TAP_HISTORY = 4
tap_timestamps = [[] for _ in range(BUTTON_COUNT)]
# Per-button tap active expiry (monotonic seconds). While now < tap_active_until[i]
# the button will visually blink.
tap_active_until = [0.0] * BUTTON_COUNT

def record_tap_tempo(idx, now):
    """Record a tap for button index `idx` (0-based) at monotonic time `now`.

    Updates `blink_rate_ms[idx]` to the average interval (ms) between recent taps.
    """
    try:
        buf = tap_timestamps[idx]
        buf.append(now)
        # Keep only the most recent TAP_HISTORY timestamps
        if len(buf) > TAP_HISTORY:
            del buf[0:len(buf)-TAP_HISTORY]

        # Need at least two taps to compute an interval
        if len(buf) < 2:
            return

        # Compute average interval between consecutive taps
        intervals = [ (buf[i] - buf[i-1]) for i in range(1, len(buf)) ]
        avg_interval = sum(intervals) / len(intervals)
        # Convert to ms and clamp
        ms = int(max(50, min(5000, avg_interval * 1000)))
        blink_rate_ms[idx] = ms
        # Extend the active window for this tap so blinking is visible
        tap_active_until[idx] = now + (blink_rate_ms[idx] / 1000.0) * 2
        print(f"[TAP] Button {idx+1} tempo set to {ms} ms ({60_000//ms} BPM approx)")
    except Exception:
        pass

# Center display label timeout: auto-return to showing selected button after inactivity
# When a non-select button is pressed, show its label briefly, then return to selected
label_timeout_return_to_select = 0.0  # Expiry time (monotonic); 0 = no timeout active
LABEL_RETURN_TIMEOUT_SEC = 3.0        # Seconds of inactivity before returning to selected button

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

# Auto-size button height based on font
button_height = BUTTON_FONT_HEIGHT + 10  # 10px padding

if BUTTON_COUNT == 6:
    # Mini6: 3 buttons per row, wider spacing
    button_width = 70
    button_spacing = 80
    row_size = 3
else:
    # STD10: 5 buttons per row
    button_width = 46
    button_spacing = 48
    row_size = 5

# Adjust row positions to center vertically based on button height
top_row_y = 5
bottom_row_y = 240 - button_height - 5

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
    off_color = get_off_color_for_display(color_rgb, off_mode)

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

# Center display area - two lines
# Line 1: Button name (configurable font, default large)
button_name_label = label.Label(
    BUTTON_NAME_FONT,
    text="",
    color=0xFFFFFF,
    anchor_point=(0.5, 0.5),
    anchored_position=(120, 100),
)
main_group.append(button_name_label)

# Line 2: MIDI/status info (smaller font, below button name)
status_label = label.Label(
    STATUS_FONT,
    text="Ready",
    color=0x888888,  # Dimmer color for technical info
    anchor_point=(0.5, 0.5),
    anchored_position=(120, 145),
)
main_group.append(status_label)

display.show(main_group)

# =============================================================================
# LED & Display Helpers
# =============================================================================

# Track previous text length per label to enable single-update clearing
_label_prev_len = {}


def set_label_text(lbl, text):
    """Update a displayio.Label's text with space padding for clean overwrite.

    Pads with spaces to previous text length to ensure single bitmap update,
    avoiding flicker and GC churn from double-update (clear then set).

    Args:
        lbl: displayio.Label instance
        text: New text string to display
    """
    lbl_id = id(lbl)
    prev_len = _label_prev_len.get(lbl_id, 0)

    # Pad with spaces if new text is shorter than previous
    if len(text) < prev_len:
        text = text + " " * (prev_len - len(text))

    lbl.text = text
    _label_prev_len[lbl_id] = len(text.rstrip())  # Store unpadded length


def get_button_color(btn_config, keytime_index):
    """Get color for button at specific keytime state.

    Args:
        btn_config: Button configuration dict
        keytime_index: Current keytime position (1-indexed)

    Returns:
        RGB tuple for the color
    """
    return get_color(get_button_state_config(btn_config, keytime_index).get("color", "white"))


def arm_label_return_timeout(btn_config=None):
    """Arm or cancel the return-to-selected-button timeout.

    If btn_config is provided and has select_group, cancels the timeout (select buttons stay displayed).
    Otherwise, arms the timeout for non-select buttons/encoder to return after inactivity.

    Args:
        btn_config: Button configuration dict, or None for encoders/non-button events
    """
    global label_timeout_return_to_select

    if btn_config and btn_config.get("select_group"):
        # Select button pressed - cancel timeout (stay on this button)
        label_timeout_return_to_select = 0.0
    else:
        # Non-select button or encoder - arm timeout to return to selected
        label_timeout_return_to_select = time.monotonic() + LABEL_RETURN_TIMEOUT_SEC


def find_selected_button():
    """Find the currently selected button (button with select_group and state=True).

    Returns:
        tuple: (button_index, button_config) or (None, None) if no button is selected
    """
    for i, btn_config in enumerate(buttons):
        if btn_config.get("select_group") and button_states[i].state:
            return i, btn_config
    return None, None


def show_selected_button_label():
    """Update center display to show the currently selected button's label.

    If no select button is active, clears the display to show a ready state.
    """
    idx, btn_config = find_selected_button()
    if idx is not None:
        set_label_text(button_name_label, btn_config.get("label", str(idx + 1)))
        set_label_text(status_label, "")  # Clear status line
    else:
        # No select button active - clear display to ready state
        set_label_text(button_name_label, "")
        set_label_text(status_label, "Ready")


def _make_simple_toggle_cmd(btn_config, is_on, idx):
    """Synthesize a CC command for simplified toggle mode.

    Used when mode='toggle' but no press/release event arrays are defined.
    The CC number, channel, and values are read directly from btn_config.

    Args:
        btn_config: Button config dict with optional 'cc', 'channel', 'value_on', 'value_off'
        is_on: True = turning ON (send value_on), False = turning OFF (send value_off)
        idx: 0-indexed button index (used for default CC fallback)

    Returns:
        List with one CC command dict ready for _send_action_from_cfg
    """
    cc_num = btn_config.get("cc", 20 + idx)
    ch = btn_config.get("channel", 0)
    val = btn_config.get("value_on", 127) if is_on else btn_config.get("value_off", 0)
    return [{"type": "cc", "cc": cc_num, "value": val, "channel": ch}]


def _get_effective_action_cfg(btn_config, action_name, keytime_index):
    """Get action config with per-state override if available.

    Args:
        btn_config: Button config dict
        action_name: "press", "release", "long_press", or "long_release"
        keytime_index: Current keytime position (1-indexed)

    Returns:
        Action config (dict or list), or None if not configured
    """
    # Check for per-state override first
    states = btn_config.get("states", [])
    if states and 0 < keytime_index <= len(states):
        state = states[keytime_index - 1]
        if action_name in state:
            return state[action_name]

    # Fall back to button-level action
    return btn_config.get(action_name)


def _has_long_press_actions(btn_config):
    """Check if button has any long-press or long-release actions.

    Returns True if button-level or any per-state override has
    long_press or long_release configured.
    """
    # Check button-level
    if btn_config.get("long_press") or btn_config.get("long_release"):
        return True

    # Check all states for overrides
    states = btn_config.get("states", [])
    for state in states:
        if state.get("long_press") or state.get("long_release"):
            return True

    return False


def _send_action_from_cfg(action_cfg, btn_num, idx, action_name=None):
    """Send MIDI from action config (single dict or list of dicts).

    Args:
        action_cfg: Single command dict or list of command dicts
        btn_num: 1-indexed button number
        idx: 0-indexed button index
        action_name: Optional action type ("press", "release", "long_press", "long_release")
                     Used to display long_press_label when available

    Supports:
    - Single command: {"type":"cc","cc":20,"value":127,"channel":0}
    - Multiple commands: [{"type":"cc",...}, {"type":"pc",...}]

    Command types: cc, note, pc, pc_inc, pc_dec
    """
    if not action_cfg:
        return

    # Normalize to list
    if isinstance(action_cfg, dict):
        commands = [action_cfg]
    elif isinstance(action_cfg, list):
        commands = action_cfg
    else:
        print(f"[WARN] Invalid action_cfg type (button {btn_num}): {type(action_cfg)}")
        return

    # Display button name in center (large font)
    btn_config = buttons[idx] if idx < len(buttons) else {}
    # Use long_press_label if action is long_press and label is configured
    label_text = btn_config.get("label", str(btn_num))
    if action_name == "long_press" and "long_press_label" in btn_config:
        label_text = btn_config.get("long_press_label", label_text)
    set_label_text(button_name_label, label_text)
    arm_label_return_timeout(btn_config)

    # Track if any PC command executed (for LED flash feedback)
    pc_command_sent = False

    # Execute each command in sequence
    for cmd_idx, cmd in enumerate(commands):
        if not isinstance(cmd, dict):
            print(f"[WARN] Invalid command in action (button {btn_num}): {cmd}")
            continue

        # Small delay between commands for MIDI buffer management (MIDI Thru chains)
        # Skip delay before first command for immediate response
        if cmd_idx > 0:
            time.sleep(0.002)  # 2ms between commands

        msg_type = cmd.get("type", "cc")
        channel = cmd.get("channel", 0)

        try:
            if msg_type == "cc":
                cc = cmd.get("cc", 20 + idx)
                val = cmd.get("value", cmd.get("cc_on", 127))
                send_midi_message(ControlChange(cc, val), channel=channel)
                print(f"[MIDI TX] Ch{channel+1} CC{cc}={val} (switch {btn_num})")
                set_label_text(status_label, f"TX CC{cc}={val}")

            elif msg_type == "note":
                note = cmd.get("note", 60)
                vel = cmd.get("velocity", cmd.get("velocity_on", 127))
                send_midi_message(NoteOn(note, vel), channel=channel)
                print(f"[MIDI TX] Ch{channel+1} NoteOn{note} vel{vel} (switch {btn_num})")
                set_label_text(status_label, f"TX Note{note}")

            elif msg_type == "pc":
                program = cmd.get("program", 0)
                send_midi_message(ProgramChange(program), channel=channel)
                print(f"[MIDI TX] Ch{channel+1} PC{program} (switch {btn_num})")
                set_label_text(status_label, f"TX PC{program}")
                pc_command_sent = True

            elif msg_type == "pc_inc":
                step = cmd.get("pc_step", 1)
                pc_values[channel] = clamp_pc_value(pc_values[channel] + step)
                send_midi_message(ProgramChange(pc_values[channel]), channel=channel)
                print(f"[MIDI TX] Ch{channel+1} PC{pc_values[channel]} +{step} (switch {btn_num})")
                set_label_text(status_label, f"TX PC{pc_values[channel]}")
                pc_command_sent = True

            elif msg_type == "pc_dec":
                step = cmd.get("pc_step", 1)
                pc_values[channel] = clamp_pc_value(pc_values[channel] - step)
                send_midi_message(ProgramChange(pc_values[channel]), channel=channel)
                print(f"[MIDI TX] Ch{channel+1} PC{pc_values[channel]} -{step} (switch {btn_num})")
                set_label_text(status_label, f"TX PC{pc_values[channel]}")
                pc_command_sent = True

            else:
                print(f"[WARN] Unknown command type '{msg_type}' (button {btn_num})")

        except Exception as e:
            print(f"[ERROR] Failed to send command (button {btn_num}): {e}")
            # Continue to next command
            continue

    # Flash LED once if any PC command was sent in this action
    if pc_command_sent:
        flash_pc_button(btn_num)


def set_button_state(switch_idx, on):
    """Update LED and display for a button (1-indexed).

    Now uses ButtonState objects and supports keytime colors.
    """
    idx = switch_idx - 1

    # (helper _send_action_from_cfg moved to module scope)
    if idx < 0 or idx >= BUTTON_COUNT:
        return

    btn_state = button_states[idx]
    btn_config = buttons[idx] if idx < len(buttons) else {"color": "white"}

    # Get color for current keytime state
    color_rgb = get_button_color(btn_config, btn_state.get_keytime())
    off_mode = btn_config.get("off_mode", "dim")  # "dim" or "off"
    dim_brightness = btn_config.get("dim_brightness", 15)  # 0-100, default 15%

    # Update LED
    led_idx = switch_to_led(switch_idx)
    if led_idx is not None:
        rgb = color_rgb if on else get_off_color(color_rgb, off_mode, dim_brightness)
        base = led_idx * 3
        for j in range(3):
            if base + j < LED_COUNT:
                pixels[base + j] = rgb
        pixels.show()

    # If this button uses 'tap' led_mode, manage blink state/timers
    try:
        idx = switch_idx - 1
        btn_cfg = buttons[idx] if idx < len(buttons) else {}
        if btn_cfg.get("led_mode") == "tap":
            # Turning on: start blinking with short flash
            if on:
                blink_state[idx] = True
                blink_next_toggle[idx] = time.monotonic() + 0.1  # 100ms flash
            else:
                # Turning off: ensure LED shows off state and stop blinking
                blink_state[idx] = False
                blink_next_toggle[idx] = 0.0
    except Exception:
        pass

    # Update display
    if idx < len(button_labels):
        color_hex = rgb_to_hex(color_rgb if on else get_off_color_for_display(color_rgb, off_mode))
        button_labels[idx].color = color_hex
        if idx < len(button_boxes):
            _, box_palette = button_boxes[idx]
            box_palette[1] = color_hex


def init_leds():
    """Initialize all LEDs to off/dim state."""
    for i in range(1, BUTTON_COUNT + 1):
        set_button_state(i, False)


def clamp_pc_value(value):
    """Clamp PC value to valid MIDI range (0-127)."""
    return max(0, min(127, value))


def flash_pc_button(button_idx, flash_ms=PC_FLASH_DURATION_MS):
    """Light LED briefly for PC button press feedback.

    Args:
        button_idx: 1-indexed button number (matches set_button_state convention)
        flash_ms: flash duration in milliseconds
    """
    set_button_state(button_idx, True)
    pc_flash_timers[button_idx - 1] = time.monotonic() + flash_ms / 1000.0


def update_pc_flash_timers():
    """Turn off LEDs whose flash period has expired. Call each main loop."""
    now = time.monotonic()
    for i in range(BUTTON_COUNT):
        if pc_flash_timers[i] > 0 and now >= pc_flash_timers[i]:
            pc_flash_timers[i] = 0.0
            set_button_state(i + 1, False)


def update_blink_timers():
    """Toggle blink states for buttons configured with led_mode 'tap'.

    Blinking is non-blocking and driven by monotonic time checks.
    When a button is active (logical state True) and has led_mode 'tap',
    its LED alternates between ON color and OFF color at `tap_rate_ms`.
    """
    now = time.monotonic()
    for i in range(BUTTON_COUNT):
        try:
            btn_cfg = buttons[i] if i < len(buttons) else {}
            if btn_cfg.get("led_mode") != "tap":
                # ensure any lingering blink timers are cleared
                blink_next_toggle[i] = 0.0
                blink_state[i] = False
                continue

            # Blink while logical state is active OR while within the recent
            # tap active window (user tapped recently).
            active_window = now < tap_active_until[i]
            if not (button_states[i].state or active_window):
                if blink_state[i]:
                    blink_state[i] = False
                    set_button_state(i + 1, False)
                    blink_next_toggle[i] = 0.0
                continue

            # Active and tap mode: initialize timer if needed
            if blink_next_toggle[i] == 0.0:
                blink_state[i] = True
                set_button_state(i + 1, True)
                blink_next_toggle[i] = now + 0.1  # Start with 100ms flash
                continue

            if now >= blink_next_toggle[i]:
                blink_state[i] = not blink_state[i]
                set_button_state(i + 1, blink_state[i])
                
                # Use different durations for on vs off to match tempo
                # ON = short flash (100ms), OFF = rest of beat interval
                if blink_state[i]:
                    # Just turned ON - flash briefly
                    blink_next_toggle[i] = now + 0.1  # 100ms flash
                else:
                    # Just turned OFF - wait for next beat
                    beat_interval = blink_rate_ms[i] / 1000.0
                    flash_duration = 0.1
                    blink_next_toggle[i] = now + max(0.05, beat_interval - flash_duration)
        except Exception:
            # Defensive: don't let blinking crash the loop
            pass


def update_label_timeout():
    """Check if label timeout has expired and return to showing selected button."""
    global label_timeout_return_to_select

    if label_timeout_return_to_select == 0.0:
        return  # No timeout active

    now = time.monotonic()
    if now >= label_timeout_return_to_select:
        # Timeout expired - return to showing selected button
        label_timeout_return_to_select = 0.0
        show_selected_button_label()


# =============================================================================
# Polling Functions
# =============================================================================


def handle_midi():
    """Handle incoming MIDI messages from USB and TRS transports.

    Uses attribute-based detection (duck-typing) instead of strict isinstance()
    which avoids issues in test environments where message classes may differ.

    Checks both USB and TRS/serial MIDI for incoming messages (like Helmut's
    original firmware). Some pedals connected via TRS need bidirectional comms.
    """
    # Check USB MIDI
    msg = midi_usb.receive()
    if msg:
        _process_incoming_midi(msg)

    # Check TRS/serial MIDI
    msg = midi_trs.receive()
    if msg:
        _process_incoming_midi(msg)


def _get_button_expected_cc_value(btn_config):
    """Extract expected CC number, channel, and value from button's press action.

    Returns tuple: (cc, channel, value) or None if button doesn't send CC on press.
    Used for bidirectional MIDI sync with value-based scene switching (Quad Cortex style).
    """
    press_cfg = btn_config.get("press")
    if not press_cfg:
        return None

    # Normalize to list
    if isinstance(press_cfg, dict):
        commands = [press_cfg]
    elif isinstance(press_cfg, list):
        commands = press_cfg
    else:
        return None

    # Find first CC command
    for cmd in commands:
        if not isinstance(cmd, dict):
            continue
        if cmd.get("type", "cc") == "cc":
            cc = cmd.get("cc")
            channel = cmd.get("channel", btn_config.get("channel", 0))
            value = cmd.get("value", cmd.get("cc_on", 127))
            if cc is not None:
                return (cc, channel, value)

    return None


def _process_incoming_midi(msg):
    """Process a received MIDI message (from any transport).

    Extracted to avoid code duplication between USB and TRS receive paths.

    For ControlChange messages, matches CC number, channel, AND value for
    value-based scene switching (e.g., Quad Cortex: CC43=0, CC43=2, CC43=4 for scenes).
    """
    if not msg:
        return

    # Defensive: coerce channel to int when possible, fallback to 0
    raw_ch = getattr(msg, 'channel', None)
    try:
        msg_channel = int(raw_ch) if raw_ch is not None else 0
    except Exception:
        msg_channel = 0

    # ControlChange - duck-typed by presence of `control` attribute
    if hasattr(msg, 'control'):
        cc = getattr(msg, 'control')
        val = getattr(msg, 'value', 0)
        print(f"[MIDI RX] Ch{msg_channel+1} CC{cc}={val}")

        # Match CC number, channel, AND value for value-based scene switching
        for i, btn_config in enumerate(buttons):
            expected = _get_button_expected_cc_value(btn_config)
            if expected is None:
                continue

            exp_cc, exp_channel, exp_value = expected
            if cc == exp_cc and msg_channel == exp_channel and val == exp_value:
                # Exact match - turn this button ON
                button_states[i].state = True
                set_button_state(i + 1, True)

                # Deselect other buttons in the same group
                sg = btn_config.get("select_group")
                if sg:
                    _deselect_group(sg, i)

                set_label_text(button_name_label, btn_config.get("label", str(i + 1)))
                set_label_text(status_label, f"RX CC{cc}={val}")
                arm_label_return_timeout(btn_config)
                break

    # NoteOn/NoteOff - duck-typed by `note` and optionally `velocity`
    elif hasattr(msg, 'note'):
        note = getattr(msg, 'note')
        vel = getattr(msg, 'velocity', None)
        if vel is not None:
            # NoteOn-like message
            print(f"[MIDI RX] Ch{msg_channel+1} NoteOn{note} vel{vel}")
            for i, btn_config in enumerate(buttons):
                if btn_config.get("type") == "note" and btn_config.get("note") == note and btn_config.get("channel", 0) == msg_channel:
                    set_button_state(i + 1, vel > 0)
                    if vel > 0:
                        sg = btn_config.get("select_group")
                        if sg:
                            _deselect_group(sg, i)
                    set_label_text(button_name_label, btn_config.get("label", str(i + 1)))
                    set_label_text(status_label, f"RX Note{note}")
                    arm_label_return_timeout(btn_config)
                    break
        else:
            # NoteOff-like message
            print(f"[MIDI RX] Ch{msg_channel+1} NoteOff{note}")
            for i, btn_config in enumerate(buttons):
                if btn_config.get("type") == "note" and btn_config.get("note") == note and btn_config.get("channel", 0) == msg_channel:
                    set_button_state(i + 1, False)
                    set_label_text(button_name_label, btn_config.get("label", str(i + 1)))
                    set_label_text(status_label, f"RX NoteOff{note}")
                    arm_label_return_timeout(btn_config)
                    break

    # ProgramChange-like: look for `patch` attribute
    elif hasattr(msg, 'patch'):
        program = getattr(msg, 'patch')
        print(f"[MIDI RX] Ch{msg_channel+1} PC{program}")
        # pc_values is per-channel, so one assignment covers all pc_inc/pc_dec buttons on this channel
        pc_values[msg_channel] = program
        set_label_text(status_label, f"RX PC{program}")
        arm_label_return_timeout()  # No button config for PC messages


def _deselect_group(group_name, keep_idx):
    """Turn off any other buttons that share select_group == group_name.

    Sends OFF MIDI messages for siblings when applicable and updates visual state.
    keep_idx is the index (0-based) of the button to keep ON.

    Uses the new event-based dispatch: sends `release` event if configured,
    otherwise falls back to legacy cc_off/velocity_off behavior.
    """
    if not group_name:
        return
    for j, bcfg in enumerate(buttons):
        if j == keep_idx:
            continue
        if bcfg.get("select_group") == group_name:
            # If sibling is currently on, turn it off
            try:
                if button_states[j].state:
                    button_states[j].state = False
                    set_button_state(j + 1, False)

                    # Try new event-based release first (with per-state override)
                    release_cfg = _get_effective_action_cfg(bcfg, "release", button_states[j].get_keytime())
                    if release_cfg:
                        _send_action_from_cfg(release_cfg, j + 1, j, "release")
                        print(f"[SELECT] Deselected sibling {j+1} (group {group_name}) via release event")
                    else:
                        # Fall back to legacy behavior for backward compatibility
                        msg_type = bcfg.get("type", "cc")
                        ch = bcfg.get("channel", 0)
                        state_cfg = get_button_state_config(bcfg, button_states[j].get_keytime())
                        if msg_type == "cc":
                            cc = state_cfg.get("cc", 20 + j)
                            cc_off = state_cfg.get("cc_off", 0)
                            send_midi_message(ControlChange(cc, cc_off, channel=ch))
                            print(f"[MIDI TX] Ch{ch+1} CC{cc}={cc_off} (deselect sibling {j+1}, group {group_name})")
                        elif msg_type == "note":
                            note = state_cfg.get("note", 60)
                            vel_off = state_cfg.get("velocity_off", 0)
                            send_midi_message(NoteOff(note, vel_off, channel=ch))
                            print(f"[MIDI TX] Ch{ch+1} NoteOff{note} (deselect sibling {j+1}, group {group_name})")
            except Exception:
                pass


def handle_switches():
    """Handle footswitch presses using event-based dispatch.

    Refactored to use the new multi-command event system:
    - "press" event: dispatched when button is pressed
    - "release" event: dispatched when button is released (short press)
    - "long_press" event: dispatched when hold threshold is exceeded
    - "long_release" event: dispatched when button released after long press

    State management (toggle, momentary, keytimes, select_group) is handled
    here, while MIDI dispatch is delegated to _send_action_from_cfg().
    """
    # STD10: index 0 is encoder push, 1-10 are footswitches
    # Mini6: indices 0-5 are footswitches (no encoder)
    start_idx = 1 if HAS_ENCODER else 0
    now = time.monotonic()

    for i in range(start_idx, len(switches)):
        sw = switches[i]
        changed, pressed = sw.changed()

        # Convert to 1-indexed button number and index
        btn_num = i if HAS_ENCODER else i + 1
        idx = btn_num - 1
        btn_state = button_states[idx]
        btn_config = buttons[idx] if idx < len(buttons) else {"cc": 20 + idx}

        mode = btn_config.get("mode", "toggle")

        # Check for long-press configuration (button-level or per-state)
        long_enabled = _has_long_press_actions(btn_config)

        # --- Handle edge events ---
        if changed:
            if pressed:
                # PRESSED: Initialize press timing
                if not press_start_times[idx]:
                    press_start_times[idx] = now
                    long_press_triggered[idx] = False
                    short_action_executed[idx] = False

                # Handle tap tempo recording
                if mode == "tap":
                    record_tap_tempo(idx, now)
                    # Start blinking for tap mode - short flash at tempo
                    blink_state[idx] = True
                    blink_next_toggle[idx] = now + 0.1  # 100ms flash

                # Dispatch press event
                if not long_enabled:
                    # No long-press: execute press action immediately
                    if mode in ("toggle", "normal", "select", "tap"):
                        # Advance keytime for toggle modes
                        btn_state.advance_keytime()
                        # For toggle/select: update state and LED, dispatch appropriate event
                        if mode in ("toggle", "normal", "select"):
                            # For buttons with select_group: pressing when already ON keeps it ON (radio button behavior)
                            # For toggle/normal mode without select_group: flip state
                            # For select mode: always turns ON
                            if btn_state.keytimes > 1:
                                new_state = True
                            elif mode == "select":
                                new_state = True
                            elif btn_config.get("select_group") and btn_state.state:
                                # Radio button behavior: if already selected, stay selected
                                new_state = True
                            elif mode in ("toggle", "normal"):
                                new_state = not btn_state.state
                            else:
                                new_state = True

                            btn_state.state = new_state
                            set_button_state(btn_num, new_state)
                            # Handle select_group exclusivity (applies to both toggle and select modes)
                            if new_state:
                                sg = btn_config.get("select_group")
                                if sg:
                                    _deselect_group(sg, idx)
                            # Dispatch press (ON) or release (OFF) based on new state
                            action_cfg = _get_effective_action_cfg(btn_config, "press" if new_state else "release", btn_state.get_keytime())
                            # Simplified toggle: synthesize CC on/off if no explicit action defined
                            if action_cfg is None and mode == "toggle":
                                action_cfg = _make_simple_toggle_cmd(btn_config, new_state, idx)
                            if action_cfg:
                                _send_action_from_cfg(action_cfg, btn_num, idx, "press" if new_state else "release")
                                short_action_executed[idx] = True
                        else:
                            # Tap mode: always dispatch press
                            press_cfg = _get_effective_action_cfg(btn_config, "press", btn_state.get_keytime())
                            if press_cfg:
                                _send_action_from_cfg(press_cfg, btn_num, idx, "press")
                                short_action_executed[idx] = True
                    else:
                        # Momentary or other modes: dispatch press event
                        press_cfg = _get_effective_action_cfg(btn_config, "press", btn_state.get_keytime())
                        if press_cfg:
                            _send_action_from_cfg(press_cfg, btn_num, idx, "press")
                            short_action_executed[idx] = True

                    # For momentary mode, also set LED on
                    if mode == "momentary":
                        set_button_state(btn_num, True)

                else:
                    # Long-press configured: for momentary, dispatch press immediately
                    # For toggle modes, defer until we know if it's short or long
                    if mode == "momentary":
                        btn_state.advance_keytime()
                        press_cfg = _get_effective_action_cfg(btn_config, "press", btn_state.get_keytime())
                        if press_cfg:
                            _send_action_from_cfg(press_cfg, btn_num, idx, "press")
                        set_button_state(btn_num, True)

            else:
                # RELEASED: Dispatch appropriate release event
                press_start_times[idx] = 0.0
                was_long = long_press_triggered[idx]
                long_press_triggered[idx] = False

                if was_long:
                    # Long-press completed: dispatch long_release if configured
                    long_release_cfg = _get_effective_action_cfg(btn_config, "long_release", btn_state.get_keytime())
                    if long_release_cfg:
                        _send_action_from_cfg(long_release_cfg, btn_num, idx, "long_release")

                    # For momentary mode, set LED off after long press
                    if mode == "momentary":
                        set_button_state(btn_num, False)
                else:
                    # Short press: handle deferred actions
                    if long_enabled:
                        # Deferred press action (for toggle modes with long-press configured)
                        if mode in ("toggle", "normal", "select", "tap") and not short_action_executed[idx]:
                            btn_state.advance_keytime()
                            if mode in ("toggle", "normal", "select"):
                                # For buttons with select_group: pressing when already ON keeps it ON (radio button behavior)
                                # For toggle/normal mode without select_group: flip state
                                # For select mode: always turns ON
                                if btn_state.keytimes > 1:
                                    new_state = True
                                elif mode == "select":
                                    new_state = True
                                elif btn_config.get("select_group") and btn_state.state:
                                    # Radio button behavior: if already selected, stay selected
                                    new_state = True
                                elif mode in ("toggle", "normal"):
                                    new_state = not btn_state.state
                                else:
                                    new_state = True

                                btn_state.state = new_state
                                set_button_state(btn_num, new_state)
                                # Handle select_group exclusivity (applies to both toggle and select modes)
                                if new_state:
                                    sg = btn_config.get("select_group")
                                    if sg:
                                        _deselect_group(sg, idx)
                                # Dispatch press (ON) or release (OFF) based on new state
                                action_cfg = _get_effective_action_cfg(btn_config, "press" if new_state else "release", btn_state.get_keytime())
                                # Simplified toggle: synthesize CC on/off if no explicit action defined
                                if action_cfg is None and mode == "toggle":
                                    action_cfg = _make_simple_toggle_cmd(btn_config, new_state, idx)
                                if action_cfg:
                                    _send_action_from_cfg(action_cfg, btn_num, idx, "press" if new_state else "release")
                                    short_action_executed[idx] = True
                            else:
                                # Tap mode: always dispatch press
                                press_cfg = _get_effective_action_cfg(btn_config, "press", btn_state.get_keytime())
                                if press_cfg:
                                    _send_action_from_cfg(press_cfg, btn_num, idx, "press")
                                    short_action_executed[idx] = True

                    # Dispatch release event
                    release_cfg = _get_effective_action_cfg(btn_config, "release", btn_state.get_keytime())
                    if release_cfg:
                        _send_action_from_cfg(release_cfg, btn_num, idx, "release")

                    # For momentary mode, set LED off
                    if mode == "momentary":
                        set_button_state(btn_num, False)

        # --- Handle held buttons for long-press threshold crossing ---
        if pressed and long_enabled and not long_press_triggered[idx] and press_start_times[idx]:
            # Get effective long_press config for current keytime (may be per-state override)
            effective_long_press = _get_effective_action_cfg(btn_config, "long_press", btn_state.get_keytime())

            # Determine threshold (ms) from effective config
            threshold_ms = DEFAULT_LONG_PRESS_MS
            if effective_long_press and isinstance(effective_long_press, dict):
                threshold_ms = effective_long_press.get("threshold_ms", threshold_ms)
            elif isinstance(effective_long_press, list) and len(effective_long_press) > 0:
                # If it's an array, check first command for threshold
                first_cmd = effective_long_press[0]
                if isinstance(first_cmd, dict):
                    threshold_ms = first_cmd.get("threshold_ms", threshold_ms)

            if (now - press_start_times[idx]) >= (threshold_ms / 1000.0):
                # Trigger long-press action
                long_press_triggered[idx] = True

                # For toggle/normal/select modes: update button state and LED before sending MIDI
                if mode in ("toggle", "normal", "select") and not short_action_executed[idx]:
                    btn_state.advance_keytime()
                    # For buttons with select_group: pressing when already ON keeps it ON (radio button behavior)
                    # For toggle/normal mode without select_group: flip state
                    # For select mode: always turns ON
                    if btn_state.keytimes > 1:
                        new_state = True
                    elif mode == "select":
                        new_state = True
                    elif btn_config.get("select_group") and btn_state.state:
                        # Radio button behavior: if already selected, stay selected
                        new_state = True
                    elif mode in ("toggle", "normal"):
                        new_state = not btn_state.state
                    else:
                        new_state = True

                    btn_state.state = new_state
                    set_button_state(btn_num, new_state)
                    # Handle select_group exclusivity (applies to both toggle and select modes)
                    if new_state:
                        sg = btn_config.get("select_group")
                        if sg:
                            _deselect_group(sg, idx)
                    short_action_executed[idx] = True

                # Send long_press MIDI action
                if effective_long_press:
                    _send_action_from_cfg(effective_long_press, btn_num, idx, "long_press")


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
                cc_val = ENC_PUSH_CC_ON if encoder_push_state else ENC_PUSH_CC_OFF
                send_midi_message(ControlChange(CC_ENCODER_PUSH, cc_val, channel=ENC_PUSH_CHANNEL))
                print(f"[MIDI TX] Ch{ENC_PUSH_CHANNEL+1} CC{CC_ENCODER_PUSH}={cc_val} (encoder push, toggle)")
                set_label_text(button_name_label, ENC_PUSH_LABEL)
                set_label_text(status_label, f"TX CC{CC_ENCODER_PUSH}={'ON' if encoder_push_state else 'OFF'}")
                arm_label_return_timeout()
        else:
            # Momentary mode: send on press and release
            cc_val = ENC_PUSH_CC_ON if pressed else ENC_PUSH_CC_OFF
            send_midi_message(ControlChange(CC_ENCODER_PUSH, cc_val, channel=ENC_PUSH_CHANNEL))
            print(f"[MIDI TX] Ch{ENC_PUSH_CHANNEL+1} CC{CC_ENCODER_PUSH}={cc_val} (encoder push, momentary)")
            set_label_text(button_name_label, ENC_PUSH_LABEL)
            set_label_text(status_label, f"TX CC{CC_ENCODER_PUSH}={cc_val}")
            arm_label_return_timeout()


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
                send_midi_message(ControlChange(CC_ENCODER, encoder_slot, channel=ENC_CHANNEL))
                print(f"[ENCODER] Ch{ENC_CHANNEL+1} CC{CC_ENCODER}={encoder_slot} (slot)")
                set_label_text(button_name_label, ENC_LABEL)
                set_label_text(status_label, f"ENC slot {encoder_slot}")
                arm_label_return_timeout()
        else:
            # Normal mode: send every change
            send_midi_message(ControlChange(CC_ENCODER, encoder_value, channel=ENC_CHANNEL))
            print(f"[ENCODER] Ch{ENC_CHANNEL+1} CC{CC_ENCODER}={encoder_value}")
            set_label_text(button_name_label, ENC_LABEL)
            set_label_text(status_label, f"ENC={encoder_value}")
            arm_label_return_timeout()


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
                send_midi_message(ControlChange(CC_EXP1, val1, channel=EXP1_CHANNEL))
                lbl = exp1_config.get("label", "EXP1")
                print(f"[{lbl}] Ch{EXP1_CHANNEL+1} CC{CC_EXP1}={val1}")

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
                send_midi_message(ControlChange(CC_EXP2, val2, channel=EXP2_CHANNEL))
                lbl = exp2_config.get("label", "EXP2")
                print(f"[{lbl}] Ch{EXP2_CHANNEL+1} CC{CC_EXP2}={val2}")


# =============================================================================
# Startup
# =============================================================================

print("Initializing...")
init_leds()

# Apply select_group default selections: if a button has default_selected, turn it on
# Keep at most one per group (normalize earlier in config.validate_config)
group_chosen = {}
for i, b in enumerate(buttons):
    g = b.get("select_group")
    if not g:
        continue
    if b.get("default_selected"):
        if g in group_chosen:
            # already handled by config normalization, but be defensive
            continue
        group_chosen[g] = i
        try:
            button_states[i].state = True
            set_button_state(i + 1, True)
            # Send the press MIDI message for default_selected button at startup (uses initial keytime state)
            press_cfg = _get_effective_action_cfg(b, "press", button_states[i].get_keytime())
            if press_cfg:
                _send_action_from_cfg(press_cfg, i + 1, i, "press")
                print(f"[STARTUP] Activated default_selected button {i+1}: {b.get('label', '')}")
        except Exception as e:
            print(f"[WARN] Failed to activate default_selected button {i+1}: {e}")

# Apply default_on state for simplified toggle buttons at startup
for i, b in enumerate(buttons):
    if b.get("mode") == "toggle" and b.get("default_on"):
        try:
            button_states[i].state = True
            set_button_state(i + 1, True)
            startup_cmd = _make_simple_toggle_cmd(b, True, i)
            _send_action_from_cfg(startup_cmd, i + 1, i, "press")
            print(f"[STARTUP] default_on toggle button {i+1}: {b.get('label', '')}")
        except Exception as e:
            print(f"[WARN] Failed to activate default_on button {i+1}: {e}")

# Ensure tap-mode buttons are visually ON (they have no off state)
for i, b in enumerate(buttons):
    try:
        if b.get("mode") == "tap" or b.get("led_mode") == "tap":
            button_states[i].state = True
            set_button_state(i + 1, True)
    except Exception:
        pass

# Startup animation
pixels.fill((0, 255, 0))
pixels.show()
time.sleep(0.5)
init_leds()

# Show CC mapping info
if HAS_ENCODER:
    if ENC_STEPS and ENC_STEPS > 1:
        print(f"Encoder: Ch{ENC_CHANNEL+1} CC{CC_ENCODER} ({ENC_STEPS} slots, outputs 0-{ENC_STEPS-1})")
    else:
        print(f"Encoder: Ch{ENC_CHANNEL+1} CC{CC_ENCODER} (range {ENC_MIN}-{ENC_MAX}, init={ENC_INITIAL})")
    print(f"Encoder Push: Ch{ENC_PUSH_CHANNEL+1} CC{CC_ENCODER_PUSH} ({ENC_PUSH_MODE})")
if HAS_EXPRESSION:
    print(f"Expression 1: Ch{EXP1_CHANNEL+1} CC{CC_EXP1}")
    print(f"Expression 2: Ch{EXP2_CHANNEL+1} CC{CC_EXP2}")
for i, btn in enumerate(buttons):
    btn_channel = btn.get("channel", 0)
    print(f"Button {i+1}: Ch{btn_channel+1} CC{btn.get('cc', 20+i)} ({btn.get('label', '')})")

print("\nRunning...")

# Initialize display to show currently selected button
show_selected_button_label()

# =============================================================================
# Main Loop
# =============================================================================

while True:
    handle_midi()
    handle_switches()
    update_pc_flash_timers()
    update_blink_timers()
    update_label_timeout()
    if HAS_ENCODER:
        handle_encoder_button()
        handle_encoder()
    if HAS_EXPRESSION:
        handle_expression()
