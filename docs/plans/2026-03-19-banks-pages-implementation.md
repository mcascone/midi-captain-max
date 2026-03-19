# Banks/Pages System Implementation Plan

**Feature:** Banks/Pages System (SI-1 from Feature Analysis Report)  
**Branch:** `feature/banks-pages-system`  
**Start Date:** 2026-03-19  
**Estimated Effort:** 1-2 weeks  
**Priority:** Critical

---

## Overview

Enable users to access more than 10/6 button configurations without reconnecting the device. Essential for complex live setups where musicians need access to hundreds of button configurations across multiple songs or scenes.

---

## Goals

1. **Firmware:** Support 4-8 banks per device, instant switching (<100ms)
2. **Editor:** Bank management UI with tabs, copy/paste, templates
3. **Config:** Backward-compatible schema (single-bank configs still work)
4. **UX:** Clear visual indication of active bank, smooth transitions

---

## Non-Goals

- MIDI bank select standard (MSB/LSB) — use simple approach first
- Bank-specific global settings (encoder, expression) — all banks share global config
- Unlimited banks — cap at 8 for Flash storage limits

---

## Implementation Phases

### Phase 1: Config Schema & Validation (Days 1-2)

#### Config Schema Design

**New format (multi-bank):**
```json
{
  "device": "std10",
  "banks": [
    {
      "name": "Live Set 1",
      "buttons": [
        {"label": "Scene A", "press": [...], ...}
      ]
    },
    {
      "name": "Studio", 
      "buttons": [...]
    }
  ],
  "bank_switch": {
    "method": "button",      // "button" | "cc" | "pc"
    "button": 10,            // 1-10 for STD10, 1-6 for Mini6
    "cc": 120,               // CC number for bank switching (if method="cc")
    "channel": 0             // MIDI channel for bank switching
  },
  "active_bank": 0,          // Boot to this bank (0-indexed)
  "encoder": {...},          // Shared across all banks
  "expression": {...},       // Shared across all banks
  "display": {...}           // Shared across all banks
}
```

**Backward compatibility (single-bank, existing configs):**
```json
{
  "device": "std10",
  "buttons": [...]  // Legacy format
}
```

Migration strategy:
- If `banks` field exists → multi-bank mode
- If `buttons` field exists → single-bank mode (auto-wrap in bank on load)
- Both exist → `banks` takes precedence (ignore `buttons`)

#### Tasks

- [ ] Update `config-editor/src/lib/types.ts`:
  - Add `BankConfig` interface
  - Add `BankSwitchConfig` interface
  - Update `MidiCaptainConfig` to include optional `banks` array
  - Keep `buttons` optional for backward compatibility

- [ ] Update `config-editor/src-tauri/src/config.rs`:
  - Add `BankConfig` struct
  - Add `BankSwitchConfig` struct
  - Update `MidiCaptainConfig` struct
  - Add migration logic in `validate()` method
  - Add validation: max 8 banks, bank names unique, button arrays valid

- [ ] Update `firmware/circuitpython/core/config.py`:
  - Add `load_banks()` function
  - Add `get_active_bank_config()` function
  - Add `migrate_legacy_config()` function (wrap buttons in bank)
  - Add validation helpers

- [ ] Write tests:
  - `tests/test_banks_config.py` — config loading, migration, validation
  - `config-editor/src-tauri/src/config.rs` — Rust roundtrip tests
  - Test empty banks array (fallback to single bank)
  - Test invalid bank switch button number
  - Test bank name uniqueness validation

---

### Phase 2: Firmware Implementation (Days 3-6)

#### Core Functionality

**State Management:**
- `current_bank_index: int` — 0-indexed, active bank
- `banks: List[BankConfig]` — Array of bank configurations
- `bank_button_states: List[List[ButtonState]]` — Per-bank button states

**Bank Switching Logic:**
```python
def switch_bank(new_bank_index):
    # Validate index
    if not 0 <= new_bank_index < len(banks):
        return False
    
    # Save current bank state
    save_bank_state(current_bank_index, button_states)
    
    # Load new bank
    current_bank_index = new_bank_index
    buttons = banks[current_bank_index]["buttons"]
    
    # Restore button states for new bank
    button_states = load_bank_state(new_bank_index)
    
    # Update all LEDs
    for i in range(BUTTON_COUNT):
        set_button_state(i + 1, button_states[i].state)
    
    # Update display
    bank_name = banks[current_bank_index]["name"]
    set_label_text(button_name_label, bank_name)
    set_label_text(status_label, f"Bank {new_bank_index + 1}/{len(banks)}")
    
    # Optional: LED animation (brief flash)
    flash_all_leds()
    
    return True
```

#### Tasks

- [ ] Add `firmware/circuitpython/core/banks.py`:
  - `BankManager` class
  - `switch_bank(index)` method
  - `get_current_bank()` method
  - `save_bank_state()` method
  - `load_bank_state()` method

