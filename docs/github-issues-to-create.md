# GitHub Issues to Create

These are the top 5 priority features identified in the March 2026 investigation. Copy each issue template below and create it on GitHub.

---

## Issue 1: Conditional Actions (PRD Feature 3)

**Title:** Implement Conditional Actions (PRD Feature 3) - Smart context-aware button behavior

**Labels:** `enhancement`, `feature`, `firmware`, `editor`, `high-priority`

**Body:**
```markdown
## Summary
Implement smart buttons that adapt to context - buttons can change behavior based on other button states, received MIDI values, encoder position, or expression pedal input.

## User Value
- Transform device from "controller" to "intelligent system"
- Enable complex conditional logic: "If delay is ON, send CC 20=0, else send CC 20=127"
- Significantly reduces manual button presses for common workflows
- **Impact:** ⭐⭐⭐⭐⭐ Game-changer

## Example Use Case
```json
{
  "press": [{
    "if": {"button": 2, "state": "on"},
    "then": [{"type": "cc", "cc": 20, "value": 0}],
    "else": [{"type": "cc", "cc": 20, "value": 127}]
  }]
}
```

## Condition Types
- Button state (on/off, keytime)
- Received MIDI values (host state)
- Expression pedal value
- Encoder value

## Implementation Plan

### Firmware Changes
- [ ] Condition evaluator in `_send_action_from_cfg()`
- [ ] State tracking system (button states, last received CC values)
- [ ] Nested condition support (limited depth for embedded)
- [ ] Add to `core/config.py` schema

### Editor Changes
- [ ] Condition builder UI (visual or form-based)
- [ ] Validation (prevent infinite loops, circular dependencies)
- [ ] Preview/simulation (show which branch would execute)
- [ ] Update TypeScript types and Rust structs

### Testing
- [ ] Unit tests for condition evaluation
- [ ] Integration tests for complex conditions
- [ ] Hardware validation on STD10 and Mini6

## Dependencies
State tracking (mostly exists)

## Estimated Effort
2-3 weeks

## Priority
**High** - PRD Feature 3, major differentiator

## Related Documents
- [PRD Feature 3](docs/features/PRD.md)
- [Conditional Actions Design](docs/features/device-profiles.md)
- [March 2026 Investigation](docs/reports/2026-03-20-project-state-investigation.md)
```

---

## Issue 2: MIDI Monitor Panel

**Title:** Add MIDI Monitor Panel to Config Editor

**Labels:** `enhancement`, `feature`, `editor`, `high-priority`, `quick-win`

**Body:**
```markdown
## Summary
Add a real-time MIDI monitor panel to the config editor for debugging and setup validation.

## User Value
- Essential debugging tool - see exactly what MIDI messages are sent/received
- No need for external MIDI monitoring software
- Helps users verify their configurations work correctly
- **Impact:** ⭐⭐⭐⭐⭐ Critical for user experience

## Features
- [ ] Live MIDI message display (IN/OUT)
- [ ] Filter by message type (CC/Note/PC/SysEx)
- [ ] Filter by channel (1-16)
- [ ] Pause/resume stream
- [ ] Clear log button
- [ ] Export log to file
- [ ] Highlight device messages (vs other MIDI sources)
- [ ] Timestamp each message (relative + absolute)
- [ ] Color-coded by type (CC=blue, Note=green, PC=yellow)

## Implementation Plan

### UI Component
- [ ] Collapsible panel in editor (bottom or right side)
- [ ] Message list with virtualization (for performance)
- [ ] Filter controls (type, channel, pause)
- [ ] Export button

### Backend (Tauri)
- [ ] Serial port monitoring of device
- [ ] MIDI message parsing
- [ ] IPC command: `start_midi_monitor`, `stop_midi_monitor`
- [ ] Stream messages to frontend

### Testing
- [ ] Verify all message types displayed correctly
- [ ] Test with high MIDI traffic (100+ msgs/sec)
- [ ] Test export functionality

## Dependencies
Serial console access from Tauri (already exists for device detection)

## Estimated Effort
2-3 days

## Priority
**High** - Quick win, essential for user experience

## Related Documents
- [March 2026 Investigation](docs/reports/2026-03-20-project-state-investigation.md)
- [FEATURE-ANALYSIS-REPORT.md](docs/FEATURE-ANALYSIS-REPORT.md)
```

---

## Issue 3: Configuration Presets Library

**Title:** Add Configuration Presets Library to Config Editor

**Labels:** `enhancement`, `feature`, `editor`, `high-priority`, `quick-win`

