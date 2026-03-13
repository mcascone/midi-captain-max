"""
Tests for multi-command per action feature.

This test suite validates:
- Config normalization (old format → new format migration)
- Event array validation
- Backwards compatibility
- Multi-command execution scenarios
- Edge cases

All tests focus on config processing, not hardware dispatch.
"""

import pytest
import sys
from pathlib import Path

# Add firmware/dev to path
sys.path.insert(0, str(Path(__file__).parent.parent / "firmware" / "dev"))

from core.config import normalize_button_config, validate_config


class TestConfigNormalization:
    """Test old format → new format migration"""

    def test_normalize_cc_toggle_to_press_release(self):
        """CC toggle button should only get press array (toggle mode has no release)"""
        old_btn = {
            "label": "TEST",
            "type": "cc",
            "mode": "toggle",
            "channel": 0,
            "cc": 20,
            "cc_on": 127,
            "cc_off": 0,
            "color": "green"
        }
        normalized = normalize_button_config(old_btn)
        
        assert "press" in normalized
        assert "release" not in normalized  # Toggle mode: state managed internally
        assert len(normalized["press"]) == 1
        assert normalized["press"][0]["type"] == "cc"
        assert normalized["press"][0]["cc"] == 20
        assert normalized["press"][0]["value"] == 127  # cc_on → value

    def test_normalize_cc_momentary_to_press_release(self):
        """CC momentary button should get separate press/release arrays"""
        old_btn = {
            "label": "MOM",
            "type": "cc",
            "mode": "momentary",
            "cc": 21,
            "cc_on": 100,
            "cc_off": 0,
            "color": "blue"
        }
        normalized = normalize_button_config(old_btn)
        
        assert "press" in normalized
        assert "release" in normalized
        assert normalized["press"][0]["value"] == 100
        assert normalized["release"][0]["value"] == 0

    def test_normalize_note_toggle_to_press_release(self):
        """Note toggle button should only get press array (toggle mode has no release)"""
        old_btn = {
            "label": "NOTE",
            "type": "note",
            "mode": "toggle",
            "note": 60,
            "velocity_on": 100,
            "velocity_off": 0,
            "color": "red"
        }
        normalized = normalize_button_config(old_btn)
        
        assert "press" in normalized
        assert "release" not in normalized  # Toggle mode: state managed internally
        assert normalized["press"][0]["type"] == "note"
        assert normalized["press"][0]["note"] == 60
        assert normalized["press"][0]["velocity"] == 100  # velocity_on → velocity

    def test_normalize_pc_to_press_only(self):
        """PC button should only get press array (no release)"""
        old_btn = {
            "label": "PC5",
            "type": "pc",
            "program": 5,
            "flash_ms": 200,
            "color": "yellow"
        }
        normalized = normalize_button_config(old_btn)
        
        assert "press" in normalized
        assert "release" not in normalized
        assert normalized["press"][0]["type"] == "pc"
        assert normalized["press"][0]["program"] == 5

    def test_normalize_pc_inc_to_press_only(self):
        """PC inc button should only get press array"""
        old_btn = {
            "label": "UP",
            "type": "pc_inc",
            "pc_step": 5,
            "color": "cyan"
        }
        normalized = normalize_button_config(old_btn)
        
        assert "press" in normalized
        assert "release" not in normalized
        assert normalized["press"][0]["type"] == "pc_inc"
        assert normalized["press"][0]["pc_step"] == 5

    def test_normalize_pc_dec_to_press_only(self):
        """PC dec button should only get press array"""
        old_btn = {
            "label": "DN",
            "type": "pc_dec",
            "pc_step": 2,
            "color": "magenta"
        }
        normalized = normalize_button_config(old_btn)
        
        assert "press" in normalized
        assert "release" not in normalized
        assert normalized["press"][0]["type"] == "pc_dec"
        assert normalized["press"][0]["pc_step"] == 2

    def test_normalize_preserves_long_press_arrays(self):
        """If old format has long_press/long_release arrays, preserve them"""
        old_btn = {
            "label": "LONG",
            "type": "cc",
            "cc": 30,
            "color": "white",
            "long_press": [
                {"type": "pc", "program": 10}
            ]
        }
        normalized = normalize_button_config(old_btn)
        
        assert "long_press" in normalized
        assert normalized["long_press"][0]["program"] == 10

    def test_normalize_preserves_keytimes(self):
        """Keytimes and states should be preserved during normalization"""
        old_btn = {
            "label": "CYCLE",
            "type": "cc",
            "cc": 20,
            "keytimes": 3,
            "states": [
                {"cc": 1, "cc_on": 127},
                {"cc": 2, "cc_on": 100}
            ],
            "color": "purple"
        }
        normalized = normalize_button_config(old_btn)
        
        assert normalized.get("keytimes") == 3
        assert "states" in normalized
        assert len(normalized["states"]) == 2

    def test_normalize_already_new_format_unchanged(self):
        """Buttons already in new format should pass through unchanged"""
        new_btn = {
            "label": "MULTI",
            "color": "green",
            "press": [
                {"type": "cc", "cc": 20, "value": 127},
                {"type": "cc", "cc": 21, "value": 64}
            ]
        }
        normalized = normalize_button_config(new_btn)
        
        # Should be unchanged
        assert normalized == new_btn


