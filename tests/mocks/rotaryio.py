"""
Mock rotaryio module - simulates CircuitPython rotary encoder.
"""


class IncrementalEncoder:
    """Mock rotary encoder."""
    
    def __init__(self, pin_a, pin_b, divisor=4):
        self.pin_a = pin_a
        self.pin_b = pin_b
        self.divisor = divisor
        self._position = 0
    
    @property
    def position(self):
        return self._position
    
    @position.setter
    def position(self, value):
        self._position = value
    
    def deinit(self):
        pass
    
    # Test helpers
    def simulate_turn(self, clicks):
        """Simulate turning the encoder by a number of clicks."""
        self._position += clicks
