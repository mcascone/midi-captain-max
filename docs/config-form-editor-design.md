# Config Form Editor Design

**Created:** 2026-02-09
**Status:** Implemented
**Related:** [Config Editor Implementation Plan](plans/2026-02-02-config-editor.md)

---

## Overview

Visual form editor replacing the raw JSON editor. Features proper UI controls (dropdowns, toggles, text fields), undo/redo, validation, and device-specific field handling.

**Key Goals:**
- Form-first UX (hide JSON complexity from users)
- Undo/redo support (critical for good editing experience)
- Real-time validation with inline errors
- Device-specific behavior (Mini6 vs STD10)
- No data loss when switching device types

---

## Architecture Decisions

### 1. UI Approach: Form-First

**Choice:** Pure form UI replaces JSON editor
- Visual editor is the primary interface
- "View JSON" modal for power users
- No split-pane or hybrid view

**Rationale:** Cleaner, more professional experience. JSON editing is for debugging only.

---

### 2. Form Organization: Accordion Sections

**Choice:** Collapsible sections for each config area
```
▼ Device Settings
▼ Buttons (10 of 10)
▼ Encoder
▼ Expression Pedals
▼ Display
```

**Rationale:**
- Visual separation of concerns
- Can collapse irrelevant sections
- Matches plugin UI conventions

---

### 3. Button Row Layout: Horizontal Inline

**Choice:** Each button row shows all fields horizontally
```
Button 1:  [TSC     ] Ch:[1 ] CC:[20  ] ON:[127] OFF:[0] Color:[●Green ▼] Mode:[Toggle  ▼] Off:[Dim ▼]
```

**Rationale:**
- Compact, see many buttons at once
- Easy to compare settings across buttons
- Standard pattern for multi-item editors

---

### 4. Color Selection: Dropdown with Swatches

**Choice:** Custom dropdown showing color circles + names
```
Color: [●Green ▼]
       ↓
   [● Red    ]
   [● Green  ] ✓
   [● Blue   ]
   ...
```

**Rationale:**
- Visual feedback matches hardware LEDs
- Clear what color you're selecting
- Standard pattern in design tools

---

### 5. Device Switching: Preserve + Hide

**Choice:** When switching Mini6 ↔ STD10, preserve all data
```
Mini6 mode:
  Buttons 1-6: Visible and editable
  Buttons 7-10: Grayed out "Not available on Mini6" (data preserved)
  Encoder: Section collapsed "Disabled on Mini6" (config preserved)
```

**Rationale:**
- No data loss when experimenting
- Forgiving UX
- User can see what they'd lose before committing

---

## Component Architecture

### State Management: `formStore.ts`

**Single source of truth:**
```typescript
interface FormState {
  config: MidiCaptainConfig;             // Current values
  history: MidiCaptainConfig[];          // Past states for undo (max 50)
  historyIndex: number;                  // Position in history
  validationErrors: Map<string, string>; // field path → error
  isDirty: boolean;                      // Unsaved changes flag
  _hiddenButtons?: ButtonConfig[];       // Buttons 7-10 when Mini6
  _hiddenEncoder?: EncoderConfig;        // Encoder config when Mini6
}
```

**Derived stores:**
- `config` — current config
- `isDirty` — unsaved changes flag
- `validationErrors` — error map
- `canUndo` / `canRedo` — history state

**Core actions:**
- `loadConfig(config)` - Initialize from device, clears history
- `updateField(path, value)` - Single field change (creates history checkpoint, debounced 500ms)
- `setDevice(type)` - Device switch with data preservation
- `undo()` / `redo()` - History navigation
- `validate()` - Run all validation rules

**History checkpoints:**
- Every field change (debounced 500ms to batch rapid typing)
- Device type switch

---

### Component Hierarchy

**Top level:** `ConfigForm.svelte`
- Consumes `formStore` for all state
- Toolbar: [Undo] [Redo] [View JSON] [Save to Device]
- Keyboard shortcuts (⌘Z/⌘⇧Z/⌘S)
- Renders section components in accordion

**Sections:**
```
DeviceSection.svelte
  ├─ <select> for device type
  └─ <input type="number"> global MIDI channel

ButtonsSection.svelte
  └─ ButtonRow.svelte (×6 or ×10)
      ├─ <input type="text"> label (max 6 chars)
      ├─ <input type="number"> channel (1-16, stored as 0-15)
      ├─ <input type="number"> CC (0-127)
      ├─ <input type="number"> ON value (cc_on, default 127)
      ├─ <input type="number"> OFF value (cc_off, default 0)
      ├─ ColorSelect.svelte (custom dropdown)
      ├─ <select> mode (toggle/momentary)
      └─ <select> off_mode (dim/off)

EncoderSection.svelte
  ├─ Device check: gray out if Mini6
  ├─ <input type="checkbox"> enabled
  ├─ <input type="number"> CC, min, max, initial, channel
  └─ EncoderPush fields (nested): CC, ON value, OFF value, mode, channel

ExpressionSection.svelte
  └─ ExpressionPedal.svelte (×2: exp1, exp2)
      ├─ <input type="checkbox"> enabled
      ├─ <input type="number"> CC, min, max, threshold, channel
      └─ <select> polarity (normal/inverted)

DisplaySection.svelte
  └─ <select> text sizes (small/medium/large) ×3
```

