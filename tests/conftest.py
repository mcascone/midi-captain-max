"""
Pytest configuration and fixtures for MIDI Captain tests.

This file sets up the mock modules before any firmware code is imported.
"""

import sys
from pathlib import Path

# Add tests/mocks to the path so we can import our mock modules
TESTS_DIR = Path(__file__).parent
MOCKS_DIR = TESTS_DIR / "mocks"


def install_mocks():
    """Install mock modules into sys.modules before importing firmware code."""
    from tests.mocks import board, digitalio, neopixel, displayio, busio
    from tests.mocks import usb_midi, rotaryio, analogio, terminalio, supervisor
    from tests.mocks import adafruit_midi
    from tests.mocks.adafruit_midi import control_change, program_change, note_on, note_off, system_exclusive

    sys.modules["board"] = board
    sys.modules["digitalio"] = digitalio
    sys.modules["neopixel"] = neopixel
    sys.modules["displayio"] = displayio
    sys.modules["busio"] = busio
    sys.modules["usb_midi"] = usb_midi
    sys.modules["rotaryio"] = rotaryio
    sys.modules["analogio"] = analogio
    sys.modules["terminalio"] = terminalio
    sys.modules["supervisor"] = supervisor

    # Adafruit MIDI mocks
    sys.modules["adafruit_midi"] = adafruit_midi
    sys.modules["adafruit_midi.control_change"] = control_change
    sys.modules["adafruit_midi.program_change"] = program_change
    sys.modules["adafruit_midi.note_on"] = note_on
    sys.modules["adafruit_midi.note_off"] = note_off
    sys.modules["adafruit_midi.system_exclusive"] = system_exclusive

    # Mock additional CircuitPython modules that may be needed
    # These are stub modules for imports that we don't need to fully mock

    class StubModule:
        def __getattr__(self, name):
            return StubModule()
        def __call__(self, *args, **kwargs):
            return StubModule()

    # Adafruit libraries that need stubs
    sys.modules["adafruit_display_text"] = StubModule()
    sys.modules["adafruit_display_text.label"] = StubModule()
    sys.modules["adafruit_bitmap_font"] = StubModule()
    sys.modules["adafruit_bitmap_font.bitmap_font"] = StubModule()
    sys.modules["adafruit_st7789"] = StubModule()


# Install mocks at import time (before tests run)
install_mocks()


# Fixtures
import pytest


@pytest.fixture
def mock_board():
    """Provide access to mock board module."""
    from tests.mocks import board
    return board


@pytest.fixture
def mock_neopixel():
    """Provide a fresh NeoPixel instance for testing."""
    from tests.mocks.neopixel import NeoPixel
    from tests.mocks.board import GP7
    return NeoPixel(GP7, 30)


@pytest.fixture
def mock_switches():
    """Provide mock switch inputs for testing."""
    from tests.mocks.digitalio import DigitalInOut, Direction, Pull
    from tests.mocks import board

    switch_pins = [
        board.GP0, board.GP1, board.GP25, board.GP24, board.GP23,
        board.GP20, board.GP9, board.GP10, board.GP11, board.GP18, board.GP19
    ]

    switches = []
    for pin in switch_pins:
        sw = DigitalInOut(pin)
        sw.direction = Direction.INPUT
        sw.pull = Pull.UP
        switches.append(sw)

    return switches


@pytest.fixture
def sample_config():
    """Provide a sample configuration dict."""
    return {
        "buttons": [
            {"label": "1", "cc": 20, "color": "red"},
            {"label": "2", "cc": 21, "color": "green"},
            {"label": "3", "cc": 22, "color": "blue"},
            {"label": "4", "cc": 23, "color": "yellow"},
            {"label": "Down", "cc": 24, "color": "cyan"},
            {"label": "A", "cc": 25, "color": "magenta"},
            {"label": "B", "cc": 26, "color": "orange"},
            {"label": "C", "cc": 27, "color": "purple"},
            {"label": "D", "cc": 28, "color": "white"},
            {"label": "Up", "cc": 29, "color": "red"},
        ]
    }


@pytest.fixture
def mock_time(monkeypatch):
    """
    Provide a controllable time mock for testing cooldowns and timing.
    Returns a dict with 'current' key that can be modified to advance time.
    """
    time_state = {"current": 0.0}
    
    def fake_monotonic():
        return time_state["current"]
    
    import time
    monkeypatch.setattr(time, "monotonic", fake_monotonic)
    
    return time_state


# Cache for compiled firmware code (immutable) to speed up runtime tests
_firmware_compiled_code = None


@pytest.fixture
def firmware_module():
    """
    Load firmware code module for runtime tests with per-test isolation.
    
    Compiles the firmware code once per session but creates a fresh module
    instance for each test to avoid state pollution between tests.
    """
    global _firmware_compiled_code
    
    import importlib.util
    
    FIRMWARE_DIR = Path(__file__).parent.parent / "firmware" / "circuitpython"
    FIRMWARE_CODE = FIRMWARE_DIR / "code.py"
    
    # Compile firmware code once per session (immutable cache)
    if _firmware_compiled_code is None:
        src = FIRMWARE_CODE.read_text()
        loop_idx = src.rfind('\nwhile True:')
        if loop_idx != -1:
            src = src[:loop_idx]
        _firmware_compiled_code = compile(src, str(FIRMWARE_CODE), 'exec')
    
    # Create fresh module instance for this test (mutable, isolated state)
    spec = importlib.util.spec_from_file_location("firmware_code", str(FIRMWARE_CODE))
    fw = importlib.util.module_from_spec(spec)
    exec(_firmware_compiled_code, fw.__dict__)
    
    return fw
