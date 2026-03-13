# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-03-13

### Added
- `select` button mode (editor, Rust config, and firmware) allowing radio-group behavior per `select_group`.
- `select_group` support in firmware: selecting one button deselects other group members (`_deselect_group`).
- Editor UI: enable/disable toggles for `long_press` and `long_release` on per-button rows.
- Unit/runtime test: `tests/test_select_group_runtime.py` to exercise select-group behavior.

### Changed
- Editor: `config-editor/src/lib/types.ts`, `ButtonRow.svelte` — added `select` option and long-press UX improvements.
- Firmware: `firmware/dev/code.py`, `firmware/dev/core/config.py` — enforced select-group exclusivity and normalized select-related config.
- Rust backend: `config-editor/src-tauri/src/config.rs` — added `Select` enum variant.

### Fixed
- Defensive MIDI receive handling in firmware to be compatible with test harness mocks and avoid runtime errors during message handling.

### Tests & CI
- Python tests: 141 passed (local run).
- Rust tests (config-editor): 28 passed after environment adjustments.

### Deployment
- Branch: `feature/select-button` pushed with changes and tests; PR available to review.
- Firmware deployed to device during manual testing (example Version: `f8f09c7`).

---

Please update this file when releasing or adding more notable changes.
