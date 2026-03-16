"""
Mini6 Hardware Constants

Physical layout (as seen from front):
    Top row:    TL    TM    TR    (switch indices 1-3)
    Bottom row: BL    BM    BR    (switch indices 4-6)

LED NeoPixel chain (18 LEDs, 3 per switch):
    LEDs 0-2:   Top row (TL, TM, TR)
    LEDs 3-5:   Bottom row (BL, BM, BR)

Note: Mini6 has no encoder or expression pedal inputs.
Some pins use unusual assignments (board.LED, board.VBUS_SENSE).
"""

import board

# NeoPixels
LED_PIN = board.GP7
LED_COUNT = 18  # 6 switches * 3 LEDs each

# Footswitches - GPIO pins in index order
# Note: No encoder on Mini6, so no index 0
SWITCH_PINS = [
    board.GP1,         # 1: Top-left (TL)
    board.LED,         # 2: Top-middle (TM) - repurposed LED pin
    board.VBUS_SENSE,  # 3: Top-right (TR) - repurposed VBUS sense pin
    board.GP9,         # 4: Bottom-left (BL)
    board.GP10,        # 5: Bottom-middle (BM)
    board.GP11,        # 6: Bottom-right (BR)
]


def switch_to_led(switch_idx):
    """
    Convert switch index (1-6) to LED index (0-5).
    Returns None for invalid indices.
    
    Mapping:
        Switch 1-3 (top row)    → LED 0-2
        Switch 4-6 (bottom row) → LED 3-5
    """
    if 1 <= switch_idx <= 6:
        return switch_idx - 1
    return None


# No encoder on Mini6
ENCODER_A_PIN = None
ENCODER_B_PIN = None

# No expression pedals on Mini6 (TBD - may need probing)
EXP1_PIN = None
EXP2_PIN = None
BATTERY_PIN = None

# Display (ST7789 over SPI) - same as STD10
TFT_DC_PIN = board.GP12
TFT_CS_PIN = board.GP13
TFT_SCK_PIN = board.GP14
TFT_MOSI_PIN = board.GP15

# ST7789 parameters - same as STD10
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 240
DISPLAY_ROWSTART = 80
DISPLAY_ROTATION = 180
