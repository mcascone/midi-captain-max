use midir::{Ignore, MidiInput, MidiOutput};
use serde::Serialize;
use std::sync::{Arc, Mutex};
use std::thread;

use crossbeam_channel::{Receiver, Sender};

use tauri::AppHandle;
use tauri::Emitter;

#[derive(Serialize, Debug, Clone)]
pub struct MidiEvent {
    pub timestamp: u64,
    pub data: Vec<u8>,
    pub port: String,
}

/// Simple MIDI manager state stored as a global singleton.
struct MidiState {
    // Currently only track a running listener thread handle via channel
    _listener_tx: Option<Sender<()>>,
}

impl MidiState {
    fn new() -> Self {
        MidiState { _listener_tx: None }
    }
}

static MIDI_STATE: once_cell::sync::Lazy<Arc<Mutex<MidiState>>> =
    once_cell::sync::Lazy::new(|| Arc::new(Mutex::new(MidiState::new())));

/// List available MIDI input ports (names)
pub fn list_midi_ports() -> Result<Vec<String>, String> {
    let in_ports = MidiInput::new("midi-captain-editor-list").map_err(|e| e.to_string())?;
    let mut names = Vec::new();
    for p in in_ports.ports() {
        let name = in_ports
            .port_name(&p)
            .map(|s| s.to_string())
            .unwrap_or_else(|_| "Unknown MIDI Port".to_string());
        names.push(name);
    }
    Ok(names)
}

/// Send raw MIDI bytes to the first matching output port by name.
pub fn send_midi_message(port_name: &str, data: Vec<u8>) -> Result<(), String> {
    let midi_out = MidiOutput::new("midi-captain-editor-out").map_err(|e| e.to_string())?;
    let ports = midi_out.ports();
    for p in &ports {
        if let Ok(name) = midi_out.port_name(p) {
            if name == port_name {
                let mut conn_out = midi_out.connect(p, "midi-captain-editor-conn").map_err(|e| e.to_string())?;
                conn_out.send(&data).map_err(|e| e.to_string())?;
                return Ok(());
            }
        }
    }
    Err(format!("MIDI output port '{}' not found", port_name))
}

/// Start a MIDI input listener on the named port and emit `midi-event` on the Tauri app handle
pub fn start_midi_input_listener(app: AppHandle, port_name: String) -> Result<(), String> {
    // Verify port exists first
    let mut midi_in_check = MidiInput::new("midi-captain-editor-check").map_err(|e| e.to_string())?;
    midi_in_check.ignore(Ignore::None);
    let ports = midi_in_check.ports();
    let port_exists = ports.iter().any(|p| {
        midi_in_check.port_name(p).map(|n| n == port_name).unwrap_or(false)
    });

    if !port_exists {
        return Err(format!("MIDI input port '{}' not found", port_name));
    }

    // Create channel for stopping the listener
    let (stop_tx, stop_rx): (Sender<()>, Receiver<()>) = crossbeam_channel::unbounded();

    // Store sender so stop can be called later
    {
        let mut st = MIDI_STATE.lock().unwrap();
        st._listener_tx = Some(stop_tx.clone());
    }

    let app_handle = app.clone();
    let port_name_clone = port_name.clone();

    // Spawn thread that owns its own MidiInput instance
    thread::spawn(move || {
        let mut midi_in_thread = match MidiInput::new("midi-captain-editor-in-thread") {
            Ok(m) => m,
            Err(e) => {
                eprintln!("[MIDI] Failed to create MidiInput in thread: {}", e);
                return;
            }
        };
        midi_in_thread.ignore(Ignore::None);

        // Find the port by name in THIS thread's MidiInput instance
        let ports = midi_in_thread.ports();
        let target_port = ports.iter().find(|p| {
            midi_in_thread.port_name(p).map(|n| n == port_name_clone).unwrap_or(false)
        });

        let port = match target_port {
            Some(p) => p,
            None => {
                eprintln!("[MIDI] Port '{}' not found in thread", port_name_clone);
                return;
            }
        };

        let port_name_for_event = port_name_clone.clone();
        let conn = match midi_in_thread.connect(port, "midi-captain-editor-input", move |stamp, message, _| {
            let evt = MidiEvent {
                timestamp: stamp as u64,
                data: message.to_vec(),
                port: port_name_for_event.clone(),
            };
            if let Err(e) = app_handle.emit("midi-event", evt.clone()) {
                eprintln!("[MIDI] Failed to emit event: {}", e);
            } else {
                println!("[MIDI] Event emitted: {:?}", evt);
            }
        }, ()) {
            Ok(c) => c,
            Err(e) => {
                eprintln!("[MIDI] Failed to connect to port: {}", e);
                return;
            }
        };

        println!("[MIDI] Listener thread started for port: {}", port_name_clone);

        // Block until stop signal; keep conn alive while waiting
        let _ = stop_rx.recv();
        drop(conn);
        println!("[MIDI] Listener thread stopped");
    });

    Ok(())
}

/// Stop listener (best-effort)
pub fn stop_midi_input_listener() {
    if let Some(tx) = &MIDI_STATE.lock().unwrap()._listener_tx {
        let _ = tx.send(());
    }
    let mut st = MIDI_STATE.lock().unwrap();
    st._listener_tx = None;
}
