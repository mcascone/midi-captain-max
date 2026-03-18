"""
Tests for config migration tool (tools/migrate_config.py).

Tests the migration of old config format to new format.
"""

import sys
import json
import tempfile
from pathlib import Path

# Add tools directory to path to import migrate_config
tools_dir = Path(__file__).parent.parent / "tools"
sys.path.insert(0, str(tools_dir))

from migrate_config import migrate_button_to_event_format, migrate_config


def test_migrate_cc_button():
    """Test migration of old CC button format."""
    old_btn = {
        "label": "TSC",
        "type": "cc",
        "cc": 20,
        "cc_on": 127,
        "cc_off": 0,
        "color": "green"
    }
    
    migrated = migrate_button_to_event_format(old_btn, index=0, global_channel=0)
    
    assert "press" in migrated
    assert len(migrated["press"]) == 1
    assert migrated["press"][0]["type"] == "cc"
    assert migrated["press"][0]["cc"] == 20
    assert migrated["press"][0]["value"] == 127
    assert migrated["label"] == "TSC"
    assert migrated["color"] == "green"
    # Legacy fields should be removed
    assert "type" not in migrated
    assert "cc_on" not in migrated
    assert "cc_off" not in migrated


def test_migrate_momentary_button():
    """Test migration of momentary button with release action."""
    old_btn = {
        "label": "TREM",
        "type": "cc",
        "cc": 30,
        "cc_on": 127,
        "cc_off": 0,
        "mode": "momentary",
        "color": "white"
    }
    
    migrated = migrate_button_to_event_format(old_btn, index=0, global_channel=0)
    
    assert "press" in migrated
    assert "release" in migrated
    assert migrated["press"][0]["value"] == 127
    assert migrated["release"][0]["value"] == 0
    assert migrated["mode"] == "momentary"


def test_migrate_pc_button():
    """Test migration of PC button (no release)."""
    old_btn = {
        "label": "DRIVE",
        "type": "pc",
        "program": 5,
        "color": "red"
    }
    
    migrated = migrate_button_to_event_format(old_btn, index=0, global_channel=0)
    
    assert "press" in migrated
    assert migrated["press"][0]["type"] == "pc"
    assert migrated["press"][0]["program"] == 5
    # PC buttons don't have release
    assert "release" not in migrated


def test_migrate_long_press_dict_to_array():
    """Test migration of old-style long_press dict to array."""
    old_btn = {
        "label": "EDGE",
        "type": "cc",
        "cc": 30,
        "cc_on": 127,
        "long_press": {"type": "cc", "cc": 31, "value": 127, "threshold_ms": 700}
    }
    
    migrated = migrate_button_to_event_format(old_btn, index=0, global_channel=0)
    
    assert "long_press" in migrated
    assert isinstance(migrated["long_press"], list)
    assert len(migrated["long_press"]) == 1
    assert migrated["long_press"][0]["cc"] == 31
    assert migrated["long_press"][0]["threshold_ms"] == 700


def test_migrate_button_already_new_format():
    """Test that already-migrated buttons pass through unchanged."""
    new_btn = {
        "label": "TSC",
        "cc": 20,
        "color": "green",
        "press": [{"type": "cc", "cc": 20, "value": 127, "channel": 0}]
    }
    
    migrated = migrate_button_to_event_format(new_btn, index=0, global_channel=0)
    
    # Should pass through unchanged
    assert "press" in migrated
    assert migrated["press"][0]["cc"] == 20
    assert migrated["label"] == "TSC"


def test_migrate_full_config():
    """Test migration of complete config with multiple buttons."""
    old_config = {
        "device": "std10",
        "global_channel": 0,
        "buttons": [
            {"label": "TSC", "type": "cc", "cc": 20, "cc_on": 127, "color": "green"},
            {"label": "DRIVE", "type": "pc", "program": 5, "color": "red"}
        ],
        "encoder": {
            "enabled": True,
            "cc": 11
        }
    }
    
    template_config = {
        "device": "std10",
        "usb_drive_name": "MIDICAPTAIN",
        "dev_mode": False,
        "display": {
            "button_text_size": "medium",
            "status_text_size": "medium"
        },
        "long_press_threshold_ms": 600
    }
    
    migrated = migrate_config(old_config, template_config)
    
    # Check new fields added
    assert migrated["usb_drive_name"] == "MIDICAPTAIN"
    assert migrated["dev_mode"] is False
    assert "display" in migrated
    
    # Check buttons migrated
    assert len(migrated["buttons"]) == 2
    assert "press" in migrated["buttons"][0]
    assert migrated["buttons"][0]["label"] == "TSC"
    assert "press" in migrated["buttons"][1]
    assert migrated["buttons"][1]["label"] == "DRIVE"
    
    # Check user encoder config preserved
    assert migrated["encoder"]["enabled"] is True
    assert migrated["encoder"]["cc"] == 11
    
    # Check template field added
    assert migrated["long_press_threshold_ms"] == 600


def test_migrate_preserves_user_customizations():
    """Test that user customizations are preserved during migration."""
    old_config = {
        "device": "mini6",
        "global_channel": 5,
        "usb_drive_name": "MY_DEVICE",
        "buttons": [
            {"label": "CUSTOM", "type": "cc", "cc": 99, "cc_on": 64, "color": "purple"}
        ]
    }
    
    template_config = {
        "device": "std10",
        "usb_drive_name": "MIDICAPTAIN",
        "dev_mode": False,
        "display": {}
    }
    
    migrated = migrate_config(old_config, template_config)
    
    # User customizations should be preserved
    assert migrated["device"] == "mini6"  # User's device
    assert migrated["global_channel"] == 5  # User's channel
    assert migrated["usb_drive_name"] == "MY_DEVICE"  # User's name
    assert migrated["buttons"][0]["label"] == "CUSTOM"
    assert migrated["buttons"][0]["press"][0]["cc"] == 99
    assert migrated["buttons"][0]["press"][0]["value"] == 64
    assert migrated["buttons"][0]["color"] == "purple"


def test_migrate_with_channel_override():
    """Test that per-button channel overrides are preserved."""
    old_btn = {
        "label": "MULTI",
        "type": "cc",
        "cc": 20,
        "cc_on": 127,
        "channel": 3,  # Different from global
        "color": "blue"
    }
    
    migrated = migrate_button_to_event_format(old_btn, index=0, global_channel=0)
    
    assert migrated["press"][0]["channel"] == 3
    assert migrated["channel"] == 3


def test_migrate_pc_inc_button():
    """Test migration of PC increment button."""
    old_btn = {
        "label": "NEXT",
        "type": "pc_inc",
        "pc_step": 1,
        "color": "cyan"
    }
    
    migrated = migrate_button_to_event_format(old_btn, index=0, global_channel=0)
    
    assert "press" in migrated
    assert migrated["press"][0]["type"] == "pc_inc"
    assert migrated["press"][0]["pc_step"] == 1


def test_migrate_note_button():
    """Test migration of Note button."""
    old_btn = {
        "label": "KICK",
        "type": "note",
        "note": 36,
        "velocity_on": 127,
        "velocity_off": 0,
        "mode": "momentary"
    }
    
    migrated = migrate_button_to_event_format(old_btn, index=0, global_channel=0)
    
    assert "press" in migrated
    assert "release" in migrated
    assert migrated["press"][0]["type"] == "note"
    assert migrated["press"][0]["note"] == 36
    assert migrated["press"][0]["velocity"] == 127
    assert migrated["release"][0]["velocity"] == 0
