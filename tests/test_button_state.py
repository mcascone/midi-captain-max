"""
Tests for the ButtonState class from core/button.py.
"""

import pytest
import sys
from pathlib import Path

# Add firmware/dev to path
FIRMWARE_DIR = Path(__file__).parent.parent / "firmware" / "dev"
sys.path.insert(0, str(FIRMWARE_DIR))

from core.button import ButtonState


class TestButtonStateToggle:
    """Tests for toggle mode buttons."""
    
    def test_initial_state_off(self):
        """Button starts in off state by default."""
        btn = ButtonState(cc=20)
        assert btn.state == False
    
    def test_initial_state_on(self):
        """Can start button in on state."""
        btn = ButtonState(cc=20, initial_state=True)
        assert btn.state == True
    
    def test_press_toggles_on(self):
        """First press turns button on."""
        btn = ButtonState(cc=20, mode="toggle")
        changed, state, value = btn.on_press()
        
        assert changed == True
        assert state == True
        assert value == 127
        assert btn.state == True
    
    def test_press_toggles_off(self):
        """Second press turns button off."""
        btn = ButtonState(cc=20, mode="toggle", initial_state=True)
        changed, state, value = btn.on_press()
        
        assert changed == True
        assert state == False
        assert value == 0
        assert btn.state == False
    
    def test_release_does_nothing_in_toggle(self):
        """Release has no effect in toggle mode."""
        btn = ButtonState(cc=20, mode="toggle")
        btn.on_press()  # Turn on
        
        changed, state, value = btn.on_release()
        
        assert changed == False
        assert state == True  # Still on
        assert value is None
        assert btn.state == True


class TestButtonStateMomentary:
    """Tests for momentary mode buttons."""
    
    def test_press_turns_on(self):
        """Press turns button on."""
        btn = ButtonState(cc=20, mode="momentary")
        changed, state, value = btn.on_press()
        
        assert changed == True
        assert state == True
        assert value == 127
    
    def test_release_turns_off(self):
        """Release turns button off."""
        btn = ButtonState(cc=20, mode="momentary")
        btn.on_press()
        changed, state, value = btn.on_release()
        
        assert changed == True
        assert state == False
        assert value == 0


class TestButtonStateMidiReceive:
    """Tests for host override via MIDI."""
    
    def test_high_value_turns_on(self):
        """CC value > 63 turns button on."""
        btn = ButtonState(cc=20)
        result = btn.on_midi_receive(127)
        
        assert result == True
        assert btn.state == True
    
    def test_low_value_turns_off(self):
        """CC value <= 63 turns button off."""
        btn = ButtonState(cc=20, initial_state=True)
        result = btn.on_midi_receive(0)
        
        assert result == False
        assert btn.state == False
    
    def test_threshold_at_64(self):
        """Value 64 is on, 63 is off."""
        btn = ButtonState(cc=20)
        
        btn.on_midi_receive(63)
        assert btn.state == False
        
        btn.on_midi_receive(64)
        assert btn.state == True
    
    def test_host_override_persists(self):
        """Host can override local toggle state."""
        btn = ButtonState(cc=20, mode="toggle", initial_state=True)
        
        # Host says off
        btn.on_midi_receive(0)
        assert btn.state == False
        
        # Local press toggles back on
        btn.on_press()
        assert btn.state == True
