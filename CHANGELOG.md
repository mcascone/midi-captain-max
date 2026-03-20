# Changelog

All notable changes to this project will be documented in this file.

## [Banks/Pages System] - 2026-03-20

### Added
- **Banks/Pages System** (SI-1 from Feature Analysis): Multi-bank button configurations for complex live setups
  - **Up to 8 banks per device**: Switch between complete button configurations without reconnecting
  - **Three switching methods**:
    - **Button**: Assign one button for cycling or two buttons for up/down
    - **MIDI CC**: Switch banks via incoming Control Change messages
    - **MIDI PC**: Switch banks via Program Change (with configurable base number)
  - **State persistence**: Button states saved independently per bank
  - **Instant switching**: Sub-100ms transitions with 200ms cooldown protection
  - **Visual feedback**: LED flash animation and bank name displayed on switch
  - **Dual-button mode**: Separate Bank Up and Bank Down buttons (or legacy single-button cycling)
  - **Encoder push support**: Button 11 (encoder push) can trigger bank switching on STD10
  - **Backward compatible**: Existing single-bank configs auto-migrate to multi-bank format
  
- **BankManager Class** (firmware): Core bank switching engine
  - Per-bank ButtonState storage for instant state restoration
  - Cooldown timer prevents rapid accidental switches
  - CC/PC trigger mapping with value-to-bank-index translation
  - Wrap-around navigation (bank 8 → bank 1, bank 1 → bank 8)
  
- **Banks Editor UI** (config-editor): Full bank management interface
  - BanksPanel: Tabbed interface with add/duplicate/delete/rename operations
  - BankSettingsPanel: Configure switching method and trigger assignments
  - Bank-aware button editing with active bank selector
  - Visual device layout updates to show active bank buttons
  - Per-bank validation with error path prefixes (`banks[N].buttons[M]`)
  
- **Config Schema Extensions**:
  - `banks[]`: Array of `BankConfig` objects (name + buttons array)
  - `bank_switch`: Switching configuration (method, button, cc, pc_base, channel)
  - `active_bank`: Initial bank index on boot (0-indexed)
  - Legacy `buttons` field now optional (migrated to `banks` automatically)

