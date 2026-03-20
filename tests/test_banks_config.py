"""
Tests for banks configuration functions.

Tests config migration, bank loading, and bank switching logic.
"""

import sys
import os

# Add firmware directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../firmware/circuitpython"))

from core.config import migrate_legacy_config, load_banks, get_active_bank_config, get_bank_switch_config


def test_migrate_legacy_config_with_buttons():
    """Test that legacy config with 'buttons' is migrated to banks format."""
    legacy_cfg = {
        "device": "std10",
        "buttons": [
            {"label": "Btn1", "cc": 20},
            {"label": "Btn2", "cc": 21},
        ]
    }

    migrated = migrate_legacy_config(legacy_cfg, button_count=2)

    assert "banks" in migrated
    assert len(migrated["banks"]) == 1
    assert migrated["banks"][0]["name"] == "Bank 1"
    assert len(migrated["banks"][0]["buttons"]) == 2
    assert migrated["banks"][0]["buttons"][0]["label"] == "Btn1"
    assert "buttons" not in migrated  # Legacy field removed
    assert migrated["active_bank"] == 0


def test_migrate_legacy_config_already_multi_bank():
    """Test that config with 'banks' passes through unchanged."""
    multi_bank_cfg = {
        "device": "std10",
        "banks": [
            {"name": "Live", "buttons": [{"label": "A"}]},
            {"name": "Studio", "buttons": [{"label": "B"}]},
        ],
        "active_bank": 1
    }

    migrated = migrate_legacy_config(multi_bank_cfg, button_count=1)

    assert "banks" in migrated
    assert len(migrated["banks"]) == 2
    assert migrated["banks"][0]["name"] == "Live"
    assert migrated["banks"][1]["name"] == "Studio"
    assert migrated["active_bank"] == 1


def test_migrate_legacy_config_empty():
    """Test that config with neither buttons nor banks gets default bank."""
    empty_cfg = {"device": "mini6"}

    migrated = migrate_legacy_config(empty_cfg, button_count=6)

    assert "banks" in migrated
    assert len(migrated["banks"]) == 1
    assert migrated["banks"][0]["name"] == "Bank 1"
    assert len(migrated["banks"][0]["buttons"]) == 6
    # Check default button config
    assert migrated["banks"][0]["buttons"][0]["label"] == "1"
    assert migrated["banks"][0]["buttons"][0]["cc"] == 20
    assert migrated["active_bank"] == 0


def test_load_banks():
    """Test loading banks array from config."""
    cfg = {
        "banks": [
            {"name": "Bank A", "buttons": []},
            {"name": "Bank B", "buttons": []},
            {"name": "Bank C", "buttons": []},
        ]
    }

    banks = load_banks(cfg)

    assert len(banks) == 3
    assert banks[0]["name"] == "Bank A"
    assert banks[1]["name"] == "Bank B"
    assert banks[2]["name"] == "Bank C"


def test_load_banks_empty():
    """Test loading banks from config with no banks."""
    cfg = {"device": "std10"}

    banks = load_banks(cfg)

    assert banks == []


def test_get_active_bank_config():
    """Test getting active bank configuration."""
    cfg = {
        "banks": [
            {"name": "Bank 1", "buttons": [{"label": "A"}]},
            {"name": "Bank 2", "buttons": [{"label": "B"}]},
            {"name": "Bank 3", "buttons": [{"label": "C"}]},
        ],
        "active_bank": 1
    }

    bank_idx, bank_cfg = get_active_bank_config(cfg)

    assert bank_idx == 1
    assert bank_cfg["name"] == "Bank 2"
    assert bank_cfg["buttons"][0]["label"] == "B"


def test_get_active_bank_config_default():
    """Test getting active bank when active_bank not specified."""
    cfg = {
        "banks": [
            {"name": "Bank 1", "buttons": [{"label": "A"}]},
            {"name": "Bank 2", "buttons": [{"label": "B"}]},
        ]
    }

    bank_idx, bank_cfg = get_active_bank_config(cfg)

    assert bank_idx == 0
    assert bank_cfg["name"] == "Bank 1"


def test_get_active_bank_config_out_of_range():
    """Test that out-of-range active_bank is clamped to 0."""
    cfg = {
        "banks": [
            {"name": "Bank 1", "buttons": []},
        ],
        "active_bank": 10  # Out of range
    }

    bank_idx, bank_cfg = get_active_bank_config(cfg)

    assert bank_idx == 0
    assert bank_cfg["name"] == "Bank 1"


def test_get_active_bank_config_no_banks():
    """Test getting active bank when no banks exist."""
    cfg = {"device": "std10"}

    bank_idx, bank_cfg = get_active_bank_config(cfg)

    assert bank_idx == 0
    assert bank_cfg is None


def test_get_bank_switch_config():
    """Test getting bank switch configuration."""
    cfg = {
        "bank_switch": {
            "method": "button",
            "button": 10,
            "channel": 0
        }
    }

    switch_cfg = get_bank_switch_config(cfg)

    assert switch_cfg is not None
    assert switch_cfg["method"] == "button"
    assert switch_cfg["button"] == 10


def test_get_bank_switch_config_none():
    """Test getting bank switch config when not configured."""
    cfg = {"device": "std10"}

    switch_cfg = get_bank_switch_config(cfg)

    assert switch_cfg is None


def test_full_migration_workflow():
    """Test complete migration workflow: legacy → multi-bank → load banks."""
    legacy_cfg = {
        "device": "std10",
        "global_channel": 0,
        "buttons": [
            {"label": f"Btn{i+1}", "cc": 20 + i}
            for i in range(10)
        ]
    }

    # Migrate
    migrated = migrate_legacy_config(legacy_cfg, button_count=10)

    # Load banks
    banks = load_banks(migrated)
    assert len(banks) == 1
    assert len(banks[0]["buttons"]) == 10

    # Get active bank
    bank_idx, bank_cfg = get_active_bank_config(migrated)
    assert bank_idx == 0
    assert bank_cfg["name"] == "Bank 1"
    assert len(bank_cfg["buttons"]) == 10
    assert bank_cfg["buttons"][0]["label"] == "Btn1"
    assert bank_cfg["buttons"][9]["label"] == "Btn10"