**Utility components:**
- `Accordion.svelte` - Reusable collapsible section with optional disabled state
- `ColorSelect.svelte` - Custom color picker (native `<select>` doesn't support swatches)
- `JsonEditor.svelte` - CodeMirror JSON viewer, used in "View JSON" modal

**Rationale:** Avoid over-componentization. Native elements are simpler and more accessible.

---

## Validation System

### Field-Level Validation (runs on blur, re-validates on change if already invalid)

| Field | Rules |
|-------|-------|
| Label | Required, max 6 chars, alphanumeric/spaces/hyphens only |
| CC number | Required, integer 0-127 |
| Color | Must be valid enum (enforced by `<select>`) |
| Mode | Must be toggle/momentary (enforced by `<select>`) |
| Min/Max | Integer 0-127, min < max |
| Initial | Integer 0-127, within min-max range |

### Form-Level Validation (runs before save)

- Device-specific checks:
  - Mini6: buttons.length ≤ 6
  - Mini6: encoder disabled (or missing)
  - STD10: buttons.length ≤ 10
- All required fields present and valid

### Error Display

- **Inline errors:** Red text below each invalid field
- **Form-level errors:** Yellow banner at top listing all issues
- **Save button states:**
  - Valid: "Save to Device"
  - Invalid: "Fix 3 errors to save" (button disabled)

---

## Data Flow

### Loading Config
```
User selects device → readConfigRaw() → Parse JSON → formStore.loadConfig()
  ↓
Clear history, set initial state
  ↓
All components reactively update
  ↓
Validation runs, errors shown if any
```

### Editing Field
```
User changes input → onBlur → formStore.updateField(path, value)
  ↓
Validate field
  ↓
If valid: Push current state to history (debounced 500ms)
  ↓
Update config, trigger reactivity
  ↓
Component re-renders
```

### Undo/Redo
```
User presses ⌘Z → formStore.undo()
  ↓
historyIndex--, restore config from history[index]
  ↓
All components reactively update
  ↓
No new history entry (just pointer movement)
```

### Saving
```
User clicks "Save" → formStore.validate()
  ↓ All valid?
YES: writeConfigRaw() → Clear dirty flag + history
NO: Show errors, disable save button
```

### Device Type Switch (Special Case)
```
User changes device selector → formStore.setDevice(newType)
  ↓
Switching TO Mini6?
  ├─ Store buttons[6..9] in _hiddenButtons
  └─ Store encoder in _hiddenEncoder (mark disabled)
  ↓
Switching TO STD10?
  ├─ Restore _hiddenButtons (or create defaults)
  └─ Restore _hiddenEncoder (or create default)
  ↓
Push to history, re-validate, components update
```

---

## UI/UX Details

### Accordion Behavior
- All sections expanded by default
- Click header to collapse/expand
- State persists in localStorage
- Smooth CSS transitions

### Button Row Styling
```
Button 1:  [TSC     ] Ch:[1] CC:[20] ON:[127] OFF:[0] Color:[●Green ▼] Mode:[Toggle ▼] Off:[Dim ▼]
           └─6 chars        └─0-127  └─0-127  └─0-127  └─visual swatch
```
- Fixed-width label input (prevents layout shift)
- Inline field labels ("CC:", "Color:", etc.)
- Optional fields show placeholder when default

### Device-Specific Visibility
- **Mini6:** Buttons 7-10 grayed with overlay "Not available on Mini6"
- **Mini6:** Encoder section collapsed with "(Disabled on Mini6)" in header
- **STD10:** Everything visible and editable

### Keyboard Shortcuts
- ⌘S: Save to device
- ⌘Z: Undo
- ⌘⇧Z: Redo
- Tab/Shift-Tab: Navigate fields
- Enter: Move to next field (not submit)

### Error States
- Invalid field: Red border + error text below
- Form-level: Yellow banner at top with issue list

---

## Future Enhancements

- LCD preview pane (show what display will look like)
- Copy/paste button configs
- Preset library (save/load common configs)
- Drag-and-drop button reordering
- Bulk edit mode (change CC numbers by offset)
- Import from OEM SuperMode configs
- Multiple messages per button press (requires firmware + schema changes)
