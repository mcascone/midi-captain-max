"""
MIDI Captain MAX - Configuration Constants

Centralizes all magic numbers and configuration constants used throughout
the firmware. Extracted for maintainability and easier tuning.

Author: Max Cascone
Date: 2026-03-15
"""

# =============================================================================
# Display Configuration
# =============================================================================

# Display dimensions (pixels)
DISPLAY_WIDTH = 240
DISPLAY_HEIGHT = 240

# Display colors
DISPLAY_BACKGROUND_COLOR = 0x000000  # Black
DISPLAY_STATUS_TEXT_COLOR = 0x888888  # Gray for technical info
COLOR_WHITE = 0xFFFFFF  # White (standard RGB)

# Display positioning
DISPLAY_CENTER_X = 120
DISPLAY_CENTER_Y = 120
BUTTON_LABEL_TOP_ROW_Y = 5
BUTTON_LABEL_HEIGHT = 35

# =============================================================================
# LED Configuration
# =============================================================================

# NeoPixel brightness (0.0 - 1.0)
LED_GLOBAL_BRIGHTNESS = 0.3  # 30% to prevent eye strain

# LED off-mode defaults
LED_DEFAULT_OFF_MODE = "dim"  # "dim" or "off"
LED_DEFAULT_DIM_BRIGHTNESS = 15  # Percentage (0-100) for dim mode

# =============================================================================
# MIDI Configuration
# =============================================================================

# MIDI channel configuration
DEFAULT_MIDI_CHANNEL = 0  # 0-15 (displayed as 1-16 in UI)
MIDI_CHANNEL_COUNT = 16

# MIDI value ranges
MIDI_MIN_VALUE = 0
MIDI_MAX_VALUE = 127
MIDI_VALUE_CENTER = 64  # Center value for encoders, etc.

# MIDI communication
USB_MIDI_BUFFER_SIZE = 64  # USB MIDI input buffer size

# =============================================================================
# Timing Configuration (milliseconds and seconds)
# =============================================================================

# Display timeouts
LABEL_RETURN_TIMEOUT_SEC = 3.0  # Seconds before label returns to selected button

# Button behavior
DEFAULT_LONG_PRESS_MS = 500  # Default long-press threshold
PC_FLASH_DURATION_MS = 200  # PC button visual flash duration

# Tap tempo
TAP_HISTORY_SIZE = 4  # Number of taps to track for tempo calculation
TAP_MIN_INTERVAL_MS = 50  # Minimum tap interval (max 1200 BPM)
TAP_MAX_INTERVAL_MS = 5000  # Maximum tap interval (min 12 BPM)
TAP_DEFAULT_RATE_MS = 500  # Default blink rate if not configured
TAP_ACTIVE_WINDOW_MULTIPLIER = 2  # Extend blink window by this factor

# Battery monitoring
VBAT_FILTER_ALPHA = 0.01  # Exponential moving average smoothing factor

# =============================================================================
# Performance Thresholds
# =============================================================================

# Performance monitoring (for future instrumentation)
SLOW_OPERATION_THRESHOLD_MS = 10  # Warn if operation exceeds this

# =============================================================================
# Program Change Tracking
# =============================================================================

# PC value state storage size
PC_VALUES_SIZE = MIDI_CHANNEL_COUNT  # One PC value per MIDI channel

# =============================================================================
# Calculated Bounds
# =============================================================================

def calculate_bottom_row_y(button_height):
    """Calculate Y position for bottom row of button labels."""
    return DISPLAY_HEIGHT - button_height - 5

# =============================================================================
# Validation Helpers
# =============================================================================

def clamp_midi_value(value):
    """Clamp value to valid MIDI range (0-127)."""
    return max(MIDI_MIN_VALUE, min(MIDI_MAX_VALUE, int(value)))

def clamp_midi_channel(channel):
    """Clamp channel to valid MIDI range (0-15)."""
    return max(0, min(MIDI_CHANNEL_COUNT - 1, int(channel)))

def clamp_tap_interval_ms(interval_ms):
    """Clamp tap interval to valid range."""
    return max(TAP_MIN_INTERVAL_MS, min(TAP_MAX_INTERVAL_MS, int(interval_ms)))
