# Device Eject on Save - Implementation Plan

## Feature Overview

After saving config changes to a MIDI Captain device, automatically prompt the user to safely eject the device so they can power-cycle it to apply changes. This eliminates the manual USB unplugging step and provides better cross-platform device management.

## Current State Analysis

### Save Flow (config-editor/src/routes/+page.svelte)
```typescript
async function saveToDevice() {
  // Validates, normalizes, writes config
  // Shows success toast
  // Does NOT prompt for eject or device restart
}
```

### Reset Device Button
```typescript
async function resetDevice() {
  await message(
    'To apply config changes, reset your MIDI Captain device:\n\n' +
    '1. Unplug the USB cable\n2. Wait 2 seconds\n3. Plug it back in',
    { title: 'Reset Device', kind: 'info' }
  );
}
```

**Issue:** Instructions say "Unplug USB cable" but the device has a power button on the back. This is misleading.

### Device Detection (config-editor/src-tauri/src/device.rs)
- Watches `/Volumes` (macOS), `/media/$USER` (Linux), drive letters (Windows)
- Emits `device-connected` and `device-disconnected` events
- Frontend auto-selects device when available
- `scan_devices()` returns list of currently connected devices

## Implementation Plan

### 1. Add Tauri `eject_device` Command

**File:** `config-editor/src-tauri/src/commands.rs`

```rust
/// Safely eject/unmount a device volume
#[command]
pub async fn eject_device(path: String) -> Result<String, ConfigError> {
    let path = std::path::Path::new(&path);
    let volume_path = get_volume_path(path).ok_or_else(|| ConfigError {
        message: "Could not determine volume path".to_string(),
        details: None,
    })?;
    
    let volume_name = volume_path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("device");
    
    #[cfg(target_os = "macos")]
    {
        let output = std::process::Command::new("diskutil")
            .args(&["eject", volume_path.to_str().unwrap()])
            .output()
            .map_err(|e| ConfigError {
                message: format!("Failed to eject device: {}", e),
                details: None,
            })?;
        
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(ConfigError {
                message: format!("Eject failed: {}", stderr),
                details: None,
            });
        }
        
        Ok(format!("Device '{}' ejected successfully", volume_name))
    }
    
    #[cfg(target_os = "linux")]
    {
        // Try gio first (modern GNOME/GTK)
        let gio_result = std::process::Command::new("gio")
            .args(&["mount", "-u", volume_path.to_str().unwrap()])
            .output();
        
        if let Ok(output) = gio_result {
            if output.status.success() {
                return Ok(format!("Device '{}' ejected successfully", volume_name));
            }
        }
        
        // Fallback to umount
        let output = std::process::Command::new("umount")
            .arg(volume_path.to_str().unwrap())
            .output()
            .map_err(|e| ConfigError {
                message: format!("Failed to unmount device: {}", e),
                details: None,
            })?;
        
        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            return Err(ConfigError {
                message: format!("Unmount failed: {}", stderr),
                details: None,
            });
        }
        
        Ok(format!("Device '{}' unmounted successfully", volume_name))
    }
    
    #[cfg(target_os = "windows")]
    {
        // Windows doesn't have a simple eject command for USB drives
        // Recommend using the system tray "Safely Remove Hardware"
        Err(ConfigError {
            message: format!(
                "On Windows, please use the system tray 'Safely Remove Hardware' icon to eject '{}'",
                volume_name
            ),
            details: Some(vec![
                "Look for the USB icon in the system tray (bottom-right)".to_string(),
                "Click it and select 'Eject {}'".to_string().replace("{}", volume_name),
            ]),
        })
    }
}
```

### 2. Add Frontend API Wrapper

**File:** `config-editor/src/lib/api.ts`

```typescript
export async function ejectDevice(path: string): Promise<string> {
  return invoke('eject_device', { path });
}
```

### 3. Update Save Flow with Eject Prompt

**File:** `config-editor/src/routes/+page.svelte`

