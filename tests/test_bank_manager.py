"""
Tests for BankManager class.

Tests bank switching, state persistence, and trigger detection.
"""

import sys
import os
import time

# Add firmware directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../firmware/circuitpython"))

from core.banks import BankManager
from core.button import ButtonState


def create_button_states(count):
    """Helper to create a list of ButtonState objects."""
    return [ButtonState(cc=20 + i) for i in range(count)]


def test_bank_manager_initialization():
    """Test BankManager initializes with correct state."""
    banks = [
        {"name": "Bank 1", "buttons": [{}, {}]},
        {"name": "Bank 2", "buttons": [{}, {}]},
        {"name": "Bank 3", "buttons": [{}, {}]},
    ]

    button_states = create_button_states(2)
    manager = BankManager(banks, button_states, active_bank=1)

    assert manager.current_bank_index == 1
    assert len(manager.banks) == 3
    assert manager.button_count == 2
    # Bank states dict should have entry for bank 1
    assert 1 in manager.bank_states


def test_bank_manager_default_initial_bank():
    """Test BankManager defaults to bank 0 when not specified."""
    banks = [{"name": "Bank 1", "buttons": [{}]}]

    button_states = create_button_states(1)
    manager = BankManager(banks, button_states)

    assert manager.current_bank_index == 0


def test_bank_manager_out_of_range_initial_bank():
    """Test BankManager clamps invalid initial bank to 0."""
    banks = [{"name": "Bank 1", "buttons": [{}]}]

    button_states = create_button_states(1)
    manager = BankManager(banks, button_states, active_bank=10)

    assert manager.current_bank_index == 0


def test_get_current_bank_config():
    """Test getting current bank configuration."""
    banks = [
        {"name": "Live", "buttons": [{"label": "A"}]},
        {"name": "Studio", "buttons": [{"label": "B"}]},
    ]

    button_states = create_button_states(1)
    manager = BankManager(banks, button_states, active_bank=1)

    bank_cfg = manager.get_current_bank_config()

    assert bank_cfg["name"] == "Studio"
    assert bank_cfg["buttons"][0]["label"] == "B"


def test_get_bank_button_states():
    """Test getting button states for current bank."""
    banks = [
        {"name": "Bank 1", "buttons": [{}, {}]},
        {"name": "Bank 2", "buttons": [{}, {}]},
    ]

    button_states = create_button_states(2)
    manager = BankManager(banks, button_states)

    # Get states for bank 0
    states = manager.get_button_states()

    assert isinstance(states, list)
    assert len(states) == 2
    assert all(isinstance(s, ButtonState) for s in states)


def test_switch_bank_valid():
    """Test switching to a valid bank."""
    banks = [
        {"name": "Bank 1", "buttons": [{}]},
        {"name": "Bank 2", "buttons": [{}]},
        {"name": "Bank 3", "buttons": [{}]},
    ]

    button_states = create_button_states(1)
    manager = BankManager(banks, button_states)

    result = manager.switch_bank(2)

    assert result is True
    assert manager.current_bank_index == 2


def test_switch_bank_invalid_negative():
    """Test switching to negative bank index fails."""
    banks = [{"name": "Bank 1", "buttons": [{}]}]

    button_states = create_button_states(1)
    manager = BankManager(banks, button_states)

    result = manager.switch_bank(-1)

    assert result is False
    assert manager.current_bank_index == 0  # Stayed at initial


def test_switch_bank_invalid_out_of_range():
    """Test switching to out-of-range bank fails."""
    banks = [
        {"name": "Bank 1", "buttons": [{}]},
        {"name": "Bank 2", "buttons": [{}]},
    ]

    button_states = create_button_states(1)
    manager = BankManager(banks, button_states)

    result = manager.switch_bank(5)

    assert result is False
    assert manager.current_bank_index == 0


