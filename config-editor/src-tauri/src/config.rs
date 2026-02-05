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
}

/// Button trigger mode
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(rename_all = "lowercase")]
pub enum ButtonMode {
    #[default]
    Toggle,
    Momentary,
}

/// LED behavior when button is off
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(rename_all = "lowercase")]
pub enum OffMode {
    #[default]
    Dim,
    Off,
}

/// Button configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ButtonConfig {
    pub label: String,
    pub cc: u8,
    pub color: ButtonColor,
    #[serde(default)]
    pub mode: ButtonMode,
    #[serde(default, skip_serializing_if = "is_default_off_mode")]
    pub off_mode: OffMode,
}

fn is_default_off_mode(mode: &OffMode) -> bool {
    *mode == OffMode::Dim
}

/// Encoder push button configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EncoderPush {
    pub enabled: bool,
    pub cc: u8,
    pub label: String,
    #[serde(default)]
    pub mode: ButtonMode,
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

/// Complete MIDI Captain configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MidiCaptainConfig {
    #[serde(default)]
    pub device: DeviceType,
    pub buttons: Vec<ButtonConfig>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub encoder: Option<EncoderConfig>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub expression: Option<ExpressionPedals>,
}

impl MidiCaptainConfig {
    /// Validate the configuration
    pub fn validate(&self) -> Result<(), Vec<String>> {
        let mut errors = Vec::new();

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

        // Validate CC numbers (0-127)
        for (i, button) in self.buttons.iter().enumerate() {
            if button.cc > 127 {
                errors.push(format!("Button {} CC {} exceeds 127", i + 1, button.cc));
            }
            if button.label.len() > 8 {
                errors.push(format!(
                    "Button {} label '{}' exceeds 8 chars",
                    i + 1,
                    button.label
                ));
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
            if let Some(ref push) = enc.push {
                if push.cc > 127 {
                    errors.push(format!("Encoder push CC {} exceeds 127", push.cc));
                }
                if push.label.len() > 8 {
                    errors.push(format!("Encoder push label '{}' exceeds 8 chars", push.label));
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
            if exp.exp2.cc > 127 {
                errors.push(format!("EXP2 CC {} exceeds 127", exp.exp2.cc));
            }
            if exp.exp2.label.len() > 8 {
                errors.push(format!("EXP2 label '{}' exceeds 8 chars", exp.exp2.label));
            }
            if exp.exp2.max < exp.exp2.min {
                errors.push(format!("EXP2 max ({}) must be >= min ({})", exp.exp2.max, exp.exp2.min));
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
}
