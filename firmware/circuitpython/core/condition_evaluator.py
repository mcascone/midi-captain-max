"""
Condition Evaluator for Conditional MIDI Commands

Evaluates conditions at runtime before dispatching MIDI commands.
Supports 5 condition types:
- button_state: Check if another button is on/off
- button_keytime: Check keytime state of another button
- received_midi: Check value of received MIDI messages
- expression: Check expression pedal position
- encoder: Check encoder position

Author: Maximilian Cascone
Date: 2026-01-26
"""


class ConditionEvaluator:
    """Evaluates conditions for conditional MIDI commands."""
    
    def __init__(self, button_states, received_cc_values, encoder_value, expression_values):
        """
        Initialize evaluator with current device state.
        
        Args:
            button_states: List of ButtonState objects (indexed by button number)
            received_cc_values: Dict[int, Dict[int, int]] - received_cc_values[channel][cc] = value
            encoder_value: Current encoder value (int, 0-127 or configured range)
            expression_values: Dict with 'exp1' and 'exp2' keys mapping to current values
        """
        self.button_states = button_states
        self.received_cc_values = received_cc_values
        self.encoder_value = encoder_value
        self.expression_values = expression_values
    
    def evaluate(self, condition):
        """
        Evaluate a condition and return True/False.
        
        Args:
            condition: Dict with 'type' field and type-specific fields
        
        Returns:
            bool: True if condition is met, False otherwise
        """
        cond_type = condition.get('type')
        
        if cond_type == 'button_state':
            return self._eval_button_state(condition)
        elif cond_type == 'button_keytime':
            return self._eval_button_keytime(condition)
        elif cond_type == 'received_midi':
            return self._eval_received_midi(condition)
        elif cond_type == 'expression':
            return self._eval_expression(condition)
        elif cond_type == 'encoder':
            return self._eval_encoder(condition)
        else:
            print(f"[EVAL] Unknown condition type: {cond_type}")
            return False
    
    def _eval_button_state(self, cond):
        """
        Evaluate button_state condition.
        
        Checks if specified button is 'on' or 'off'.
        """
        button_idx = cond.get('button', 0)
        expected_state = cond.get('state', 'on')  # 'on' or 'off'
        
        if button_idx < 0 or button_idx >= len(self.button_states):
            return False
        
        button = self.button_states[button_idx]
        actual_state = button.state  # True = on, False = off
        
        if expected_state == 'on':
            return actual_state
        else:  # 'off'
            return not actual_state
    
    def _eval_button_keytime(self, cond):
        """
        Evaluate button_keytime condition.
        
        Checks if specified button's keytime index matches expected value.
        Note: Keytimes are 0-indexed in config, but 1-indexed in ButtonState.current_keytime.
        """
        button_idx = cond.get('button', 0)
        expected_keytime = cond.get('keytime', 0)  # 0-indexed in config
        
        if button_idx < 0 or button_idx >= len(self.button_states):
            return False
        
        button = self.button_states[button_idx]
        # Convert 0-indexed config value to 1-indexed current_keytime for comparison
        return button.current_keytime == (expected_keytime + 1)
    
    def _eval_received_midi(self, cond):
        """
        Evaluate received_midi condition.
        
        Checks if a received CC value meets the condition (eq/ne/gt/lt/gte/lte).
        """
        channel = cond.get('channel', 0)
        cc = cond.get('cc')
        operator = cond.get('operator', 'eq')
        value = cond.get('value', 0)
        
        if cc is None:
            return False
        
        # Get the last received value for this CC on this channel
        if channel not in self.received_cc_values:
            return False
        if cc not in self.received_cc_values[channel]:
            return False
        
        actual_value = self.received_cc_values[channel][cc]
        
        if operator == 'eq':
            return actual_value == value
        elif operator == 'ne':
            return actual_value != value
        elif operator == 'gt':
            return actual_value > value
        elif operator == 'lt':
            return actual_value < value
        elif operator == 'gte':
            return actual_value >= value
        elif operator == 'lte':
            return actual_value <= value
        else:
            print(f"[EVAL] Unknown operator: {operator}")
            return False
    
    def _eval_expression(self, cond):
        """
        Evaluate expression pedal condition.
        
        Checks if expression pedal value meets the condition.
        """
        pedal = cond.get('pedal', 'exp1')  # 'exp1' or 'exp2'
        operator = cond.get('operator', 'gt')
        value = cond.get('value', 64)
        
        if pedal not in self.expression_values:
            return False
        
        actual_value = self.expression_values[pedal]
        
        if operator == 'eq':
            return actual_value == value
        elif operator == 'ne':
            return actual_value != value
        elif operator == 'gt':
            return actual_value > value
        elif operator == 'lt':
            return actual_value < value
        elif operator == 'gte':
            return actual_value >= value
        elif operator == 'lte':
            return actual_value <= value
        else:
            print(f"[EVAL] Unknown operator: {operator}")
            return False
    
    def _eval_encoder(self, cond):
        """
        Evaluate encoder position condition.
        
        Checks if encoder value meets the condition.
        """
        operator = cond.get('operator', 'gt')
        value = cond.get('value', 64)
        
        actual_value = self.encoder_value
        
        if operator == 'eq':
            return actual_value == value
        elif operator == 'ne':
            return actual_value != value
        elif operator == 'gt':
            return actual_value > value
        elif operator == 'lt':
            return actual_value < value
        elif operator == 'gte':
            return actual_value >= value
        elif operator == 'lte':
            return actual_value <= value
        else:
            print(f"[EVAL] Unknown operator: {operator}")
            return False
