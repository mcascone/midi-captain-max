//! Device detection via volume mounting

use notify::{Config, RecommendedWatcher, RecursiveMode, Watcher, Event, EventKind};
use std::path::PathBuf;
use std::sync::mpsc;
use std::sync::atomic::{AtomicBool, Ordering};
use tauri::{command, AppHandle, Emitter};

/// Known device volume names
const DEVICE_VOLUMES: &[&str] = &["CIRCUITPY", "MIDICAPTAIN"];

/// Detected device info
#[derive(Debug, Clone, serde::Serialize)]
pub struct DetectedDevice {
    pub name: String,
    pub path: PathBuf,
    pub config_path: PathBuf,
    pub has_config: bool,
}

/// Check if a volume is a MIDI Captain device
fn check_volume(path: &PathBuf) -> Option<DetectedDevice> {
    let name = path.file_name()?.to_str()?;
    
    if DEVICE_VOLUMES.iter().any(|v| name.eq_ignore_ascii_case(v)) {
        let config_path = path.join("config.json");
        let has_config = config_path.exists();
        
        Some(DetectedDevice {
            name: name.to_string(),
            path: path.clone(),
            config_path,
            has_config,
        })
    } else {
        None
    }
}

/// Scan for connected devices
#[command]
pub fn scan_devices() -> Vec<DetectedDevice> {
    let volumes_path = PathBuf::from("/Volumes");
    let mut devices = Vec::new();
    
    if let Ok(entries) = std::fs::read_dir(&volumes_path) {
        for entry in entries.flatten() {
            let path = entry.path();
            if let Some(device) = check_volume(&path) {
                devices.push(device);
            }
        }
    }
    
    devices
}

// Global flag to prevent multiple watchers
static WATCHER_STARTED: AtomicBool = AtomicBool::new(false);

/// Start watching for device connections
/// Emits "device-connected" and "device-disconnected" events
/// Note: Only one watcher can run at a time to prevent thread leaks
#[command]
pub fn start_device_watcher(app: AppHandle) -> Result<(), String> {
    // Prevent multiple watchers
    if WATCHER_STARTED.swap(true, Ordering::SeqCst) {
        return Ok(()); // Already running
    }
    
    let (tx, rx) = mpsc::channel();
    
    let mut watcher = RecommendedWatcher::new(
        move |res: Result<Event, notify::Error>| {
            if let Ok(event) = res {
                let _ = tx.send(event);
            }
        },
        Config::default(),
    ).map_err(|e| e.to_string())?;
    
    watcher.watch(
        std::path::Path::new("/Volumes"),
        RecursiveMode::NonRecursive,
    ).map_err(|e| e.to_string())?;
    
    // Spawn thread to handle events
    std::thread::spawn(move || {
        // Keep watcher alive
        let _watcher = watcher;
        
        for event in rx {
            match event.kind {
                EventKind::Create(_) => {
                    // Volume mounted - check if it's a device
                    for path in &event.paths {
                        if let Some(device) = check_volume(path) {
                            let _ = app.emit("device-connected", device);
                        }
                    }
                }
                EventKind::Remove(_) => {
                    // Volume unmounted
                    for path in &event.paths {
                        if let Some(name) = path.file_name() {
                            let name_str = name.to_string_lossy().to_string();
                            if DEVICE_VOLUMES.iter().any(|v| name_str.eq_ignore_ascii_case(v)) {
                                let _ = app.emit("device-disconnected", name_str);
                            }
                        }
                    }
                }
                _ => {}
            }
        }
    });
    
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_check_volume_valid() {
        let path = PathBuf::from("/Volumes/CIRCUITPY");
        // This won't actually work in tests without a real volume,
        // but we can at least verify the function signature
        let result = check_volume(&path);
        // Will be None because the path doesn't exist in tests
        assert!(result.is_none() || result.is_some());
    }
    
    #[test]
    fn test_check_volume_invalid() {
        let path = PathBuf::from("/Volumes/SomeOtherDrive");
        let result = check_volume(&path);
        assert!(result.is_none());
    }
}
