"""
Tests for long-press config validation.
"""

import sys
from pathlib import Path

FIRMWARE_DIR = Path(__file__).parent.parent / "firmware" / "dev"
sys.path.insert(0, str(FIRMWARE_DIR))

from core.config import validate_button, validate_config


def test_validate_button_long_press_cc():
    btn = validate_button({
        "long_press": {"type": "cc", "cc": 40, "value": 100, "threshold_ms": 600}
    }, index=0)

    assert "long_press" in btn
    lp = btn["long_press"]
    assert isinstance(lp, list), "long_press should be converted to array"
    assert len(lp) == 1
    cmd = lp[0]
    assert cmd["type"] == "cc"
    assert cmd["cc"] == 40
    assert cmd["value"] == 100
    assert cmd["threshold_ms"] == 600


def test_validate_button_long_press_note():
    btn = validate_button({
        "long_press": {"type": "note", "note": 36, "value": 80}
    }, index=1)

    assert "long_press" in btn
    lp = btn["long_press"]
    assert isinstance(lp, list), "long_press should be converted to array"
    assert len(lp) == 1
    cmd = lp[0]
    assert cmd["type"] == "note"
    assert cmd["note"] == 36
    assert cmd["velocity"] == 80  # 'value' is converted to 'velocity' for note type


def test_validate_config_preserves_global_threshold():
    cfg = validate_config({"buttons": [], "long_press_threshold_ms": 750}, button_count=2)
    assert cfg.get("long_press_threshold_ms") == 750
