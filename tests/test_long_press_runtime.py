"""
Runtime-style tests for long-press behavior.
Uses the existing switch mocks to simulate press/release and calls `handle_switches`.
"""

import sys
import time
from pathlib import Path

FIRMWARE_DIR = Path(__file__).parent.parent / "firmware" / "dev"
sys.path.insert(0, str(FIRMWARE_DIR))

from core.config import validate_config
import importlib.util

# Load firmware/dev/code.py as module `fw` to avoid stdlib `code` module collision
FIRMWARE_CODE = FIRMWARE_DIR / "code.py"
src = FIRMWARE_CODE.read_text()
# Strip the infinite main loop at the end for test import so module-level
# initialization runs but the runtime polling loop does not start.
loop_idx = src.rfind('\nwhile True:')
if loop_idx != -1:
    src = src[:loop_idx]

spec = importlib.util.spec_from_file_location("firmware_code", str(FIRMWARE_CODE))
fw = importlib.util.module_from_spec(spec)
exec(compile(src, str(FIRMWARE_CODE), 'exec'), fw.__dict__)


def _find_first_button_switch_index():
    # In STD10, if encoder present, footswitches start at index 1; else 0
    return 1 if fw.HAS_ENCODER else 0


def test_long_press_action_triggers(tmp_path, monkeypatch):
    # Use a minimal config with a long_press on first button
    cfg = {
        "device": "std10",
        "buttons": [
            {"label": "LP", "cc": 40, "color": "red", "long_press": {"type": "cc", "cc": 41, "value": 100, "threshold_ms": 200}}
        ]
    }
    validated = validate_config(cfg, button_count=fw.BUTTON_COUNT)

    # Inject validated config into firmware globals used by handle_switches
    fw.buttons = validated["buttons"]

    # Simulate a press on the first switch
    idx = _find_first_button_switch_index()
    sw = fw.switches[idx]

    # Press: monkeypatch the Switch.changed() to first return (True, True) then (False, True) while held
    seq = [(True, True)] + [(False, True)] * 5 + [(True, False)]
    calls = {"i": 0}

    def fake_changed():
        res = seq[calls["i"]]
        calls["i"] = min(calls["i"] + 1, len(seq) - 1)
        return res

    monkeypatch.setattr(sw, "changed", fake_changed)

    # Call handle_switches repeatedly to simulate time passing
    start = time.monotonic()
    for _ in range(len(seq)):
        fw.handle_switches()
        time.sleep(0.05)

    # If long-press triggered, status_label should reflect CC41 send
    assert "CC41" in fw.status_label.text or "PC41" in fw.status_label.text or "Note41" in fw.status_label.text


def test_short_press_does_not_trigger_longpress(tmp_path, monkeypatch):
    cfg = {
        "device": "std10",
        "buttons": [
            {"label": "SP", "cc": 50, "color": "green", "long_press": {"type": "cc", "cc": 51, "value": 100, "threshold_ms": 500}}
        ]
    }
    validated = validate_config(cfg, button_count=fw.BUTTON_COUNT)
    fw.buttons = validated["buttons"]

    idx = _find_first_button_switch_index()
    sw = fw.switches[idx]

    # Simulate a quick press/release sequence shorter than threshold
    seq = [(True, True), (True, False)]
    calls = {"i": 0}

    def fake_changed():
        res = seq[calls["i"]]
        calls["i"] = min(calls["i"] + 1, len(seq) - 1)
        return res

    monkeypatch.setattr(sw, "changed", fake_changed)

    for _ in range(3):
        fw.handle_switches()
        time.sleep(0.05)

    # Ensure long-press CC51 was not sent (status_label should not contain CC51)
    assert "CC51" not in fw.status_label.text