class TestEventArrayValidation:
    """Test validation of command arrays"""

    def test_validate_single_command_array(self):
        """Single-command press array should validate"""
        config = {
            "device": "std10",
            "buttons": [
                {
                    "label": "ONE",
                    "color": "green",
                    "press": [
                        {"type": "cc", "cc": 20, "value": 127}
                    ]
                }
            ]
        }
        result = validate_config(config)
        assert "buttons" in result
        # validate_config fills to 10 buttons for std10
        assert len(result["buttons"]) == 10

    def test_validate_multi_command_array(self):
        """Multi-command press array should validate"""
        config = {
            "device": "std10",
            "buttons": [
                {
                    "label": "DUAL",
                    "color": "cyan",
                    "press": [
                        {"type": "cc", "channel": 0, "cc": 20, "value": 127},
                        {"type": "cc", "channel": 1, "cc": 21, "value": 64}
                    ]
                }
            ]
        }
        result = validate_config(config)
        assert len(result["buttons"][0]["press"]) == 2

    def test_validate_all_event_arrays(self):
        """Button with all event types should validate"""
        config = {
            "device": "std10",
            "buttons": [
                {
                    "label": "FULL",
                    "color": "white",
                    "press": [{"type": "cc", "cc": 20, "value": 127}],
                    "release": [{"type": "cc", "cc": 20, "value": 0}],
                    "long_press": [{"type": "pc", "program": 5}],
                    "long_release": [{"type": "note", "note": 60, "velocity": 0}]
                }
            ]
        }
        result = validate_config(config)
        btn = result["buttons"][0]
        assert "press" in btn
        assert "release" in btn
        assert "long_press" in btn
        assert "long_release" in btn

    def test_validate_invalid_command_type_defaults_to_cc(self):
        """Invalid command type should default to 'cc'"""
        config = {
            "device": "std10",
            "buttons": [
                {
                    "label": "BAD",
                    "color": "red",
                    "press": [
                        {"type": "invalid_type", "cc": 20, "value": 127}
                    ]
                }
            ]
        }
        result = validate_config(config)
        # Validation should clamp/fix the type to 'cc' (default)
        btn = result["buttons"][0]
        assert "press" in btn
        assert btn["press"][0]["type"] == "cc"

    def test_validate_missing_fields_get_defaults(self):
        """Commands missing optional fields should get defaults"""
        config = {
            "device": "std10",
            "buttons": [
                {
                    "label": "MIN",
                    "color": "yellow",
                    "press": [
                        {"type": "cc", "cc": 20}  # missing value
                    ]
                }
            ]
        }
        result = validate_config(config)
        # Should fill in default value
        assert "value" in result["buttons"][0]["press"][0]

    def test_validate_out_of_range_values_clamped(self):
        """Out-of-range MIDI values should be clamped (not rejected)"""
        config = {
            "device": "std10",
            "buttons": [
                {
                    "label": "HIGH",
                    "color": "orange",
                    "press": [
                        {"type": "cc", "cc": 20, "value": 999}  # > 127
                    ]
                }
            ]
        }
        result = validate_config(config)
        # Validation clamps, doesn't raise exception
        assert result["buttons"][0]["press"][0]["value"] == 127

    def test_validate_note_with_velocity(self):
        """Note commands should validate with velocity field"""
        config = {
            "device": "std10",
            "buttons": [
                {
                    "label": "NOTE",
                    "color": "blue",
                    "press": [
                        {"type": "note", "note": 60, "velocity": 100}
                    ]
                }
            ]
        }
        result = validate_config(config)
        cmd = result["buttons"][0]["press"][0]
        assert cmd["type"] == "note"
        assert cmd["note"] == 60
        assert cmd["velocity"] == 100

    def test_validate_empty_event_arrays(self):
        """Empty event arrays are removed (become None) during validation"""
        config = {
            "device": "std10",
            "buttons": [
                {
                    "label": "NOP",
                    "color": "white",
                    "press": [],
                    "release": []
                }
            ]
        }
        result = validate_config(config)
        # Empty arrays become None and are not included in output
        assert "press" not in result["buttons"][0]
        assert "release" not in result["buttons"][0]


