mod commands;
mod config;

use commands::{read_config, read_config_raw, validate_config, write_config, write_config_raw};

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
            validate_config
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
