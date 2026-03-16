"""
Combined MIDI + Display Demo for MIDI Captain STD10

Features:
- Button labels displayed in 2x5 grid matching physical layout
- Switch presses send CC and highlight button on screen
- Incoming CC updates both LED and screen highlight
- Center area shows status

Deploy: Copy this file to MIDICAPTAIN as code.py

Author: Max Cascone
Date: 2026-01-26
"""

print("\n=== MIDI + DISPLAY DEMO ===\n")

import board
import busio
import displayio
import digitalio
import neopixel
import usb_midi
import adafruit_midi
from adafruit_st7789 import ST7789
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
from adafruit_midi.control_change import ControlChange
import terminalio

# Import hardware constants
from devices.std10 import (
    LED_PIN,
    LED_COUNT,
    SWITCH_PINS,
    switch_to_led,
    TFT_DC_PIN,
    TFT_CS_PIN,
    TFT_SCK_PIN,
    TFT_MOSI_PIN,
    DISPLAY_WIDTH,
    DISPLAY_HEIGHT,
    DISPLAY_ROWSTART,
    DISPLAY_ROTATION,
)

# --- Configuration ---
MIDI_CHANNEL = 0
CC_START = 20
LED_BRIGHTNESS = 0.3

# --- Colors ---
COLOR_OFF = (10, 10, 10)
COLOR_ON = (0, 255, 0)
COLOR_BG = 0x000000
COLOR_LABEL_BG = 0x333333
COLOR_LABEL_ON = 0x00AA00
COLOR_TEXT = 0xFFFFFF
COLOR_TEXT_ON = 0x000000

# --- Display Setup ---
displayio.release_displays()

spi = busio.SPI(TFT_SCK_PIN, TFT_MOSI_PIN)
while not spi.try_lock():
    pass
spi.configure(baudrate=24000000)
spi.unlock()

display_bus = displayio.FourWire(
    spi, command=TFT_DC_PIN, chip_select=TFT_CS_PIN, reset=None, baudrate=24000000
)

display = ST7789(
    display_bus,
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    rowstart=DISPLAY_ROWSTART,
    rotation=DISPLAY_ROTATION
)
print(f"Display: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}")

# --- Layout ---
TOP_ROW_LABELS = ["1", "2", "3", "4", "Dn"]
BOTTOM_ROW_LABELS = ["A", "B", "C", "D", "Up"]

COLS = 5
BUTTON_WIDTH = DISPLAY_WIDTH // COLS
BUTTON_HEIGHT = 40
TOP_ROW_Y = 0
BOTTOM_ROW_Y = DISPLAY_HEIGHT - BUTTON_HEIGHT

# --- Build Display ---
root = displayio.Group()
display.show(root)

# Background
bg_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)
bg_palette = displayio.Palette(1)
bg_palette[0] = COLOR_BG
root.append(displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette))

# Button slots (store references for updating)
button_rects = []
button_texts = []

def create_button_slot(x, y, label_text):
    group = displayio.Group()
    rect = Rect(x + 1, y + 1, BUTTON_WIDTH - 2, BUTTON_HEIGHT - 2, fill=COLOR_LABEL_BG)
    group.append(rect)
    text = label.Label(
        terminalio.FONT,
        text=label_text,
        color=COLOR_TEXT,
        anchor_point=(0.5, 0.5),
        anchored_position=(x + BUTTON_WIDTH // 2, y + BUTTON_HEIGHT // 2)
    )
    group.append(text)
    return group, rect, text

# Top row (switches 1-5)
for i, lbl in enumerate(TOP_ROW_LABELS):
    group, rect, text = create_button_slot(i * BUTTON_WIDTH, TOP_ROW_Y, lbl)
    root.append(group)
    button_rects.append(rect)
    button_texts.append(text)

# Bottom row (switches 6-10)
for i, lbl in enumerate(BOTTOM_ROW_LABELS):
    group, rect, text = create_button_slot(i * BUTTON_WIDTH, BOTTOM_ROW_Y, lbl)
    root.append(group)
    button_rects.append(rect)
    button_texts.append(text)

# Center status
status_label = label.Label(
    terminalio.FONT,
    text="Ready",
    color=COLOR_TEXT,
    anchor_point=(0.5, 0.5),
    anchored_position=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2)
)
root.append(status_label)

