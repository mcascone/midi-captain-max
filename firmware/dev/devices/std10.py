"""
STD10 Hardware Constants

Physical layout (as seen from front):
    Top row:    1   2   3   4   Down    (switch indices 1-5)
    Bottom row: A   B   C   D   Up      (switch indices 6-10)

LED NeoPixel chain (30 LEDs, 3 per switch):
    LEDs 0-4:   Top row (1, 2, 3, 4, Down)
    LEDs 5-9:   Bottom row (A, B, C, D, Up)

Switch index 0 is the encoder push (no LED).
"""

import board

# NeoPixels
LED_PIN = board.GP7
LED_COUNT = 30  # 10 switches * 3 LEDs each

# Footswitches - GPIO pins in index order
SWITCH_PINS = [
    board.GP0,   # 0: Encoder push (no LED)
    board.GP1,   # 1: Top-left (1)
    board.GP25,  # 2: Top (2)
    board.GP24,  # 3: Top (3)
    board.GP23,  # 4: Top (4)
    board.GP20,  # 5: Top-right (Down)
    board.GP9,   # 6: Bottom-left (A)
    board.GP10,  # 7: Bottom (B)
    board.GP11,  # 8: Bottom (C)
    board.GP18,  # 9: Bottom (D)
    board.GP19,  # 10: Bottom-right (Up)
]

def switch_to_led(switch_idx):
    """
    Convert switch index (1-10) to LED index (0-9).
    Returns None for encoder (index 0) or invalid indices.
    
    Mapping:
        Switch 1-5 (top row)    → LED 0-4
        Switch 6-10 (bottom row) → LED 5-9
    """
    if 1 <= switch_idx <= 5:
        # Top row: switch 1→LED 0, switch 5→LED 4
        return switch_idx - 1
    elif 6 <= switch_idx <= 10:
        # Bottom row: switch 6→LED 5, switch 10→LED 9
        return switch_idx - 1
    return None

# Encoder
ENCODER_A_PIN = board.GP2
ENCODER_B_PIN = board.GP3

# Analog inputs
EXP1_PIN = board.A1
EXP2_PIN = board.A2
BATTERY_PIN = board.A3

# Display (ST7789 over SPI)
TFT_DC_PIN = board.GP12
TFT_CS_PIN = board.GP13
TFT_SCK_PIN = board.GP14
TFT_MOSI_PIN = board.GP15

# ST7789 parameters
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 240
DISPLAY_ROWSTART = 80
DISPLAY_ROTATION = 180