- [ ] Update `firmware/circuitpython/code.py`:
  - Load banks from config
  - Initialize `BankManager`
  - Add bank switch button handler
  - Add bank switch MIDI handler (CC/PC)
  - Display bank name on boot

- [ ] Update `firmware/circuitpython/handlers/button.py`:
  - Bank switch button special handling
  - Detect long-press on bank button for prev/next bank

- [ ] Update `firmware/circuitpython/handlers/midi.py`:
  - Handle bank switch CC/PC messages
  - Send bank change confirmation (optional)

- [ ] Add visual feedback:
  - Flash all LEDs on bank switch (100ms pulse)
  - Display bank name for 2 seconds
  - Show bank number in status line

- [ ] Write tests:
  - `tests/test_banks_runtime.py` — bank switching logic
  - `tests/test_banks_state_persistence.py` — state save/restore
  - Test invalid bank index handling
  - Test bank switch button detection
  - Test MIDI bank switch commands

---

### Phase 3: Editor UI (Days 7-10)

#### UI Components

**BanksPanel.svelte** (new component)
```svelte
- Bank tabs (horizontal tabs at top of left panel)
- Active bank indicator (highlight current tab)
- "Add Bank" button (max 8)
- "Duplicate Bank" button
- "Delete Bank" button (confirm dialog)
- Bank rename (inline edit)
```

**DeviceLayout.svelte** (update)
```svelte
- Show active bank buttons only
- Bank indicator in corner (e.g., "Bank 2/3")
```

**BankSettingsPanel.svelte** (new component)
```svelte
- Bank switch method dropdown (Button / MIDI CC / MIDI PC)
- Bank switch button selector (if method=button)
- Bank switch CC number (if method=cc)
- Bank switch channel
- Active bank on boot selector
```

#### Tasks

- [ ] Create `config-editor/src/lib/components/BanksPanel.svelte`:
  - Horizontal tab bar for banks
  - Tab click → switch active bank
  - Add/duplicate/delete buttons
  - Inline bank rename
  - Drag-drop bank reordering (optional)

- [ ] Create `config-editor/src/lib/components/BankSettingsPanel.svelte`:
  - Bank switch configuration form
  - Validation (button number in range)
  - Method-specific fields (show/hide based on selection)

- [ ] Update `config-editor/src/lib/formStore.ts`:
  - Add `activeBankIndex` state
  - Add `switchBank(index)` function
  - Add `addBank()` function
  - Add `duplicateBank(index)` function
  - Add `deleteBank(index)` function (with confirmation)
  - Add `renameBank(index, newName)` function

- [ ] Update `config-editor/src/routes/+page.svelte`:
  - Integrate BanksPanel above DeviceLayout
  - Integrate BankSettingsPanel in right sidebar

- [ ] Update `config-editor/src/lib/components/ButtonSettingsPanel.svelte`:
  - Show bank context (e.g., "Bank 2 - Live Set")
  - Copy button → copy across banks option

- [ ] Add keyboard shortcuts:
  - `Ctrl+Shift+[` → Previous bank
  - `Ctrl+Shift+]` → Next bank
  - `Ctrl+B` → Add new bank
  - `Ctrl+D` → Duplicate active bank

- [ ] Add visual polish:
  - Bank tab colors (subtle differentiation)
  - Smooth transitions when switching banks
  - Loading state during bank switch

---

### Phase 4: Testing & Documentation (Days 11-12)

#### Testing

- [ ] Integration tests:
  - Full workflow: create banks → configure buttons → save → load on device → switch banks
  - Bank state persistence (button states survive switch)
  - Select groups per-bank (deselect siblings in same bank, not other banks)

- [ ] Edge cases:
  - Empty bank (no buttons configured)
  - Single bank (no bank switching UI shown)
  - Max banks reached (disable "Add Bank" button)
  - Delete last bank (prevent, minimum 1 bank)

- [ ] Hardware testing:
  - Test on STD10 with 4 banks
  - Test on Mini6 with 3 banks
  - Bank switch latency (target <100ms)
  - LED flash animation smooth

#### Documentation

- [ ] Update `docs/USER-GUIDE-EN.md`:
  - Banks/Pages section (what are banks, when to use them)
  - How to add/delete/rename banks
  - How to switch banks (button vs MIDI)
  - Limitations (max 8 banks, shared encoder/expression)

- [ ] Update `docs/USER-GUIDE-PT-BR.md`:
  - Portuguese translation of banks documentation

- [ ] Update `README.md`:
  - Add "Banks/Pages" to feature list
  - Mention max configurations (e.g., "80 buttons with 8 banks on STD10")

- [ ] Create example configs:
  - `config-examples/std10-4banks-live-rig.json`
  - `config-examples/mini6-3banks-studio.json`