def test_switch_bank_cooldown():
    """Test bank switch cooldown prevents rapid switching."""
    banks = [
        {"name": "Bank 1", "buttons": [{}]},
        {"name": "Bank 2", "buttons": [{}]},
    ]

    button_states = create_button_states(1)
    manager = BankManager(banks, button_states)

    # First switch should succeed
    result1 = manager.switch_bank(1)
    assert result1 is True
    assert manager.current_bank_index == 1

    # Immediate second switch should fail (cooldown)
    result2 = manager.switch_bank(0)
    assert result2 is False
    assert manager.current_bank_index == 1  # Stayed at bank 1


def test_switch_bank_cooldown_expires():
    """Test bank switch succeeds after cooldown expires."""
    banks = [
        {"name": "Bank 1", "buttons": [{}]},
        {"name": "Bank 2", "buttons": [{}]},
    ]

    button_states = create_button_states(1)
    manager = BankManager(banks, button_states)

    # First switch
    manager.switch_bank(1)
    assert manager.current_bank_index == 1

    # Wait for cooldown to expire (200ms)
    time.sleep(0.25)

    # Second switch should succeed
    result = manager.switch_bank(0)
    assert result is True
    assert manager.current_bank_index == 0


def test_switch_bank_preserves_state():
    """Test switching banks preserves button states."""
    banks = [
        {"name": "Bank 1", "buttons": [{}, {}]},
        {"name": "Bank 2", "buttons": [{}, {}]},
    ]

    button_states = create_button_states(2)
    manager = BankManager(banks, button_states)

    # Modify button states in bank 0
    states_bank0 = manager.get_button_states()
    states_bank0[0].state = True
    states_bank0[1].keytime = 2

    # Switch to bank 1
    manager.switch_bank(1)

    # Switch back to bank 0
    time.sleep(0.25)  # Wait for cooldown
    manager.switch_bank(0)

    # Check states were preserved
    restored_states = manager.get_button_states()
    assert restored_states[0].state is True
    assert restored_states[1].keytime == 2


def test_next_bank():
    """Test cycling to next bank."""
    banks = [
        {"name": "Bank 1", "buttons": [{}]},
        {"name": "Bank 2", "buttons": [{}]},
        {"name": "Bank 3", "buttons": [{}]},
    ]

    button_states = create_button_states(1)
    manager = BankManager(banks, button_states)

    # Start at bank 0
    assert manager.current_bank_index == 0

    # Next bank
    manager.next_bank()
    assert manager.current_bank_index == 1

    time.sleep(0.25)

    # Next bank
    manager.next_bank()
    assert manager.current_bank_index == 2


def test_next_bank_wraps():
    """Test next_bank wraps from last to first."""
    banks = [
        {"name": "Bank 1", "buttons": [{}]},
        {"name": "Bank 2", "buttons": [{}]},
        {"name": "Bank 3", "buttons": [{}]},
    ]

    button_states = create_button_states(1)
    manager = BankManager(banks, button_states, active_bank=2)

    # At bank 2 (last), next should wrap to 0
    manager.next_bank()

    assert manager.current_bank_index == 0


def test_previous_bank():
    """Test cycling to previous bank."""
    banks = [
        {"name": "Bank 1", "buttons": [{}]},
        {"name": "Bank 2", "buttons": [{}]},
        {"name": "Bank 3", "buttons": [{}]},
    ]

    button_states = create_button_states(1)
    manager = BankManager(banks, button_states, active_bank=2)

    # Start at bank 2
    assert manager.current_bank_index == 2

    # Previous bank
    manager.previous_bank()
    assert manager.current_bank_index == 1

    time.sleep(0.25)

    # Previous bank
    manager.previous_bank()
    assert manager.current_bank_index == 0


def test_previous_bank_wraps():
    """Test previous_bank wraps from first to last."""
    banks = [
        {"name": "Bank 1", "buttons": [{}]},
        {"name": "Bank 2", "buttons": [{}]},
        {"name": "Bank 3", "buttons": [{}]},
    ]

    button_states = create_button_states(1)
    manager = BankManager(banks, button_states)

    # At bank 0 (first), previous should wrap to 2 (last)
    manager.previous_bank()

    assert manager.current_bank_index == 2


