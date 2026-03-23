//! MIDI Captain configuration enum types
//!
//! Basic type definitions for configuration validation.

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

/// Expression pedal polarity
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(rename_all = "lowercase")]
pub enum Polarity {
    #[default]
    Normal,
    Inverted,
}

/// Device type
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(rename_all = "lowercase")]
pub enum DeviceType {
    #[default]
    Std10,
    Mini6,
}

/// Bank switching method
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Default)]
#[serde(rename_all = "lowercase")]
pub enum BankSwitchMethod {
    #[default]
    Button,
    Cc,
    Pc,
}

/// Condition operator for comparisons
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub enum ConditionOperator {
    #[serde(rename = "==")]
    Equals,
    #[serde(rename = "!=")]
    NotEquals,
    #[serde(rename = ">")]
    GreaterThan,
    #[serde(rename = "<")]
    LessThan,
    #[serde(rename = ">=")]
    GreaterOrEqual,
    #[serde(rename = "<=")]
    LessOrEqual,
}

/// Type of condition to evaluate
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(tag = "type", rename_all = "snake_case")]
pub enum Condition {
    /// Check if a button is ON or OFF
    ButtonState {
        button: u8,
        state: ButtonState,
    },
    /// Check which keytime state a button is in
    ButtonKeytime {
        button: u8,
        keytime: u8,
    },
    /// Check last received MIDI CC value from host
    ReceivedMidi {
        cc: u8,
        channel: u8,
        operator: ConditionOperator,
        value: u8,
    },
    /// Check expression pedal position
    Expression {
        pedal: String, // "exp1" or "exp2"
        operator: ConditionOperator,
        value: u8,
    },
    /// Check encoder position
    Encoder {
        operator: ConditionOperator,
        value: u8,
    },
}

/// Button state for conditional checks
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum ButtonState {
    On,
    Off,
}
