//! MIDI Captain configuration types and validation
//!
//! Matches the JSON schema used by the CircuitPython firmware.

use serde::{Deserialize, Serialize};

/// Valid button colors
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum ButtonColor {
    Red,
    Green,
    Blue,
    Yellow,
    Cyan,
    Magenta,
    Orange,
    Purple,
    White,
    Pink,
    Lime,
    Amber,
    Teal,
    Violet,
    Gold,
}

/// Button trigger mode
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(rename_all = "lowercase")]
pub enum ButtonMode {
    #[default]
    Toggle,
    Normal,
    Momentary,
    Select,
    Tap,
}

/// LED behavior when button is off
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(rename_all = "lowercase")]
pub enum OffMode {
    #[default]
    Dim,
    Off,
}

/// Message type for a button
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(rename_all = "snake_case")]
pub enum MessageType {
    #[default]
    Cc,
    Note,
    Pc,
    PcInc,
    PcDec,
}

/// Per-state overrides for keytimes cycling
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StateOverride {
    // Multi-command event arrays (per-state actions)
    #[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "deserialize_one_or_many")]
    pub press: Option<Vec<MidiCommand>>,
    #[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "deserialize_one_or_many")]
    pub release: Option<Vec<MidiCommand>>,
    #[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "deserialize_one_or_many")]
    pub long_press: Option<Vec<MidiCommand>>,
    #[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "deserialize_one_or_many")]
    pub long_release: Option<Vec<MidiCommand>>,

    // Legacy single-type field overrides
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cc: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cc_on: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cc_off: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub note: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub velocity_on: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub velocity_off: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub program: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pc_step: Option<u8>,

    // Visual overrides
    #[serde(skip_serializing_if = "Option::is_none")]
    pub color: Option<ButtonColor>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub label: Option<String>,
}

/// MIDI command for multi-command event arrays
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MidiCommand {
    #[serde(rename = "type", default)]
    pub command_type: MessageType,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub channel: Option<u8>,
    // CC fields
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cc: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub value: Option<u8>,
    // Note fields
    #[serde(skip_serializing_if = "Option::is_none")]
    pub note: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub velocity: Option<u8>,
    // PC fields
    #[serde(skip_serializing_if = "Option::is_none")]
    pub program: Option<u8>,
    // PC inc/dec fields
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pc_step: Option<u8>,
    // Optional threshold for long-press (on first command only)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub threshold_ms: Option<u32>,
}

/// Helper type to deserialize either a single MidiCommand object or an array
/// Supports backward compatibility with legacy configs that use single objects
#[derive(Debug, Clone, Deserialize)]
#[serde(untagged)]
enum OneOrMany {
    One(MidiCommand),
    Many(Vec<MidiCommand>),
}

impl OneOrMany {
    fn into_vec(self) -> Vec<MidiCommand> {
        match self {
            OneOrMany::One(cmd) => vec![cmd],
            OneOrMany::Many(cmds) => cmds,
        }
    }
}

impl Serialize for OneOrMany {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        // Always serialize as array
        match self {
            OneOrMany::One(cmd) => vec![cmd.clone()].serialize(serializer),
            OneOrMany::Many(cmds) => cmds.serialize(serializer),
        }
    }
}

/// Custom deserializer for backward compatibility: accepts single object or array
fn deserialize_one_or_many<'de, D>(deserializer: D) -> Result<Option<Vec<MidiCommand>>, D::Error>
where
    D: serde::Deserializer<'de>,
{
    Option::<OneOrMany>::deserialize(deserializer)
        .map(|opt| opt.map(|one_or_many| one_or_many.into_vec()))
}