class TestBackwardsCompatibility:
    """Test that old configs still work"""

    def test_old_format_cc_button_validates(self):
        """Old-style CC button config should auto-migrate and validate"""
        config = {
            "device": "std10",
            "buttons": [
                {
                    "label": "OLD",
                    "type": "cc",
                    "cc": 20,
                    "cc_on": 127,
                    "cc_off": 0,
                    "color": "green"
                }
            ]
        }
        result = validate_config(config)
        # Should have been normalized to new format
        btn = result["buttons"][0]
        assert "press" in btn
        # Toggle mode (default): no release array
        assert "release" not in btn

    def test_mixed_old_and_new_buttons(self):
        """Config with both old and new format buttons should work"""
        config = {
            "device": "std10",
            "buttons": [
                # Old format
                {
                    "label": "OLD",
                    "type": "cc",
                    "cc": 20,
                    "color": "green"
                },
                # New format
                {
                    "label": "NEW",
                    "color": "blue",
                    "press": [
                        {"type": "cc", "cc": 21, "value": 127}
                    ]
                }
            ]
        }
        result = validate_config(config)
        # Both should validate, fills to 10 for std10
        assert len(result["buttons"]) == 10


class TestMultiCommandScenarios:
    """Test realistic multi-command use cases"""

    def test_dual_channel_cc(self):
        """Button sends same CC on two channels"""
        config = {
            "device": "std10",
            "buttons": [
                {
                    "label": "DUAL",
                    "color": "cyan",
                    "press": [
                        {"type": "cc", "channel": 0, "cc": 20, "value": 127},
                        {"type": "cc", "channel": 1, "cc": 20, "value": 127}
                    ]
                }
            ]
        }
        result = validate_config(config)
        cmds = result["buttons"][0]["press"]
        assert len(cmds) == 2
        assert cmds[0]["channel"] == 0
        assert cmds[1]["channel"] == 1

    def test_scene_change_macro(self):
        """Button sends multiple CCs to set up a scene"""
        config = {
            "device": "std10",
            "buttons": [
                {
                    "label": "SCENE",
                    "color": "purple",
                    "press": [
                        {"type": "pc", "program": 5},
                        {"type": "cc", "cc": 7, "value": 100},  # Volume
                        {"type": "cc", "cc": 10, "value": 64},  # Pan
                        {"type": "cc", "cc": 91, "value": 80}   # Reverb
                    ]
                }
            ]
        }
        result = validate_config(config)
        cmds = result["buttons"][0]["press"]
        assert len(cmds) == 4
        assert cmds[0]["type"] == "pc"
        assert cmds[1]["cc"] == 7
        assert cmds[2]["cc"] == 10
        assert cmds[3]["cc"] == 91

    def test_panic_button_all_notes_off(self):
        """Button sends all-notes-off on multiple channels"""
        config = {
            "device": "std10",
            "buttons": [
                {
                    "label": "PANIC",
                    "color": "red",
                    "press": [
                        {"type": "cc", "channel": ch, "cc": 123, "value": 0}
                        for ch in range(4)
                    ]
                }
            ]
        }
        result = validate_config(config)
        cmds = result["buttons"][0]["press"]
        assert len(cmds) == 4
        for i, cmd in enumerate(cmds):
            assert cmd["channel"] == i
            assert cmd["cc"] == 123

    def test_pc_plus_led_feedback(self):
        """Button sends PC and a CC for LED feedback"""
        config = {
            "device": "std10",
            "buttons": [
                {
                    "label": "PC+LED",
                    "color": "yellow",
                    "press": [
                        {"type": "pc", "program": 10},
                        {"type": "cc", "cc": 20, "value": 127}
                    ]
                }
            ]
        }
        result = validate_config(config)
        cmds = result["buttons"][0]["press"]
        assert len(cmds) == 2
        assert cmds[0]["type"] == "pc"
        assert cmds[1]["type"] == "cc"


class TestNormalizationEdgeCases:
    """Edge cases for config normalization"""

    def test_normalize_minimal_button(self):
        """Button with minimal fields should normalize"""
        old_btn = {
            "label": "MIN",
            "color": "white"
        }
        normalized = normalize_button_config(old_btn)
        # Should get default type (cc) and be normalized
        assert "press" in normalized or "type" in normalized

    def test_normalize_preserves_flash_ms(self):
        """flash_ms field should be preserved"""
        old_btn = {
            "label": "FLASH",
            "type": "pc",
            "program": 1,
            "flash_ms": 500,
            "color": "orange"
        }
        normalized = normalize_button_config(old_btn)
        assert normalized.get("flash_ms") == 500

    def test_normalize_preserves_select_group(self):
        """select_group field should be preserved"""
        old_btn = {
            "label": "GRP",
            "type": "cc",
            "cc": 20,
            "select_group": "scene_a",
            "default_selected": True,
            "color": "green"
        }
        normalized = normalize_button_config(old_btn)
        assert normalized.get("select_group") == "scene_a"
        assert normalized.get("default_selected") is True
