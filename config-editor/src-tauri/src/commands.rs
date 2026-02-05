//! Tauri commands for config file operations

use crate::config::MidiCaptainConfig;
use std::fs;
use tauri::command;

/// Error type for config operations
#[derive(Debug, serde::Serialize)]
pub struct ConfigError {
    pub message: String,
    pub details: Option<Vec<String>>,
}

impl From<std::io::Error> for ConfigError {
    fn from(e: std::io::Error) -> Self {
        ConfigError {
            message: e.to_string(),
            details: None,
        }
    }
}

impl From<serde_json::Error> for ConfigError {
    fn from(e: serde_json::Error) -> Self {
        ConfigError {
            message: format!("JSON parse error: {}", e),
            details: None,
        }
    }
}

/// Read config from a file path
#[command]
pub fn read_config(path: String) -> Result<MidiCaptainConfig, ConfigError> {
    let contents = fs::read_to_string(&path)?;
    let config: MidiCaptainConfig = serde_json::from_str(&contents)?;
    Ok(config)
}

/// Read raw JSON from a file (for text editor)
#[command]
pub fn read_config_raw(path: String) -> Result<String, ConfigError> {
    let contents = fs::read_to_string(&path)?;
    // Pretty-print the JSON
    let value: serde_json::Value = serde_json::from_str(&contents)?;
    let pretty = serde_json::to_string_pretty(&value)?;
    Ok(pretty)
}

/// Write config to a file path
#[command]
pub fn write_config(path: String, config: MidiCaptainConfig) -> Result<(), ConfigError> {
    // Validate before writing
    if let Err(errors) = config.validate() {
        return Err(ConfigError {
            message: "Validation failed".to_string(),
            details: Some(errors),
        });
    }

    let json = serde_json::to_string_pretty(&config)?;
    fs::write(&path, json)?;
    Ok(())
}

/// Write raw JSON to a file (from text editor)
#[command]
pub fn write_config_raw(path: String, json: String) -> Result<(), ConfigError> {
    // Validate JSON is parseable
    let config: MidiCaptainConfig = serde_json::from_str(&json)?;

    // Validate config
    if let Err(errors) = config.validate() {
        return Err(ConfigError {
            message: "Validation failed".to_string(),
            details: Some(errors),
        });
    }

    // Pretty-print and write
    let pretty = serde_json::to_string_pretty(&config)?;
    fs::write(&path, pretty)?;
    Ok(())
}

/// Validate JSON without writing
#[command]
pub fn validate_config(json: String) -> Result<(), ConfigError> {
    let config: MidiCaptainConfig = serde_json::from_str(&json)?;

    if let Err(errors) = config.validate() {
        return Err(ConfigError {
            message: "Validation failed".to_string(),
            details: Some(errors),
        });
    }

    Ok(())
}
