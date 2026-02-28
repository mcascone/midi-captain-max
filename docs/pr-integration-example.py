"""
Example integration of PR #51 (PC Messages) and PR #50 (Keytimes)

This file demonstrates how to merge both features into a cohesive design.
NOT EXECUTABLE - for reference only.
"""

# ============================================================================
# 1. ENHANCED ButtonState CLASS (core/button.py)
# ============================================================================

class ButtonState:
    """Tracks state, mode, keytimes, and message type for a button.
    
    Supports CC, PC, PC_inc, PC_dec message types with keytime cycling.
    """
    
    def __init__(self, cc=20, mode="toggle", initial_state=False, keytimes=1,
                 type="cc", program=0, pc_step=1):
        """Initialize button state.
        
        Args:
            cc: MIDI CC number (for CC type)
            mode: "toggle" or "momentary"
            initial_state: Initial on/off state
            keytimes: Number of states to cycle (1-99)
            type: Message type ("cc", "pc", "pc_inc", "pc_dec")
            program: Program number (for "pc" type)
            pc_step: Increment/decrement step (for "pc_inc"/"pc_dec")
        """
        self.cc = cc
        self.mode = mode
        self.type = type
        self.program = program
        self.pc_step = pc_step
        self._state = initial_state
        
        # Keytimes support (from PR #50)
        self.keytimes = max(1, min(99, keytimes))
        self.current_keytime = 1
    
    @property
    def state(self):
        """Current on/off state."""
        return self._state
    
    @state.setter
    def state(self, value):
        """Set state (used by host override)."""
        self._state = bool(value)
    
    def get_keytime(self):
        """Get current keytime position (1-indexed)."""
        return self.current_keytime
    
    def reset_keytime(self):
        """Reset to keytime 1 and off state."""
        self.current_keytime = 1
        self._state = False
    
    def on_press(self):
        """Handle button press.
        
        Returns:
            Tuple of (state_changed: bool, new_state: bool, midi_value: int/None)
        """
        # Advance keytime (cycles after reaching max)
        if self.keytimes > 1:
            self.current_keytime = (self.current_keytime % self.keytimes) + 1
        
        # Type-specific behavior
        if self.type in ("pc", "pc_inc", "pc_dec"):
            # PC messages: always trigger, no persistent state
            # (LED flash handled in main code)
            return True, False, None  # Return None, actual value computed in main
        elif self.mode == "momentary":
            self._state = True
            return True, True, 127
        else:  # toggle mode, CC type
            if self.keytimes > 1:
                # With keytimes, pressing always turns ON (sends cc_on for current state)
                self._state = True
                return True, True, 127
            else:
                # Standard toggle
                self._state = not self._state
                return True, self._state, 127 if self._state else 0
    
    def on_release(self):
        """Handle button release.
        
        Returns:
            Tuple of (state_changed: bool, new_state: bool, midi_value: int/None)
        """
        if self.mode == "momentary" and self.type == "cc":
            self._state = False
            return True, False, 0
        else:
            return False, self._state, None
    
    def on_midi_receive(self, value, is_pc=False):
        """Handle incoming MIDI message (host override).
        
        Args:
            value: MIDI CC/PC value (0-127)
            is_pc: True if this is a PC message
            
        Returns:
            New state (True if value > 63)
        """
        if is_pc and self.type in ("pc", "pc_inc", "pc_dec"):
            # Update internal PC value (stored elsewhere)
            return None  # Don't affect button state
        else:
            # CC message
            self._state = value > 63
            return self._state


# ============================================================================
# 2. ENHANCED validate_button() (core/config.py)
# ============================================================================

