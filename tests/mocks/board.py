"""
Mock board module - simulates CircuitPython board pin definitions.

Provides fake pin objects for all GPIO pins used by MIDI Captain devices.
"""


class MockPin:
    """A fake GPIO pin for testing."""
    
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return f"MockPin({self.name})"


# Standard GPIO pins (RP2040)
GP0 = MockPin("GP0")
GP1 = MockPin("GP1")
GP2 = MockPin("GP2")
GP3 = MockPin("GP3")
GP4 = MockPin("GP4")
GP5 = MockPin("GP5")
GP6 = MockPin("GP6")
GP7 = MockPin("GP7")
GP8 = MockPin("GP8")
GP9 = MockPin("GP9")
GP10 = MockPin("GP10")
GP11 = MockPin("GP11")
GP12 = MockPin("GP12")
GP13 = MockPin("GP13")
GP14 = MockPin("GP14")
GP15 = MockPin("GP15")
GP16 = MockPin("GP16")
GP17 = MockPin("GP17")
GP18 = MockPin("GP18")
GP19 = MockPin("GP19")
GP20 = MockPin("GP20")
GP21 = MockPin("GP21")
GP22 = MockPin("GP22")
GP23 = MockPin("GP23")
GP24 = MockPin("GP24")
GP25 = MockPin("GP25")
GP26 = MockPin("GP26")
GP27 = MockPin("GP27")
GP28 = MockPin("GP28")

# Special pins
LED = MockPin("LED")  # GP25 on Pico
VBUS_SENSE = MockPin("VBUS_SENSE")

# Analog pins
A0 = MockPin("A0")
A1 = MockPin("A1")
A2 = MockPin("A2")
A3 = MockPin("A3")
