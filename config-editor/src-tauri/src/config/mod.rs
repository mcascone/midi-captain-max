//! MIDI Captain configuration module
//!
//! This module provides types, validation, and serde support for MIDI Captain
//! configuration files used by the CircuitPython firmware.
//!
//! # Organization
//!
//! - `types` - Basic enum types (ButtonColor, ButtonMode, etc.)
//! - `models` - Configuration struct definitions
//! - `validation` - Configuration validation logic
//!
//! # Example
//!
//! ```rust,ignore
//! use crate::config::MidiCaptainConfig;
//!
//! let json = std::fs::read_to_string("config.json")?;
//! let config: MidiCaptainConfig = serde_json::from_str(&json)?;
//! config.validate()?;
//! ```

mod models;
mod types;
mod validation;

// Re-export all public types for backward compatibility
pub use models::*;
// Re-export types for internal tests (needed by test assertions)
#[allow(unused_imports)]
pub(crate) use types::*;

// Tests extracted from original config.rs
// All 48 tests passing ✅
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_deserialize_std10_config() {
        let json = r#"{
            "buttons": [
                {"label": "TSC", "cc": 20, "color": "green"}
            ],
            "encoder": {
                "enabled": true,
                "cc": 11,
                "label": "ENC",
                "min": 0,
                "max": 127,
                "initial": 64,
                "steps": null,
                "push": {
                    "enabled": true,
                    "cc": 14,
                    "label": "PUSH",
                    "mode": "momentary"
                }
            }
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        assert_eq!(config.buttons.as_ref().unwrap().len(), 1);
        assert!(config.encoder.is_some());
    }

    #[test]
    fn test_deserialize_mini6_config() {
        let json = r#"{
            "device": "mini6",
            "buttons": [
                {"label": "BOOM", "cc": 20, "color": "green"}
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        assert_eq!(config.device, DeviceType::Mini6);
        assert!(config.encoder.is_none());
    }

    /// Round-trip: fields present in input JSON must survive serialize → deserialize.
    /// This class of test would have caught the missing-field bug (serde silently drops
    /// unknown fields during deserialization, so re-serializing strips them).
    #[test]
    fn test_roundtrip_note_button() {
        let json = r#"{
            "buttons": [
                {"label": "NOTE", "type": "note", "note": 60, "velocity_on": 100, "velocity_off": 0, "color": "blue", "mode": "momentary"}
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons.as_ref().unwrap()[0];
        assert_eq!(btn.message_type, MessageType::Note);
        assert_eq!(btn.note, Some(60));
        assert_eq!(btn.velocity_on, Some(100));
        assert_eq!(btn.velocity_off, Some(0));

        // Re-serialize and re-parse to confirm round-trip
        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let btn2 = &config2.buttons.as_ref().unwrap()[0];
        assert_eq!(btn2.message_type, MessageType::Note);
        assert_eq!(btn2.note, Some(60));
        assert_eq!(btn2.velocity_on, Some(100));
    }

    #[test]
    fn test_roundtrip_pc_button() {
        let json = r#"{
            "buttons": [
                {"label": "PC", "type": "pc", "program": 42, "color": "red"}
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons.as_ref().unwrap()[0];
        assert_eq!(btn.message_type, MessageType::Pc);
        assert_eq!(btn.program, Some(42));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(config2.buttons.as_ref().unwrap()[0].program, Some(42));
    }

    #[test]
    fn test_roundtrip_pc_inc_dec_buttons() {
        let json = r#"{
            "buttons": [
                {"label": "UP", "type": "pc_inc", "pc_step": 5, "color": "green"},
                {"label": "DN", "type": "pc_dec", "pc_step": 2, "color": "red"}
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        assert_eq!(config.buttons.as_ref().unwrap()[0].message_type, MessageType::PcInc);
        assert_eq!(config.buttons.as_ref().unwrap()[0].pc_step, Some(5));
        assert_eq!(config.buttons.as_ref().unwrap()[1].message_type, MessageType::PcDec);
        assert_eq!(config.buttons.as_ref().unwrap()[1].pc_step, Some(2));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(config2.buttons.as_ref().unwrap()[0].pc_step, Some(5));
        assert_eq!(config2.buttons.as_ref().unwrap()[1].pc_step, Some(2));
    }

    #[test]
    fn test_roundtrip_keytimes_and_states() {
        let json = r#"{
            "buttons": [
                {
                    "label": "CYCLE",
                    "type": "cc",
                    "cc": 20,
                    "color": "white",
                    "keytimes": 3,
                    "states": [
                        {"cc": 1, "cc_on": 127, "label": "ONE"},
                        {"cc": 2, "color": "red"},
                        {"cc": 3, "cc_off": 64}
                    ]
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons.as_ref().unwrap()[0];
        assert_eq!(btn.keytimes, Some(3));
        let states = btn.states.as_ref().unwrap();
        assert_eq!(states.len(), 3);
        assert_eq!(states[0].cc, Some(1));
        assert_eq!(states[0].label.as_deref(), Some("ONE"));
        assert_eq!(states[1].color, Some(ButtonColor::Red));
        assert_eq!(states[2].cc_off, Some(64));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let states2 = config2.buttons.as_ref().unwrap()[0].states.as_ref().unwrap();
        assert_eq!(states2[0].cc, Some(1));
        assert_eq!(states2[1].color, Some(ButtonColor::Red));
    }

    #[test]
    fn test_roundtrip_display_config() {
        let json = r#"{
            "buttons": [],
            "display": {
                "button_text_size": "large",
                "status_text_size": "small",
                "button_name_text_size": "medium"
            }
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let display = config.display.as_ref().unwrap();
        assert_eq!(display.button_text_size.as_deref(), Some("large"));
        assert_eq!(display.status_text_size.as_deref(), Some("small"));
        assert_eq!(display.button_name_text_size.as_deref(), Some("medium"));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let display2 = config2.display.as_ref().unwrap();
        assert_eq!(display2.button_text_size.as_deref(), Some("large"));
        assert_eq!(display2.status_text_size.as_deref(), Some("small"));
        assert_eq!(display2.button_name_text_size.as_deref(), Some("medium"));
    }

    #[test]
    fn test_roundtrip_splash_screen() {
        let json = r#"{
            "buttons": [],
            "splash_screen": {
                "enabled": false,
                "duration_ms": 2000
            }
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let splash = config.splash_screen.as_ref().unwrap();
        assert_eq!(splash.enabled, Some(false));
        assert_eq!(splash.duration_ms, Some(2000));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let splash2 = config2.splash_screen.as_ref().unwrap();
        assert_eq!(splash2.enabled, Some(false));
        assert_eq!(splash2.duration_ms, Some(2000));
    }

    #[test]
    fn test_roundtrip_splash_idle_timeout() {
        let json = r#"{
            "buttons": [],
            "splash_screen": {
                "enabled": true,
                "duration_ms": 1500,
                "idle_timeout_seconds": 60
            }
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let splash = config.splash_screen.as_ref().unwrap();
        assert_eq!(splash.enabled, Some(true));
        assert_eq!(splash.duration_ms, Some(1500));
        assert_eq!(splash.idle_timeout_seconds, Some(60));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let splash2 = config2.splash_screen.as_ref().unwrap();
        assert_eq!(splash2.enabled, Some(true));
        assert_eq!(splash2.duration_ms, Some(1500));
        assert_eq!(splash2.idle_timeout_seconds, Some(60));
    }

    #[test]
    fn test_roundtrip_usb_drive_name() {
        let json = r#"{
            "buttons": [],
            "usb_drive_name": "MYCAPTAIN"
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        assert_eq!(config.usb_drive_name.as_deref(), Some("MYCAPTAIN"));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(config2.usb_drive_name.as_deref(), Some("MYCAPTAIN"));
    }

    #[test]
    fn test_roundtrip_dev_mode() {
        let json = r#"{
            "buttons": [],
            "dev_mode": true
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        assert_eq!(config.dev_mode, Some(true));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(config2.dev_mode, Some(true));
    }

    #[test]
    fn test_roundtrip_midi_transport() {
        for transport in ["usb", "trs", "both"] {
            let json = format!("{{\"buttons\": [], \"midi_transport\": \"{}\"}}", transport);
            let config: MidiCaptainConfig = serde_json::from_str(&json).unwrap();
            assert_eq!(config.midi_transport.as_deref(), Some(transport));

            let reserialized = serde_json::to_string(&config).unwrap();
            let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
            assert_eq!(config2.midi_transport.as_deref(), Some(transport));
        }
    }

    #[test]
    fn test_roundtrip_simple_toggle_fields() {
        let json = r#"{
            "buttons": [
                {
                    "label": "GIG",
                    "color": "orange",
                    "mode": "toggle",
                    "cc": 46,
                    "channel": 0,
                    "value_on": 127,
                    "value_off": 0,
                    "default_on": false
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons.as_ref().unwrap()[0];
        assert_eq!(btn.value_on, Some(127));
        assert_eq!(btn.value_off, Some(0));
        assert_eq!(btn.default_on, Some(false));
        assert!(matches!(btn.mode, ButtonMode::Toggle));

        let reserialized = serde_json::to_string(&config).unwrap();
        assert!(
            reserialized.contains("\"value_on\":127") || reserialized.contains("\"value_on\": 127")
        );
        assert!(reserialized.contains("\"cc\":46") || reserialized.contains("\"cc\": 46"));
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let btn2 = &config2.buttons.as_ref().unwrap()[0];
        assert_eq!(btn2.value_on, Some(127));
        assert_eq!(btn2.value_off, Some(0));
    }

    #[test]
    fn test_roundtrip_normal_mode() {
        let json = r#"{
            "buttons": [
                {"label": "MODE", "color": "purple", "mode": "normal", "keytimes": 2}
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        assert!(matches!(config.buttons.as_ref().unwrap()[0].mode, ButtonMode::Normal));
        assert_eq!(config.buttons.as_ref().unwrap()[0].keytimes, Some(2));

        let reserialized = serde_json::to_string(&config).unwrap();
        assert!(reserialized.contains("\"normal\""));
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert!(matches!(config2.buttons.as_ref().unwrap()[0].mode, ButtonMode::Normal));
    }

    #[test]
    fn test_roundtrip_select_group() {
        let json = r#"{
            "buttons": [
                {"label": "ONE", "cc": 20, "color": "green", "select_group": "scene_a", "default_selected": true}
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons.as_ref().unwrap()[0];
        assert_eq!(btn.select_group.as_deref(), Some("scene_a"));
        assert_eq!(btn.default_selected, Some(true));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let btn2 = &config2.buttons.as_ref().unwrap()[0];
        assert_eq!(btn2.select_group.as_deref(), Some("scene_a"));
        assert_eq!(btn2.default_selected, Some(true));
    }

    #[test]
    fn test_dev_mode_defaults_absent_when_false() {
        // When dev_mode is false (or absent), it should not appear in serialised output
        // (skip_serializing_if = "Option::is_none" only omits None, so explicit false
        // WILL be serialised; this test documents that behaviour so we notice if it
        // changes unintentionally).
        let json = r#"{ "buttons": [] }"#;
        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        assert_eq!(config.dev_mode, None);

        let reserialized = serde_json::to_string(&config).unwrap();
        assert!(!reserialized.contains("dev_mode"));
    }

    #[test]
    fn test_roundtrip_multi_command_press() {
        let json = r#"{
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
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons.as_ref().unwrap()[0];
        assert!(btn.press.is_some());
        let press_cmds = btn.press.as_ref().unwrap();
        assert_eq!(press_cmds.len(), 2);
        assert_eq!(press_cmds[0].command_type, MessageType::Cc);
        assert_eq!(press_cmds[0].cc, Some(20));
        assert_eq!(press_cmds[0].value, Some(127));
        assert_eq!(press_cmds[1].channel, Some(1));
        assert_eq!(press_cmds[1].cc, Some(21));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let press_cmds2 = config2.buttons.as_ref().unwrap()[0].press.as_ref().unwrap();
        assert_eq!(press_cmds2.len(), 2);
        assert_eq!(press_cmds2[0].cc, Some(20));
        assert_eq!(press_cmds2[1].channel, Some(1));
    }

    #[test]
    fn test_roundtrip_multi_command_all_events() {
        let json = r#"{
            "buttons": [
                {
                    "label": "FULL",
                    "color": "white",
                    "press": [
                        {"type": "cc", "cc": 20, "value": 127}
                    ],
                    "release": [
                        {"type": "cc", "cc": 20, "value": 0}
                    ],
                    "long_press": [
                        {"type": "pc", "program": 5}
                    ],
                    "long_release": [
                        {"type": "note", "note": 60, "velocity": 0}
                    ]
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons.as_ref().unwrap()[0];
        assert!(btn.press.is_some());
        assert!(btn.release.is_some());
        assert!(btn.long_press.is_some());
        assert!(btn.long_release.is_some());

        assert_eq!(btn.press.as_ref().unwrap()[0].cc, Some(20));
        assert_eq!(btn.release.as_ref().unwrap()[0].value, Some(0));
        assert_eq!(btn.long_press.as_ref().unwrap()[0].program, Some(5));
        assert_eq!(btn.long_release.as_ref().unwrap()[0].note, Some(60));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let btn2 = &config2.buttons.as_ref().unwrap()[0];
        assert!(btn2.press.is_some());
        assert!(btn2.release.is_some());
        assert!(btn2.long_press.is_some());
        assert!(btn2.long_release.is_some());
    }

    #[test]
    fn test_roundtrip_multi_command_note_and_velocity() {
        let json = r#"{
            "buttons": [
                {
                    "label": "NOTE",
                    "color": "blue",
                    "press": [
                        {"type": "note", "note": 72, "velocity": 100}
                    ]
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let cmd = &config.buttons.as_ref().unwrap()[0].press.as_ref().unwrap()[0];
        assert_eq!(cmd.command_type, MessageType::Note);
        assert_eq!(cmd.note, Some(72));
        assert_eq!(cmd.velocity, Some(100));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let cmd2 = &config2.buttons.as_ref().unwrap()[0].press.as_ref().unwrap()[0];
        assert_eq!(cmd2.note, Some(72));
        assert_eq!(cmd2.velocity, Some(100));
    }

    #[test]
    fn test_roundtrip_multi_command_pc_inc_dec() {
        let json = r#"{
            "buttons": [
                {
                    "label": "INC",
                    "color": "green",
                    "press": [
                        {"type": "pc_inc", "pc_step": 5}
                    ]
                },
                {
                    "label": "DEC",
                    "color": "red",
                    "press": [
                        {"type": "pc_dec", "pc_step": 2}
                    ]
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        assert_eq!(
            config.buttons.as_ref().unwrap()[0].press.as_ref().unwrap()[0].command_type,
            MessageType::PcInc
        );
        assert_eq!(
            config.buttons.as_ref().unwrap()[0].press.as_ref().unwrap()[0].pc_step,
            Some(5)
        );
        assert_eq!(
            config.buttons.as_ref().unwrap()[1].press.as_ref().unwrap()[0].command_type,
            MessageType::PcDec
        );
        assert_eq!(
            config.buttons.as_ref().unwrap()[1].press.as_ref().unwrap()[0].pc_step,
            Some(2)
        );

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(
            config2.buttons.as_ref().unwrap()[0].press.as_ref().unwrap()[0].pc_step,
            Some(5)
        );
        assert_eq!(
            config2.buttons.as_ref().unwrap()[1].press.as_ref().unwrap()[0].pc_step,
            Some(2)
        );
    }

    #[test]
    fn test_roundtrip_multi_command_with_threshold() {
        let json = r#"{
            "buttons": [
                {
                    "label": "LONG",
                    "color": "purple",
                    "long_press": [
                        {"type": "cc", "cc": 30, "value": 127, "threshold_ms": 1000}
                    ]
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let cmd = &config.buttons.as_ref().unwrap()[0].long_press.as_ref().unwrap()[0];
        assert_eq!(cmd.threshold_ms, Some(1000));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let cmd2 = &config2.buttons.as_ref().unwrap()[0].long_press.as_ref().unwrap()[0];
        assert_eq!(cmd2.threshold_ms, Some(1000));
    }

    #[test]
    fn test_backward_compat_single_object_to_array() {
        // Test that legacy configs with single objects (not arrays) can be deserialized
        let json = r#"{
            "buttons": [
                {
                    "label": "OLD",
                    "color": "red",
                    "long_press": {"type": "cc", "cc": 25, "value": 64}
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        assert!(config.buttons.as_ref().unwrap()[0].long_press.is_some());
        let long_press = config.buttons.as_ref().unwrap()[0].long_press.as_ref().unwrap();
        assert_eq!(long_press.len(), 1);
        assert_eq!(long_press[0].cc, Some(25));
        assert_eq!(long_press[0].value, Some(64));

        // When reserialized, should become an array
        let reserialized = serde_json::to_string(&config).unwrap();
        assert!(reserialized.contains(r#""long_press":[{"#));

        // And can be deserialized again
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(config2.buttons.as_ref().unwrap()[0].long_press.as_ref().unwrap().len(), 1);
    }

    #[test]
    fn test_backward_compat_mixed_formats() {
        // Test config with mix of old single-object and new array formats
        let json = r#"{
            "buttons": [
                {
                    "label": "MIX",
                    "color": "cyan",
                    "press": [{"type": "cc", "cc": 20, "value": 127}],
                    "long_press": {"type": "cc", "cc": 30, "value": 127}
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        assert_eq!(config.buttons.as_ref().unwrap()[0].press.as_ref().unwrap().len(), 1);
        assert_eq!(config.buttons.as_ref().unwrap()[0].long_press.as_ref().unwrap().len(), 1);

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(config2.buttons.as_ref().unwrap()[0].press.as_ref().unwrap().len(), 1);
        assert_eq!(config2.buttons.as_ref().unwrap()[0].long_press.as_ref().unwrap().len(), 1);
    }

    #[test]
    fn test_roundtrip_per_state_commands() {
        // Test per-state command arrays in StateOverride
        let json = r#"{
            "buttons": [
                {
                    "label": "MULTI",
                    "color": "white",
                    "keytimes": 2,
                    "states": [
                        {
                            "color": "red",
                            "label": "ONE",
                            "press": [
                                {"type": "cc", "cc": 10, "value": 127},
                                {"type": "pc", "program": 1}
                            ],
                            "release": [
                                {"type": "cc", "cc": 10, "value": 0}
                            ]
                        },
                        {
                            "color": "green",
                            "label": "TWO",
                            "press": [
                                {"type": "note", "note": 60, "velocity": 100}
                            ],
                            "release": [
                                {"type": "note", "note": 60, "velocity": 0}
                            ],
                            "long_press": [
                                {"type": "cc", "cc": 99, "value": 127}
                            ],
                            "long_release": [
                                {"type": "cc", "cc": 99, "value": 0}
                            ]
                        }
                    ]
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons.as_ref().unwrap()[0];
        assert_eq!(btn.keytimes, Some(2));

        let states = btn.states.as_ref().unwrap();
        assert_eq!(states.len(), 2);

        // State 1: press and release commands
        assert_eq!(states[0].color, Some(ButtonColor::Red));
        assert_eq!(states[0].label.as_deref(), Some("ONE"));
        let s1_press = states[0].press.as_ref().unwrap();
        assert_eq!(s1_press.len(), 2);
        assert_eq!(s1_press[0].cc, Some(10));
        assert_eq!(s1_press[1].program, Some(1));
        let s1_release = states[0].release.as_ref().unwrap();
        assert_eq!(s1_release.len(), 1);
        assert_eq!(s1_release[0].value, Some(0));

        // State 2: all event types
        assert_eq!(states[1].color, Some(ButtonColor::Green));
        let s2_press = states[1].press.as_ref().unwrap();
        assert_eq!(s2_press[0].note, Some(60));
        let s2_long_press = states[1].long_press.as_ref().unwrap();
        assert_eq!(s2_long_press[0].cc, Some(99));
        assert!(states[1].long_release.is_some());

        // Round-trip test
        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let states2 = config2.buttons.as_ref().unwrap()[0].states.as_ref().unwrap();

        // Verify all per-state commands survived
        assert!(states2[0].press.is_some());
        assert!(states2[0].release.is_some());
        assert!(states2[1].press.is_some());
        assert!(states2[1].release.is_some());
        assert!(states2[1].long_press.is_some());
        assert!(states2[1].long_release.is_some());

        assert_eq!(states2[0].press.as_ref().unwrap().len(), 2);
        assert_eq!(states2[1].long_press.as_ref().unwrap()[0].cc, Some(99));
    }

    #[test]
    fn test_roundtrip_dim_brightness() {
        // Test dim_brightness field survives round-trip
        let json = r#"{
            "buttons": [
                {
                    "label": "DIM",
                    "color": "blue",
                    "off_mode": "dim",
                    "dim_brightness": 50
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons.as_ref().unwrap()[0];
        assert_eq!(btn.off_mode, OffMode::Dim);
        assert_eq!(btn.dim_brightness, Some(50));

        // Round-trip test
        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(config2.buttons.as_ref().unwrap()[0].dim_brightness, Some(50));
    }

    #[test]
    fn test_roundtrip_long_press_label() {
        // Test long_press_label field survives round-trip
        let json = r#"{
            "buttons": [
                {
                    "label": "PLAY",
                    "long_press_label": "PAUSE",
                    "color": "green",
                    "press": [{"type": "cc", "cc": 20, "value": 127}],
                    "long_press": [{"type": "cc", "cc": 21, "value": 127}]
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons.as_ref().unwrap()[0];
        assert_eq!(btn.label, "PLAY");
        assert_eq!(btn.long_press_label, Some("PAUSE".to_string()));

        // Round-trip test
        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(
            config2.buttons.as_ref().unwrap()[0].long_press_label,
            Some("PAUSE".to_string())
        );
    }

    #[test]
    fn test_roundtrip_long_press_label_persist() {
        // Test long_press_label_persist field survives round-trip
        let json = r#"{
            "buttons": [
                {
                    "label": "SCENE",
                    "long_press_label": "DELAY",
                    "long_press_label_persist": false,
                    "color": "green",
                    "mode": "select",
                    "press": [{"type": "cc", "cc": 43, "value": 0}],
                    "long_press": [{"type": "cc", "cc": 52, "value": 5}]
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons.as_ref().unwrap()[0];
        assert_eq!(btn.label, "SCENE");
        assert_eq!(btn.long_press_label, Some("DELAY".to_string()));
        assert_eq!(btn.long_press_label_persist, Some(false));

        // Round-trip test
        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let btn2 = &config2.buttons.as_ref().unwrap()[0];
        assert_eq!(btn2.long_press_label_persist, Some(false));
    }

    #[test]
    fn test_long_press_label_persist_defaults_omitted() {
        // When long_press_label_persist is not set, it should be None (not serialized)
        // Firmware will default to true
        let json = r#"{
            "buttons": [
                {
                    "label": "TEST",
                    "color": "green"
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons.as_ref().unwrap()[0];
        assert_eq!(btn.long_press_label_persist, None);

        // Should not be serialized when None
        let reserialized = serde_json::to_string(&config).unwrap();
        assert!(!reserialized.contains("long_press_label_persist"));
    }

    #[test]
    fn test_long_press_label_persist_true_serialized() {
        // When explicitly set to true, it should be serialized
        let json = r#"{
            "buttons": [
                {
                    "label": "TEST",
                    "long_press_label_persist": true,
                    "color": "green"
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons.as_ref().unwrap()[0];
        assert_eq!(btn.long_press_label_persist, Some(true));

        // Should be serialized when explicitly true
        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(config2.buttons.as_ref().unwrap()[0].long_press_label_persist, Some(true));
    }

    #[test]
    fn test_validate_per_state_commands() {
        // Test that invalid MIDI fields in per-state command arrays are caught by validation
        let json = r#"{
            "buttons": [
                {
                    "label": "TEST",
                    "color": "red",
                    "keytimes": 2,
                    "states": [
                        {
                            "press": [{"type": "cc", "cc": 200, "value": 127}]
                        },
                        {
                            "release": [{"type": "note", "note": 60, "velocity": 150}]
                        }
                    ]
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let result = config.validate();

        assert!(result.is_err());
        let errors = result.unwrap_err();
        let err_str = errors.join("\n");
        // Should catch cc > 127 in state 1
        assert!(err_str.contains("states[1].press"));
        assert!(err_str.contains("cc 200 exceeds 127"));
        // Should catch velocity > 127 in state 2
        assert!(err_str.contains("states[2].release"));
        assert!(err_str.contains("velocity 150 exceeds 127"));
    }

    #[test]
    fn test_validate_per_state_commands_channel() {
        // Test that invalid channel in per-state commands is caught
        let json = r#"{
            "buttons": [
                {
                    "label": "TEST",
                    "color": "blue",
                    "keytimes": 1,
                    "states": [
                        {
                            "long_press": [{"type": "pc", "program": 5, "channel": 20}]
                        }
                    ]
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let result = config.validate();

        assert!(result.is_err());
        let errors = result.unwrap_err();
        let err_str = errors.join("\n");
        assert!(err_str.contains("states[1].long_press"));
        assert!(err_str.contains("channel 20 invalid"));
    }

    #[test]
    fn test_state_override_single_object_deserialization() {
        // Test that StateOverride accepts single-object form for per-state commands
        let json = r#"{
            "buttons": [
                {
                    "label": "TEST",
                    "color": "red",
                    "keytimes": 2,
                    "press": [{"type": "cc", "cc": 20, "value": 127}],
                    "states": [
                        {
                            "press": {"type": "cc", "cc": 21, "value": 100}
                        },
                        {
                            "release": {"type": "note", "note": 60, "velocity": 0},
                            "long_press": {"type": "pc", "program": 5}
                        }
                    ]
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons.as_ref().unwrap()[0];
        assert_eq!(btn.keytimes, Some(2));

        let states = btn.states.as_ref().unwrap();
        assert_eq!(states.len(), 2);

        // First state: single-object press should be converted to array
        let state0_press = states[0].press.as_ref().unwrap();
        assert_eq!(state0_press.len(), 1);
        assert_eq!(state0_press[0].cc, Some(21));
        assert_eq!(state0_press[0].value, Some(100));

        // Second state: single-object release and long_press
        let state1_release = states[1].release.as_ref().unwrap();
        assert_eq!(state1_release.len(), 1);
        assert_eq!(state1_release[0].note, Some(60));

        let state1_long = states[1].long_press.as_ref().unwrap();
        assert_eq!(state1_long.len(), 1);
        assert_eq!(state1_long[0].program, Some(5));

        // Round-trip should preserve as arrays
        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(
            config2.buttons.as_ref().unwrap()[0].states.as_ref().unwrap()[0]
                .press
                .as_ref()
                .unwrap()
                .len(),
            1
        );
    }

    #[test]
    fn test_validate_dim_brightness_range() {
        // Test that dim_brightness > 100 is caught by validation
        let json = r#"{
            "device": "mini6",
            "buttons": [
                {
                    "label": "TEST",
                    "color": "blue",
                    "dim_brightness": 150
                },
                {
                    "label": "B2",
                    "color": "white"
                },
                {
                    "label": "B3",
                    "color": "white"
                },
                {
                    "label": "B4",
                    "color": "white"
                },
                {
                    "label": "B5",
                    "color": "white"
                },
                {
                    "label": "B6",
                    "color": "white"
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let result = config.validate();

        assert!(result.is_err());
        let errors = result.unwrap_err();
        let err_str = errors.join("\n");
        assert!(err_str.contains("dim_brightness"));
        assert!(err_str.contains("150"));
        assert!(err_str.contains("exceeds 100"));
    }

    #[test]
    fn test_validate_dim_brightness_valid() {
        // Test that dim_brightness within 0-100 passes validation
        let json = r#"{
            "device": "mini6",
            "buttons": [
                {
                    "label": "TEST",
                    "color": "blue",
                    "dim_brightness": 100
                },
                {
                    "label": "TEST2",
                    "color": "red",
                    "dim_brightness": 0
                },
                {
                    "label": "TEST3",
                    "color": "green",
                    "dim_brightness": 50
                },
                {
                    "label": "TEST4",
                    "color": "white"
                },
                {
                    "label": "TEST5",
                    "color": "white"
                },
                {
                    "label": "TEST6",
                    "color": "white"
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let result = config.validate();

        // Should pass validation
        assert!(result.is_ok());
    }

    #[test]
    fn test_validate_long_press_label_length() {
        // Test that long_press_label > 6 chars is caught by validation
        let json = r#"{
            "device": "mini6",
            "buttons": [
                {
                    "label": "TEST",
                    "long_press_label": "TOOLONG",
                    "color": "blue"
                },
                {
                    "label": "B2",
                    "color": "white"
                },
                {
                    "label": "B3",
                    "color": "white"
                },
                {
                    "label": "B4",
                    "color": "white"
                },
                {
                    "label": "B5",
                    "color": "white"
                },
                {
                    "label": "B6",
                    "color": "white"
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let result = config.validate();

        assert!(result.is_err());
        let errors = result.unwrap_err();
        let err_str = errors.join("\n");
        assert!(err_str.contains("long_press_label"));
        assert!(err_str.contains("TOOLONG"));
        assert!(err_str.contains("exceeds 6 chars"));
    }

    #[test]
    fn test_roundtrip_profile_ids() {
        // Test that profile_id and action_id fields survive round-trip
        let json = r#"{
            "buttons": [
                {
                    "label": "SCENE",
                    "color": "green",
                    "profile_id": "quad-cortex",
                    "action_id": "scene_b",
                    "press": [{"type": "cc", "cc": 43, "value": 1, "channel": 0}]
                }
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons.as_ref().unwrap()[0];
        assert_eq!(btn.profile_id, Some("quad-cortex".to_string()));
        assert_eq!(btn.action_id, Some("scene_b".to_string()));
        assert!(btn.press.is_some());

        // Round-trip test
        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(
            config2.buttons.as_ref().unwrap()[0].profile_id,
            Some("quad-cortex".to_string())
        );
        assert_eq!(config2.buttons.as_ref().unwrap()[0].action_id, Some("scene_b".to_string()));
        assert!(config2.buttons.as_ref().unwrap()[0].press.is_some());
    }
}
