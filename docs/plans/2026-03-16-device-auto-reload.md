# Device Auto-Reload After Save

**Date:** 2026-03-16  
**Status:** Planned

## Problem

After the editor saves `config.json` to the device, the user must manually power-cycle
the unit for the firmware to pick up the new config. This is a significant UX friction
point, especially during live setup and iteration.

## Chosen Approach: Serial-triggered soft reload (Option 1)

After the editor saves `config.json`, the Tauri backend sends a single control byte
over USB CDC serial. The firmware detects it and calls `supervisor.reload()`. The
device restarts in ~2–3 seconds — no power cycle needed. USB briefly disconnects
and reconnects, then the device comes back with the new config loaded.

### Why this approach

| Option | Restart required | Complexity | Reliability |
|--------|-----------------|------------|-------------|
| **Serial-triggered soft reload** | Yes (~2s) | Low | High |
| Runtime hot-reload (no restart) | No | High | Medium — complex state teardown |
| Dev mode autoreload | Yes (~2s) | None | Low — triggers on any file write |

Runtime hot-reload (Option 2) requires carefully tearing down and rebuilding all
button state, LED assignments, and display layout — any missed state causes subtle
bugs. FAT32 `st_mtime` is also unreliable over USB. Serial-triggered reload is the
correct tradeoff: simple, reliable, and fast enough for the use case.

---

## Implementation Scope

### 1. Firmware — `firmware/dev/code.py`

Listen for a reload signal byte in the main loop. Use `\x12` (Ctrl+R) as the trigger.

```python
import sys
import supervisor

# In main loop, alongside existing handle_midi() / handle_switches() calls:
if supervisor.runtime.serial_bytes_available:
    byte = sys.stdin.read(1)
    if byte == '\x12':  # Ctrl+R = reload signal from editor
        supervisor.reload()
```

**Notes:**
- `supervisor.runtime.serial_bytes_available` is non-blocking — zero overhead when idle
- `supervisor.reload()` is the same call CircuitPython autoreload uses internally
- Must guard against false positives — only the specific byte triggers reload
- Should NOT conflict with existing serial console usage (screen, etc.)

---

### 2. Rust backend — `config-editor/src-tauri/src/commands.rs`

New Tauri command `trigger_device_reload` that:
1. Enumerates available serial ports
2. Identifies the CircuitPython CDC port (by USB VID/PID or port name heuristic)
3. Opens the port at 115200 baud
4. Writes the reload signal byte `0x12`
5. Closes the port

```rust
#[tauri::command]
pub async fn trigger_device_reload(device_path: String) -> Result<(), String> {
    // Find the serial port associated with this device mount path
    let port_name = find_serial_port_for_device(&device_path)
        .ok_or("Could not find serial port for device")?;

    let mut port = serialport::new(&port_name, 115_200)
        .timeout(Duration::from_millis(500))
        .open()
        .map_err(|e| e.to_string())?;

    port.write_all(&[0x12]).map_err(|e| e.to_string())?;
    Ok(())
}
```

**Dependencies to add to `Cargo.toml`:**
```toml
serialport = "4"
```

**Serial port detection strategy:**
- On macOS: CircuitPython appears as `/dev/tty.usbmodem*`
- On Windows: `COMx` with USB VID `0x239A` (Adafruit) or `0x2E8A` (Raspberry Pi)
- On Linux: `/dev/ttyACM*`
- Look for VID/PID matching known RP2040/CircuitPython devices
- Fallback: try all candidate ports in order, first successful write wins

---

### 3. TypeScript API — `config-editor/src/lib/api.ts`

New IPC wrapper:

```typescript
export async function triggerDeviceReload(devicePath: string): Promise<void> {
  await invoke('trigger_device_reload', { devicePath });
}
```

---

### 4. Device service — `config-editor/src/lib/services/deviceService.ts`

Call `triggerDeviceReload` automatically after a successful save in `saveToDevice()`:

```typescript
// After successful writeConfigRaw():
try {
  await triggerDeviceReload(device.path);
  statusMessage.set('Config saved — device reloading…');
} catch {
  // Non-fatal: save succeeded, reload failed — user can power-cycle manually
  statusMessage.set('Config saved — please restart the device to apply changes');
}
```

The reload failure must be non-fatal: the save already succeeded. If serial port
access fails (port busy, permissions, wrong OS), the user falls back to manual
power-cycle — no regression from current behavior.

---

## UX Flow After Implementation

1. User edits config in editor
2. User clicks Save (or ⌘S)
3. Editor writes `config.json` to device mass storage
4. Editor sends `0x12` over serial
5. Device calls `supervisor.reload()` — USB briefly disconnects (~1s)
6. Device reboots, reads new `config.json`, comes back online (~2s total)
7. Editor status bar shows "Config saved — device reloading…"
8. Editor auto-reconnects to device after USB reconnect (if device watcher is live)

---

## Out of Scope for This Phase

- True runtime hot-reload (no restart) — deferred, high complexity
- Reload progress indicator / reconnect polling in editor
- MIDI SysEx-triggered reload (alternative transport)

---

## Files to Modify

| File | Change |
|------|--------|
| `firmware/dev/code.py` | Add serial byte listener in main loop |
| `config-editor/src-tauri/Cargo.toml` | Add `serialport = "4"` dependency |
| `config-editor/src-tauri/src/commands.rs` | Add `trigger_device_reload` command |
| `config-editor/src-tauri/tauri.conf.json` | Register new command in allowlist |
| `config-editor/src/lib/api.ts` | Add `triggerDeviceReload()` IPC wrapper |
| `config-editor/src/lib/services/deviceService.ts` | Call reload after save |

---

## Testing Plan

1. **Happy path**: Save config → device restarts in ~2s → new config active
2. **Serial port busy** (screen attached): reload fails gracefully, save still succeeds, user prompted to power-cycle
3. **No serial port found**: same graceful fallback
4. **False positive prevention**: send other bytes over serial → firmware ignores them
5. **Dev mode**: verify reload signal works alongside dev mode USB drive mount
6. **Platform coverage**: macOS, Windows, Linux serial port detection
