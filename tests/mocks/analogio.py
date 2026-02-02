"""
Mock analogio module - simulates CircuitPython analog I/O.
"""


class AnalogIn:
    """Mock analog input pin."""
    
    def __init__(self, pin):
        self.pin = pin
        self._value = 32768  # Mid-range (16-bit ADC)
    
    @property
    def value(self):
        """Raw 16-bit ADC value (0-65535)."""
        return self._value
    
    @property
    def reference_voltage(self):
        """ADC reference voltage."""
        return 3.3
    
    def deinit(self):
        pass
    
    # Test helpers
    def set_value(self, value):
        """Set the raw ADC value (0-65535)."""
        self._value = max(0, min(65535, value))
    
    def set_voltage(self, voltage):
        """Set the voltage (0-3.3V)."""
        self._value = int((voltage / 3.3) * 65535)


class AnalogOut:
    """Mock analog output pin."""
    
    def __init__(self, pin):
        self.pin = pin
        self._value = 0
    
    @property
    def value(self):
        return self._value
    
    @value.setter
    def value(self, val):
        self._value = max(0, min(65535, val))
    
    def deinit(self):
        pass