/// Button configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ButtonConfig {
    pub label: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub long_press_label: Option<String>,
    pub color: ButtonColor,

    // ===== NEW: Multi-command event arrays =====
    #[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "deserialize_one_or_many")]
    pub press: Option<Vec<MidiCommand>>,
    #[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "deserialize_one_or_many")]
    pub release: Option<Vec<MidiCommand>>,
    #[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "deserialize_one_or_many")]
    pub long_press: Option<Vec<MidiCommand>>,
    #[serde(default, skip_serializing_if = "Option::is_none", deserialize_with = "deserialize_one_or_many")]
    pub long_release: Option<Vec<MidiCommand>>,

    // ===== LEGACY: Single-type fields (for backwards compatibility) =====
    #[serde(rename = "type", default, skip_serializing_if = "is_default_message_type")]
    pub message_type: MessageType,
    #[serde(default)]
    pub mode: ButtonMode,
    #[serde(default, skip_serializing_if = "is_default_off_mode")]
    pub off_mode: OffMode,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub dim_brightness: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub channel: Option<u8>,
    // CC fields
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cc: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cc_on: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cc_off: Option<u8>,
    // Note fields
    #[serde(skip_serializing_if = "Option::is_none")]
    pub note: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub velocity_on: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub velocity_off: Option<u8>,
    // PC fields
    #[serde(skip_serializing_if = "Option::is_none")]
    pub program: Option<u8>,
    // PC inc/dec fields
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pc_step: Option<u8>,
    // PC flash feedback (all PC types)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub flash_ms: Option<u16>,

    // ===== SIMPLIFIED TOGGLE FIELDS =====
    // Used when mode='toggle' to auto-derive CC on/off without defining press/release arrays
    #[serde(skip_serializing_if = "Option::is_none")]
    pub value_on: Option<u8>,   // CC value sent when turning ON (default 127)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub value_off: Option<u8>,  // CC value sent when turning OFF (default 0)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub default_on: Option<bool>, // If true, button boots in ON state and sends value_on

    // ===== COMMON FIELDS =====
    // Keytimes cycling
    #[serde(skip_serializing_if = "Option::is_none")]
    pub keytimes: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub states: Option<Vec<StateOverride>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub select_group: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub default_selected: Option<bool>,
}

fn is_default_off_mode(mode: &OffMode) -> bool {
    *mode == OffMode::Dim
}

fn is_default_message_type(t: &MessageType) -> bool {
    *t == MessageType::Cc
}

/// Encoder push button configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncoderPush {
    pub enabled: bool,
    pub cc: u8,
    pub label: String,
    #[serde(default)]
    pub mode: ButtonMode,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub channel: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cc_on: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cc_off: Option<u8>,
}

/// Rotary encoder configuration (STD10 only)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncoderConfig {
    pub enabled: bool,
    pub cc: u8,
    pub label: String,
    #[serde(default)]
    pub min: u8,
    #[serde(default = "default_max")]
    pub max: u8,
    #[serde(default = "default_initial")]
    pub initial: u8,
    pub steps: Option<u8>,
    pub push: Option<EncoderPush>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub channel: Option<u8>,
}

fn default_max() -> u8 {
    127
}
fn default_initial() -> u8 {
    64
}

/// Expression pedal polarity
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(rename_all = "lowercase")]
pub enum Polarity {
    #[default]
    Normal,
    Inverted,
}

/// Expression pedal configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExpressionConfig {
    pub enabled: bool,
    pub cc: u8,
    pub label: String,
    #[serde(default)]
    pub min: u8,
    #[serde(default = "default_max")]
    pub max: u8,
    #[serde(default)]
    pub polarity: Polarity,
    #[serde(default = "default_threshold")]
    pub threshold: u8,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub channel: Option<u8>,
}

fn default_threshold() -> u8 {
    2
}

/// Expression pedals container
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExpressionPedals {
    pub exp1: ExpressionConfig,
    pub exp2: ExpressionConfig,
}

/// Device type
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(rename_all = "lowercase")]
pub enum DeviceType {
    #[default]
    Std10,
    Mini6,
}

/// Display text size settings
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DisplayConfig {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub button_text_size: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub status_text_size: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub expression_text_size: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub button_name_text_size: Option<String>,
}

/// Complete MIDI Captain configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MidiCaptainConfig {
    #[serde(default)]
    pub device: DeviceType,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub global_channel: Option<u8>,
    /// Custom USB volume label (max 11 chars, alphanumeric + underscore).
    /// Applied by boot.py via storage.remount() when the drive is enabled.
    #[serde(skip_serializing_if = "Option::is_none")]
    pub usb_drive_name: Option<String>,
    /// Development mode: when true the USB drive always mounts on boot without
    /// needing to hold Switch 1.  Defaults to false (performance mode).
    #[serde(skip_serializing_if = "Option::is_none")]
    pub dev_mode: Option<bool>,
    /// MIDI output transport: "usb" (default), "trs", or "both".
    /// "usb"  — USB MIDI only (adafruit_midi over usb_midi.ports)
    /// "trs"  — TRS/serial MIDI only (UART on GP16/GP17 at 31250 baud)
    /// "both" — send to USB and TRS simultaneously
    #[serde(skip_serializing_if = "Option::is_none")]
    pub midi_transport: Option<String>,
    pub buttons: Vec<ButtonConfig>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub encoder: Option<EncoderConfig>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub expression: Option<ExpressionPedals>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub display: Option<DisplayConfig>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub long_press_threshold_ms: Option<u32>,
}

