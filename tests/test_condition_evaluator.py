"""Unit tests for condition evaluator."""

import sys
from pathlib import Path

# Add firmware/circuitpython to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'firmware' / 'circuitpython'))

from core.condition_evaluator import ConditionEvaluator
from core.button import ButtonState


def test_button_state_condition():
    """Test button_state condition type."""
    
    # Create button states
    buttons = [ButtonState(cc=20), ButtonState(cc=21), ButtonState(cc=22)]
    buttons[0].state = True   # Button 0 is ON
    buttons[1].state = False  # Button 1 is OFF
    
    evaluator = ConditionEvaluator(
        button_states=buttons,
        received_cc_values={},
        encoder_value=64,
        expression_values={'exp1': 0, 'exp2': 0}
    )
    
    # Test button 0 is on
    assert evaluator.evaluate({'type': 'button_state', 'button': 0, 'state': 'on'}) == True
    assert evaluator.evaluate({'type': 'button_state', 'button': 0, 'state': 'off'}) == False
    
    # Test button 1 is off
    assert evaluator.evaluate({'type': 'button_state', 'button': 1, 'state': 'on'}) == False
    assert evaluator.evaluate({'type': 'button_state', 'button': 1, 'state': 'off'}) == True


def test_button_keytime_condition():
    """Test button_keytime condition type."""
    
    buttons = [ButtonState(cc=20, keytimes=3), ButtonState(cc=21, keytimes=5)]
    buttons[0].current_keytime = 1  # keytime_index property uses current_keytime - 1
    buttons[1].current_keytime = 3
    
    evaluator = ConditionEvaluator(
        button_states=buttons,
        received_cc_values={},
        encoder_value=64,
        expression_values={'exp1': 0, 'exp2': 0}
    )
    
    # ButtonState.keytime_index is current_keytime - 1 (0-indexed)
    assert evaluator.evaluate({'type': 'button_keytime', 'button': 0, 'keytime': 0}) == True
    assert evaluator.evaluate({'type': 'button_keytime', 'button': 0, 'keytime': 1}) == False
    assert evaluator.evaluate({'type': 'button_keytime', 'button': 1, 'keytime': 2}) == True


def test_received_midi_condition():
    """Test received_midi condition type."""
    
    # Simulate received CC values
    received = {
        0: {20: 127, 21: 64},  # Channel 0
        1: {22: 0}              # Channel 1
    }
    
    evaluator = ConditionEvaluator(
        button_states=[],
        received_cc_values=received,
        encoder_value=64,
        expression_values={'exp1': 0, 'exp2': 0}
    )
    
    # Test equality
    assert evaluator.evaluate({'type': 'received_midi', 'channel': 0, 'cc': 20, 'operator': 'eq', 'value': 127}) == True
    assert evaluator.evaluate({'type': 'received_midi', 'channel': 0, 'cc': 20, 'operator': 'eq', 'value': 0}) == False
    
    # Test greater than
    assert evaluator.evaluate({'type': 'received_midi', 'channel': 0, 'cc': 21, 'operator': 'gt', 'value': 50}) == True
    assert evaluator.evaluate({'type': 'received_midi', 'channel': 0, 'cc': 21, 'operator': 'gt', 'value': 64}) == False
    
    # Test less than
    assert evaluator.evaluate({'type': 'received_midi', 'channel': 1, 'cc': 22, 'operator': 'lt', 'value': 10}) == True
    
    # Test non-existent CC
    assert evaluator.evaluate({'type': 'received_midi', 'channel': 0, 'cc': 99, 'operator': 'eq', 'value': 0}) == False


def test_expression_condition():
    """Test expression pedal condition type."""
    
    evaluator = ConditionEvaluator(
        button_states=[],
        received_cc_values={},
        encoder_value=64,
        expression_values={'exp1': 100, 'exp2': 20}
    )
    
    # Test exp1 greater than
    assert evaluator.evaluate({'type': 'expression', 'pedal': 'exp1', 'operator': 'gt', 'value': 64}) == True
    assert evaluator.evaluate({'type': 'expression', 'pedal': 'exp1', 'operator': 'gt', 'value': 100}) == False
    
    # Test exp2 less than
    assert evaluator.evaluate({'type': 'expression', 'pedal': 'exp2', 'operator': 'lt', 'value': 50}) == True
    
    # Test equality
    assert evaluator.evaluate({'type': 'expression', 'pedal': 'exp1', 'operator': 'eq', 'value': 100}) == True


def test_encoder_condition():
    """Test encoder position condition type."""
    
    evaluator = ConditionEvaluator(
        button_states=[],
        received_cc_values={},
        encoder_value=75,
        expression_values={'exp1': 0, 'exp2': 0}
    )
    
    # Test greater than or equal
    assert evaluator.evaluate({'type': 'encoder', 'operator': 'gte', 'value': 64}) == True
    assert evaluator.evaluate({'type': 'encoder', 'operator': 'gte', 'value': 75}) == True
    assert evaluator.evaluate({'type': 'encoder', 'operator': 'gte', 'value': 76}) == False
    
    # Test less than
    assert evaluator.evaluate({'type': 'encoder', 'operator': 'lt', 'value': 100}) == True


def test_all_operators():
    """Test all comparison operators work correctly."""
    
    received = {0: {20: 50}}
    evaluator = ConditionEvaluator(
        button_states=[],
        received_cc_values=received,
        encoder_value=64,
        expression_values={'exp1': 0, 'exp2': 0}
    )
    
    cond_base = {'type': 'received_midi', 'channel': 0, 'cc': 20}
    
    # Value is 50
    assert evaluator.evaluate({**cond_base, 'operator': 'eq', 'value': 50}) == True
    assert evaluator.evaluate({**cond_base, 'operator': 'eq', 'value': 51}) == False
    
    assert evaluator.evaluate({**cond_base, 'operator': 'ne', 'value': 51}) == True
    assert evaluator.evaluate({**cond_base, 'operator': 'ne', 'value': 50}) == False
    
    assert evaluator.evaluate({**cond_base, 'operator': 'gt', 'value': 49}) == True
    assert evaluator.evaluate({**cond_base, 'operator': 'gt', 'value': 50}) == False
    
    assert evaluator.evaluate({**cond_base, 'operator': 'lt', 'value': 51}) == True
    assert evaluator.evaluate({**cond_base, 'operator': 'lt', 'value': 50}) == False
    
    assert evaluator.evaluate({**cond_base, 'operator': 'gte', 'value': 50}) == True
    assert evaluator.evaluate({**cond_base, 'operator': 'gte', 'value': 49}) == True
    assert evaluator.evaluate({**cond_base, 'operator': 'gte', 'value': 51}) == False
    
    assert evaluator.evaluate({**cond_base, 'operator': 'lte', 'value': 50}) == True
    assert evaluator.evaluate({**cond_base, 'operator': 'lte', 'value': 51}) == True
    assert evaluator.evaluate({**cond_base, 'operator': 'lte', 'value': 49}) == False


if __name__ == '__main__':
    test_button_state_condition()
    test_button_keytime_condition()
    test_received_midi_condition()
    test_expression_condition()
    test_encoder_condition()
    test_all_operators()
    print("✅ All condition evaluator tests passed!")
