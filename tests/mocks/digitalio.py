"""
Mock digitalio module - simulates CircuitPython digital I/O.
"""


class Direction:
    INPUT = "INPUT"
    OUTPUT = "OUTPUT"


class Pull:
    UP = "UP"
    DOWN = "DOWN"


class DigitalInOut:
    """Mock digital I/O pin."""
    
    def __init__(self, pin):
        self.pin = pin
        self.direction = None
        self.pull = None
        self._value = True  # Default: pulled high (not pressed)
    
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, val):
        self._value = val
    
    def deinit(self):
        """Release the pin."""
        pass
    
    def simulate_press(self):
        """Simulate a button press (active low)."""
        self._value = False
    
    def simulate_release(self):
        """Simulate a button release."""
        self._value = True
