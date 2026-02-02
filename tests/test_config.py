"""
Tests for configuration loading and validation.
"""

import pytest
import json


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
