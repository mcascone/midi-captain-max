"""
Tests for the switch/digitalio mock.
"""

import pytest


class TestSwitchMock:
    """Verify the mock switch inputs work correctly."""
    
    def test_initial_state_is_released(self, mock_switches):
        """All switches should start in released (high) state."""
        for sw in mock_switches:
            assert sw.value == True  # Active-low: high = not pressed
    
    def test_simulate_press(self, mock_switches):
        """Can simulate a button press."""
        mock_switches[1].simulate_press()
        assert mock_switches[1].value == False  # Active-low: low = pressed
        assert mock_switches[2].value == True   # Others unchanged
    
    def test_simulate_release(self, mock_switches):
        """Can simulate a button release."""
        mock_switches[1].simulate_press()
        mock_switches[1].simulate_release()
        assert mock_switches[1].value == True
    
    def test_multiple_presses(self, mock_switches):
        """Can press multiple buttons simultaneously."""
        mock_switches[1].simulate_press()
        mock_switches[6].simulate_press()
        
        assert mock_switches[1].value == False
        assert mock_switches[6].value == False
        assert mock_switches[2].value == True  # Others still released


class TestButtonDebounce:
    """Test button debouncing logic (to be extracted from code.py)."""
    
    # This is a placeholder for debounce logic that should be extracted
    # into a testable module. For now, just demonstrate the pattern.
    
    def test_placeholder(self):
        """Placeholder test - implement when debounce is extracted."""
        # TODO: Extract ButtonState class from code.py and test here
        assert True