def test_get_bank_switch_trigger_button():
    """Test button-triggered bank switching returns None (handled externally)."""
    switch_config = {
        "method": "button",
        "button": 10
    }

    button_states = create_button_states(1)
    manager = BankManager([], button_states)
    trigger = manager.get_bank_switch_trigger(switch_config, message_type=None)

    assert trigger is None  # Button triggers handled externally


def test_get_bank_switch_trigger_cc():
    """Test CC-triggered bank switching."""
    banks = [
        {"name": "Bank 1", "buttons": [{}]},
        {"name": "Bank 2", "buttons": [{}]},
        {"name": "Bank 3", "buttons": [{}]},
    ]
    switch_config = {
        "method": "cc",
        "cc": 64,
        "channel": 3
    }

    button_states = create_button_states(1)
    manager = BankManager(banks, button_states)
    
    # CC value 1 should switch to bank 1
    target = manager.get_bank_switch_trigger(switch_config, message_type="cc", value=1)
    assert target == 1
    
    # CC value 0 should switch to bank 0
    target = manager.get_bank_switch_trigger(switch_config, message_type="cc", value=0)
    assert target == 0
    
    # Out of range value returns None
    target = manager.get_bank_switch_trigger(switch_config, message_type="cc", value=10)
    assert target is None


def test_get_bank_switch_trigger_pc():
    """Test PC-triggered bank switching."""
    banks = [
        {"name": "Bank 1", "buttons": [{}]},
        {"name": "Bank 2", "buttons": [{}]},
        {"name": "Bank 3", "buttons": [{}]},
    ]
    switch_config = {
        "method": "pc",
        "channel": 1,
        "pc_base": 0
    }

    button_states = create_button_states(1)
    manager = BankManager(banks, button_states)
    
    # PC 0 → bank 0
    target = manager.get_bank_switch_trigger(switch_config, message_type="pc", value=0)
    assert target == 0
    
    # PC 1 → bank 1
    target = manager.get_bank_switch_trigger(switch_config, message_type="pc", value=1)
    assert target == 1
    
    # PC 2 → bank 2
    target = manager.get_bank_switch_trigger(switch_config, message_type="pc", value=2)
    assert target == 2


def test_get_bank_switch_trigger_pc_with_offset():
    """Test PC-triggered bank switching with pc_base offset."""
    banks = [
        {"name": "Bank 1", "buttons": [{}]},
        {"name": "Bank 2", "buttons": [{}]},
    ]
    switch_config = {
        "method": "pc",
        "channel": 0,
        "pc_base": 10  # PC 10 → bank 0, PC 11 → bank 1
    }

    button_states = create_button_states(1)
    manager = BankManager(banks, button_states)
    
    # PC 10 → bank 0
    target = manager.get_bank_switch_trigger(switch_config, message_type="pc", value=10)
    assert target == 0
    
    # PC 11 → bank 1
    target = manager.get_bank_switch_trigger(switch_config, message_type="pc", value=11)
    assert target == 1
    
    # PC 9 (before base) → None
    target = manager.get_bank_switch_trigger(switch_config, message_type="pc", value=9)
    assert target is None


def test_get_bank_switch_trigger_invalid_method():
    """Test invalid method returns None."""
    switch_config = {
        "method": "invalid"
    }

    button_states = create_button_states(1)
    manager = BankManager([], button_states)
    trigger = manager.get_bank_switch_trigger(switch_config)

    assert trigger is None


def test_bank_manager_empty_banks():
    """Test BankManager handles empty banks list."""
    button_states = create_button_states(1)
    manager = BankManager([], button_states)

    assert manager.current_bank_index == 0
    assert len(manager.banks) == 0

    # Operations should fail gracefully
    result = manager.switch_bank(0)
    assert result is False

    manager.next_bank()  # Should not crash
    assert manager.current_bank_index == 0

    manager.previous_bank()  # Should not crash
    assert manager.current_bank_index == 0
