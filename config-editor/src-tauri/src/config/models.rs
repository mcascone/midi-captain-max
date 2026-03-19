//! MIDI Captain configuration data structures
//!
//! Configuration model definitions for buttons, encoders, expressions, and main config.

use super::types::*;
use serde::{Deserialize, Serialize};

/// Per-state overrides for keytimes cycling
#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct StateOverride {
    // Multi-command event arrays (per-state actions)
    #[serde(
        default,
        skip_serializing_if = "Option::is_none",
        deserialize_with = "deserialize_one_or_many"
    )]
    pub press: Option<Vec<MidiCommand>>,
    #[serde(
        default,
        skip_serializing_if = "Option::is_none",
        deserialize_with = "deserialize_one_or_many"
    )]
    pub release: Option<Vec<MidiCommand>>,
    #[serde(
        default,
        skip_serializing_if = "Option::is_none",
        deserialize_with = "deserialize_one_or_many"
    )]
    pub long_press: Option<Vec<MidiCommand>>,
    #[serde(
        default,
        skip_serializing_if = "Option::is_none",
        deserialize_with = "deserialize_one_or_many"
    )]
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
    #[serde(skip_serializing_if = "Option::is_none")]
    pub long_press_color: Option<ButtonColor>,
    pub color: ButtonColor,

    // ===== DEVICE PROFILE SUPPORT =====
    /// Device profile ID (e.g., 'quad-cortex', 'helix')
    /// When set with action_id, editor resolves to MIDI before saving
    #[serde(skip_serializing_if = "Option::is_none")]
    pub profile_id: Option<String>,
    /// Action within profile (e.g., 'scene_b', 'snapshot_3')
    #[serde(skip_serializing_if = "Option::is_none")]
    pub action_id: Option<String>,

    // ===== NEW: Multi-command event arrays =====
    #[serde(
        default,
        skip_serializing_if = "Option::is_none",
        deserialize_with = "deserialize_one_or_many"
    )]
    pub press: Option<Vec<MidiCommand>>,
    #[serde(
        default,
        skip_serializing_if = "Option::is_none",
        deserialize_with = "deserialize_one_or_many"
    )]
    pub release: Option<Vec<MidiCommand>>,
    #[serde(
        default,
        skip_serializing_if = "Option::is_none",
        deserialize_with = "deserialize_one_or_many"
    )]
    pub long_press: Option<Vec<MidiCommand>>,
    #[serde(
        default,
        skip_serializing_if = "Option::is_none",
        deserialize_with = "deserialize_one_or_many"
    )]
    pub long_release: Option<Vec<MidiCommand>>,

    // ===== LEGACY: Single-type fields (for backwards compatibility) =====
    #[serde(
        rename = "type",
        default,
        skip_serializing_if = "is_default_message_type"
    )]
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
    pub value_on: Option<u8>, // CC value sent when turning ON (default 127)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub value_off: Option<u8>, // CC value sent when turning OFF (default 0)
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

/// Splash screen configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SplashScreenConfig {
    #[serde(skip_serializing_if = "Option::is_none")]
    pub enabled: Option<bool>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub duration_ms: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub idle_timeout_seconds: Option<u32>,
}

/// Bank configuration for multi-bank mode
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BankConfig {
    pub name: String,
    pub buttons: Vec<ButtonConfig>,
}

/// Bank switching configuration
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BankSwitchConfig {
    pub method: BankSwitchMethod,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub button: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cc: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pc_base: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub channel: Option<u8>,
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
    
    // ===== MULTI-BANK SUPPORT =====
    /// Array of banks (max 8 recommended for Flash storage)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub banks: Option<Vec<BankConfig>>,
    /// Bank switching configuration (method, button/CC/PC, channel)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub bank_switch: Option<BankSwitchConfig>,
    /// Active bank on boot (0-indexed, default: 0)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub active_bank: Option<u8>,
    
    // ===== SINGLE-BANK MODE (legacy, backward compatibility) =====
    /// Legacy: single bank of buttons (auto-wrapped in banks[0] on load if banks not present)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub buttons: Option<Vec<ButtonConfig>>,
    
    // ===== SHARED ACROSS ALL BANKS =====
    #[serde(skip_serializing_if = "Option::is_none")]
    pub encoder: Option<EncoderConfig>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub expression: Option<ExpressionPedals>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub display: Option<DisplayConfig>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub splash_screen: Option<SplashScreenConfig>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub long_press_threshold_ms: Option<u32>,
}
