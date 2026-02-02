"""
Core modules for MIDI Captain firmware.

These modules contain pure logic that can be tested without hardware.
"""

from .colors import COLORS, get_color, dim_color, rgb_to_hex, get_off_color
from .config import load_config, validate_config, validate_button
from .button import Switch, ButtonState

__all__ = [
    "COLORS",
    "get_color",
    "dim_color", 
    "rgb_to_hex",
    "get_off_color",
    "load_config",
    "validate_config",
    "validate_button",
    "Switch",
    "ButtonState",
]