impl MidiCaptainConfig {
    /// Validate the configuration
    pub fn validate(&self) -> Result<(), Vec<String>> {
        let mut errors = Vec::new();

        // Validate global channel (0-15 internally, display as 1-16)
        if let Some(ch) = self.global_channel {
            if ch > 15 {
                errors.push(format!("Global channel value {} is invalid (must be 1-16, stored as 0-15)", ch + 1));
            }
        }

        // Check button count matches device
        let expected_buttons = match self.device {
            DeviceType::Std10 => 10,
            DeviceType::Mini6 => 6,
        };

        if self.buttons.len() != expected_buttons {
            errors.push(format!(
                "Expected {} buttons for {:?}, found {}",
                expected_buttons,
                self.device,
                self.buttons.len()
            ));
        }

        // Validate CC numbers (0-127) and button-specific fields
        for (i, button) in self.buttons.iter().enumerate() {
            if let Some(cc) = button.cc {
                if cc > 127 {
                    errors.push(format!("Button {} CC {} exceeds 127", i + 1, cc));
                }
            }
            if button.label.len() > 6 {
                errors.push(format!(
                    "Button {} label '{}' exceeds 6 chars",
                    i + 1,
                    button.label
                ));
            }
            if let Some(ref long_label) = button.long_press_label {
                if long_label.len() > 6 {
                    errors.push(format!(
                        "Button {} long_press_label '{}' exceeds 6 chars",
                        i + 1,
                        long_label
                    ));
                }
            }
            if let Some(ch) = button.channel {
                if ch > 15 {
                    errors.push(format!("Button {} channel {} is invalid (must be 1-16)", i + 1, ch + 1));
                }
            }
            if let Some(val) = button.cc_on {
                if val > 127 {
                    errors.push(format!("Button {} cc_on {} exceeds 127", i + 1, val));
                }
            }
            if let Some(val) = button.cc_off {
                if val > 127 {
                    errors.push(format!("Button {} cc_off {} exceeds 127", i + 1, val));
                }
            }
            if let Some(ms) = button.flash_ms {
                if ms < 50 || ms > 5000 {
                    errors.push(format!("Button {} flash_ms {} out of range (50-5000)", i + 1, ms));
                }
            }
            if let Some(brightness) = button.dim_brightness {
                if brightness > 100 {
                    errors.push(format!("Button {} dim_brightness {} exceeds 100 (must be 0-100)", i + 1, brightness));
                }
            }

            // Validate event command arrays (press, release, long_press, long_release)
            let validate_command = |cmd: &MidiCommand, event_name: &str, cmd_idx: usize| {
                let mut cmd_errors = Vec::new();
                if let Some(ch) = cmd.channel {
                    if ch > 15 {
                        cmd_errors.push(format!("Button {} {}.{} channel {} invalid (must be 0-15)", i+1, event_name, cmd_idx, ch));
                    }
                }
                if let Some(cc) = cmd.cc {
                    if cc > 127 {
                        cmd_errors.push(format!("Button {} {}.{} cc {} exceeds 127", i+1, event_name, cmd_idx, cc));
                    }
                }
                if let Some(val) = cmd.value {
                    if val > 127 {
                        cmd_errors.push(format!("Button {} {}.{} value {} exceeds 127", i+1, event_name, cmd_idx, val));
                    }
                }
                if let Some(note) = cmd.note {
                    if note > 127 {
                        cmd_errors.push(format!("Button {} {}.{} note {} exceeds 127", i+1, event_name, cmd_idx, note));
                    }
                }
                if let Some(vel) = cmd.velocity {
                    if vel > 127 {
                        cmd_errors.push(format!("Button {} {}.{} velocity {} exceeds 127", i+1, event_name, cmd_idx, vel));
                    }
                }
                if let Some(prog) = cmd.program {
                    if prog > 127 {
                        cmd_errors.push(format!("Button {} {}.{} program {} exceeds 127", i+1, event_name, cmd_idx, prog));
                    }
                }
                if let Some(step) = cmd.pc_step {
                    if step < 1 || step > 127 {
                        cmd_errors.push(format!("Button {} {}.{} pc_step {} out of range (1-127)", i+1, event_name, cmd_idx, step));
                    }
                }
                if let Some(thresh) = cmd.threshold_ms {
                    if thresh < 50 || thresh > 10000 {
                        cmd_errors.push(format!("Button {} {}.{} threshold_ms {} out of range (50-10000)", i+1, event_name, cmd_idx, thresh));
                    }
                }
                cmd_errors
            };

            if let Some(ref cmds) = button.press {
                for (idx, cmd) in cmds.iter().enumerate() {
                    errors.extend(validate_command(cmd, "press", idx));
                }
            }
            if let Some(ref cmds) = button.release {
                for (idx, cmd) in cmds.iter().enumerate() {
                    errors.extend(validate_command(cmd, "release", idx));
                }
            }
            if let Some(ref cmds) = button.long_press {
                for (idx, cmd) in cmds.iter().enumerate() {
                    errors.extend(validate_command(cmd, "long_press", idx));
                }
            }
            if let Some(ref cmds) = button.long_release {
                for (idx, cmd) in cmds.iter().enumerate() {
                    errors.extend(validate_command(cmd, "long_release", idx));
                }
            }

            // Validate per-state event arrays (states[*].press/release/long_press/long_release)
            if let Some(ref states) = button.states {
                for (state_idx, state) in states.iter().enumerate() {
                    let state_num = state_idx + 1;

                    if let Some(ref cmds) = state.press {
                        for (cmd_idx, cmd) in cmds.iter().enumerate() {
                            errors.extend(validate_command(cmd, &format!("states[{}].press", state_num), cmd_idx));
                        }
                    }
                    if let Some(ref cmds) = state.release {
                        for (cmd_idx, cmd) in cmds.iter().enumerate() {
                            errors.extend(validate_command(cmd, &format!("states[{}].release", state_num), cmd_idx));
                        }
                    }
                    if let Some(ref cmds) = state.long_press {
                        for (cmd_idx, cmd) in cmds.iter().enumerate() {
                            errors.extend(validate_command(cmd, &format!("states[{}].long_press", state_num), cmd_idx));
                        }
                    }
                    if let Some(ref cmds) = state.long_release {
                        for (cmd_idx, cmd) in cmds.iter().enumerate() {
                            errors.extend(validate_command(cmd, &format!("states[{}].long_release", state_num), cmd_idx));
                        }
                    }
                }
            }

            // select_group rules: not allowed with momentary, tap, or keytimes > 1
            if let Some(_) = button.select_group {
                if button.mode == ButtonMode::Momentary {
                    errors.push(format!("Button {} select_group not supported for momentary mode", i + 1));
                }
                if button.mode == ButtonMode::Tap {
                    errors.push(format!("Button {} select_group not supported for tap mode", i + 1));
                }
                if let Some(kt) = button.keytimes {
                    if kt > 1 {
                        errors.push(format!("Button {} select_group not supported with keytimes > 1", i + 1));
                    }
                }
            }
            if let Some(ds) = button.default_selected {
                // no extra check here; normalization performed elsewhere
                let _ = ds;
            }
        }

        // Validate encoder if present
        if let Some(ref enc) = self.encoder {
            // Mini6 does not support encoder
            if self.device == DeviceType::Mini6 {
                errors.push("Mini6 does not support encoder".to_string());
            }
            if enc.cc > 127 {
                errors.push(format!("Encoder CC {} exceeds 127", enc.cc));
            }
            if enc.label.len() > 8 {
                errors.push(format!("Encoder label '{}' exceeds 8 chars", enc.label));
            }
            if enc.max < enc.min {
                errors.push(format!("Encoder max ({}) must be >= min ({})", enc.max, enc.min));
            }
            if enc.initial < enc.min || enc.initial > enc.max {
                errors.push(format!("Encoder initial ({}) must be between min ({}) and max ({})", enc.initial, enc.min, enc.max));
            }
            if let Some(ch) = enc.channel {
                if ch > 15 {
                    errors.push(format!("Encoder channel {} is invalid (must be 1-16)", ch + 1));
                }
            }
            if let Some(ref push) = enc.push {
                if push.cc > 127 {
                    errors.push(format!("Encoder push CC {} exceeds 127", push.cc));
                }
                if push.label.len() > 8 {
                    errors.push(format!("Encoder push label '{}' exceeds 8 chars", push.label));
                }
                if let Some(ch) = push.channel {
                    if ch > 15 {
                        errors.push(format!("Encoder push channel {} is invalid (must be 1-16)", ch + 1));
                    }
                }
                if let Some(val) = push.cc_on {
                    if val > 127 {
                        errors.push(format!("Encoder push cc_on {} exceeds 127", val));
                    }
                }
                if let Some(val) = push.cc_off {
                    if val > 127 {
                        errors.push(format!("Encoder push cc_off {} exceeds 127", val));
                    }
                }
            }
        }

        // Validate expression pedals if present
        if let Some(ref exp) = self.expression {
            // Mini6 does not support expression pedals
            if self.device == DeviceType::Mini6 {
                errors.push("Mini6 does not support expression pedals".to_string());
            }
            if exp.exp1.cc > 127 {
                errors.push(format!("EXP1 CC {} exceeds 127", exp.exp1.cc));
            }
            if exp.exp1.label.len() > 8 {
                errors.push(format!("EXP1 label '{}' exceeds 8 chars", exp.exp1.label));
            }
            if exp.exp1.max < exp.exp1.min {
                errors.push(format!("EXP1 max ({}) must be >= min ({})", exp.exp1.max, exp.exp1.min));
            }
            if let Some(ch) = exp.exp1.channel {
                if ch > 15 {
                    errors.push(format!("EXP1 channel {} is invalid (must be 1-16)", ch + 1));
                }
            }
            if exp.exp2.cc > 127 {
                errors.push(format!("EXP2 CC {} exceeds 127", exp.exp2.cc));
            }
            if exp.exp2.label.len() > 8 {
                errors.push(format!("EXP2 label '{}' exceeds 8 chars", exp.exp2.label));
            }
            if exp.exp2.max < exp.exp2.min {
                errors.push(format!("EXP2 max ({}) must be >= min ({})", exp.exp2.max, exp.exp2.min));
            }
            if let Some(ch) = exp.exp2.channel {
                if ch > 15 {
                    errors.push(format!("EXP2 channel {} is invalid (must be 1-16)", ch + 1));
                }
            }
        }

        if errors.is_empty() {
            Ok(())
        } else {
            Err(errors)
        }
    }
}

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
        assert_eq!(config.buttons.len(), 1);
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
        let btn = &config.buttons[0];
        assert_eq!(btn.message_type, MessageType::Note);
        assert_eq!(btn.note, Some(60));
        assert_eq!(btn.velocity_on, Some(100));
        assert_eq!(btn.velocity_off, Some(0));

        // Re-serialize and re-parse to confirm round-trip
        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let btn2 = &config2.buttons[0];
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
        let btn = &config.buttons[0];
        assert_eq!(btn.message_type, MessageType::Pc);
        assert_eq!(btn.program, Some(42));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(config2.buttons[0].program, Some(42));
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
        assert_eq!(config.buttons[0].message_type, MessageType::PcInc);
        assert_eq!(config.buttons[0].pc_step, Some(5));
        assert_eq!(config.buttons[1].message_type, MessageType::PcDec);
        assert_eq!(config.buttons[1].pc_step, Some(2));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(config2.buttons[0].pc_step, Some(5));
        assert_eq!(config2.buttons[1].pc_step, Some(2));
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
        let btn = &config.buttons[0];
        assert_eq!(btn.keytimes, Some(3));
        let states = btn.states.as_ref().unwrap();
        assert_eq!(states.len(), 3);
        assert_eq!(states[0].cc, Some(1));
        assert_eq!(states[0].label.as_deref(), Some("ONE"));
        assert_eq!(states[1].color, Some(ButtonColor::Red));
        assert_eq!(states[2].cc_off, Some(64));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let states2 = config2.buttons[0].states.as_ref().unwrap();
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
        let btn = &config.buttons[0];
        assert_eq!(btn.value_on, Some(127));
        assert_eq!(btn.value_off, Some(0));
        assert_eq!(btn.default_on, Some(false));
        assert!(matches!(btn.mode, ButtonMode::Toggle));

        let reserialized = serde_json::to_string(&config).unwrap();
        assert!(reserialized.contains("\"value_on\":127") || reserialized.contains("\"value_on\": 127"));
        assert!(reserialized.contains("\"cc\":46") || reserialized.contains("\"cc\": 46"));
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let btn2 = &config2.buttons[0];
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
        assert!(matches!(config.buttons[0].mode, ButtonMode::Normal));
        assert_eq!(config.buttons[0].keytimes, Some(2));

        let reserialized = serde_json::to_string(&config).unwrap();
        assert!(reserialized.contains("\"normal\""));
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert!(matches!(config2.buttons[0].mode, ButtonMode::Normal));
    }

    #[test]
    fn test_roundtrip_select_group() {
        let json = r#"{
            "buttons": [
                {"label": "ONE", "cc": 20, "color": "green", "select_group": "scene_a", "default_selected": true}
            ]
        }"#;

        let config: MidiCaptainConfig = serde_json::from_str(json).unwrap();
        let btn = &config.buttons[0];
        assert_eq!(btn.select_group.as_deref(), Some("scene_a"));
        assert_eq!(btn.default_selected, Some(true));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let btn2 = &config2.buttons[0];
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
        let btn = &config.buttons[0];
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
        let press_cmds2 = config2.buttons[0].press.as_ref().unwrap();
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
        let btn = &config.buttons[0];
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
        let btn2 = &config2.buttons[0];
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
        let cmd = &config.buttons[0].press.as_ref().unwrap()[0];
        assert_eq!(cmd.command_type, MessageType::Note);
        assert_eq!(cmd.note, Some(72));
        assert_eq!(cmd.velocity, Some(100));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let cmd2 = &config2.buttons[0].press.as_ref().unwrap()[0];
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
        assert_eq!(config.buttons[0].press.as_ref().unwrap()[0].command_type, MessageType::PcInc);
        assert_eq!(config.buttons[0].press.as_ref().unwrap()[0].pc_step, Some(5));
        assert_eq!(config.buttons[1].press.as_ref().unwrap()[0].command_type, MessageType::PcDec);
        assert_eq!(config.buttons[1].press.as_ref().unwrap()[0].pc_step, Some(2));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(config2.buttons[0].press.as_ref().unwrap()[0].pc_step, Some(5));
        assert_eq!(config2.buttons[1].press.as_ref().unwrap()[0].pc_step, Some(2));
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
        let cmd = &config.buttons[0].long_press.as_ref().unwrap()[0];
        assert_eq!(cmd.threshold_ms, Some(1000));

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        let cmd2 = &config2.buttons[0].long_press.as_ref().unwrap()[0];
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
        assert!(config.buttons[0].long_press.is_some());
        let long_press = config.buttons[0].long_press.as_ref().unwrap();
        assert_eq!(long_press.len(), 1);
        assert_eq!(long_press[0].cc, Some(25));
        assert_eq!(long_press[0].value, Some(64));

        // When reserialized, should become an array
        let reserialized = serde_json::to_string(&config).unwrap();
        assert!(reserialized.contains(r#""long_press":[{"#));

        // And can be deserialized again
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(config2.buttons[0].long_press.as_ref().unwrap().len(), 1);
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
        assert_eq!(config.buttons[0].press.as_ref().unwrap().len(), 1);
        assert_eq!(config.buttons[0].long_press.as_ref().unwrap().len(), 1);

        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(config2.buttons[0].press.as_ref().unwrap().len(), 1);
        assert_eq!(config2.buttons[0].long_press.as_ref().unwrap().len(), 1);
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
        let btn = &config.buttons[0];
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
        let states2 = config2.buttons[0].states.as_ref().unwrap();

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
        let btn = &config.buttons[0];
        assert_eq!(btn.off_mode, OffMode::Dim);
        assert_eq!(btn.dim_brightness, Some(50));

        // Round-trip test
        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(config2.buttons[0].dim_brightness, Some(50));
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
        let btn = &config.buttons[0];
        assert_eq!(btn.label, "PLAY");
        assert_eq!(btn.long_press_label, Some("PAUSE".to_string()));

        // Round-trip test
        let reserialized = serde_json::to_string(&config).unwrap();
        let config2: MidiCaptainConfig = serde_json::from_str(&reserialized).unwrap();
        assert_eq!(config2.buttons[0].long_press_label, Some("PAUSE".to_string()));
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
        let btn = &config.buttons[0];
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
        assert_eq!(config2.buttons[0].states.as_ref().unwrap()[0].press.as_ref().unwrap().len(), 1);
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
}
