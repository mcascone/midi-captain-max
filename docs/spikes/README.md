# SPIKE Documents

This directory contains research and investigation documents for technical decisions in the MIDI Captain project.

## 2026-02-17: WebUSB vs Tauri Investigation

**File:** [2026-02-17-webusb-investigation.md](./2026-02-17-webusb-investigation.md)

**Question:** Could WebUSB replace the Tauri config editor with a platform-independent web application?

**TL;DR:** No. WebUSB blocks USB MIDI and Mass Storage devices by design. The correct API is Web MIDI API, but it can't access the device filesystem. **Recommendation: Continue with Tauri.**

**Key Findings:**
- ❌ WebUSB explicitly blocks USB MIDI and Mass Storage for security
- ⚠️ Web MIDI API works for MIDI but can't access config.json on device volume
- ⚠️ Manual file operations (File System Access API) possible but terrible UX
- ✅ Tauri provides best user experience with automatic detection and file operations
- ⚠️ Future option: SysEx-based config protocol (8-10 weeks effort)

**Browser Support:**
- WebUSB: Chrome, Edge, Opera only (no Firefox, Safari)
- Web MIDI: Chrome, Edge, partial Firefox (no iOS)
- Tauri: macOS, Windows, Linux (all browsers irrelevant)

**Decision:** Continue with Tauri app. Consider SysEx protocol as future enhancement for browser/mobile support.

**Addendum (2026-02-17):** Evaluated simplified requirement (USB storage only, no MIDI/Serial). File System Access API *can* access USB volumes but requires manual file selection—user must navigate to device and pick files every session. UX significantly worse than Tauri's automatic detection. Recommendation unchanged: Continue with Tauri.
