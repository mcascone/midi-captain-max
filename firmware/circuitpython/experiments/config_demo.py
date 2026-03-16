"""
Config-driven MIDI + Display Demo

Loads button configuration from config.json and uses it for:
- Display labels and colors
- LED colors
- CC number assignments

Author: Max Cascone
Date: 2026-01-26
"""

print("Config Demo starting...")

import board
import busio
import digitalio
import displayio
import terminalio
import json
import neopixel
import usb_midi
import adafruit_midi
from adafruit_midi.control_change import ControlChange
from adafruit_display_text import label
from adafruit_st7789 import ST7789
from adafruit_bitmap_font import bitmap_font

# Import device constants
from devices.std10 import (
    LED_PIN, LED_COUNT, SWITCH_PINS, switch_to_led,
    TFT_DC_PIN, TFT_CS_PIN, TFT_SCK_PIN, TFT_MOSI_PIN,
    DISPLAY_WIDTH, DISPLAY_HEIGHT, DISPLAY_ROWSTART, DISPLAY_ROTATION
)

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

# =============================================================================
# Fonts
# =============================================================================

# Try to load PCF fonts, fall back to built-in
# Note: 20pt font works well for Mini6 (6 switches = wider boxes)
# For STD10 (10 switches), built-in font fits better
try:
    # BUTTON_FONT = bitmap_font.load_font("/fonts/PTSans-Regular-20.pcf")  # Use for Mini6
    BUTTON_FONT = terminalio.FONT  # Better for STD10's narrow boxes
    STATUS_FONT = bitmap_font.load_font("/fonts/PTSans-Regular-20.pcf")
    print("Loaded PCF fonts")
except Exception as e:
    print(f"Font load failed: {e}, using built-in")
    BUTTON_FONT = terminalio.FONT
    STATUS_FONT = terminalio.FONT

def get_color(name):
    """Get RGB tuple from color name, with fallback to white."""
    return COLORS.get(name.lower(), COLORS["white"])

def dim_color(rgb, factor=0.2):
    """Return a dimmed version of an RGB color."""
    return tuple(int(c * factor) for c in rgb)

# =============================================================================
# Load Configuration
# =============================================================================

