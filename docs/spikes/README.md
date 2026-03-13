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

---

## 2026-02-27: GUI Firmware Installation Feature

**File:** [2026-02-27-gui-firmware-installation-spike.md](./2026-02-27-gui-firmware-installation-spike.md)

**Question:** Should we add firmware installation capabilities to the Config Editor GUI, bundling firmware with the app?

**TL;DR:** Yes. Bundle firmware with Config Editor and implement one-click installation. **Recommendation: Proceed with implementation.**

**Key Findings:**
- ✅ Technically feasible — all capabilities of deploy.sh can be replicated in Tauri/Rust
- ✅ Strong UX gains — reduces installation from 7 steps to 3, eliminates terminal requirement
- ✅ Cross-platform — works on macOS, Windows, Linux
- ⚠️ Moderate complexity — ~500KB added to app bundle, requires careful file ordering
- ✅ Leverages existing capabilities — device detection and filesystem access already working

**User Benefits:**
- Single download (app includes firmware)
- No terminal knowledge required
- Windows users get scripted install (vs manual file copying)
- Version consistency guaranteed
- Guided UI with progress feedback

**Implementation:**
- Phase 1: Bundle firmware in app resources (CI coordination)
- Phase 2: Rust installer module (file ordering, sync, manifest)
- Phase 3: GUI integration (Install tab with progress bar)
- Phase 4: Testing on all platforms + device types
- Timeline: ~3 weeks from approval to stable release

**Risks & Mitigations:**
- File ordering bugs → integration tests on real hardware
- Config overwrite → explicit preservation logic + dry-run mode
- Platform-specific sync issues → fsync + eject option

**Decision:** Proceed with bundled firmware approach. Keep deploy.sh as fallback for power users.
