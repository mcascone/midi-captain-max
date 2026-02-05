//! Tauri commands for config file operations

use crate::config::MidiCaptainConfig;
use std::fs::{self, File};
use std::path::Path;
use tauri::command;

#[cfg(unix)]
use std::os::unix::fs::MetadataExt;

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

/// Check if a volume is still mounted (not being ejected)
/// Compares device ID of volume vs root - if same, volume is not a separate filesystem
#[cfg(unix)]
fn is_volume_mounted(volume_path: &Path) -> bool {
    if let (Ok(vol_meta), Ok(root_meta)) = (
        volume_path.metadata(),
        Path::new("/").metadata()
    ) {
        vol_meta.dev() != root_meta.dev()
    } else {
        false
    }
}

#[cfg(not(unix))]
fn is_volume_mounted(volume_path: &Path) -> bool {
    // On non-Unix systems, just check if path exists
    volume_path.exists()
}

/// Get the volume path from a file path (e.g., /Volumes/CIRCUITPY from /Volumes/CIRCUITPY/config.json)
fn get_volume_path(path: &Path) -> Option<std::path::PathBuf> {
    path.ancestors()
        .find(|p| p.parent() == Some(Path::new("/Volumes")))
        .map(|p| p.to_path_buf())
}

/// Verify the device is still mounted before writing
fn verify_device_connected(path: &Path) -> Result<(), ConfigError> {
    if let Some(volume_path) = get_volume_path(path) {
        if !is_volume_mounted(&volume_path) {
            return Err(ConfigError {
                message: "Device was disconnected".to_string(),
                details: None,
            });
        }
    }
    Ok(())
}

/// Sync file to ensure data reaches device before user ejects
fn sync_file(path: &Path) {
    if let Ok(file) = File::open(path) {
        let _ = file.sync_all();
    }
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
    
    let path_obj = Path::new(&path);
    
    // Verify volume is still mounted
    verify_device_connected(path_obj)?;
    
    // Validate before writing
    if let Err(errors) = config.validate() {
        return Err(ConfigError {
            message: "Validation failed".to_string(),
            details: Some(errors),
        });
    }

    let json = serde_json::to_string_pretty(&config)?;
    fs::write(&path, &json)?;
    
    // Sync to ensure data reaches device before user ejects
    sync_file(path_obj);
    
    Ok(())
}

/// Write raw JSON to a file (from text editor)
#[command]
pub fn write_config_raw(path: String, json: String) -> Result<(), ConfigError> {
    validate_device_path(&path)?;
    
    let path_obj = Path::new(&path);
    
    // Verify volume is still mounted
    verify_device_connected(path_obj)?;
    
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
    fs::write(&path, &pretty)?;
    
    // Sync to ensure data reaches device before user ejects
    sync_file(path_obj);
    
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
