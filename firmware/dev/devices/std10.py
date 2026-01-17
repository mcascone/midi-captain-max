import board

# NeoPixels
LED_PIN = board.GP7
LED_COUNT = 30  # 10 switches * 3 pixels

# Footswitches (as used by Helmut firmware)
SWITCH_PINS = [
    board.GP0,
    board.GP1,
    board.GP25,
    board.GP24,
    board.GP23,
    board.GP20,
    board.GP9,
    board.GP10,
    board.GP11,
    board.GP18,
    board.GP19,
]

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
