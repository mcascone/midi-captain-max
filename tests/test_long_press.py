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
    assert lp["type"] == "cc"
    assert lp["cc"] == 40
    assert lp["value"] == 100
    assert lp["threshold_ms"] == 600


def test_validate_button_long_press_note():
    btn = validate_button({
        "long_press": {"type": "note", "note": 36, "value": 80}
    }, index=1)

    assert "long_press" in btn
    lp = btn["long_press"]
    assert lp["type"] == "note"
    assert lp["note"] == 36
    assert lp["value"] == 80


def test_validate_config_preserves_global_threshold():
    cfg = validate_config({"buttons": [], "long_press_threshold_ms": 750}, button_count=2)
    assert cfg.get("long_press_threshold_ms") == 750
