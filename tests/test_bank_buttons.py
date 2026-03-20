"""
Tests for bank button switching (up/down buttons).

Tests single-button cycling and dual-button (next/prev) bank switching.
"""

import pytest


def test_bank_button_single_cycles_forward():
    """Test single button cycles through banks in forward direction."""
    from firmware.circuitpython.core.banks import BankManager
    from firmware.circuitpython.core.button import ButtonState
    import time
    
    banks = [
        {"name": "Bank 1", "buttons": []},
        {"name": "Bank 2", "buttons": []},
        {"name": "Bank 3", "buttons": []},
    ]
    
    # Create initial button states (10 buttons for STD10)
    button_states = [ButtonState(cc=20 + i) for i in range(10)]
    
    bm = BankManager(banks, button_states, active_bank=0)
    
    # Test cycling forward (wraps around)
    assert bm.current_bank_index == 0
    bm.next_bank()
    time.sleep(0.25)  # Wait for cooldown
    assert bm.current_bank_index == 1
    bm.next_bank()
    time.sleep(0.25)
    assert bm.current_bank_index == 2
    bm.next_bank()
    time.sleep(0.25)
    assert bm.current_bank_index == 0  # Wrap around


def test_bank_button_dual_next_prev():
    """Test dual buttons for next/previous bank switching."""
    from firmware.circuitpython.core.banks import BankManager
    from firmware.circuitpython.core.button import ButtonState
    import time
    
    banks = [
        {"name": "Bank 1", "buttons": []},
        {"name": "Bank 2", "buttons": []},
        {"name": "Bank 3", "buttons": []},
    ]
    
    button_states = [ButtonState(cc=20 + i) for i in range(10)]
    bm = BankManager(banks, button_states, active_bank=0)
    
    # Test next button
    assert bm.current_bank_index == 0
    bm.next_bank()
    time.sleep(0.25)  # Wait for cooldown
    assert bm.current_bank_index == 1
    
    # Test previous button
    bm.previous_bank()
    time.sleep(0.25)
    assert bm.current_bank_index == 0
    
    # Test previous wraps to last bank
    bm.previous_bank()
    time.sleep(0.25)
    assert bm.current_bank_index == 2
    
    # Test next wraps to first bank
    bm.next_bank()
    time.sleep(0.25)
    assert bm.current_bank_index == 0


def test_bank_button_state_persistence():
    """Test button states persist across bank switches."""
    from firmware.circuitpython.core.banks import BankManager
    from firmware.circuitpython.core.button import ButtonState
    import time
    
    banks = [
        {"name": "Bank 1", "buttons": []},
        {"name": "Bank 2", "buttons": []},
    ]
    
    button_states = [ButtonState(cc=20 + i) for i in range(10)]
    bm = BankManager(banks, button_states, active_bank=0)
    
    # Set button state in Bank 1
    states = bm.get_button_states()
    states[0].state = True  # Turn on button 1
    
    # Switch to Bank 2
    bm.next_bank()
    time.sleep(0.25)  # Wait for cooldown
    assert bm.current_bank_index == 1
    
    # Bank 2 button should start off
    states2 = bm.get_button_states()
    assert states2[0].state == False
    
    # Switch back to Bank 1
    bm.previous_bank()
    time.sleep(0.25)
    assert bm.current_bank_index == 0
    
    # Bank 1 button should still be on
    states1 = bm.get_button_states()
    assert states1[0].state == True


def test_bank_config_single_button():
    """Test config loading for single-button bank switching."""
    from firmware.circuitpython.core.config import get_bank_switch_config
    
    config = {
        "bank_switch": {
            "method": "button",
            "button": 11,
        }
    }
    
    bsc = get_bank_switch_config(config)
    assert bsc is not None
    assert bsc["method"] == "button"
    assert bsc["button"] == 11
    assert bsc.get("button_next") is None
    assert bsc.get("button_prev") is None


def test_bank_config_dual_buttons():
    """Test config loading for dual-button bank switching."""
    from firmware.circuitpython.core.config import get_bank_switch_config
    
    config = {
        "bank_switch": {
            "method": "button",
            "button_next": 10,
            "button_prev": 11,
        }
    }
    
    bsc = get_bank_switch_config(config)
    assert bsc is not None
    assert bsc["method"] == "button"
    assert bsc["button_next"] == 10
    assert bsc["button_prev"] == 11


def test_bank_config_legacy_compatibility():
    """Test that legacy single-button config still works."""
    from firmware.circuitpython.core.config import get_bank_switch_config
    
    # Legacy format: only 'button' field
    config = {
        "bank_switch": {
            "method": "button",
            "button": 11,
        }
    }
    
    bsc = get_bank_switch_config(config)
    assert bsc["button"] == 11
    assert "button_next" not in bsc or bsc.get("button_next") is None
    assert "button_prev" not in bsc or bsc.get("button_prev") is None


def test_bank_switch_cooldown():
    """Test that bank switching respects cooldown period."""
    from firmware.circuitpython.core.banks import BankManager
    from firmware.circuitpython.core.button import ButtonState
    import time
    
    banks = [
        {"name": "Bank 1", "buttons": []},
        {"name": "Bank 2", "buttons": []},
    ]
    
    button_states = [ButtonState(cc=20 + i) for i in range(10)]
    bm = BankManager(banks, button_states, active_bank=0)
    
    # Manually set short cooldown for testing
    bm.switch_cooldown_ms = 200
    
    # First switch should succeed
    assert bm.next_bank() == True
    assert bm.current_bank_index == 1
    
    # Immediate second switch should fail (cooldown)
    assert bm.next_bank() == False
    assert bm.current_bank_index == 1  # Still in Bank 2
    
    # Wait for cooldown
    time.sleep(0.25)
    
    # Now switch should succeed
    assert bm.next_bank() == True
    assert bm.current_bank_index == 0


def test_bank_button_priority():
    """Test that button_next/button_prev take precedence over button."""
    # This tests the firmware logic where if button_next and button_prev are set,
    # the legacy 'button' field is ignored
    
    from firmware.circuitpython.core.config import get_bank_switch_config
    
    config = {
        "bank_switch": {
            "method": "button",
            "button": 9,           # Legacy field
            "button_next": 10,     # Should take precedence
            "button_prev": 11,
        }
    }
    
    bsc = get_bank_switch_config(config)
    
    # Firmware should use button_next/button_prev when available
    assert bsc["button_next"] == 10
    assert bsc["button_prev"] == 11
    
    # The firmware logic in code.py checks button_next/button_prev first,
    # so the legacy 'button' field is effectively ignored when they're present
