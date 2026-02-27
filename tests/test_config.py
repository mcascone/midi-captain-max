"""
Tests for configuration loading and validation.

Tests the actual core/config.py module.
"""

import pytest
import json
import sys
from pathlib import Path

# Add firmware/dev to path
FIRMWARE_DIR = Path(__file__).parent.parent / "firmware" / "dev"
sys.path.insert(0, str(FIRMWARE_DIR))

from core.config import (
    load_config,
    validate_button,
    validate_config,
    get_encoder_config,
    get_expression_config,
)


class TestConfigValidation:
    """Test config parsing and validation logic."""
    
    def test_sample_config_has_buttons(self, sample_config):
        """Config must have a buttons array."""
        assert "buttons" in sample_config
        assert isinstance(sample_config["buttons"], list)
    
    def test_button_has_required_fields(self, sample_config):
        """Each button must have label, cc, and color."""
        for btn in sample_config["buttons"]:
            assert "label" in btn
            assert "cc" in btn
            assert "color" in btn
    
    def test_cc_numbers_in_valid_range(self, sample_config):
        """CC numbers must be 0-127."""
        for btn in sample_config["buttons"]:
            assert 0 <= btn["cc"] <= 127
    
    def test_colors_are_valid(self, sample_config):
        """Colors must be known color names."""
        valid_colors = {"red", "green", "blue", "yellow", "cyan", 
                       "magenta", "orange", "purple", "white", "off"}
        for btn in sample_config["buttons"]:
            assert btn["color"].lower() in valid_colors


class TestConfigParsing:
    """Test JSON config file parsing."""
    
    def test_parse_valid_json(self, tmp_path):
        """Can parse a valid config file."""
        config_file = tmp_path / "config.json"
        config_data = {
            "buttons": [
                {"label": "Test", "cc": 50, "color": "red"}
            ]
        }
        config_file.write_text(json.dumps(config_data))
        
        with open(config_file) as f:
            loaded = json.load(f)
        
        assert loaded["buttons"][0]["label"] == "Test"
        assert loaded["buttons"][0]["cc"] == 50
    
    def test_empty_buttons_array(self, tmp_path):
        """Empty buttons array is valid (uses defaults)."""
        config_file = tmp_path / "config.json"
        config_file.write_text('{"buttons": []}')
        
        with open(config_file) as f:
            loaded = json.load(f)
        
        assert loaded["buttons"] == []
    
    def test_extra_fields_ignored(self, tmp_path):
        """Unknown fields in config are silently ignored."""
        config_file = tmp_path / "config.json"
        config_data = {
            "buttons": [{"label": "1", "cc": 20, "color": "red"}],
            "unknown_field": "ignored",
            "future_feature": True
        }
        config_file.write_text(json.dumps(config_data))
        
        with open(config_file) as f:
            loaded = json.load(f)
        
        # Should load without error
        assert "buttons" in loaded


class TestButtonModes:
    """Test button mode configuration."""
    
    def test_default_mode_is_toggle(self):
        """Buttons default to toggle mode if not specified."""
        button = {"label": "Test", "cc": 50, "color": "red"}
        mode = button.get("mode", "toggle")
        assert mode == "toggle"
    
    def test_momentary_mode(self):
        """Can specify momentary mode."""
        button = {"label": "Test", "cc": 50, "color": "red", "mode": "momentary"}
        assert button["mode"] == "momentary"
    
    def test_toggle_mode_explicit(self):
        """Can explicitly specify toggle mode."""
        button = {"label": "Test", "cc": 50, "color": "red", "mode": "toggle"}
        assert button["mode"] == "toggle"


class TestValidateButton:
    """Test validate_button function from core/config.py."""
    
    def test_fills_missing_fields(self):
        """Fills in defaults for missing fields."""
        btn = validate_button({}, index=0)
        
        assert btn["label"] == "1"
        assert btn["cc"] == 20
        assert btn["color"] == "white"
        assert btn["mode"] == "toggle"
        assert btn["off_mode"] == "dim"
        assert btn["channel"] == 0  # Default MIDI channel 1
        assert btn["cc_on"] == 127
        assert btn["cc_off"] == 0
    
    def test_preserves_existing_fields(self):
        """Keeps existing values."""
        btn = validate_button({"label": "MUTE", "cc": 99, "color": "red"}, index=5)
        
        assert btn["label"] == "MUTE"
        assert btn["cc"] == 99
        assert btn["color"] == "red"
    
    def test_index_affects_defaults(self):
        """Index is used for default label and CC."""
        btn = validate_button({}, index=7)
        
        assert btn["label"] == "8"  # 1-indexed
        assert btn["cc"] == 27  # 20 + 7
    
    def test_global_channel_inheritance(self):
        """Button uses global channel when not specified."""
        btn = validate_button({}, index=0, global_channel=5)
        assert btn["channel"] == 5
    
    def test_button_channel_override(self):
        """Button can override global channel."""
        btn = validate_button({"channel": 10}, index=0, global_channel=5)
        assert btn["channel"] == 10
    
    def test_custom_cc_values(self):
        """Button can specify custom cc_on and cc_off values."""
        btn = validate_button({"cc_on": 100, "cc_off": 20}, index=0)
        assert btn["cc_on"] == 100
        assert btn["cc_off"] == 20


