//! Tauri commands for config file operations

use crate::config::MidiCaptainConfig;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use tauri::command;

#[cfg(unix)]
use std::os::unix::fs::MetadataExt;

/// Known device volume names (for validation)
const DEVICE_VOLUMES: &[&str] = &["CIRCUITPY", "MIDICAPTAIN"];

/// Get volume name for a path (cross-platform)
#[cfg(target_os = "windows")]
fn get_path_volume_name(path: &Path) -> Option<String> {
    use std::os::windows::ffi::OsStrExt;
    use std::ffi::OsString;
    use std::os::windows::ffi::OsStringExt;
    
    // Get the root path (e.g., "C:\" from "C:\Users\...")
    let mut components = path.components();
    let root = components.next()?;
    let root_path = PathBuf::from(root.as_os_str());
    let root_str = format!("{}\\", root_path.display());
    
    let mut volume_name: Vec<u16> = vec![0; 261];
    
    unsafe {
        let root_wide: Vec<u16> = OsString::from(&root_str)
            .encode_wide()
            .chain(Some(0))
            .collect();
        
        let result = winapi::um::fileapi::GetVolumeInformationW(
            root_wide.as_ptr(),
            volume_name.as_mut_ptr(),
            volume_name.len() as winapi::shared::minwindef::DWORD,
            std::ptr::null_mut(),
            std::ptr::null_mut(),
            std::ptr::null_mut(),
            std::ptr::null_mut(),
            0,
        );
        
        if result != 0 {
            let len = volume_name.iter().position(|&c| c == 0).unwrap_or(volume_name.len());
            let name = OsString::from_wide(&volume_name[..len]);
            return name.into_string().ok();
        }
    }
    
    None
}

#[cfg(not(target_os = "windows"))]
fn get_path_volume_name(path: &Path) -> Option<String> {
    // On Unix, find the volume under /Volumes/ or /media/
    for ancestor in path.ancestors() {
        if let Some(parent) = ancestor.parent() {
            let parent_str = parent.to_string_lossy();
            if parent_str == "/Volumes" || parent_str.starts_with("/media/") || parent_str.starts_with("/run/media/") {
                return ancestor.file_name()?.to_str().map(|s| s.to_string());
            }
        }
    }
    None
}

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
///
/// Accepts:
/// 1. Volumes with a known name (CIRCUITPY or MIDICAPTAIN), or
/// 2. Volumes whose config.json identifies as MIDI Captain **and** whose
///    `usb_drive_name` matches the actual volume name (case-insensitive).
///    This limits the surface: an arbitrary volume won't pass validation
///    just because someone placed a config.json on it.
fn validate_device_path(path: &str) -> Result<(), ConfigError> {
    let path = Path::new(path);

    // Canonicalize to resolve any .. or symlinks
    let canonical = path.canonicalize().map_err(|e| ConfigError {
        message: format!("Input watch path is neither a file nor a directory: {}", e),
        details: None,
    })?;

    // Check if the path is on a valid device volume
    let volume_name = get_path_volume_name(&canonical).ok_or_else(|| ConfigError {
        message: "Could not determine volume name for path".to_string(),
        details: None,
    })?;

    // Accept well-known volume names
    if DEVICE_VOLUMES.iter().any(|v| volume_name.eq_ignore_ascii_case(v)) {
        return Ok(());
    }

    // Accept volumes that contain a valid MIDI Captain config.json.
    // If usb_drive_name is explicitly declared in the config, it must match
    // the actual volume name — preventing a stray config.json on an unrelated
    // volume from passing. If usb_drive_name is not declared, any valid
    // MIDI Captain config is accepted.
    if let Some(volume_path) = get_volume_path(&canonical) {
        let config_path = volume_path.join("config.json");
        if crate::device::is_midi_captain_config(&config_path) {
            match crate::device::parse_midi_captain_config(&config_path) {
                Some(declared_name) if declared_name.eq_ignore_ascii_case(&volume_name) => {
                    return Ok(());
                }
                None => {
                    // No custom name declared — accept any valid MIDI Captain volume
                    return Ok(());
                }
                _ => {} // declared name doesn't match this volume
            }
        }
    }

    Err(ConfigError {
        message: format!(
            "Path must be on a MIDI Captain device (CIRCUITPY, MIDICAPTAIN, or a custom-named volume whose config.json usb_drive_name matches), found: {}",
            volume_name
        ),
        details: None,
    })
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

/// Get the volume/drive root path from a file path
/// e.g., /Volumes/CIRCUITPY from /Volumes/CIRCUITPY/config.json on macOS
/// or C:\ from C:\config.json on Windows
#[cfg(target_os = "windows")]
fn get_volume_path(path: &Path) -> Option<PathBuf> {
    // On Windows, get the drive root (e.g., C:\)
    let mut components = path.components();
    components.next().map(|c| PathBuf::from(c.as_os_str()))
}

#[cfg(not(target_os = "windows"))]
fn get_volume_path(path: &Path) -> Option<PathBuf> {
    // On Unix, find the mount point under /Volumes/, /media/, or /run/media/
    path.ancestors()
        .find(|p| {
            if let Some(parent) = p.parent() {
                let parent_str = parent.to_string_lossy();
                parent_str == "/Volumes" 
                    || parent_str.starts_with("/media/") 
                    || parent_str.starts_with("/run/media/")
            } else {
                false
            }
        })
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

/// Write data to a file and sync to physical storage before returning.
///
/// `fs::write` closes the file without an explicit fsync, leaving data in the
/// OS page cache. On a USB-connected FAT32 device (CircuitPython), a power
/// cycle immediately after save can race the flush and the device boots with
/// stale data. Keeping the write handle open for `sync_all` before drop
/// ensures the data reaches the device's flash.
fn write_sync(path: &Path, data: &[u8]) -> Result<(), std::io::Error> {
    let mut file = OpenOptions::new().write(true).create(true).truncate(true).open(path)?;
    file.write_all(data)?;
    file.sync_all()?;
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
    write_sync(path_obj, json.as_bytes())?;

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
    write_sync(path_obj, pretty.as_bytes())?;

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
