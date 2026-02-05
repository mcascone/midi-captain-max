//! Tauri commands for config file operations

use crate::config::MidiCaptainConfig;
use std::fs;
use std::path::Path;
use tauri::command;

/// Known device volume prefixes (for path validation)
const VALID_VOLUME_PREFIXES: &[&str] = &["/Volumes/CIRCUITPY", "/Volumes/MIDICAPTAIN"];

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

/// Validate that a path is on a recognized MIDI Captain device volume.
/// Prevents path traversal attacks by ensuring paths are within expected directories.
fn validate_device_path(path: &str) -> Result<(), ConfigError> {
    let path = Path::new(path);
    
    // Canonicalize to resolve any .. or symlinks
    let canonical = path.canonicalize().map_err(|_| ConfigError {
        message: "Invalid path: could not resolve".to_string(),
        details: None,
    })?;
    
    let path_str = canonical.to_string_lossy();
    
    // Check if path starts with a valid volume prefix
    if !VALID_VOLUME_PREFIXES.iter().any(|prefix| path_str.starts_with(prefix)) {
        return Err(ConfigError {
            message: "Path must be on a MIDI Captain device (CIRCUITPY or MIDICAPTAIN volume)".to_string(),
            details: None,
        });
    }
    
    Ok(())
}

/// Read config from a file path
#[command]
pub fn read_config(path: String) -> Result<MidiCaptainConfig, ConfigError> {
    validate_device_path(&path)?;
    let contents = fs::read_to_string(&path)?;
    let config: MidiCaptainConfig = serde_json::from_str(&contents)?;
    Ok(config)
}

/// Read raw JSON from a file (for text editor)
#[command]
pub fn read_config_raw(path: String) -> Result<String, ConfigError> {
    validate_device_path(&path)?;
    let contents = fs::read_to_string(&path)?;
    // Pretty-print the JSON
    let value: serde_json::Value = serde_json::from_str(&contents)?;
    let pretty = serde_json::to_string_pretty(&value)?;
    Ok(pretty)
}

/// Write config to a file path
#[command]
pub fn write_config(path: String, config: MidiCaptainConfig) -> Result<(), ConfigError> {
    validate_device_path(&path)?;
    
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
    validate_device_path(&path)?;
    
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