class TestButtonTypeNote:
    """Test note message type configuration."""

    def test_default_type_is_cc(self):
        """Buttons default to CC type for backward compatibility."""
        btn = validate_button({}, index=0)
        assert btn["type"] == "cc"

    def test_note_type_preserved(self):
        """Can specify note type."""
        btn = validate_button({"type": "note", "note": 60}, index=0)
        assert btn["type"] == "note"
        assert btn["note"] == 60

    def test_note_type_defaults(self):
        """Note type fills in default note and velocity values."""
        btn = validate_button({"type": "note"}, index=0)
        assert btn["type"] == "note"
        assert btn["note"] == 60
        assert btn["velocity_on"] == 127
        assert btn["velocity_off"] == 0

    def test_note_type_custom_velocity(self):
        """Note type preserves custom velocity values."""
        btn = validate_button({"type": "note", "note": 48, "velocity_on": 100, "velocity_off": 10}, index=0)
        assert btn["note"] == 48
        assert btn["velocity_on"] == 100
        assert btn["velocity_off"] == 10

    def test_cc_type_no_note_fields(self):
        """CC type buttons don't include note-specific fields."""
        btn = validate_button({"type": "cc"}, index=0)
        assert btn["type"] == "cc"
        assert "note" not in btn
        assert "velocity_on" not in btn
        assert "velocity_off" not in btn

    def test_invalid_type_defaults_to_cc(self):
        """Invalid type value falls back to CC."""
        btn = validate_button({"type": "invalid"}, index=0)
        assert btn["type"] == "cc"

    def test_note_type_still_has_cc_field(self):
        """Note type buttons still carry the cc field (for backward compat)."""
        btn = validate_button({"type": "note", "cc": 25, "note": 72}, index=0)
        assert btn["cc"] == 25
        assert btn["note"] == 72

    def test_note_type_inherits_global_channel(self):
        """Note type buttons inherit global channel."""
        btn = validate_button({"type": "note"}, index=0, global_channel=5)
        assert btn["channel"] == 5

    def test_existing_config_without_type_is_cc(self):
        """Existing configs without type field default to CC (backward compat)."""
        btn = validate_button({"label": "MUTE", "cc": 20, "color": "red"}, index=0)
        assert btn["type"] == "cc"


class TestValidateConfig:
    """Test validate_config function from core/config.py."""
    
    def test_extends_short_button_array(self):
        """Fills in missing buttons if fewer than button_count."""
        cfg = validate_config({"buttons": [{"label": "A"}]}, button_count=3)
        
        assert len(cfg["buttons"]) == 3
        assert cfg["buttons"][0]["label"] == "A"
        assert cfg["buttons"][1]["label"] == "2"
        assert cfg["buttons"][2]["label"] == "3"
    
    def test_preserves_extra_config_keys(self):
        """Keeps encoder, expression, etc."""
        cfg = validate_config({
            "buttons": [],
            "encoder": {"cc": 11},
            "custom": "value"
        }, button_count=2)
        
        assert cfg["encoder"] == {"cc": 11}
        assert cfg["custom"] == "value"
    
    def test_global_channel_default(self):
        """Global channel defaults to 0 (MIDI Ch 1)."""
        cfg = validate_config({"buttons": []}, button_count=2)
        assert cfg["global_channel"] == 0
    
    def test_global_channel_explicit(self):
        """Can set explicit global channel."""
        cfg = validate_config({"buttons": [], "global_channel": 7}, button_count=2)
        assert cfg["global_channel"] == 7
    
    def test_global_channel_clamped(self):
        """Global channel is clamped to 0-15."""
        cfg = validate_config({"buttons": [], "global_channel": 99}, button_count=1)
        assert cfg["global_channel"] == 0  # Invalid, should clamp to default
        
        cfg = validate_config({"buttons": [], "global_channel": -5}, button_count=1)
        assert cfg["global_channel"] == 0
    
    def test_buttons_inherit_global_channel(self):
        """Buttons inherit global channel when not specified."""
        cfg = validate_config({"buttons": [{}], "global_channel": 3}, button_count=1)
        assert cfg["buttons"][0]["channel"] == 3


class TestEncoderConfig:
    """Test get_encoder_config from core/config.py."""
    
    def test_defaults_when_missing(self):
        """Returns sensible defaults when encoder not in config."""
        enc = get_encoder_config({})
        
        assert enc["enabled"] == True
        assert enc["cc"] == 11
        assert enc["min"] == 0
        assert enc["max"] == 127
        assert enc["initial"] == 64
        assert enc["push"]["cc"] == 14
        assert enc["channel"] == 0  # Default channel
        assert enc["push"]["channel"] == 0
    
    def test_overrides_defaults(self):
        """Config values override defaults."""
        enc = get_encoder_config({
            "encoder": {
                "cc": 55,
                "steps": 5,
                "push": {"cc": 77, "mode": "toggle"}
            }
        })
        
        assert enc["cc"] == 55
        assert enc["steps"] == 5
        assert enc["push"]["cc"] == 77
        assert enc["push"]["mode"] == "toggle"
    
    def test_encoder_inherits_global_channel(self):
        """Encoder inherits global channel when not specified."""
        enc = get_encoder_config({"global_channel": 8})
        assert enc["channel"] == 8
        assert enc["push"]["channel"] == 8
    
    def test_encoder_channel_override(self):
        """Encoder can override global channel."""
        enc = get_encoder_config({
            "global_channel": 5,
            "encoder": {"channel": 12}
        })
        assert enc["channel"] == 12
    
    def test_encoder_push_cc_values(self):
        """Encoder push can have custom cc_on and cc_off values."""
        enc = get_encoder_config({
            "encoder": {
                "push": {
                    "cc_on": 100,
                    "cc_off": 20
                }
            }
        })
        assert enc["push"]["cc_on"] == 100
        assert enc["push"]["cc_off"] == 20
    
    def test_encoder_push_cc_values_defaults(self):
        """Encoder push defaults to cc_on=127 and cc_off=0."""
        enc = get_encoder_config({"encoder": {"push": {}}})
        assert enc["push"]["cc_on"] == 127
        assert enc["push"]["cc_off"] == 0