# --- LED Setup ---
pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, auto_write=False)

def get_led_indices(led_idx):
    base = led_idx * 3
    return [base, base + 1, base + 2]

def set_led(led_idx, color):
    for i in get_led_indices(led_idx):
        pixels[i] = color
    pixels.show()

def init_leds():
    for i in range(10):
        for j in get_led_indices(i):
            pixels[j] = COLOR_OFF
    pixels.show()

# --- Switch Setup ---
class Switch:
    def __init__(self, pin):
        self.io = digitalio.DigitalInOut(pin)
        self.io.direction = digitalio.Direction.INPUT
        self.io.pull = digitalio.Pull.UP
        self.last_state = True
    
    @property
    def pressed(self):
        return not self.io.value
    
    def changed(self):
        current = self.pressed
        changed = current != self.last_state
        self.last_state = current
        return changed, current

switches = [Switch(pin) for pin in SWITCH_PINS]
print(f"Switches: {len(switches)}")

# --- MIDI Setup ---
midi_usb = adafruit_midi.MIDI(
    midi_in=usb_midi.ports[0],
    midi_out=usb_midi.ports[1],
    in_channel=MIDI_CHANNEL,
    out_channel=MIDI_CHANNEL,
)
print(f"MIDI channel: {MIDI_CHANNEL + 1}")

# --- State ---
button_states = [False] * 10

def update_button_display(btn_idx, on):
    """Update both LED and screen for a button."""
    if 0 <= btn_idx < 10:
        button_states[btn_idx] = on
        # Update LED
        led_idx = switch_to_led(btn_idx + 1)  # switch indices are 1-based
        if led_idx is not None:
            set_led(led_idx, COLOR_ON if on else COLOR_OFF)
        # Update screen
        button_rects[btn_idx].fill = COLOR_LABEL_ON if on else COLOR_LABEL_BG
        button_texts[btn_idx].color = COLOR_TEXT_ON if on else COLOR_TEXT

def switch_idx_to_button_idx(switch_idx):
    """Convert switch index (0-10) to button index (0-9). Returns None for encoder."""
    if switch_idx == 0:
        return None  # Encoder
    return switch_idx - 1

# --- Main Loop ---
def handle_incoming_midi():
    while True:
        msg = midi_usb.receive()
        if msg is None:
            break
        if isinstance(msg, ControlChange):
            cc_num = msg.control
            cc_val = msg.value
            switch_idx = cc_num - CC_START
            btn_idx = switch_idx_to_button_idx(switch_idx)
            if btn_idx is not None and 0 <= btn_idx < 10:
                on = cc_val > 63
                update_button_display(btn_idx, on)
                status_label.text = f"CC{cc_num}={'ON' if on else 'OFF'}"
                print(f"RX: CC{cc_num}={cc_val} → btn {btn_idx}")

def handle_switches():
    for i, switch in enumerate(switches):
        changed, pressed = switch.changed()
        if changed:
            cc_num = CC_START + i
            cc_val = 127 if pressed else 0
            midi_usb.send(ControlChange(cc_num, cc_val))
            
            btn_idx = switch_idx_to_button_idx(i)
            if btn_idx is not None and pressed:
                # Toggle on press
                new_state = not button_states[btn_idx]
                update_button_display(btn_idx, new_state)
                status_label.text = f"Sw{i}={'ON' if new_state else 'OFF'}"
            print(f"TX: sw{i} {'dn' if pressed else 'up'} → CC{cc_num}")

# --- Startup ---
print("\nStarting...")
print(f"CC range: {CC_START}-{CC_START + 10}")
init_leds()

while True:
    handle_incoming_midi()
    handle_switches()
