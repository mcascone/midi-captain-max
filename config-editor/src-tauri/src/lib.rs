mod commands;
mod midi;
mod config;
mod device;

use commands::*;
use device::{scan_devices, start_device_watcher, stop_device_watcher};

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_fs::init())
        .invoke_handler(tauri::generate_handler![
            read_config,
            read_config_raw,
            write_config,
            write_config_raw,
            validate_config,
            eject_device,
            trigger_device_reload,
            list_midi_ports_cmd,
            send_midi_message_cmd,
            start_midi_input_listener_cmd,
            stop_midi_input_listener_cmd,
            scan_devices,
            start_device_watcher,
            stop_device_watcher
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
