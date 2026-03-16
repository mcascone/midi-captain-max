"""
Button and switch handling for MIDI Captain firmware.

Provides Switch class for input handling and ButtonState for state tracking.
"""


class Switch:
    """Footswitch with state tracking and edge detection.
    
    Expects a CircuitPython digitalio.DigitalInOut object or compatible mock.
    Uses pull-up configuration (True = not pressed, False = pressed).
    """

    def __init__(self, pin, digitalio_module=None):
        """Initialize switch on given pin.
        
        Args:
            pin: Board pin object
            digitalio_module: Optional digitalio module (for dependency injection in tests)
        """
        if digitalio_module is None:
            import digitalio as digitalio_module
        
        self.io = digitalio_module.DigitalInOut(pin)
        self.io.direction = digitalio_module.Direction.INPUT
        self.io.pull = digitalio_module.Pull.UP
        self.last_state = True  # Pull-up: True = not pressed

    @property
    def pressed(self):
        """Return True if switch is currently pressed."""
        return not self.io.value

    def changed(self):
        """Check if switch state changed since last call.
        
        Returns:
            Tuple of (changed: bool, pressed: bool)
        """
        current = self.pressed
        changed = current != self.last_state
        self.last_state = current
        return changed, current


class ButtonState:
    """Tracks toggle state and mode for a button.
    
    Supports toggle and momentary modes with bidirectional sync.
    Also supports keytimes (multi-press cycling through states).
    """
    
    def __init__(self, cc, mode="toggle", initial_state=False, keytimes=1):
        """Initialize button state.
        
        Args:
            cc: MIDI CC number for this button
            mode: "toggle" or "momentary"
            initial_state: Initial on/off state
            keytimes: Number of states to cycle through (1-99), default 1 (no cycling)
        """
        self.cc = cc
        self.mode = mode
        self._state = initial_state
        self.keytimes = max(1, min(99, keytimes))  # Clamp to 1-99
        self.current_keytime = 1  # Current position in keytime cycle (1-indexed)
    
    @property
    def state(self):
        """Current on/off state."""
        return self._state
    
    @state.setter
    def state(self, value):
        """Set state (used by host override)."""
        self._state = bool(value)
    
    def advance_keytime(self):
        """Advance to next keytime state, cycling back to 1 after max.

        No-op when keytimes == 1.
        """
        if self.keytimes > 1:
            self.current_keytime = (self.current_keytime % self.keytimes) + 1

    def on_press(self):
        """Handle button press.

        For keytimes > 1: advances to next keytime state via advance_keytime().

        NOTE: handle_switches() in code.py does NOT call this method — it calls
        advance_keytime() directly to keep keytime management and MIDI dispatch
        in one place. This method is used by tests and any external consumers
        that need the full ButtonState API without MIDI dispatch.

        Returns:
            Tuple of (state_changed: bool, new_state: bool, midi_value: int)
        """
        if self.mode == "momentary":
            self._state = True
            self.advance_keytime()
            return True, True, 127
        else:  # toggle
            if self.keytimes > 1:
                self.advance_keytime()
                self._state = True  # Always "on" when cycling keytimes
                return True, True, 127
            else:
                # Standard toggle behavior
                self._state = not self._state
                return True, self._state, 127 if self._state else 0
    
    def on_release(self):
        """Handle button release.

        NOTE: handle_switches() in code.py does NOT call this method — release
        handling is inlined there alongside MIDI dispatch. This method is used
        by tests and any external consumers that need the full ButtonState API.

        Returns:
            Tuple of (state_changed: bool, new_state: bool, midi_value: int)
            For toggle mode, returns (False, state, None) - no action on release
        """
        if self.mode == "momentary":
            self._state = False
            return True, False, 0
        else:  # toggle
            return False, self._state, None
    
    def on_midi_receive(self, value):
        """Handle incoming MIDI CC value (host override).
        
        Args:
            value: MIDI CC value (0-127)
            
        Returns:
            New state (True if value > 63)
        """
        self._state = value > 63
        return self._state
    
    def get_keytime(self):
        """Get current keytime index (1-indexed).
        
        Returns:
            Current keytime position (1 to keytimes)
        """
        return self.current_keytime
    
    def reset_keytime(self):
        """Reset keytime cycle back to position 1."""
        self.current_keytime = 1
        self._state = False
