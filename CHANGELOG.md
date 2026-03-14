# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-03-14

### Added
- **Center display with dual-line layout**: Button name (large, 60px font) + MIDI info (medium, 20px font) centered on screen.
- **Smart label timeout**: Non-select buttons display for 3 seconds then automatically return to showing the active select button.
- **Startup default selection**: Buttons with `default_selected: true` now send their `press` MIDI messages on device boot.
- **Display state management**: `find_selected_button()` and `show_selected_button_label()` helper functions for intelligent display updates.
- **Multi-command arrays**: All button events (Press, Release, Long Press, Long Release) now support executing multiple MIDI commands per event.
- **Multi-command visual indicators** in DeviceGrid:
  - Count badge showing number of commands (e.g., `CC20 ×2`)
  - Gradient background styling for multi-command buttons
  - Hover tooltip displaying all commands across all events
- **Value-based bidirectional MIDI sync**: Incoming MIDI now matches CC number, channel, **and value** for scene switching (Quad Cortex use case).
- **Per-message MIDI channel support**: Added `channel` parameter to all `send_midi_message()` calls, allowing each command in a multi-command sequence to target different MIDI channels.
- **Labeled value pills** in DeviceGrid: All channel and value displays now show labels (`Ch:`, `On:`, `Off:`, `Vel:`) with dark pill backgrounds for clarity.
- ButtonCommandsEditor component for unified command editing across all event types.
- `select` button mode (editor, Rust config, and firmware) allowing radio-group behavior per `select_group`.
- `select_group` support in firmware: selecting one button deselects other group members (`_deselect_group`).
- Editor UI: enable/disable toggles for `long_press` and `long_release` on per-button rows.
- Unit/runtime test: `tests/test_select_group_runtime.py` to exercise select-group behavior.

### Changed
- **BREAKING**: Removed simple/advanced mode toggle - all buttons now use multi-command arrays exclusively.
- **BREAKING**: Removed legacy single-action fields from config (type, cc, cc_on, cc_off, note, velocity_on, velocity_off, program, pc_step, flash_ms).
- **MIDI transport initialization**: Removed `out_channel` parameter from USB/TRS MIDI transport setup - now set dynamically per message.
- **MIDI send architecture**: `send_midi_message()` now accepts `channel` parameter and sets `transport.out_channel` before each send to support per-message channel control (adafruit_midi library limitation workaround).
- **DeviceGrid value display**: Combined on/off values in single pill for toggle/momentary buttons; hide off values for select buttons (they don't send release).
- **DeviceGrid card heights**: Changed from `min-height: 110px` to fixed `height: 135px` to prevent label overlap.
- **2ms inter-command delay**: Added small delay between multi-command sequence for MIDI buffer management in Thru chains.
- Config normalization automatically strips legacy fields on save and converts single objects to arrays.
- ButtonSettingsPanel simplified: always shows Actions section, removed ~400 lines of conditional logic.
- DeviceGrid now reads command info from multi-command arrays instead of legacy fields.
- Standardized all form control heights to 36px across ButtonSettingsPanel and ButtonCommandsEditor.
- Editor: `config-editor/src/lib/types.ts`, `ButtonRow.svelte` — added `select` option and long-press UX improvements.
- Firmware: `firmware/dev/code.py`, `firmware/dev/core/config.py` — enforced select-group exclusivity and normalized select-related config.
- Rust backend: `config-editor/src-tauri/src/config.rs` — added `Select` enum variant and multi-command validation.
- **Expression pedal labels removed from display** for cleaner center display focus (pedals still functional).
- **Display timeout in main loop**: `update_label_timeout()` called every iteration to check for expired timeouts.
- **Ready state fallback**: Display shows "Ready" when no select buttons are configured or active.

### Fixed
- **Text overlap on display**: Added `set_label_text()` helper that clears labels before updating to prevent CircuitPython displayio.Label text persistence issue.
- **Multi-command MIDI channel mismatch**: Fixed issue where multi-command buttons sent all commands on the same channel instead of respecting per-command channel settings.
- **TAP LED tempo appearing at half speed**: Changed from 50% duty cycle (equal on/off) to short flash pattern (100ms ON, rest OFF) to match actual tap tempo visually. Fixed in all 4 blink timer initialization locations.
- **Bidirectional MIDI scene switching**: Added value matching to incoming CC handlers to support devices (like Quad Cortex) that send specific values for scene changes.
- **DeviceGrid simplified toggle display**: Fixed "—" display for buttons using simplified toggle format (`cc` and `value_on` fields).
- **DeviceGrid value label clarity**: Numbers now have descriptive labels making it clear which is channel, on value, and off value.
- Display showing stale text when new text was shorter than previous text.
- DeviceGrid showing "CC?" when legacy fields were missing - now extracts from press command arrays.
- DeviceGrid showing channel twice ("1 1") - now displays channel+value and off value correctly.
- Simple mode action objects causing JSON parse errors - normalization converts to arrays.
- Advanced mode toggle persisting incorrectly after save - removed toggle entirely for consistent UX.
- Input/select height inconsistencies between components.
- Defensive MIDI receive handling in firmware to be compatible with test harness mocks and avoid runtime errors during message handling.

### Tests & CI
- Python tests: 178 passed (all multi-command tests updated, TAP tempo tests added).
- Rust tests (config-editor): 19 passing.
- Firmware deployed and tested on STD10 hardware with multi-command configurations.
- Verified per-message channel routing with multi-pedal TAP tempo setup.

### Deployment
- Branch: `feature/keytimes-state-overrides` with multi-command MIDI, bidirectional sync, and TAP tempo fixes.
- PR: https://github.com/MC-Music-Workshop/midi-captain-max/pull/12
- Firmware Version: tested with config containing multiple commands per press event on different MIDI channels.

---

Please update this file when releasing or adding more notable changes.
