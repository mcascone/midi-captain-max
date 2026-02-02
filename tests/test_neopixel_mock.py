"""
Tests for the NeoPixel mock and LED logic.
"""

import pytest


class TestNeoPixelMock:
    """Verify the mock NeoPixel behaves correctly."""
    
    def test_initial_state_is_off(self, mock_neopixel):
        """All LEDs should start off (black)."""
        for i in range(len(mock_neopixel)):
            assert mock_neopixel[i] == (0, 0, 0)
    
    def test_set_single_pixel(self, mock_neopixel):
        """Can set a single pixel color."""
        mock_neopixel[0] = (255, 0, 0)
        assert mock_neopixel[0] == (255, 0, 0)
        assert mock_neopixel[1] == (0, 0, 0)  # Others unchanged
    
    def test_fill(self, mock_neopixel):
        """Fill sets all pixels to the same color."""
        mock_neopixel.fill((0, 255, 0))
        for i in range(len(mock_neopixel)):
            assert mock_neopixel[i] == (0, 255, 0)
    
    def test_length(self, mock_neopixel):
        """Length matches constructor argument."""
        assert len(mock_neopixel) == 30
    
    def test_get_all_colors(self, mock_neopixel):
        """Helper method returns all colors."""
        mock_neopixel[0] = (255, 0, 0)
        mock_neopixel[5] = (0, 255, 0)
        
        colors = mock_neopixel.get_all_colors()
        assert len(colors) == 30
        assert colors[0] == (255, 0, 0)
        assert colors[5] == (0, 255, 0)
        assert colors[1] == (0, 0, 0)


class TestLEDMapping:
    """Test switch-to-LED mapping logic (extracted from devices/std10.py)."""
    
    def switch_to_led(self, switch_idx):
        """Convert switch index (1-10) to LED index (0-9)."""
        if 1 <= switch_idx <= 5:
            return switch_idx - 1
        elif 6 <= switch_idx <= 10:
            return switch_idx - 1
        return None
    
    def test_top_row_mapping(self):
        """Top row switches (1-5) map to LEDs 0-4."""
        assert self.switch_to_led(1) == 0
        assert self.switch_to_led(2) == 1
        assert self.switch_to_led(3) == 2
        assert self.switch_to_led(4) == 3
        assert self.switch_to_led(5) == 4
    
    def test_bottom_row_mapping(self):
        """Bottom row switches (6-10) map to LEDs 5-9."""
        assert self.switch_to_led(6) == 5
        assert self.switch_to_led(7) == 6
        assert self.switch_to_led(8) == 7
        assert self.switch_to_led(9) == 8
        assert self.switch_to_led(10) == 9
    
    def test_encoder_returns_none(self):
        """Encoder (index 0) has no LED."""
        assert self.switch_to_led(0) is None
    
    def test_invalid_indices(self):
        """Out-of-range indices return None."""
        assert self.switch_to_led(-1) is None
        assert self.switch_to_led(11) is None
        assert self.switch_to_led(100) is None