def validate_button(btn, index=0, global_channel=None):
    """Validate a button config dict, filling in defaults.
    
    Args:
        btn: Button config dict
        index: Button index (for default CC calculation)
        global_channel: Global MIDI channel (0-15)
        
    Returns:
        Validated button config with all required fields
    """
    # Channel handling
    default_channel = global_channel if global_channel is not None else 0
    
    # Message type
    message_type = btn.get("type", "cc")
    
    # Keytimes (clamped to 1-99)
    keytimes = btn.get("keytimes", 1)
    if not isinstance(keytimes, int):
        keytimes = 1
    keytimes = max(1, min(99, keytimes))
    
    # Base config (common to all types)
    validated = {
        "label": btn.get("label", str(index + 1)),
        "color": btn.get("color", "white"),
        "mode": btn.get("mode", "toggle"),
        "off_mode": btn.get("off_mode", "dim"),
        "channel": btn.get("channel", default_channel),
        "type": message_type,
        "keytimes": keytimes,
    }
    
    # Type-specific fields
    if message_type == "cc":
        validated["cc"] = btn.get("cc", 20 + index)
        validated["cc_on"] = btn.get("cc_on", 127)
        validated["cc_off"] = btn.get("cc_off", 0)
    elif message_type == "pc":
        validated["program"] = btn.get("program", 0)
    elif message_type in ("pc_inc", "pc_dec"):
        validated["pc_step"] = btn.get("pc_step", 1)
    
    # Keytimes states array (if keytimes > 1)
    if keytimes > 1:
        states = btn.get("states", [])
        if isinstance(states, list):
            # Filter to recognized fields only
            filtered_states = []
            for state in states:
                if isinstance(state, dict):
                    filtered = {}
                    # Copy recognized fields
                    for key in ["cc", "cc_on", "cc_off", "color", "label", 
                                "program", "pc_step", "type"]:
                        if key in state:
                            filtered[key] = state[key]
                    filtered_states.append(filtered)
            validated["states"] = filtered_states
        else:
            validated["states"] = []
    
    return validated


# ============================================================================
# 3. INITIALIZATION IN code.py
# ============================================================================

# Initialize ButtonState objects with both keytimes and type support
button_states = []
for i in range(BUTTON_COUNT):
    btn_config = buttons[i] if i < len(buttons) else {}
    button_states.append(ButtonState(
        cc=btn_config.get("cc", 20 + i),
        mode=btn_config.get("mode", "toggle"),
        keytimes=btn_config.get("keytimes", 1),
        type=btn_config.get("type", "cc"),
        program=btn_config.get("program", 0),
        pc_step=btn_config.get("pc_step", 1),
    ))

# PC-specific state (from PR #51)
pc_values = [0] * BUTTON_COUNT  # Current PC value per channel
pc_flash_timers = [0] * BUTTON_COUNT  # LED flash timers for PC buttons


# ============================================================================
# 4. HELPER FUNCTION: get_button_state_config()
# ============================================================================

def get_button_state_config(btn_config, keytime_index):
    """Get configuration for button at specific keytime state.
    
    Supports both CC and PC message types with per-state overrides.
    
    Args:
        btn_config: Button configuration dict
        keytime_index: Current keytime position (1-indexed)
        
    Returns:
        Dict with cc/program, cc_on, cc_off, color, and type for this state
    """
    states = btn_config.get("states", [])
    message_type = btn_config.get("type", "cc")
    
    # Get per-state overrides if available
    if states and 0 < keytime_index <= len(states):
        state_config = states[keytime_index - 1]
        
        # Type can be overridden per-state (future enhancement)
        state_type = state_config.get("type", message_type)
        
        # Type-specific fields
        if state_type == "cc":
            cc = state_config.get("cc", btn_config.get("cc", 20))
            cc_on = state_config.get("cc_on", btn_config.get("cc_on", 127))
            cc_off = state_config.get("cc_off", btn_config.get("cc_off", 0))
            result = {"type": "cc", "cc": cc, "cc_on": cc_on, "cc_off": cc_off}
        elif state_type == "pc":
            program = state_config.get("program", btn_config.get("program", 0))
            result = {"type": "pc", "program": program}
        elif state_type in ("pc_inc", "pc_dec"):
            pc_step = state_config.get("pc_step", btn_config.get("pc_step", 1))
            result = {"type": state_type, "pc_step": pc_step}
        else:
            # Fallback to base config
            result = _get_base_config(btn_config, message_type)
        
        color = get_color(state_config.get("color", btn_config.get("color", "white")))
    else:
        # Fallback to base button config
        result = _get_base_config(btn_config, message_type)
        color = get_color(btn_config.get("color", "white"))
    
    result["color"] = color
    return result


def _get_base_config(btn_config, message_type):
    """Helper to extract base config for a message type."""
    if message_type == "cc":
        return {
            "type": "cc",
            "cc": btn_config.get("cc", 20),
            "cc_on": btn_config.get("cc_on", 127),
            "cc_off": btn_config.get("cc_off", 0),
        }
    elif message_type == "pc":
        return {
            "type": "pc",
            "program": btn_config.get("program", 0),
        }
    elif message_type in ("pc_inc", "pc_dec"):
        return {
            "type": message_type,
            "pc_step": btn_config.get("pc_step", 1),
        }
    else:
        # Unknown type, default to CC
        return {
            "type": "cc",
            "cc": 20,
            "cc_on": 127,
            "cc_off": 0,
        }