- [ ] Record demo video (optional):
  - Show bank switching in action
  - Configure multiple banks in editor
  - Deploy to device and switch banks

---

## Config Migration Strategy

### Auto-Migration on Load

When config is loaded (firmware or editor):

```python
def migrate_config(cfg):
    # Multi-bank format already
    if "banks" in cfg:
        return cfg
    
    # Legacy single-bank format
    if "buttons" in cfg:
        buttons = cfg.pop("buttons")
        cfg["banks"] = [
            {
                "name": "Bank 1",
                "buttons": buttons
            }
        ]
        cfg["active_bank"] = 0
        # No bank_switch config (single bank)
    
    return cfg
```

### Backward Compatibility

- Old configs without `banks` field → loaded as single bank
- Editor detects single-bank mode → hide bank tabs
- Firmware detects single-bank mode → disable bank switching
- "Upgrade to Multi-Bank" button in editor (convert single → multi)

---

## Flash Storage Considerations

### Size Estimates

**Single bank (STD10):**
- 10 buttons × 500 bytes avg = 5KB
- Full config = ~8KB

**8 banks (STD10):**
- 8 banks × 5KB = 40KB
- Full config = ~50KB

**RP2040 Flash:**
- 2MB total
- CircuitPython firmware = ~1.2MB
- Available for config = ~800KB
- **Conclusion:** 50KB is <10% of available space, safe margin

### Optimization (if needed)

- Compress configs with gzip (CircuitPython supports)
- Store only active banks in RAM
- Lazy-load banks from Flash on switch

---

## Bank Switching Performance

### Target Latency

- Bank switch trigger → LEDs updated: **<100ms**
- User perception: instant

### Optimization

1. Pre-load button states in memory (don't reparse config)
2. Batch LED updates (single `pixels.show()` call)
3. Skip unnecessary display updates
4. Profile with `time.monotonic()` timers

---

## Alternative Designs Considered

### Bank Select via Expression Pedal

**Pros:** Hands-free, gradual control  
**Cons:** Accidental switches, uses pedal input  
**Decision:** Not in MVP, could add later

### MIDI Bank Select Standard (MSB/LSB)

**Pros:** Industry standard  
**Cons:** Complex (2-message protocol), rarely used by musicians  
**Decision:** Simple CC/PC-based switching for MVP

### Unlimited Banks

**Pros:** Maximum flexibility  
**Cons:** Flash storage limits, config file size, UX complexity  
**Decision:** Cap at 8 banks (reasonable for live performance)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Flash storage exhausted | High | Monitor config size, warn user at 80% |
| Bank switch latency too high | High | Profile and optimize, target <100ms |
| State corruption during switch | Critical | Validate state before save, graceful fallback |
| UI complexity (too many banks) | Medium | Cap at 8 banks, clear visual hierarchy |
| Backward compatibility breaks | High | Thorough migration testing, preserve legacy support |

---

## Success Criteria

- [ ] Config schema finalized and validated
- [ ] Firmware loads multi-bank configs
- [ ] Bank switching works (button and MIDI)
- [ ] Editor UI allows bank management
- [ ] State persists across bank switches
- [ ] Backward compatibility maintained (old configs work)
- [ ] Latency <100ms for bank switch
- [ ] All tests passing (188+ pytest, 50+ cargo)
- [ ] Documentation updated (user guides, README)
- [ ] Example configs provided

---

## Rollout Plan

### Beta Release (feature/banks-pages-system branch)

1. Feature complete + tests passing
2. Alpha testing with 2-3 users
3. Gather feedback, iterate
4. Performance profiling on hardware

### Production Release (merge to main)

1. PR review (focus on reliability, backward compat)
2. Final hardware testing (STD10 + Mini6)
3. Update CHANGELOG.md
4. Merge to main
5. Tag release (e.g., `v1.6.0-beta.1`)
6. Publish firmware + editor binaries

---

## Timeline

| Days | Phase | Deliverables |
|------|-------|--------------|
| 1-2 | Config Schema | Types, validation, migration logic |
| 3-6 | Firmware | Bank switching, state management |
| 7-10 | Editor UI | BanksPanel, settings, keyboard shortcuts |
| 11-12 | Testing & Docs | Integration tests, user guides |
| **Total: 12 days** | ~2 weeks | Feature complete |

---

## Next Steps

1. ✅ Create implementation plan (this document)
2. [ ] Update TypeScript types (`types.ts`)
3. [ ] Update Rust config structs (`config.rs`)
4. [ ] Write config roundtrip tests
5. [ ] Implement firmware `BankManager` class
6. [ ] Build editor `BanksPanel` component
7. [ ] Integration testing on hardware
8. [ ] Documentation updates
9. [ ] PR review and merge

---

**Status:** Ready to begin implementation  
**Next action:** Update config types (Phase 1, Day 1)