def load_config(path="/config.json"):
    """Load button configuration from JSON file."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config: {e}")
        # Return default config
        return {
            "buttons": [
                {"label": str(i+1), "cc": 20+i, "color": "white"}
                for i in range(10)
            ]
        }

config = load_config()
buttons = config.get("buttons", [])
print(f"Loaded {len(buttons)} button configs")

# =============================================================================
# Hardware Init
# =============================================================================

# NeoPixels
pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=0.3, auto_write=False)

# Display
displayio.release_displays()
spi = busio.SPI(clock=TFT_SCK_PIN, MOSI=TFT_MOSI_PIN)
display_bus = displayio.FourWire(
    spi, command=TFT_DC_PIN, chip_select=TFT_CS_PIN
)
display = ST7789(
    display_bus,
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    rowstart=DISPLAY_ROWSTART,
    rotation=DISPLAY_ROTATION
)

# Switches (skip index 0 = encoder)
switches = []
for i, pin in enumerate(SWITCH_PINS[1:11], start=1):
    sw = digitalio.DigitalInOut(pin)
    sw.direction = digitalio.Direction.INPUT
    sw.pull = digitalio.Pull.UP
    switches.append(sw)

# MIDI
midi = adafruit_midi.MIDI(
    midi_out=usb_midi.ports[1],
    midi_in=usb_midi.ports[0],
    out_channel=0
)

# =============================================================================
# State
# =============================================================================

button_states = [False] * 10
prev_switch_states = [True] * 10  # Pull-up = True when not pressed

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
# Top row (switches 1-5) at top of display
# Bottom row (switches 6-10) at bottom of display
button_labels = []
button_boxes = []
button_width = 46
button_height = 30  # Back to smaller height for 20pt font
button_spacing = 48
top_row_y = 5       # Top of display
bottom_row_y = 205  # Bottom of display

for i in range(10):
    btn_config = buttons[i] if i < len(buttons) else {"label": str(i+1), "color": "white"}
    
    if i < 5:
        # Top row (switches 1-5)
        x = 1 + i * button_spacing
        y = top_row_y
    else:
        # Bottom row (switches 6-10)
        x = 1 + (i - 5) * button_spacing
        y = bottom_row_y
    
    color_rgb = get_color(btn_config.get("color", "white"))
    
    # Create box background
    box_bitmap = displayio.Bitmap(button_width, button_height, 2)
    box_palette = displayio.Palette(2)
    box_palette[0] = 0x000000  # Background (black)
    box_palette[1] = (color_rgb[0] << 16) | (color_rgb[1] << 8) | color_rgb[2]  # Border color
    
    # Draw border (1px)
    for bx in range(button_width):
        box_bitmap[bx, 0] = 1  # Top
        box_bitmap[bx, button_height - 1] = 1  # Bottom
    for by in range(button_height):
        box_bitmap[0, by] = 1  # Left
        box_bitmap[button_width - 1, by] = 1  # Right
    
    box_sprite = displayio.TileGrid(box_bitmap, pixel_shader=box_palette, x=x, y=y)
    button_boxes.append((box_sprite, box_palette))
    main_group.append(box_sprite)
    
    # Create label centered in box
    color_hex = (color_rgb[0] << 16) | (color_rgb[1] << 8) | color_rgb[2]
    lbl = label.Label(
        BUTTON_FONT,
        text=btn_config.get("label", str(i+1))[:6],  # Max 6 chars
        color=color_hex,
        anchor_point=(0.5, 0.5),
        anchored_position=(x + button_width // 2, y + button_height // 2)
    )
    button_labels.append(lbl)
    main_group.append(lbl)

# Status area
status_label = label.Label(
    STATUS_FONT,
    text="Config Demo Ready",
    color=0xFFFFFF,
    anchor_point=(0.5, 0.5),
    anchored_position=(120, 100)
)
main_group.append(status_label)

display.show(main_group)

# =============================================================================
# LED Helpers
# =============================================================================

def set_led(switch_idx, on):
    """Set LED for a switch based on its config color."""
    led_idx = switch_to_led(switch_idx)
    if led_idx is None:
        return
    
    btn_config = buttons[switch_idx - 1] if switch_idx <= len(buttons) else {"color": "white"}
    color = get_color(btn_config.get("color", "white"))
    
    if on:
        rgb = color
    else:
        rgb = dim_color(color)
    
    # Set all 3 pixels for this switch
    base = led_idx * 3
    for j in range(3):
        if base + j < LED_COUNT:
            pixels[base + j] = rgb
    pixels.show()

def update_display_state(switch_idx, on):
    """Update display label and box appearance based on state."""
    idx = switch_idx - 1
    if idx >= len(button_labels):
        return
    
    btn_config = buttons[idx] if idx < len(buttons) else {"color": "white"}
    color_rgb = get_color(btn_config.get("color", "white"))
    
    if on:
        color_hex = (color_rgb[0] << 16) | (color_rgb[1] << 8) | color_rgb[2]
    else:
        dim = dim_color(color_rgb)
        color_hex = (dim[0] << 16) | (dim[1] << 8) | dim[2]
    
    button_labels[idx].color = color_hex
    
    # Update box border color
    if idx < len(button_boxes):
        box_sprite, box_palette = button_boxes[idx]
        box_palette[1] = color_hex

# Initialize LEDs to dim state
for i in range(1, 11):
    set_led(i, False)

print("Config Demo ready - press switches or send CC 20-29")

# =============================================================================
# Main Loop
# =============================================================================

while True:
    # Check for incoming MIDI
    msg = midi.receive()
    if msg and isinstance(msg, ControlChange):
        cc = msg.control
        val = msg.value
        
        # Map CC to button index (CC 20 = button 1, etc.)
        for i, btn_config in enumerate(buttons):
            if btn_config.get("cc") == cc:
                switch_idx = i + 1
                on = val > 63
                button_states[i] = on
                set_led(switch_idx, on)
                update_display_state(switch_idx, on)
                status_label.text = f"RX CC{cc}={val}"
                break
    
    # Check switches
    for i, sw in enumerate(switches):
        switch_idx = i + 1
        current = sw.value  # False = pressed (pull-up)
        prev = prev_switch_states[i]
        
        if current != prev:
            prev_switch_states[i] = current
            
            if not current:  # Just pressed
                # Toggle state
                button_states[i] = not button_states[i]
                on = button_states[i]
                
                # Update LED and display
                set_led(switch_idx, on)
                update_display_state(switch_idx, on)
                
                # Send CC
                btn_config = buttons[i] if i < len(buttons) else {"cc": 20 + i}
                cc = btn_config.get("cc", 20 + i)
                midi.send(ControlChange(cc, 127 if on else 0))
                
                status_label.text = f"TX CC{cc}={'ON' if on else 'OFF'}"
