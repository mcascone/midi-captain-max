"""
Color utilities for MIDI Captain firmware.

Provides color palette and conversion functions for LEDs and display.
"""

# Named color palette (RGB tuples)
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
    """Get RGB tuple from color name, with fallback to white.
    
    Args:
        name: Color name (case-insensitive)
        
    Returns:
        RGB tuple (r, g, b) with values 0-255
    """
    return COLORS.get(name.lower(), COLORS["white"])


def dim_color(rgb, factor=0.15):
    """Return a dimmed version of an RGB color.
    
    Args:
        rgb: RGB tuple (r, g, b)
        factor: Brightness factor (0.0-1.0), default 0.15
        
    Returns:
        Dimmed RGB tuple
    """
    return tuple(int(c * factor) for c in rgb)


def rgb_to_hex(rgb):
    """Convert RGB tuple to hex integer for display.
    
    Args:
        rgb: RGB tuple (r, g, b)
        
    Returns:
        Integer in 0xRRGGBB format
    """
    return (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]


def get_off_color(color_rgb, off_mode="dim"):
    """Get the color to use when button is off.

    Args:
        color_rgb: The button's on-state RGB color
        off_mode: "dim" for dimmed color, "off" for dimmed color (labels stay visible)

    Returns:
        RGB tuple for the off state (always dimmed for visibility)
    """
    # Always return dim color to keep labels visible on display
    # Both "dim" and "off" modes now show dim labels
    return dim_color(color_rgb)
