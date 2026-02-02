"""
Mock implementations of CircuitPython hardware modules.

These mocks allow running firmware logic on desktop Python without
actual hardware. Import these before importing firmware code to
replace CircuitPython-specific modules.
"""

from .board import *
from .digitalio import *
from .neopixel import *
from .displayio import *
