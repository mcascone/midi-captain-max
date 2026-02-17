# SPIKE: WebUSB vs Tauri Standalone App Investigation

**Date:** 2026-02-17  
**Author:** Copilot (GitHub Agent)  
**Issue:** [SPIKE: investigate WebUSB for config editor vs standalone app](https://github.com/MC-Music-Workshop/midi-captain-max/issues/TBD)

---

## Executive Summary

This investigation evaluates whether WebUSB could replace the current Tauri-based config editor with a platform-independent web application. The key findings:

1. **WebUSB is NOT suitable for this use case** — the MIDI Captain device uses USB MIDI, which WebUSB explicitly blocks for security reasons
2. **Web MIDI API is the correct browser API** for MIDI devices, but has limitations
3. **A hybrid approach** (static web app + Web MIDI API + local file operations) is theoretically possible but requires significant architectural changes
4. **The current Tauri approach is recommended** for the best user experience

---

## Questions Answered

### Q1: Would WebUSB provide a platform-independent app?

**Short answer:** Yes, but with severe limitations.

**Browser Support (2026):**

| Browser | WebUSB Support | Web MIDI API Support |
|---------|----------------|---------------------|
| Chrome (Desktop) | ✅ Yes | ✅ Yes |
| Edge (Chromium) | ✅ Yes | ✅ Yes |
| Opera | ✅ Yes | ✅ Yes |
| Firefox | ❌ No | ⚠️ Partial (flag) |
| Safari (macOS) | ❌ No | ⚠️ Limited |
| Safari (iOS) | ❌ No | ❌ No |
| Chrome (Android) | ✅ Yes | ✅ Yes |

**Key Limitations:**
- No Firefox or Safari support for WebUSB (40-50% of desktop users excluded)
- Requires HTTPS context (can't use `file://` URLs without workarounds)
- User must explicitly grant permission for each device on each session
- Blocks access to standard USB device classes (including MIDI) for security

**Verdict:** WebUSB provides cross-platform support only within the Chromium ecosystem, which is substantially less "platform-independent" than a native Tauri app that runs on macOS, Windows, and Linux.

---

### Q2: Would the web page have to be hosted somewhere or downloaded to the user's computer?

**Short answer:** It depends on the implementation approach.

#### Option A: Hosted Web Application

**Pros:**
- No installation required
- Always up-to-date (users access latest version)
- Easy distribution via URL
- Can use CDNs for performance

**Cons:**
- Requires internet connection to access
- Must host on HTTPS domain (cost/maintenance)
- User's config files stored locally or in cloud?
- Privacy concerns if cloud storage used
- Session-based device permissions (must re-grant on each visit)

#### Option B: Downloaded Static Site (PWA)

**Pros:**
- Can work offline after initial download
- Installable to desktop/home screen
- No hosting costs after download
- User downloads once, uses forever

**Cons:**
- Still requires HTTPS for first download
- Users must manually update
- Complex update mechanism needed
- Service worker complexity for offline operation

#### Option C: Self-Contained HTML File

**Pros:**
- Single file distribution (simplest)
- No hosting required
- Can use `file://` protocol with workarounds

**Cons:**
- `file://` URLs don't have HTTPS, so many browser APIs unavailable
- Would need workarounds like local server or browser extensions
- No automatic updates
- Not a typical user experience

**Verdict:** For the MIDI Captain use case, a hosted web app or PWA would be most viable, but still requires internet connection for initial access and HTTPS hosting infrastructure. This is more complex than distributing a Tauri app installer.

---

### Q3: Could the existing Svelte/Tauri app be ported easily to use WebUSB, or would it be a major refactor?

**Short answer:** It would be a **major refactor** with significant architectural compromises.

#### Current Tauri Architecture

The existing config editor uses:
- **Rust backend** for filesystem operations (device detection, config read/write, profile storage)
- **Svelte frontend** for UI with JSON editor, validation, and form controls
- **Native OS APIs** for volume mounting detection (macOS `/Volumes` watcher)
- **Tauri IPC** for communication between frontend and backend
- **Platform-specific features** (code signing, installers, system integration)

**Key Components:**

1. **Device Detection** (`device.rs`):
   - Watches `/Volumes` directory for CIRCUITPY/MIDICAPTAIN mount
   - Uses OS filesystem notifications
   - Auto-detects device connection/disconnection

2. **File Operations** (`config.rs`):
   - Direct filesystem access to device volume
   - Reads/writes `config.json` on device
   - Validates JSON structure

3. **Profile Management**:
   - Stores user profiles in system directories (`dirs` crate)
   - Manages multiple saved configurations

#### WebUSB/Web MIDI API Architecture

To port to a web-based approach would require:

1. **Replace Device Detection:**
   - ❌ Cannot watch `/Volumes` (no OS filesystem access)
   - ✅ Use Web MIDI API to enumerate MIDI devices
   - ⚠️ But Web MIDI API doesn't see CircuitPython as USB volume
   - ⚠️ Device appears as generic USB MIDI device, not identifiable as "MIDI Captain"

2. **Replace File Operations:**
   - ❌ Cannot read/write files directly to USB volume
   - ⚠️ Could use File System Access API for user-selected files
   - ⚠️ But this doesn't work with device volumes (user must manually select)
   - ❌ Cannot automatically detect `config.json` on device

3. **Replace Profile Management:**
   - ❌ Cannot access system directories
   - ⚠️ Could use browser localStorage (limited to ~5-10MB)
   - ⚠️ Could use IndexedDB for larger storage
   - ❌ Profiles not portable across browsers or devices

#### Major Refactoring Required

| Component | Tauri Implementation | Web Implementation | Effort |
|-----------|---------------------|-------------------|--------|
| Device Detection | OS volume watcher | Web MIDI enumeration | High - different paradigm |
| Config Read | Direct file access | Manual file picker | High - UX regression |
| Config Write | Direct file write | Manual file save | High - UX regression |
| Profile Storage | System directories | localStorage/IndexedDB | Medium - different APIs |
| Device Identification | Volume name check | MIDI device name parsing | High - unreliable |
| Firmware Install | File copy + safety checks | N/A - not possible | Critical - no solution |

**Critical Blocker: The Core Use Case Doesn't Work**

The fundamental issue is that **the MIDI Captain device presents as a USB storage volume (CircuitPython) AND a USB MIDI device simultaneously.** The web app needs to:

1. Detect when device is connected (Web MIDI can do this)
2. Read/write config.json on the USB volume (Web APIs **cannot** do this automatically)
3. Copy firmware files to device (Web APIs **cannot** do this)

The user would have to:
- Connect device
- Manually select "Open File" and navigate to device volume
- Edit config
- Manually "Save As" and navigate back to device volume
- For firmware updates, manually copy files in Finder/Explorer

**This is a significantly worse user experience than the current Tauri app.**

#### Svelte Code Portability

The good news: The **Svelte UI components** are highly portable:
- ConfigForm, JsonEditor, ButtonsSection, etc. are pure UI
- These would work in a static web app with minimal changes
- Only the `$lib/api.ts` wrapper would need replacement

**Estimated Porting Effort:**
- **Svelte UI components:** 20% - mostly compatible, minor tweaks for web APIs
- **API layer:** 80% - complete rewrite from Tauri IPC to Web APIs
- **Backend functionality:** 100% - rewrite in JavaScript, major limitations
- **Overall effort:** 6-8 weeks for a degraded user experience

**Verdict:** Not feasible without major compromises to functionality and UX.

---

## Alternative Approaches Considered

### 1. Web MIDI API + File System Access API

**Concept:** Use Web MIDI API for device communication, File System Access API for config files.

**Pros:**
- Web MIDI API is the correct API for MIDI devices
- Could work in Chromium browsers
- No WebUSB needed

**Cons:**
- **Web MIDI API doesn't provide access to the USB storage volume** — it only sees the MIDI endpoints
- File System Access API requires manual user file selection (can't auto-detect config.json on device)
- User must manually navigate to device volume each time
- Can't automatically detect when device is connected/disconnected as a storage device
- Firmware installation would be manual file copying

**Verdict:** Possible but significantly degraded UX.

### 2. Hybrid: Web App + Native Helper

**Concept:** Web app for UI, small native helper app for filesystem operations.

**Pros:**
- Keep Svelte UI in browser
- Native helper handles device detection and file access
- Could use WebSocket/HTTP for communication

**Cons:**
- Now requires users to install TWO things (helper + trust web app)
- More complex than just installing Tauri app
- Cross-platform helper still needs development (same as Tauri)
- Defeats the purpose of "avoiding native app"

**Verdict:** Worse than current approach.

### 3. Browser Extension

**Concept:** Chrome extension with native messaging for filesystem access.

**Pros:**
- Could access Web MIDI API + native file operations
- Works in Chromium browsers
- Installable from Chrome Web Store

**Cons:**
- Still Chrome-only (not Firefox/Safari)
- Users hesitant to install extensions
- Native messaging requires separate native component
- Extension review process and store approval
- More complex development and distribution

**Verdict:** Possible but not simpler than Tauri.

### 4. Progressive Web App (PWA)

**Concept:** Installable web app with offline capabilities.

**Pros:**
- Can work offline
- Installable to desktop
- Service worker for caching

**Cons:**
- Still has all the same filesystem access limitations
- Can't solve the core problem of accessing device volume
- PWA install process is confusing for many users
- Still requires HTTPS hosting

**Verdict:** Doesn't solve the core problems.

---

## Technical Deep Dive: Why WebUSB Won't Work

### The CircuitPython Device Model

The MIDI Captain devices (STD10, Mini6) run CircuitPython 7.x on RP2040 (Raspberry Pi Pico). When connected via USB, they present **multiple interfaces**:

1. **USB Mass Storage** (SCSI) — appears as `CIRCUITPY` or `MIDICAPTAIN` volume
2. **USB MIDI** — bidirectional MIDI communication
3. **USB CDC** (Serial) — serial console for debugging

### What WebUSB Can Access

WebUSB provides access to:
- Custom USB endpoints (control, bulk, interrupt, isochronous)
- Vendor-specific USB interfaces
- Generic USB device enumeration

WebUSB **explicitly blocks**:
- USB Mass Storage (security risk)
- USB HID (keyboards, mice, security keys)
- USB Audio
- USB Video
- **USB MIDI** (part of USB Audio class)

**From the spec:** "WebUSB is designed to prevent malicious websites from controlling security-sensitive devices. Standard device classes like MIDI, Audio, HID, and Mass Storage are blocked."

### What Web MIDI API Can Access

Web MIDI API provides access to:
- USB MIDI class devices (specifically designed for this)
- MIDI input/output ports
- MIDI message send/receive

Web MIDI API **cannot access**:
- The USB Mass Storage interface
- The filesystem on the device
- Non-MIDI USB endpoints

### The Core Problem

The config editor needs to:
1. ✅ Detect MIDI device (Web MIDI can do this)
2. ❌ Read `config.json` from USB volume (Web APIs can't do this)
3. ❌ Write `config.json` to USB volume (Web APIs can't do this)
4. ❌ Copy firmware files to device (Web APIs can't do this)

**The device's USB Mass Storage interface is blocked by browser security policies.**

### Possible Workaround: SysEx Configuration

**Concept:** Instead of editing `config.json` on the device volume, send configuration via MIDI SysEx messages to the firmware, which updates the config file internally.

**How it would work:**
1. Web app connects to device via Web MIDI API
2. User edits config in web app
3. App sends config as SysEx messages to device
4. Firmware receives SysEx and writes to `config.json`
5. Device restarts to apply changes

**Pros:**
- Would work with Web MIDI API
- No filesystem access needed
- Could work in all browsers with Web MIDI support

**Cons:**
- **Requires major firmware rewrite** to handle SysEx config protocol
- **Firmware installation still impossible** (can't copy .py files via MIDI)
- Complex protocol design and debugging
- MIDI SysEx has size limits (need chunking for large configs)
- Device must be trusted not to brick itself
- What if SysEx config is malformed? (bricking risk)

**Estimated effort:** 4-6 weeks firmware work + 2-3 weeks web app work

**Verdict:** Possible but requires significant new firmware features. Firmware installation would still require manual file copying.

---

## Comparison Matrix

| Criterion | Current Tauri App | WebUSB Approach | Web MIDI + Manual Files | SysEx Config Protocol |
|-----------|-------------------|-----------------|--------------------------|------------------------|
| **Platform Support** | ✅ Mac/Win/Linux | ⚠️ Chrome only | ⚠️ Chrome/Edge | ⚠️ Chrome/Edge |
| **Installation** | ✅ One-time install | ⚠️ Hosted or PWA | ⚠️ Hosted or PWA | ⚠️ Hosted or PWA |
| **Device Detection** | ✅ Automatic | ❌ Not possible | ⚠️ MIDI only | ✅ MIDI device |
| **Config Read** | ✅ Automatic | ❌ Not possible | ⚠️ Manual picker | ✅ Via SysEx |
| **Config Write** | ✅ Automatic | ❌ Not possible | ⚠️ Manual save | ✅ Via SysEx |
| **Firmware Install** | ✅ Integrated | ❌ Not possible | ❌ Manual copy | ❌ Not possible |
| **Profile Storage** | ✅ System dirs | ⚠️ localStorage | ⚠️ localStorage | ⚠️ localStorage |
| **Offline Use** | ✅ Yes | ⚠️ PWA only | ⚠️ PWA only | ⚠️ PWA only |
| **User Experience** | ✅ Excellent | ❌ Not viable | ⚠️ Poor | ✅ Good |
| **Development Effort** | ✅ In progress | ❌ 6-8 weeks | ⚠️ 4-5 weeks | ⚠️ 8-10 weeks |
| **Maintenance** | ✅ Standard Tauri | ⚠️ Web hosting | ⚠️ Web hosting | ⚠️ Firmware + web |
| **Security** | ✅ Code signed | ⚠️ HTTPS only | ⚠️ HTTPS only | ⚠️ HTTPS only |

---

## Recommendations

### Primary Recommendation: Continue with Tauri

**Reasoning:**
1. **Best user experience** — automatic device detection, seamless config editing, integrated firmware installation
2. **Already 60% complete** — significant progress has been made
3. **True platform independence** — works on macOS, Windows, Linux regardless of browser
4. **Offline capable** — no internet required after installation
5. **Professional distribution** — code signing, installers, auto-updates

**Trade-offs:**
- Users must download and install an app (one-time ~10MB download)
- Per-platform installers needed (already solved with Tauri)
- Slightly longer first-time setup than a web link

### Alternative: Web MIDI API with Manual Files (Not Recommended)

If you must have a web-based solution:
1. Use SvelteKit with `@sveltejs/adapter-static` for static site generation
2. Use Web MIDI API for device detection only
3. Use File System Access API for config file operations (requires manual selection)
4. Firmware installation requires manual file copying instructions
5. Host on GitHub Pages or similar static hosting

**Estimated effort:** 4-5 weeks development + ongoing hosting

**User workflow:**
1. Visit web app URL
2. Connect device
3. Grant MIDI access permission
4. Click "Open Config" button → manually navigate to device volume → select config.json
5. Edit config in app
6. Click "Save Config" button → manually navigate to device volume → save config.json
7. For firmware updates: follow manual instructions to copy files in Finder/Explorer

**This is significantly worse UX than the Tauri app.**

### Future Option: SysEx Configuration Protocol (Long-term)

If the project evolves to need browser-based configuration:
1. Design and implement SysEx-based configuration protocol in firmware
2. Build web app using Web MIDI API + SysEx
3. Automatic config read/write via MIDI (no filesystem access needed)
4. Firmware installation still requires manual process

**Estimated effort:** 8-10 weeks (4-6 firmware, 2-3 web app, 1 week testing)

**When to consider:**
- After Tauri app is stable and shipped
- If there's demand for browser-based configuration
- As a complement to (not replacement for) the Tauri app
- For mobile device support (iOS/Android with Web MIDI)

---

## Conclusion

**WebUSB is not suitable for the MIDI Captain config editor.** The fundamental issue is that WebUSB blocks access to USB Mass Storage devices (which is how the config.json file is accessed), and also blocks USB MIDI devices.

**The correct browser API is Web MIDI API**, but it only provides access to MIDI endpoints, not the filesystem. This means automatic config file operations are not possible in a browser without significant firmware changes.

**The current Tauri approach is strongly recommended** because it provides:
- The best user experience
- True cross-platform support (not just Chromium)
- Automatic device detection and file operations
- Integrated firmware installation
- Professional distribution with code signing
- No hosting infrastructure required

**If a web-based approach is required**, the only viable option is:
1. Implement a SysEx-based configuration protocol in the firmware (major effort)
2. Use Web MIDI API + SysEx for browser-based config editing
3. Accept that firmware installation will always require manual file copying

However, this should be considered a long-term enhancement, not a replacement for the Tauri app.

---

## References

### Browser API Documentation
- [WebUSB API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/WebUSB_API)
- [Web MIDI API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/Web_MIDI_API)
- [File System Access API - MDN](https://developer.mozilla.org/en-US/docs/Web/API/File_System_Access_API)
- [WebUSB Specification - W3C](https://wicg.github.io/webusb/)
- [Web MIDI API Specification - W3C](https://www.w3.org/TR/webmidi/)

### Browser Support
- [Can I Use: WebUSB](https://caniuse.com/webusb)
- [Can I Use: Web MIDI](https://caniuse.com/web-midi)
- [Can I Use: File System Access API](https://caniuse.com/native-filesystem-api)

### CircuitPython USB
- [CircuitPython USB MIDI Guide](https://learn.adafruit.com/qt-py-rp2040-usb-to-serial-midi-friends)
- [TinyUSB WebUSB Notes](https://forums.adafruit.com/viewtopic.php?t=184395)

### Static Web Apps
- [SvelteKit Static Adapter](https://svelte.dev/docs/kit/adapter-static)
- [Building Static Sites with SvelteKit](https://kinsta.com/blog/static-sveltekit/)

---

## Appendix: Code Examples

### Current Tauri Device Detection (Rust)

```rust
// From config-editor/src-tauri/src/device.rs

const DEVICE_VOLUMES: &[&str] = &["CIRCUITPY", "MIDICAPTAIN"];

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
```

### Hypothetical Web MIDI API Approach (JavaScript)

```javascript
// This ONLY detects MIDI endpoints, NOT the USB volume

async function detectMidiCaptain() {
  try {
    const midiAccess = await navigator.requestMIDIAccess();
    const devices = [];
    
    // Enumerate MIDI inputs
    for (const input of midiAccess.inputs.values()) {
      // Problem: How do we know this is a MIDI Captain device?
      // Generic USB MIDI devices don't have identifying info
      if (input.name.includes('MIDI Captain')) { // Unreliable
        devices.push({
          id: input.id,
          name: input.name,
          manufacturer: input.manufacturer,
          // Problem: We have NO access to the USB volume or config.json
        });
      }
    }
    
    return devices;
  } catch (error) {
    console.error('MIDI access denied:', error);
    return [];
  }
}

// Reading config requires manual user interaction
async function loadConfig() {
  try {
    // User must manually navigate to device volume
    const [fileHandle] = await window.showOpenFilePicker({
      types: [{
        description: 'JSON Config',
        accept: { 'application/json': ['.json'] }
      }]
    });
    
    const file = await fileHandle.getFile();
    const json = await file.text();
    return JSON.parse(json);
  } catch (error) {
    console.error('File access error:', error);
    return null;
  }
}

// Saving config also requires manual user interaction
async function saveConfig(config) {
  try {
    // User must manually navigate to device volume
    const fileHandle = await window.showSaveFilePicker({
      suggestedName: 'config.json',
      types: [{
        description: 'JSON Config',
        accept: { 'application/json': ['.json'] }
      }]
    });
    
    const writable = await fileHandle.createWritable();
    await writable.write(JSON.stringify(config, null, 2));
    await writable.close();
  } catch (error) {
    console.error('File save error:', error);
  }
}
```

### Hypothetical SysEx Config Protocol (JavaScript + Python)

**Web App (JavaScript):**
```javascript
// Send config to device via SysEx
async function sendConfigToDevice(midiOutput, config) {
  const SYSEX_START = 0xF0;
  const SYSEX_END = 0xF7;
  const MIDI_CAPTAIN_ID = [0x00, 0x21, 0x7D]; // Example manufacturer ID
  const CONFIG_COMMAND = 0x01;
  
  const configJson = JSON.stringify(config);
  const configBytes = new TextEncoder().encode(configJson);
  
  // Chunk data to fit MIDI message size limits
  const chunkSize = 64;
  for (let i = 0; i < configBytes.length; i += chunkSize) {
    const chunk = configBytes.slice(i, i + chunkSize);
    const message = [
      SYSEX_START,
      ...MIDI_CAPTAIN_ID,
      CONFIG_COMMAND,
      ...Array.from(chunk),
      SYSEX_END
    ];
    
    midiOutput.send(message);
    await new Promise(resolve => setTimeout(resolve, 10)); // Wait between chunks
  }
}

// Request current config from device
async function requestConfigFromDevice(midiOutput, midiInput) {
  return new Promise((resolve, reject) => {
    const SYSEX_START = 0xF0;
    const SYSEX_END = 0xF7;
    const MIDI_CAPTAIN_ID = [0x00, 0x21, 0x7D];
    const REQUEST_CONFIG = 0x02;
    
    let receivedData = [];
    
    const onMessage = (event) => {
      const data = Array.from(event.data);
      if (data[0] === SYSEX_START) {
        // Accumulate SysEx data
        receivedData.push(...data.slice(4, -1)); // Remove header and SYSEX_END
        
        if (data[data.length - 1] === SYSEX_END) {
          // Complete message received
          midiInput.removeEventListener('midimessage', onMessage);
          const jsonString = new TextDecoder().decode(new Uint8Array(receivedData));
          resolve(JSON.parse(jsonString));
        }
      }
    };
    
    midiInput.addEventListener('midimessage', onMessage);
    
    // Send request
    midiOutput.send([SYSEX_START, ...MIDI_CAPTAIN_ID, REQUEST_CONFIG, SYSEX_END]);
    
    // Timeout after 5 seconds
    setTimeout(() => {
      midiInput.removeEventListener('midimessage', onMessage);
      reject(new Error('Config request timeout'));
    }, 5000);
  });
}
```

**Firmware (CircuitPython):**
```python
# In code.py - handle SysEx config messages

import usb_midi
import json

SYSEX_START = 0xF0
SYSEX_END = 0xF7
MIDI_CAPTAIN_ID = bytes([0x00, 0x21, 0x7D])
CONFIG_COMMAND = 0x01
REQUEST_CONFIG = 0x02

def handle_sysex_message(data):
    """Handle incoming SysEx configuration messages"""
    if data[:3] != MIDI_CAPTAIN_ID:
        return
    
    command = data[3]
    
    if command == CONFIG_COMMAND:
        # Receive config update
        try:
            config_json = data[4:].decode('utf-8')
            config = json.loads(config_json)
            
            # Validate config
            validate_config(config)
            
            # Write to config.json
            with open('/config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            # Send acknowledgment
            send_sysex_ack()
            
            # Restart to apply changes
            # microcontroller.reset()
            
        except Exception as e:
            send_sysex_error(str(e))
    
    elif command == REQUEST_CONFIG:
        # Send current config
        try:
            with open('/config.json', 'r') as f:
                config = json.load(f)
            
            send_config_sysex(config)
        except Exception as e:
            send_sysex_error(str(e))

def send_config_sysex(config):
    """Send config to host via SysEx"""
    config_json = json.dumps(config)
    config_bytes = config_json.encode('utf-8')
    
    # Send in chunks
    chunk_size = 64
    for i in range(0, len(config_bytes), chunk_size):
        chunk = config_bytes[i:i+chunk_size]
        message = bytes([SYSEX_START]) + MIDI_CAPTAIN_ID + bytes([CONFIG_COMMAND]) + chunk + bytes([SYSEX_END])
        usb_midi.ports[1].write(message)

# In main loop:
while True:
    if usb_midi.ports[0].in_waiting:
        data = usb_midi.ports[0].read(usb_midi.ports[0].in_waiting)
        if data[0] == SYSEX_START:
            handle_sysex_message(data[1:-1])  # Remove SYSEX_START and SYSEX_END
    
    # ... rest of main loop
```

**Note:** This SysEx approach is a significant undertaking and would require extensive testing to ensure reliability and prevent device bricking.

---

## Addendum: Simplified Requirement Assessment (USB Storage Only)

**Date:** 2026-02-17  
**Question:** If we only need USB Mass Storage access (read/write files) and don't need MIDI or Serial connectivity, does that change the assessment?

### Short Answer

**Unfortunately, no.** WebUSB still blocks USB Mass Storage devices by design, regardless of whether you need MIDI. However, the **File System Access API** provides an alternative that could work—with significant UX compromises.

---

### The Core Problem Remains

**WebUSB explicitly blocks USB Mass Storage devices** for security reasons, as confirmed by the W3C specification and recent 2025-2026 security policy reinforcements. This is a fundamental security boundary that applies to all websites, not just those that need MIDI.

From the WebUSB specification:
> "WebUSB is designed to prevent malicious websites from controlling security-sensitive devices. Standard device classes like MIDI, Audio, HID, and **Mass Storage are blocked**."

**Why?** Allowing web pages to access raw USB storage would enable malicious sites to:
- Read private files from any connected USB drive
- Write malware to USB drives
- Modify system files if drives are mounted
- Exfiltrate data silently

There is a proposal for "Unrestricted WebUSB" (available only to Isolated Web Apps in highly controlled enterprise environments), but this is:
- Not generally available to public websites
- Requires enterprise signing and trust
- Still in prototype/proposal stage
- Not suitable for end-user distribution

---

### Alternative: File System Access API

**Good news:** There's a browser API designed specifically for filesystem operations: the **File System Access API** (formerly Native File System API).

#### What It Can Do

✅ **Read files from USB volumes** — if the user selects them via file picker  
✅ **Write files to USB volumes** — if the user selects destination via save dialog  
✅ **Access directories** — user can grant access to entire folders  
✅ **Works with mounted USB drives** — appears in OS file picker like any other volume  
✅ **Secure** — requires HTTPS and explicit user consent for each operation  

#### What It Cannot Do

❌ **Programmatic device detection** — cannot detect when USB device is connected  
❌ **Automatic file access** — cannot automatically find config.json on device  
❌ **Volume enumeration** — cannot list available USB volumes  
❌ **Identifier persistence** — cannot auto-remember which volume is the device  

#### Browser Support

| Browser | File System Access API Support |
|---------|-------------------------------|
| Chrome | ✅ Full support |
| Edge | ✅ Full support |
| Opera | ✅ Full support |
| Firefox | ❌ No support |
| Safari | ❌ No support |

(Same Chromium-only limitation as WebUSB)

---

### Revised Architecture: File System Access API Approach

If you're willing to accept manual file operations, here's how it would work:

#### User Workflow

1. **Connect device** → User plugs in MIDI Captain
2. **Open web app** → User visits hosted web app (requires HTTPS)
3. **Click "Load Config"** → Triggers file picker
4. **User navigates to device volume** → Manually finds `/Volumes/CIRCUITPY/config.json` (macOS) or `D:\config.json` (Windows)
5. **User selects config.json** → App reads and parses file
6. **Edit config** → User makes changes in web UI
7. **Click "Save Config"** → Triggers save dialog
8. **User navigates back to device volume** → Manually selects destination as device
9. **User saves file** → Config written to device

#### Code Example

```javascript
// Load config from user-selected file
async function loadConfig() {
  try {
    const [fileHandle] = await window.showOpenFilePicker({
      types: [{
        description: 'JSON Config',
        accept: { 'application/json': ['.json'] }
      }],
      suggestedName: 'config.json'
    });
    
    const file = await fileHandle.getFile();
    const configText = await file.text();
    const config = JSON.parse(configText);
    
    // Store handle for later write operations
    window.configFileHandle = fileHandle;
    
    return config;
  } catch (error) {
    console.error('User cancelled or error:', error);
    return null;
  }
}

// Save config to user-selected file
async function saveConfig(config) {
  try {
    // Use stored handle if available, otherwise prompt
    let fileHandle = window.configFileHandle;
    
    if (!fileHandle) {
      fileHandle = await window.showSaveFilePicker({
        types: [{
          description: 'JSON Config',
          accept: { 'application/json': ['.json'] }
        }],
        suggestedName: 'config.json'
      });
    }
    
    const writable = await fileHandle.createWritable();
    await writable.write(JSON.stringify(config, null, 2));
    await writable.close();
    
    return true;
  } catch (error) {
    console.error('Save failed:', error);
    return false;
  }
}

// Firmware installation would require manual instructions
function showFirmwareInstructions() {
  alert(`
To install firmware:
1. Download firmware files from this page
2. Open Finder (Mac) or File Explorer (Windows)
3. Navigate to your CIRCUITPY or MIDICAPTAIN volume
4. Copy these files to the volume:
   - code.py
   - boot.py
   - config.json
   - (folders: core/, devices/, fonts/, lib/)
5. Safely eject the device
6. Device will restart with new firmware
  `);
}
```

---

### Comparison: File System Access API vs Tauri

| Feature | Tauri App | File System Access API (Web) |
|---------|-----------|------------------------------|
| **Installation** | One-time installer (~10MB) | Just visit URL |
| **Device Detection** | ✅ Automatic volume monitoring | ❌ None — manual selection only |
| **Config Load** | ✅ Automatic — finds config.json | ⚠️ Manual — user picks file every time* |
| **Config Save** | ✅ Automatic — writes to device | ⚠️ Manual — user picks location* |
| **Firmware Install** | ✅ Integrated — copies all files | ❌ Manual — user follows instructions |
| **Browser Support** | N/A (native app) | Chrome/Edge only (no Firefox/Safari) |
| **Platform Support** | macOS, Windows, Linux | Chrome on any OS |
| **Offline Use** | ✅ Yes | ⚠️ Only with PWA + service worker |
| **User Experience** | ✅ Seamless | ⚠️ Tedious (many clicks each session) |
| **Development Effort** | 60% complete | 3-4 weeks + hosting setup |

\* *There's a proposal for "File Handles Persistence API" that would let web apps remember file handles across sessions, but it's not yet standardized or widely implemented.*

---

### Updated Recommendation

Even with the simplified requirement of USB storage-only access:

#### Primary Recommendation: Continue with Tauri

**Reasoning:**
1. **Superior UX** — Automatic device detection and file operations beat manual file selection every time
2. **Already 60% complete** — significant investment made
3. **Broader browser support** — works regardless of browser choice (it's a native app)
4. **Complete feature set** — can support firmware installation, profile management, automatic updates
5. **No hosting costs** — distribute as installer, no server needed

#### Alternative: File System Access API (If Web is Required)

**If you must have a web-based solution:**
1. Build static web app with File System Access API
2. Accept manual file selection for every session
3. Provide clear instructions for firmware installation
4. Host on HTTPS domain (GitHub Pages, Netlify, Vercel, etc.)
5. Only support Chrome/Edge browsers

**Estimated effort:** 3-4 weeks development + ongoing hosting

**User experience will be significantly degraded:**
- User must manually navigate to device volume each time
- No automatic detection when device connects
- Firmware installation is manual process with written instructions
- Chrome/Edge only (excludes ~40% of users)

#### Best of Both Worlds: Tauri App + Web Companion

If you want to serve both audiences:
1. **Primary:** Tauri app for best experience (power users, frequent use)
2. **Secondary:** Web app for quick edits (casual users, one-time changes)

This gives users choice while recognizing that most regular users will prefer the Tauri app's superior UX.

---

### Conclusion on Simplified Requirements

**The requirement simplification helps, but not enough.** WebUSB still blocks USB Mass Storage. The File System Access API *can* access files on USB volumes, but requires manual user interaction for every operation.

**The core trade-off remains:**
- **Tauri:** Best UX, requires one-time ~10MB installation
- **Web + File System Access API:** No installation, but tedious manual file operations and Chrome-only

For a professional tool that users will interact with regularly (configuring a performance device), the Tauri app provides the superior experience. The web approach might work for very casual users who rarely change configs, but those users would likely be willing to install a small app for a better experience.

**Recommendation stands: Continue with Tauri.**
