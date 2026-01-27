"""
Display Demo for MIDI Captain STD10

Shows button labels in a 2x5 grid matching the physical layout:
    Top row:    1   2   3   4   Down
    Bottom row: A   B   C   D   Up

Deploy: Copy this file to MIDICAPTAIN as code.py

Author: Max Cascone
Date: 2026-01-26
"""

print("\n=== DISPLAY DEMO ===\n")

import board
import busio
import displayio
from adafruit_st7789 import ST7789
from adafruit_display_text import label
from adafruit_display_shapes.rect import Rect
import terminalio  # Built-in font, no file needed

# Import hardware constants
from devices.std10 import (
    TFT_DC_PIN,
    TFT_CS_PIN,
    TFT_SCK_PIN,
    TFT_MOSI_PIN,
    DISPLAY_WIDTH,
    DISPLAY_HEIGHT,
    DISPLAY_ROWSTART,
    DISPLAY_ROTATION,
)

# --- Display Setup ---

# Release any existing displays
displayio.release_displays()

# Set up SPI
spi = busio.SPI(TFT_SCK_PIN, TFT_MOSI_PIN)
while not spi.try_lock():
    pass
spi.configure(baudrate=24000000)
spi.unlock()

# Set up display bus
display_bus = displayio.FourWire(
    spi,
    command=TFT_DC_PIN,
    chip_select=TFT_CS_PIN,
    reset=None,
    baudrate=24000000
)

# Create display
display = ST7789(
    display_bus,
    width=DISPLAY_WIDTH,
    height=DISPLAY_HEIGHT,
    rowstart=DISPLAY_ROWSTART,
    rotation=DISPLAY_ROTATION
)

print(f"Display initialized: {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}")

# --- Layout Constants ---

# Button labels matching physical layout
TOP_ROW_LABELS = ["1", "2", "3", "4", "Down"]
BOTTOM_ROW_LABELS = ["A", "B", "C", "D", "Up"]

# Colors
COLOR_BG = 0x000000       # Black background
COLOR_LABEL_BG = 0x333333  # Dark gray for label boxes
COLOR_LABEL_ON = 0x00FF00  # Green when active
COLOR_TEXT = 0xFFFFFF      # White text

# Layout: 5 columns, 2 rows (matching physical buttons)
# Leave space in the middle for status area
COLS = 5
BUTTON_WIDTH = DISPLAY_WIDTH // COLS  # 48 pixels each
BUTTON_HEIGHT = 40
TOP_ROW_Y = 0
BOTTOM_ROW_Y = DISPLAY_HEIGHT - BUTTON_HEIGHT
CENTER_HEIGHT = DISPLAY_HEIGHT - (2 * BUTTON_HEIGHT)

# --- Build Display Groups ---

# Root group
root = displayio.Group()
display.show(root)

# Background
bg_bitmap = displayio.Bitmap(DISPLAY_WIDTH, DISPLAY_HEIGHT, 1)
bg_palette = displayio.Palette(1)
bg_palette[0] = COLOR_BG
bg_sprite = displayio.TileGrid(bg_bitmap, pixel_shader=bg_palette, x=0, y=0)
root.append(bg_sprite)

# Create button label boxes
button_boxes = []
button_labels = []

def create_button_slot(x, y, label_text, index):
    """Create a button display slot with background and label."""
    group = displayio.Group()
    
    # Background rectangle
    rect = Rect(x, y, BUTTON_WIDTH - 2, BUTTON_HEIGHT - 2, fill=COLOR_LABEL_BG)
    group.append(rect)
    
    # Text label (centered in box)
    text = label.Label(
        terminalio.FONT,
        text=label_text,
        color=COLOR_TEXT,
        anchor_point=(0.5, 0.5),
        anchored_position=(x + BUTTON_WIDTH // 2, y + BUTTON_HEIGHT // 2)
    )
    group.append(text)
    
    return group, rect, text

# Create top row buttons
for i, lbl in enumerate(TOP_ROW_LABELS):
    x = i * BUTTON_WIDTH
    group, rect, text = create_button_slot(x, TOP_ROW_Y, lbl, i)
    root.append(group)
    button_boxes.append(rect)
    button_labels.append(text)

# Create bottom row buttons
for i, lbl in enumerate(BOTTOM_ROW_LABELS):
    x = i * BUTTON_WIDTH
    group, rect, text = create_button_slot(x, BOTTOM_ROW_Y, lbl, i + 5)
    root.append(group)
    button_boxes.append(rect)
    button_labels.append(text)

# Center status area
status_label = label.Label(
    terminalio.FONT,
    text="MIDI Captain",
    color=COLOR_TEXT,
    anchor_point=(0.5, 0.5),
    anchored_position=(DISPLAY_WIDTH // 2, DISPLAY_HEIGHT // 2)
)
root.append(status_label)

print("Display layout complete!")
print(f"  Top row: {TOP_ROW_LABELS}")
print(f"  Bottom row: {BOTTOM_ROW_LABELS}")
print(f"  Button size: {BUTTON_WIDTH}x{BUTTON_HEIGHT}")
print("")

# --- Demo: Cycle through highlighting each button ---

import time

def highlight_button(index, on=True):
    """Highlight or unhighlight a button."""
    if 0 <= index < len(button_boxes):
        button_boxes[index].fill = COLOR_LABEL_ON if on else COLOR_LABEL_BG

print("Demo: Cycling through buttons...")

while True:
    for i in range(10):
        highlight_button(i, True)
        time.sleep(0.3)
        highlight_button(i, False)
    time.sleep(1)
