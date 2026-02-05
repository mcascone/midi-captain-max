//! Device detection via volume mounting

use notify::{Config, RecommendedWatcher, RecursiveMode, Watcher, Event, EventKind};
use std::path::PathBuf;
use std::sync::mpsc::{self, Sender, Receiver};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Mutex;
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

// Global shutdown signal sender (allows stopping the watcher thread)
static SHUTDOWN_TX: Mutex<Option<Sender<()>>> = Mutex::new(None);

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
    let (shutdown_tx, shutdown_rx): (Sender<()>, Receiver<()>) = mpsc::channel();
    
    // Store shutdown sender for later use
    if let Ok(mut guard) = SHUTDOWN_TX.lock() {
        *guard = Some(shutdown_tx);
    }
    
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
        
        loop {
            // Check for shutdown signal (non-blocking)
            if shutdown_rx.try_recv().is_ok() {
                break;
            }
            
            // Check for filesystem events (with timeout to allow shutdown checks)
            match rx.recv_timeout(std::time::Duration::from_millis(100)) {
                Ok(event) => {
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
                Err(mpsc::RecvTimeoutError::Timeout) => {
                    // No event, continue loop (allows shutdown check)
                }
                Err(mpsc::RecvTimeoutError::Disconnected) => {
                    // Channel closed, exit thread
                    break;
                }
            }
        }
        
        // Reset flag so watcher can be restarted if needed
        WATCHER_STARTED.store(false, Ordering::SeqCst);
    });
    
    Ok(())
}

/// Stop the device watcher thread (called on app shutdown)
#[command]
pub fn stop_device_watcher() -> Result<(), String> {
    if let Ok(mut guard) = SHUTDOWN_TX.lock() {
        if let Some(tx) = guard.take() {
            let _ = tx.send(());
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_check_volume_circuitpy() {
        // Test that CIRCUITPY volume name is recognized
        let path = PathBuf::from("/Volumes/CIRCUITPY");
        let result = check_volume(&path);
        // Should return Some because the name matches, has_config will be false
        assert!(result.is_some());
        let device = result.unwrap();
        assert_eq!(device.name, "CIRCUITPY");
        assert!(!device.has_config); // No actual config file exists in test
    }
    
    #[test]
    fn test_check_volume_midicaptain() {
        // Test that MIDICAPTAIN volume name is recognized
        let path = PathBuf::from("/Volumes/MIDICAPTAIN");
        let result = check_volume(&path);
        assert!(result.is_some());
        let device = result.unwrap();
        assert_eq!(device.name, "MIDICAPTAIN");
        assert!(!device.has_config);
    }
    
    #[test]
    fn test_check_volume_case_insensitive() {
        // Test case insensitivity
        let path = PathBuf::from("/Volumes/circuitpy");
        let result = check_volume(&path);
        assert!(result.is_some());
        let device = result.unwrap();
        assert_eq!(device.name, "circuitpy"); // Preserves original case
    }
    
    #[test]
    fn test_check_volume_invalid() {
        let path = PathBuf::from("/Volumes/SomeOtherDrive");
        let result = check_volume(&path);
        assert!(result.is_none());
    }
    
    #[test]
    fn test_device_volumes_list() {
        // Verify the expected device names are in the list
        assert!(DEVICE_VOLUMES.contains(&"CIRCUITPY"));
        assert!(DEVICE_VOLUMES.contains(&"MIDICAPTAIN"));
        assert!(!DEVICE_VOLUMES.contains(&"Macintosh HD"));
    }
}
