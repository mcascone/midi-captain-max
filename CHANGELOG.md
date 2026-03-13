# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-03-13

### Added
- **Multi-command arrays**: All button events (Press, Release, Long Press, Long Release) now support executing multiple MIDI commands per event.
- **Multi-command visual indicators** in DeviceGrid:
  - Count badge showing number of commands (e.g., `CC20 ×2`)
  - Gradient background styling for multi-command buttons
  - Hover tooltip displaying all commands across all events
- ButtonCommandsEditor component for unified command editing across all event types.
- `select` button mode (editor, Rust config, and firmware) allowing radio-group behavior per `select_group`.
- `select_group` support in firmware: selecting one button deselects other group members (`_deselect_group`).
- Editor UI: enable/disable toggles for `long_press` and `long_release` on per-button rows.
- Unit/runtime test: `tests/test_select_group_runtime.py` to exercise select-group behavior.

### Changed
- **BREAKING**: Removed simple/advanced mode toggle - all buttons now use multi-command arrays exclusively.
- **BREAKING**: Removed legacy single-action fields from config (type, cc, cc_on, cc_off, note, velocity_on, velocity_off, program, pc_step, flash_ms).
- Config normalization automatically strips legacy fields on save and converts single objects to arrays.
- ButtonSettingsPanel simplified: always shows Actions section, removed ~400 lines of conditional logic.
- DeviceGrid now reads command info from multi-command arrays instead of legacy fields.
- Standardized all form control heights to 36px across ButtonSettingsPanel and ButtonCommandsEditor.
- Editor: `config-editor/src/lib/types.ts`, `ButtonRow.svelte` — added `select` option and long-press UX improvements.
- Firmware: `firmware/dev/code.py`, `firmware/dev/core/config.py` — enforced select-group exclusivity and normalized select-related config.
- Rust backend: `config-editor/src-tauri/src/config.rs` — added `Select` enum variant and multi-command validation.

### Fixed
- DeviceGrid showing "CC?" when legacy fields were missing - now extracts from press command arrays.
- DeviceGrid showing channel twice ("1 1") - now displays channel+value and off value correctly.
- Simple mode action objects causing JSON parse errors - normalization converts to arrays.
- Advanced mode toggle persisting incorrectly after save - removed toggle entirely for consistent UX.
- Input/select height inconsistencies between components.
- Defensive MIDI receive handling in firmware to be compatible with test harness mocks and avoid runtime errors during message handling.

### Tests & CI
- Python tests: 168 passed (all multi-command tests updated).
- Rust tests (config-editor): 32/33 passing.
- Firmware deployed and tested on STD10 hardware with multi-command configurations.

### Deployment
- Branch: `feature/multi-command-per-action` merged with comprehensive refactor.
- Firmware Version: tested with config containing multiple commands per press event.

---

Please update this file when releasing or adding more notable changes.