# ============================================================================
# 5. MAIN LOOP: handle_switches()
# ============================================================================

def handle_switches():
    """Check all switches and send MIDI on state changes."""
    for btn_num, switch in enumerate(switches):
        changed, pressed = switch.changed()
        
        if not changed:
            continue
        
        btn_config = buttons[btn_num]
        btn_state = button_states[btn_num]
        
        if pressed:
            # Button pressed
            state_changed, new_state, _ = btn_state.on_press()
            
            if state_changed:
                # Get current keytime configuration
                keytime = btn_state.get_keytime()
                state_config = get_button_state_config(btn_config, keytime)
                
                message_type = state_config["type"]
                channel = btn_config.get("channel", 0)
                
                # Send appropriate MIDI message
                if message_type == "cc":
                    # CC message
                    cc = state_config["cc"]
                    value = state_config["cc_on"] if new_state else state_config["cc_off"]
                    midi.send(ControlChange(cc, value, channel=channel))
                    
                    # Update LED
                    color = state_config["color"]
                    if new_state:
                        pixels[btn_num * 3:(btn_num + 1) * 3] = [color] * 3
                    else:
                        off_color = get_off_color(color, btn_config.get("off_mode", "dim"))
                        pixels[btn_num * 3:(btn_num + 1) * 3] = [off_color] * 3
                
                elif message_type == "pc":
                    # Fixed PC message
                    program = state_config["program"]
                    midi.send(ProgramChange(program, channel=channel))
                    flash_pc_button(btn_num, state_config["color"])
                
                elif message_type == "pc_inc":
                    # Increment PC
                    step = state_config["pc_step"]
                    pc_values[btn_num] = clamp_pc_value(pc_values[btn_num] + step)
                    midi.send(ProgramChange(pc_values[btn_num], channel=channel))
                    flash_pc_button(btn_num, state_config["color"])
                
                elif message_type == "pc_dec":
                    # Decrement PC
                    step = state_config["pc_step"]
                    pc_values[btn_num] = clamp_pc_value(pc_values[btn_num] - step)
                    midi.send(ProgramChange(pc_values[btn_num], channel=channel))
                    flash_pc_button(btn_num, state_config["color"])
        
        else:
            # Button released
            state_changed, new_state, midi_value = btn_state.on_release()
            
            if state_changed and btn_state.type == "cc":
                # Only CC momentary buttons send on release
                keytime = btn_state.get_keytime()
                state_config = get_button_state_config(btn_config, keytime)
                cc = state_config["cc"]
                channel = btn_config.get("channel", 0)
                midi.send(ControlChange(cc, midi_value, channel=channel))
                
                # Update LED
                off_color = get_off_color(state_config["color"], 
                                         btn_config.get("off_mode", "dim"))
                pixels[btn_num * 3:(btn_num + 1) * 3] = [off_color] * 3


# ============================================================================
# 6. EXAMPLE CONFIGURATIONS
# ============================================================================

# Example 1: CC button with keytimes
CC_WITH_KEYTIMES = {
    "label": "VERB",
    "type": "cc",
    "cc": 20,
    "keytimes": 3,
    "states": [
        {"cc_on": 64, "color": "blue"},      # State 1: 50%
        {"cc_on": 96, "color": "cyan"},      # State 2: 75%
        {"cc_on": 127, "color": "white"}     # State 3: 100%
    ]
}

# Example 2: PC button with keytimes (cycle through programs)
PC_WITH_KEYTIMES = {
    "label": "PRESET",
    "type": "pc",
    "keytimes": 3,
    "states": [
        {"program": 0, "color": "red"},      # Preset 1
        {"program": 5, "color": "green"},    # Preset 6
        {"program": 10, "color": "blue"}     # Preset 11
    ]
}

# Example 3: PC inc/dec buttons (no keytimes needed)
PC_INC = {
    "label": "PC+",
    "type": "pc_inc",
    "pc_step": 1,
    "color": "orange"
}

PC_DEC = {
    "label": "PC-",
    "type": "pc_dec",
    "pc_step": 1,
    "color": "cyan"
}

# Example 4: Mixed types (FUTURE: per-state type switching)
MIXED_TYPES = {
    "label": "MULTI",
    "keytimes": 3,
    "states": [
        {"type": "cc", "cc": 20, "cc_on": 127, "color": "red"},
        {"type": "pc", "program": 5, "color": "green"},
        {"type": "cc", "cc": 21, "cc_on": 64, "color": "blue"}
    ]
}