**Body:**
```markdown
## Summary
Add a library of pre-made configuration presets for common workflows to reduce setup friction for new users.

## User Value
- Quick-load common setups without manual configuration
- Learning tool - see how others configure their devices
- Accelerates onboarding for new users
- **Impact:** ⭐⭐⭐⭐ High value, low effort

## Presets to Include
1. **DAW Transport Control**
   - Play/Stop/Record for Ableton, Logic Pro, Reaper
   - Track arming, metronome toggle

2. **Guitar Rig - Kemper Standard**
   - 5 rig slots + tuner
   - Expression pedal for volume

3. **Guitar Rig - Helix Scene Banks**
   - 8 scenes per bank, bank switching
   - Expression pedal for wah

4. **Guitar Rig - Quad Cortex**
   - Scene switching, stomp toggles
   - Expression pedal for volume/wah

5. **Synthesizer Control**
   - CC mappings for filter, resonance, LFO rate
   - Program change for patches

6. **HX Stomp 6-Button**
   - Optimized for Mini6 device

7. **MainStage Scene Control**
   - Scene switching via CC
   - Toggle effects

8. **Studio Session Template**
   - Generic CC controls for any DAW
   - Labeled for common parameters

## Implementation Plan

### Presets Storage
- [ ] Create `config-editor/src/lib/presets/` directory
- [ ] JSON files for each preset
- [ ] Include metadata (name, description, device type, author)

### UI Component
- [ ] "Load Preset" button in toolbar
- [ ] Preset picker modal with categories
- [ ] Preview preset (show button layout)
- [ ] Warning if loading will overwrite current config

### Config Editor Changes
- [ ] Import preset JSON
- [ ] Validate preset matches device type
- [ ] Load preset into formStore

### Testing
- [ ] Verify each preset loads correctly
- [ ] Test on both STD10 and Mini6
- [ ] Validate all MIDI mappings

## Dependencies
None

## Estimated Effort
1-2 days

## Priority
**High** - Highest impact/effort ratio

## Related Documents
- [Device Profiles](docs/features/device-profiles.md)
- [March 2026 Investigation](docs/reports/2026-03-20-project-state-investigation.md)
```

---

## Issue 4: Export/Import Configuration Files

**Title:** Add Export/Import Configuration Files to Config Editor

**Labels:** `enhancement`, `feature`, `editor`, `medium-priority`, `quick-win`

**Body:**
```markdown
## Summary
Add export/import functionality for configuration files to enable backup, sharing, and version control.

## User Value
- Configuration backup and restore
- Share setups with community
- Version control configs alongside project files
- Disaster recovery
- **Impact:** ⭐⭐⭐⭐ Essential utility feature

## Features
- [ ] Export button → save config.json to user-selected location
- [ ] Import button → load config.json from file picker
- [ ] Validate imported config before applying
- [ ] Show confirmation dialog on import (will overwrite current config)
- [ ] Include metadata in exported file:
  - Export date/time
  - Firmware version
  - Config schema version
  - Device type
  - Optional: user notes field

## Implementation Plan

### UI Changes
- [ ] Add "Export Config" button in toolbar
- [ ] Add "Import Config" button in toolbar
- [ ] File picker dialog (Tauri)
- [ ] Validation error dialog if import fails

### Backend (Tauri)
- [ ] `export_config` command - show save dialog, write file
- [ ] `import_config` command - show open dialog, read file
- [ ] Schema version validation
- [ ] Device type matching (warn if STD10 config on Mini6)

### Config Schema Addition
```json
{
  "_metadata": {
    "export_date": "2026-03-20T12:00:00Z",
    "firmware_version": "1.5.0",
    "schema_version": "2.0",
    "device": "std10",
    "notes": "My live performance setup"
  },
  "device": "std10",
  ...
}
```

### Testing
- [ ] Export and re-import same config (roundtrip)
- [ ] Import config from different firmware version
- [ ] Import STD10 config on Mini6 device (should warn)
- [ ] Handle corrupted JSON gracefully

## Dependencies
File I/O (already exists in Tauri commands)

## Estimated Effort
1 day

## Priority
**Medium** - Quick win, high user value

## Related Documents
- [March 2026 Investigation](docs/reports/2026-03-20-project-state-investigation.md)
```

---

## Issue 5: Dark Mode for Config Editor

**Title:** Add Dark Mode to Config Editor

**Labels:** `enhancement`, `feature`, `editor`, `low-priority`, `quick-win`, `ui/ux`

**Body:**
```markdown
## Summary
Add dark mode theme to the config editor for studio-friendly, low-light environments.

## User Value
- Studio-friendly UI (reduce eye strain in dark environments)
- System preference integration (follows OS theme)
- Professional appearance
- **Impact:** ⭐⭐⭐ Nice to have, low effort

## Features
- [ ] Dark theme CSS variables
- [ ] Light theme CSS variables (current)
- [ ] Theme toggle button in toolbar (or auto-detect system preference)
- [ ] Persist theme choice in local storage
- [ ] Smooth transition animation between themes

## Color Palette (Suggested)

### Dark Theme
- Background: `#1e1e1e`
- Surface: `#252526`
- Primary: `#0e639c`
- Text: `#cccccc`
- Border: `#3e3e42`

### Light Theme (Current)
- Maintain existing colors

## Implementation Plan

### CSS Changes
- [ ] Define CSS custom properties for both themes
- [ ] Update all components to use CSS variables
- [ ] Add `.dark-theme` class to root element

### Theme Toggle
- [ ] Theme toggle button component
- [ ] Detect system preference on first load
- [ ] Store preference in localStorage
- [ ] Apply theme on app startup

### Testing
- [ ] Verify all UI elements readable in both themes
- [ ] Test theme persistence across page reloads
- [ ] Test system preference detection on macOS/Windows

## Dependencies
None

## Estimated Effort
1-2 days

## Priority
**Low** - Nice to have, but quick win

## Related Documents
- [March 2026 Investigation](docs/reports/2026-03-20-project-state-investigation.md)
```

---

## Next Steps

1. **Create these 5 issues** on GitHub: https://github.com/guisperandio/midi-captain-max/issues/new
2. **Triage existing issues** - Review open issues, close obsolete ones, apply priority labels
3. **Plan sprint** - Decide which quick wins to tackle first (recommended: MIDI Monitor + Presets Library)

## Additional Context

See the full investigation report at [docs/reports/2026-03-20-project-state-investigation.md](docs/reports/2026-03-20-project-state-investigation.md) for comprehensive analysis and prioritization rationale.
