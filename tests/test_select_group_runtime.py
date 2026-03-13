"""
Runtime-style tests for select-group behavior combined with long-press.
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
loop_idx = src.rfind('\nwhile True:')
if loop_idx != -1:
    src = src[:loop_idx]

spec = importlib.util.spec_from_file_location("firmware_code", str(FIRMWARE_CODE))
fw = importlib.util.module_from_spec(spec)
exec(compile(src, str(FIRMWARE_CODE), 'exec'), fw.__dict__)


def _first_button_index():
    return 1 if fw.HAS_ENCODER else 0


def test_select_group_short_press_and_long_press(tmp_path, monkeypatch):
    # Two buttons in same group; second has long_press configured
    cfg = {
        "device": "std10",
        "buttons": [
            {
                "label": "A",
                "color": "green",
                "select_group": "scene_a",
                "press": [{"type": "cc", "cc": 20, "value": 127}]
            },
            {
                "label": "B",
                "color": "red",
                "select_group": "scene_a",
                "press": [{"type": "cc", "cc": 21, "value": 127}],
                "long_press": [{"type": "cc", "cc": 22, "value": 100, "threshold_ms": 150}]
            }
        ]
    }

    validated = validate_config(cfg, button_count=fw.BUTTON_COUNT)
    fw.buttons = validated["buttons"]

    idx = _first_button_index()
    sw_a = fw.switches[idx]
    sw_b = fw.switches[idx + 1]

    # Simulate pressing B (short press) to select it
    seq_b = [(True, True), (True, False)]
    calls_b = {"i": 0}

    def fake_changed_b():
        res = seq_b[calls_b["i"]]
        calls_b["i"] = min(calls_b["i"] + 1, len(seq_b) - 1)
        return res

    monkeypatch.setattr(sw_b, "changed", fake_changed_b)

    for _ in range(3):
        fw.handle_switches()
        time.sleep(0.05)

    # After selection, B should be ON and A OFF
    assert fw.button_states[0].state == False
    assert fw.button_states[1].state == True

    # Now simulate holding B long enough to trigger long_press
    seq_b_long = [(True, True)] * 6 + [(True, False)]
    calls_b_long = {"i": 0}

    def fake_changed_b_long():
        res = seq_b_long[calls_b_long["i"]]
        calls_b_long["i"] = min(calls_b_long["i"] + 1, len(seq_b_long) - 1)
        return res

    monkeypatch.setattr(sw_b, "changed", fake_changed_b_long)

    for _ in range(len(seq_b_long)):
        fw.handle_switches()
        time.sleep(0.05)

    # Long-press should have sent CC22 (status_label reflects last TX)
    assert "CC22" in fw.status_label.text
    # Selection should remain B
    assert fw.button_states[1].state == True


def test_host_driven_select_group_preserves_exclusivity(tmp_path):
    cfg = {
        "device": "std10",
        "buttons": [
            {"label": "A", "cc": 30, "color": "green", "select_group": "scene_b"},
            {"label": "B", "cc": 31, "color": "red", "select_group": "scene_b"}
        ]
    }

    validated = validate_config(cfg, button_count=fw.BUTTON_COUNT)
    fw.buttons = validated["buttons"]

    # Simulate host sending CC31=127 to turn B on
    from adafruit_midi.control_change import ControlChange
    fw.midi.receive = lambda: ControlChange(31, 127, channel=0)
    fw.handle_midi()

    # B should be on and A off
    assert fw.button_states[0].state == False
    assert fw.button_states[1].state == True
