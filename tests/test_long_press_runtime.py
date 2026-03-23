"""
Runtime-style tests for long-press behavior.
Uses the existing switch mocks to simulate press/release and calls `handle_switches`.
"""

import sys
from pathlib import Path

# Ensure firmware core modules are in path
FIRMWARE_DIR = Path(__file__).parent.parent / "firmware" / "circuitpython"
if str(FIRMWARE_DIR) not in sys.path:
    sys.path.insert(0, str(FIRMWARE_DIR))

from core.config import validate_config


def _find_first_button_switch_index(fw):
    # In STD10, if encoder present, footswitches start at index 1; else 0
    return 1 if fw.HAS_ENCODER else 0


def test_long_press_action_triggers(tmp_path, monkeypatch, firmware_module, mock_time):
    # Use a minimal config with a long_press on first button
    fw = firmware_module
    cfg = {
        "device": "std10",
        "buttons": [
            {
                "label": "LP",
                "color": "red",
                "press": [{"type": "cc", "cc": 40, "value": 127}],
                "long_press": [{"type": "cc", "cc": 41, "value": 100, "threshold_ms": 200}]
            }
        ]
    }
    validated = validate_config(cfg, button_count=fw.BUTTON_COUNT)

    # Inject validated config into firmware globals used by handle_switches
    fw.buttons = validated["buttons"]

    # Simulate a press on the first switch
    idx = _find_first_button_switch_index(fw)
    sw = fw.switches[idx]

    # Press: monkeypatch the Switch.changed() to first return (True, True) then (False, True) while held
    seq = [(True, True)] + [(False, True)] * 5 + [(True, False)]
    calls = {"i": 0}

    def fake_changed():
        res = seq[calls["i"]]
        calls["i"] = min(calls["i"] + 1, len(seq) - 1)
        return res

    monkeypatch.setattr(sw, "changed", fake_changed)

    # Call handle_switches repeatedly, advancing mocked time
    for _ in range(len(seq)):
        fw.handle_switches()
        mock_time['current'] += 0.05  # Advance 50ms per iteration

    # If long-press triggered, status_label should reflect CC41 send
    assert "CC41" in fw.status_label.text or "PC41" in fw.status_label.text or "Note41" in fw.status_label.text


def test_short_press_does_not_trigger_longpress(tmp_path, monkeypatch, firmware_module, mock_time):
    fw = firmware_module
    cfg = {
        "device": "std10",
        "buttons": [
            {
                "label": "SP",
                "color": "green",
                "press": [{"type": "cc", "cc": 50, "value": 127}],
                "long_press": [{"type": "cc", "cc": 51, "value": 100, "threshold_ms": 500}]
            }
        ]
    }
    validated = validate_config(cfg, button_count=fw.BUTTON_COUNT)
    fw.buttons = validated["buttons"]

    idx = _find_first_button_switch_index(fw)
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
        mock_time['current'] += 0.05  # Advance 50ms per iteration

    # Ensure long-press CC51 was not sent (status_label should not contain CC51)
    assert "CC51" not in fw.status_label.text