### Fixed
- **Bank switching critical bugs** (PR #27 review fixes):
  - Fixed `switch_to_led()` called as array instead of function
  - Fixed double-switching bug in button-triggered switching
  - Added channel checks for CC/PC-triggered bank switching
  - Removed blocking `time.sleep()` busy-wait during LED flash
- **Editor TypeScript compilation**: Fixed `carouselPage` undeclared variable
- **Default button values**: Fixed Mini6 compatibility with safe defaults (`maxButton - 1`)
- **Multi-bank validation**: `validateConfig()` now validates ALL banks with proper error paths
- **Config migration**: `validate_config()` properly normalizes bank button arrays
- **Rust unused variables**: Removed unused `_btn_path_prefix` and `flash_start`

### Tests & CI
- **234 total tests passing** (221 existing + 13 new bank-related tests)
  - `test_banks_config.py`: Config migration, validation, and bank helper tests (12 tests)
  - `test_bank_manager.py`: BankManager state management and switching logic (29 tests)
  - `test_bank_buttons.py`: Single/dual button mode configuration (8 tests)
- **53 Rust tests passing**: All config validation and device detection tests
- All CI checks passing: Lint, Rust tests, firmware zip, macOS/Windows builds

### Documentation
- Implementation plan: `docs/plans/2026-03-19-banks-pages-implementation.md`
- Feature analysis: `docs/FEATURE-ANALYSIS-REPORT.md` (SI-1 requirement)
- Hardware reference: Updated `docs/hardware-reference.md` with bank switching pins

### Deployment
- Branch: `feature/banks-pages-system`
- PR: https://github.com/guisperandio/midi-captain-max/pull/27
- Commits: 28 total (schema, firmware, UI, fixes)
- Merged: 2026-03-20

---

## [Unreleased] - 2026-03-18

### Added
- **Idle Timeout Screensaver** (`splash_screen.idle_timeout_seconds`): Display splash image after inactivity
  - New config field: `idle_timeout_seconds` (default: 0 = disabled)
  - Tracks user activity across all inputs (buttons, encoder, expression pedals)
  - Shows splash.bmp automatically after configured idle period
  - Wakes immediately on any input, resuming exact state
  - Persistent file handle for displayio.OnDiskBitmap compatibility
  - Config editor UI: "Idle timeout (seconds)" field in Boot tab (range 0-600)
  - Use cases: Display protection, branding during breaks, power saving
  - Documentation: Updated SPLASH_README.md and README.md with feature details

- **Long Press Visual Feedback** (`long_press_color` and `long_press_label`): Enhanced long-press UX with LED color override
  - `long_press_color` field: LED changes to configured color during long press (e.g., `"pink"`, `"orange"`)
  - `long_press_label` field: Optional custom label displayed during long press (max 6 chars)
  - Mode-specific persistence:
    - **Toggle/Select modes**: LED stays in `long_press_color` after release if button is ON
    - **Momentary mode**: LED returns to off state after release (standard momentary behavior)
  - Config editor UI: ColorSelect and text input fields in ButtonSettingsPanel Actions section
  - Full validation chain: TypeScript types → Rust config structs → CircuitPython firmware

### Fixed
- **Config validation stripping long_press_color**: `validate_button()` now preserves `long_press_color` field through normalization
- **Test brittleness**: `test_check_volume_midicaptain` no longer assumes device is unmounted (handles mounted state correctly)

### Tests & CI
- All 188 pytest tests passing
- All 50 Rust cargo tests passing (includes new roundtrip test for idle_timeout_seconds)
- Tested on hardware with pink LED override during 600ms long press

### Deployment
- Branch: `fix/firmware-broken` (long press feature)
- Branch: `feature/loading-screen` (idle timeout screensaver)
- PR: https://github.com/guisperandio/midi-captain-max/pull/25
- Ready for merge after validation

---

## [Code Quality Improvements] - 2026-03-15

### Added
- **Handler Module Extraction** (Phase 1 Modularization): Extracted 5 handler modules from `code.py`
  - `handlers/midi.py` (87 lines): Bidirectional MIDI processing
  - `handlers/display.py` (108 lines): Display management and label timeouts
  - `handlers/timers.py` (107 lines): PC flash and blink timer updates
  - `handlers/button.py` (128 lines): Button state management and LED control
  - `handlers/encoder.py` (240 lines): Rotary encoder and expression pedal handling
  - Total reduction: 182 lines from main `code.py` (-11%)
- **Constants Module** (`constants.py`, 138 lines): Centralized all magic numbers and configuration values
  - MIDI timing constants (delays, timeouts)
  - Display dimensions and positioning
  - LED brightness levels
  - PC flash and blink durations
- **Enhanced .gitignore**: Added CircuitPython-specific exclusions (`.Trashes`, `.Spotlight-V100`, `.fseventsd`, `._*`)

### Changed
- **Comprehensive Exception Handling**: Added try/except blocks to 13 critical functions
  - MIDI handlers: `handle_midi`, `handle_midi_message`, `handle_control_change`, `handle_note`, `handle_program_change`
  - Display handlers: `set_label_text`, `update_label_timeout`, `show_selected_button_label`
  - Timer handlers: `update_pc_flash_timers`, `update_blink_timers`
  - Input handlers: `handle_switches`, `handle_encoder`, `handle_expression`
  - All exceptions print error context and continue execution (no device resets during live performance)

### Fixed
- **flash_pc_button TypeError** (Copilot review): Added `PC_FLASH_DURATION_MS` default parameter
  - Prevents crash when called without `flash_ms` argument after PC command execution
- **update_label_timeout infinite loop** (Copilot review): Handler now returns tuple `(timeout, label_prev_len)`
  - Caller properly resets `label_timeout_return_to_select` to `0.0` when expired
  - Previously timeout was never cleared, causing expired branch to run forever
- **set_button_state bounds check** (Copilot review): Changed from `len(buttons)` to `len(button_states)`
  - Prevents silent LED failures when config array is shorter than physical hardware button count
  - Fallback config already existed but check was too strict
- **Variable redefinition linting error** (F811): Changed `DEFAULT_LONG_PRESS_MS` redefinition to `LONG_PRESS_THRESHOLD_MS`
- **package.json scripts** (Copilot review): Removed test/lint scripts referencing missing dependencies (vitest, eslint)
  - Will be added back in Phase 3 with proper devDependencies
- **Documentation inconsistency** (Copilot review): Updated CODE_QUALITY_IMPROVEMENTS.md to reflect CONTRIBUTING.md already exists

### Tests & CI
- All 178 tests passing after modularization and fixes
- CI workflow validates Python syntax and runs pytest on every push
- Modular architecture enables better test isolation and coverage

### Deployment
- Branch: `refactor/code-quality-improvements`
- PR: https://github.com/guisperandio/midi-captain-max/pull/19
- Commits: 12 total (modularization, exception handling, constants, Copilot review fixes)
- Ready for merge after CI validation

---

## [Device Profiles Release] - 2026-03-15

### Added
- **Device Profiles** (PRD Feature 2): Built-in MIDI mappings for popular devices
  - 6 profiles included: Quad Cortex, Helix, HX Stomp, Kemper, Ableton Live, MainStage
  - Full support for `pc_inc`/`pc_dec` command types with configurable step size
  - Profile resolver converts high-level actions (e.g., "Scene A") to MIDI commands
- **ProfileSelector component**: Visual profile assignment UI
  - Profile selection with labeled action cards
  - Per-event assignment (Press/Release/Long Press/Long Release)
  - Channel override for customizing profile defaults
  - Auto-detection badges showing matched actions
  - MIDI preview showing resolved commands before saving
  - State-specific profile support for keytimes/multi-state buttons
- **Multi-state UI enhancements** in ButtonSettingsPanel:
  - Animated state tabs with color coding
  - State-specific ProfileSelector instances
  - Compact layout with improved visual hierarchy
- **Section icons**: Added #️⃣ for ID section, 🎛️ for Behavior section
- **Resizable panel layout**: Default 65%/35% split (780px left panel on 1200px window)
- **Compact ColorSelect**: Replaced always-visible grid with popover color picker

### Changed
- Left panel default width increased from 50% to 65% (780px) for better button editing space
- ProfileMidiCommand type extended with `pc_inc` and `pc_dec` variants
- ValidationErrors refactored to use derived store for reactive error access
- Documentation improvements in device-profiles-schemas.md with type-specific field mapping

### Fixed
- **Type violations**: Added missing `pc_inc`/`pc_dec` support to ProfileMidiCommand type and resolver
- **Console spam**: Removed all debug console.log statements from ProfileSelector and ButtonSettingsPanel
- **Event badge counts**: Fixed multi-state buttons to show state-specific command counts (not base button counts)
- **MIDI preview persistence**: Changed gating from matchedActionId to targetCommands.length to prevent disappearing after edits
- **ColorSelect click handler**: Added `instanceof Element` guard before calling `.closest()` to prevent Text node errors
- **Channel override NaN handling**: Added validation to prevent writing `channel: NaN` into commands from non-numeric input
- **Profile clearing in multi-state**: Now clears commands from ALL states (not just current) when clearing profile
- **Unused imports**: Removed unused 'fade' import from ButtonSettingsPanel
- **CI macOS code signing**: Persist keychain password across CI steps and unlock before build
  - Export KEYCHAIN_PATH and KEYCHAIN_PASSWORD to GITHUB_ENV
  - Added explicit unlock step before Tauri build
  - Fixed keychain search list to include temporary keychain alongside existing
  - Added cleanup step to delete keychain after build
- **CI Windows MSI build**: Changed version format from `0.1.0-dev+N` to `0.1.0-dev.N`
  - Build metadata (`+...`) not supported by npm/tauri
  - Pre-release format with dot separator is MSI-compatible (numeric only, <65535)

### Tests & CI
- All existing tests passing with new profile types
- CI builds now succeed on all platforms (macOS, Windows, Linux)
- macOS code signing working with proper keychain unlock sequence
- Windows MSI packaging compatible with npm semver requirements

### Documentation
- Updated device-profiles-schemas.md with type-specific MIDI field documentation
- Added clear mapping of which fields (cc/value, note/velocity, program, pc_step) apply to each command type
- Clarified channel field is optional and zero-based (0-15)

### Deployment
- Branch: `fix/profile-selector-styling`
- PR: https://github.com/MC-Music-Workshop/midi-captain-max/pull/15
- All 14 Copilot review comments addressed
- Ready for merge after CI validation

---

## [Previous Release] - 2026-03-14

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
