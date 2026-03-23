"""
Runtime-style tests for tap-mode behavior: tap-mode buttons stay ON
and send their configured message on every physical press.
"""

import sys
from pathlib import Path

# Ensure firmware core modules are in path
FIRMWARE_DIR = Path(__file__).parent.parent / "firmware" / "circuitpython"
if str(FIRMWARE_DIR) not in sys.path:
    sys.path.insert(0, str(FIRMWARE_DIR))

from core.config import validate_config


def _first_button_index(fw):
    return 1 if fw.HAS_ENCODER else 0


def test_tap_mode_always_on_and_sends_on_each_press(tmp_path, monkeypatch, firmware_module, mock_time):
    fw = firmware_module
    cfg = {
        "device": "std10",
        "buttons": [
            {"label": "TAP", "cc": 40, "color": "blue", "mode": "tap"}
        ]
    }

    validated = validate_config(cfg, button_count=fw.BUTTON_COUNT)
    fw.buttons = validated["buttons"]

    idx = _first_button_index(fw)
    sw = fw.switches[idx]
    btn_num = idx + 1

    # Ensure tap-mode button does not keep persistent logical ON state
    fw.button_states[idx].state = False
    fw.set_button_state(btn_num, False)
    assert fw.button_states[idx].state is False

    # Capture outgoing MIDI sends
    sent = []
    monkeypatch.setattr(fw.midi_usb, "send", lambda msg: sent.append(msg))

    # Simulate 3 quick press/release cycles
    seq = [(True, True), (True, False)] * 3
    calls = {"i": 0}

    def fake_changed():
        res = seq[calls["i"]]
        calls["i"] = min(calls["i"] + 1, len(seq) - 1)
        return res

    monkeypatch.setattr(sw, "changed", fake_changed)

    for _ in range(len(seq)):
        fw.handle_switches()
        mock_time['current'] += 0.01  # Advance 10ms per iteration

    # Expect at least one MIDI send per physical press (3 presses)
    assert len(sent) >= 3
    # Button should remain logically OFF (tap does not persist state)
    assert fw.button_states[idx].state is False
    # Status label should reflect last TX for the configured CC
    assert "CC40" in fw.status_label.text
