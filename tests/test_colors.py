"""
Tests for color utility functions.

These are pure logic tests that don't require any hardware.
"""

import pytest


# Color functions extracted for testing (these would eventually live in a separate module)
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
    """Get RGB tuple from color name, with fallback to white."""
    return COLORS.get(name.lower(), COLORS["white"])


def dim_color(rgb, factor=0.15):
    """Return a dimmed version of an RGB color."""
    return tuple(int(c * factor) for c in rgb)


def rgb_to_hex(rgb):
    """Convert RGB tuple to hex integer for display."""
    return (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]


class TestGetColor:
    """Tests for get_color function."""
    
    def test_known_colors(self):
        assert get_color("red") == (255, 0, 0)
        assert get_color("green") == (0, 255, 0)
        assert get_color("blue") == (0, 0, 255)
    
    def test_case_insensitive(self):
        assert get_color("RED") == (255, 0, 0)
        assert get_color("Red") == (255, 0, 0)
        assert get_color("rEd") == (255, 0, 0)
    
    def test_unknown_color_returns_white(self):
        assert get_color("fuschia") == (255, 255, 255)
        assert get_color("chartreuse") == (255, 255, 255)
        assert get_color("") == (255, 255, 255)


class TestDimColor:
    """Tests for dim_color function."""
    
    def test_dim_red(self):
        result = dim_color((255, 0, 0))
        assert result == (38, 0, 0)  # int(255 * 0.15) = 38
    
    def test_dim_white(self):
        result = dim_color((255, 255, 255))
        assert result == (38, 38, 38)
    
    def test_custom_factor(self):
        result = dim_color((200, 100, 50), factor=0.5)
        assert result == (100, 50, 25)
    
    def test_already_dim(self):
        result = dim_color((10, 10, 10))
        assert result == (1, 1, 1)


class TestRgbToHex:
    """Tests for rgb_to_hex function."""
    
    def test_red(self):
        assert rgb_to_hex((255, 0, 0)) == 0xFF0000
    
    def test_green(self):
        assert rgb_to_hex((0, 255, 0)) == 0x00FF00
    
    def test_blue(self):
        assert rgb_to_hex((0, 0, 255)) == 0x0000FF
    
    def test_white(self):
        assert rgb_to_hex((255, 255, 255)) == 0xFFFFFF
    
    def test_mixed(self):
        assert rgb_to_hex((128, 64, 32)) == 0x804020