```typescript
async function saveToDevice() {
  if (!$selectedDevice) return;
  if (!validate()) {
    showToast('Please fix validation errors before saving', 'error');
    return;
  }
  $isLoading = true;
  try {
    const configObj = normalizeConfig(get(config));
    const configJson = JSON.stringify(configObj, null, 2);
    await writeConfigRaw($selectedDevice.config_path, configJson);
    $currentConfigRaw = configJson;
    $hasUnsavedChanges = false;
    $statusMessage = 'Config saved successfully';
    showToast('Config saved successfully', 'success');
    
    // Prompt to eject device
    await promptEjectDevice();
    
  } catch (e: any) {
    $statusMessage = `Error saving config: ${e.message || e}`;
    showToast($statusMessage, 'error', 5000);
  } finally {
    $isLoading = false;
  }
}

async function promptEjectDevice() {
  if (!$selectedDevice) return;
  
  const shouldEject = await confirm(
    'Config saved! Would you like to safely eject the device?\n\n' +
    'After ejecting:\n' +
    '1. Press the power button on the back of the device to turn it off\n' +
    '2. Wait 2 seconds\n' +
    '3. Press the power button again to turn it back on\n\n' +
    'The new config will be loaded on startup.'
  );
  
  if (!shouldEject) return;
  
  try {
    const devicePath = $selectedDevice.path.toString();
    const deviceName = $selectedDevice.name;
    
    const result = await ejectDevice(devicePath);
    showToast(result, 'success');
    
    // Clear current device selection
    $selectedDevice = null;
    $statusMessage = `${deviceName} ejected - waiting for reconnection...`;
    
    // Auto-select next available device if any
    if ($devices.length > 1) {
      const nextDevice = $devices.find(d => d.name !== deviceName);
      if (nextDevice) {
        await new Promise(resolve => setTimeout(resolve, 500));
        await selectDevice(nextDevice);
      }
    }
    
  } catch (e: any) {
    // On Windows or if eject fails, show manual instructions
    await message(
      e.message || 'Could not eject device automatically.\n\nPlease eject manually using your system\'s device manager.',
      { title: 'Eject Device', kind: 'info' }
    );
  }
}
```

### 4. Update Reset Device Button

**File:** `config-editor/src/routes/+page.svelte`

```typescript
async function resetDevice() {
  if (!$selectedDevice) return;
  await message(
    'To apply config changes, restart your MIDI Captain:\n\n' +
    '1. Press the power button on the BACK of the device to turn it off\n' +
    '2. Wait 2 seconds\n' +
    '3. Press the power button again to turn it back on\n\n' +
    '💡 Tip: After saving, use "Eject Device" for a cleaner workflow.',
    { title: 'Reset Device', kind: 'info' }
  );
  $statusMessage = 'Waiting for device to reconnect...';
}
```

### 5. Register Command in Tauri

**File:** `config-editor/src-tauri/src/main.rs`

Add `eject_device` to the invoke handler:

```rust
.invoke_handler(tauri::generate_handler![
    // ... existing commands ...
    eject_device,
])
```

## Testing Plan

### macOS Testing
1. Save config → Should prompt for eject
2. Confirm eject → Should run `diskutil eject /Volumes/MIDICAPTAIN`
3. Device should disappear from device list
4. Plug device back in → Should auto-reconnect
5. Multi-device: With 2 devices connected, eject one → should auto-select the other

### Linux Testing
1. Save config → Should prompt for eject
2. Try `gio mount -u` first, fallback to `umount`
3. Verify device disappears and reconnects

### Windows Testing
1. Save config → Should prompt for eject
2. Show helpful error message about using system tray
3. Provide clear instructions for manual eject

## User Benefits

1. **Clearer Instructions**: Power button location specified (back of device)
2. **Safer Workflow**: Proper eject prevents file corruption
3. **Multi-Device Support**: Auto-selects next device after eject
4. **Cross-Platform**: Works on macOS, Linux (with fallback), Windows (with instructions)
5. **Optional**: User can decline eject prompt and manually restart

## Edge Cases

- **Eject fails**: Show error, allow manual eject
- **No devices left**: Clear selection, show "waiting for device"
- **Multiple devices**: Auto-select next available device
- **Windows**: Graceful error with instructions (no native eject API)
- **Device already disconnected**: Handle gracefully
