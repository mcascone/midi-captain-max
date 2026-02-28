# PR Conflict Quick Reference

## Visual Conflict Map

```
firmware/dev/code.py
├─ Line ~377: button_states initialization
│  ├─ MAIN:  button_states = [False] * BUTTON_COUNT
│  ├─ PR#51: + pc_values, + pc_flash_timers (keeps boolean list)
│  └─ PR#50: ⚠️ REPLACE with ButtonState objects
│
├─ Line ~504+: handle_switches() logic
│  ├─ PR#51: + message_type dispatch (CC vs PC)
│  └─ PR#50: ⚠️ Uses ButtonState methods + get_button_state_config()
│
└─ New functions
   ├─ PR#51: + clamp_pc_value(), + flash_pc_button(), + update_pc_flash_timers()
   └─ PR#50: + get_button_state_config(), + get_button_color()

firmware/dev/core/config.py
└─ validate_button() function
   ├─ PR#51: ⚠️ Adds "type" field + type-specific validation
   └─ PR#50: ⚠️ Adds "keytimes" + "states" fields

firmware/dev/core/button.py
└─ ButtonState class
   ├─ MAIN:  cc, mode, _state
   └─ PR#50: ⚠️ + keytimes, + current_keytime, + methods

tests/test_config.py
├─ PR#51: + 5 tests for PC message types
└─ PR#50: + 5 tests for keytimes validation

tests/test_button_state.py
└─ PR#50: + 6 tests for keytime cycling

Legend:
  ⚠️  = Direct conflict requiring manual resolution
  +  = Addition (may conflict with other additions)
```

## Conflict Resolution Checklist

### Phase 1: Prepare PR #50 (Keytimes)
- [ ] Review and test PR #50 independently
- [ ] Ensure all tests pass
- [ ] Merge PR #50 to main

### Phase 2: Adapt PR #51 (PC Messages)
- [ ] Rebase PR #51 on updated main
- [ ] Update ButtonState class to accept type parameter
  - [ ] Add `type` field to `__init__()`
  - [ ] Add `program` and `pc_step` fields
  - [ ] Modify `on_press()` for PC behavior
  - [ ] Update `on_midi_receive()` for PC messages
- [ ] Update button_states initialization
  - [ ] Pass `type`, `program`, `pc_step` to ButtonState
  - [ ] Keep `pc_values` and `pc_flash_timers` arrays
- [ ] Update config validation
  - [ ] Merge type-specific fields with keytimes fields
  - [ ] Handle states array with PC configurations
- [ ] Update handle_switches() logic
  - [ ] Combine keytime logic with message type dispatch
  - [ ] Use get_button_state_config() for per-state values
- [ ] Add PC flash helpers (no conflicts)
- [ ] Update tests
  - [ ] Add tests for PC + keytimes combinations
  - [ ] Test CC, PC, PC_inc, PC_dec with keytimes
- [ ] Test combined functionality

### Phase 3: Integration Testing
- [ ] Test CC button with keytimes (already in #50)
- [ ] Test PC button without keytimes
- [ ] Test PC button WITH keytimes (new combination)
- [ ] Test PC inc/dec buttons
- [ ] Test mixed button types in single config
- [ ] Test bidirectional sync for both CC and PC
- [ ] Hardware test on device (if available)

## Quick Merge Simulation

```python
# Before: Main branch
button_states = [False] * BUTTON_COUNT

# After: Merge #50 → Main
button_states = [ButtonState(cc=..., mode=..., keytimes=...) 
                 for i in range(BUTTON_COUNT)]

# After: Merge adapted #51 → Main
button_states = [ButtonState(cc=..., mode=..., keytimes=...,
                              type=..., program=..., pc_step=...)
                 for i in range(BUTTON_COUNT)]
pc_values = [0] * BUTTON_COUNT         # NEW from #51
pc_flash_timers = [0] * BUTTON_COUNT   # NEW from #51
```

## Config Schema Evolution

```json
// Main branch
{
  "label": "BTN1",
  "cc": 20,
  "color": "white",
  "mode": "toggle"
}

// After PR #50
{
  "label": "VERB",
  "cc": 20,
  "keytimes": 3,
  "states": [
    {"cc_on": 64, "color": "blue"},
    {"cc_on": 96, "color": "cyan"},
    {"cc_on": 127, "color": "white"}
  ]
}

// After PR #51 (adapted on top of #50)
{
  "label": "PATCH",
  "type": "pc",
  "program": 5,
  "color": "green"
}

// Future: Combined
{
  "label": "PRESETS",
  "type": "pc",
  "keytimes": 3,
  "states": [
    {"program": 0, "color": "red"},
    {"program": 5, "color": "green"},
    {"program": 10, "color": "blue"}
  ]
}
```

## Timeline Estimate

| Task | Time | Blocker? |
|------|------|----------|
| Review & merge PR #50 | 30min | 🔴 Required |
| Rebase PR #51 | 15min | 🔴 After #50 |
| Update ButtonState class | 45min | 🔴 Core change |
| Update initialization | 15min | 🟡 Depends on ButtonState |
| Merge config validation | 30min | 🟡 Depends on ButtonState |
| Update handle_switches() | 60min | 🟡 Complex logic |
| Write integration tests | 45min | 🟢 Can parallelize |
| Manual testing | 30min | 🟢 Final validation |
| **TOTAL** | **4h** | |

## Questions for Discussion

### Design Decisions
1. **PC with keytimes**: Should PC buttons cycle through programs?
   - ✅ YES: Enables "preset banks" use case
   - ❌ NO: Simpler, PC inc/dec already exists

2. **Per-state types**: Should each state have its own type?
   - ✅ YES: Maximum flexibility (CC → PC → CC)
   - ❌ NO: Simpler validation, unclear use case

3. **LED flash + keytime colors**: How should they interact?
   - Option A: Flash overrides keytime color briefly
   - Option B: Flash uses keytime color
   - Option C: PC buttons don't support keytimes (no conflict)

### Testing Strategy
- Unit tests cover individual features ✓
- Integration tests for combinations needed
- Hardware testing required for LED timing
- Performance testing for main loop overhead

## References
- Full analysis: `docs/pr-review-51-50.md`
- Code examples: `docs/pr-integration-example.py`
- PR #50: https://github.com/MC-Music-Workshop/midi-captain-max/pull/50
- PR #51: https://github.com/MC-Music-Workshop/midi-captain-max/pull/51
