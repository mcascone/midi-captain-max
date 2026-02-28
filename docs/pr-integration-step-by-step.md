# Step-by-Step PR Integration Guide

**Date:** 2026-02-28  
**Target:** Integrate PRs #50, #51, and #53 into unified type system  
**Approach:** Hierarchical merge with minimal risk

---

## Overview

This guide provides detailed, actionable steps to integrate three conflicting PRs:
- **PR #50:** Keytimes (multi-press cycling)
- **PR #51:** Program Change messages
- **PR #53:** MIDI Note messages

**Strategy:** Merge in phases to minimize risk and maintain working state at each step.

---

## Prerequisites

### Required Knowledge
- Git branch management and merging
- CircuitPython firmware deployment
- GUI Config Editor (Tauri + SvelteKit)
- Python testing with pytest

### Required Access
- Write access to main repository
- Hardware for testing (STD10 or Mini6)
- Ability to build and run GUI Config Editor

---

## Phase 1: Merge PR #50 (Keytimes Foundation)

**Duration:** ~2 hours  
**Risk:** LOW - No conflicts with main, establishes foundation for Phase 2

### Steps for YOU (Maintainer)

#### Step 1.1: Review and Test PR #50
```bash
# Checkout PR #50 branch
git fetch origin
git checkout copilot/add-keytimes-functionality

# Run tests
pytest tests/

# Expected: All tests pass
```

**What to verify:**
- [ ] All existing tests pass
- [ ] New ButtonState tests pass
- [ ] No regressions in behavior

#### Step 1.2: Hardware Testing (Optional but Recommended)
```bash
# Deploy to device
./tools/deploy.sh --install

# Test on hardware:
# - Single button press works
# - Keytimes cycling works (if configured)
# - No unexpected crashes
```

#### Step 1.3: Merge to Main
```bash
# Return to main branch
git checkout main
git pull origin main

# Merge PR #50
git merge --no-ff copilot/add-keytimes-functionality

# Push to main
git push origin main
```

**Result:** ButtonState foundation is now in main branch.

---

## Phase 2: Create Unified Type System PR

**Duration:** ~8-10 hours (includes coordination and GUI work)  
**Risk:** MEDIUM - Requires careful integration and testing

This phase combines PR #51 and PR #53 into a single unified implementation.

### Step 2.1: Coordinate with @jjeff

**What to do:**
1. Contact @jjeff via PR #53 comments
2. Share this integration plan
3. Discuss unified type system design
4. Agree on who implements what

**Discussion points:**
- Unified type field: `"cc" | "note" | "pc" | "pc_inc" | "pc_dec"`
- GUI needs to support all 5 types
- Testing approach for all combinations
- Timeline expectations

### Step 2.2: Create Integration Branch

**For YOU (Maintainer):**

```bash
# Ensure main has PR #50 merged
git checkout main
git pull origin main

# Create new integration branch
git checkout -b feature/unified-type-system

# Cherry-pick or merge relevant commits from PR #51
git cherry-pick <commit-hash-from-pr51-for-core-config>
git cherry-pick <commit-hash-from-pr51-for-code-py>
# etc.

# Cherry-pick or merge relevant commits from PR #53
git cherry-pick <commit-hash-from-pr53-for-core-config>
git cherry-pick <commit-hash-from-pr53-for-code-py>
# etc.
```

**Alternative approach (if cherry-picking is complex):**
- Let @copilot create the integration PR (see Step 2.3)

### Step 2.3: Request @copilot to Create Integration PR

**What YOU can ask @copilot to do:**

In a new issue or PR comment:
```
@copilot create a new PR that integrates PR #51 and PR #53 into a unified type system:

1. Base the PR on current main (which includes merged PR #50)
2. Combine firmware changes from both PRs:
   - Unified validate_button() supporting all 5 types
   - Extended ButtonState for all message types
   - Unified message sending logic in code.py
3. Combine and extend GUI changes:
   - Type selector with all 5 options
   - Conditional fields for each type
4. Update tests to cover all types
5. Update documentation

Use the design from docs/pr-review-50-51-53.md as reference.
```

### Step 2.4: Core Firmware Integration

**What @copilot will do (or you can do manually):**

#### File: `firmware/dev/core/config.py`

Unified `validate_button()` function:

```python
def validate_button(btn, index=0, global_channel=None):
    """Validate and fill in missing button config fields.
    
    Supports 5 message types:
    - "cc": Control Change (default)
    - "note": MIDI Note On/Off
    - "pc": Program Change (fixed program)
    - "pc_inc": Increment Program Change
    - "pc_dec": Decrement Program Change
    """
    # Determine message type
    message_type = btn.get("type", "cc")
    
    # Channel handling
    if global_channel is not None:
        default_channel = global_channel
    else:
        default_channel = 0
    
    # Base config common to all types
    validated = {
        "label": btn.get("label", str(index + 1)),
        "color": btn.get("color", "white"),
        "mode": btn.get("mode", "toggle"),
        "off_mode": btn.get("off_mode", "dim"),
        "channel": btn.get("channel", default_channel),
        "type": message_type,
    }
    
    # Keytimes support (from PR #50)
    if "keytimes" in btn:
        validated["keytimes"] = btn["keytimes"]
        validated["states"] = btn.get("states", [])
    
    # Type-specific fields
    if message_type == "cc":
        validated["cc"] = btn.get("cc", 20 + index)
        validated["cc_on"] = btn.get("cc_on", 127)
        validated["cc_off"] = btn.get("cc_off", 0)
    elif message_type == "note":
        validated["note"] = btn.get("note", 60 + index)
        validated["velocity_on"] = btn.get("velocity_on", 127)
        validated["velocity_off"] = btn.get("velocity_off", 0)
    elif message_type == "pc":
        validated["program"] = btn.get("program", 0)
    elif message_type in ("pc_inc", "pc_dec"):
        validated["pc_step"] = btn.get("pc_step", 1)
    
    return validated
```

#### File: `firmware/dev/core/button.py`

Extend ButtonState class:

```python
class ButtonState:
    """Button state with support for all message types."""
    
    def __init__(self, cc=0, mode="toggle", keytimes=1, 
                 message_type="cc", note=60, velocity_on=127, velocity_off=0,
                 program=0, pc_step=1):
        self.cc = cc
        self.mode = mode
        self.keytimes = keytimes
        self.current_keytime = 0
        self.pressed = False
        
        # Type-specific fields
        self.message_type = message_type
        self.note = note
        self.velocity_on = velocity_on
        self.velocity_off = velocity_off
        self.program = program
        self.pc_step = pc_step
```

#### File: `firmware/dev/code.py`

Unified message sending logic:

```python
def handle_switches():
    """Handle button presses and send MIDI messages."""
    for idx in range(BUTTON_COUNT):
        btn_config = config["buttons"][idx]
        message_type = btn_config.get("type", "cc")
        
        if switch_pressed(idx):
            if message_type == "cc":
                # Control Change logic (existing)
                send_cc_message(idx, btn_config)
            elif message_type == "note":
                # Note On/Off logic (from PR #53)
                send_note_message(idx, btn_config)
            elif message_type == "pc":
                # Program Change (from PR #51)
                send_pc_message(idx, btn_config)
            elif message_type == "pc_inc":
                # Increment PC (from PR #51)
                send_pc_inc_message(idx, btn_config)
            elif message_type == "pc_dec":
                # Decrement PC (from PR #51)
                send_pc_dec_message(idx, btn_config)
```

### Step 2.5: GUI Integration

**What @copilot will do (or you can do manually):**

#### File: `config-editor/src/lib/components/ButtonRow.svelte`

Update type selector and conditional fields:

```svelte
<script>
  export let button;
  // ... existing code ...
</script>

<div class="button-config">
  <!-- Type Selector -->
  <select bind:value={button.type} on:change={handleTypeChange}>
    <option value="cc">Control Change (CC)</option>
    <option value="note">Note On/Off</option>
    <option value="pc">Program Change</option>
    <option value="pc_inc">Program Change +</option>
    <option value="pc_dec">Program Change -</option>
  </select>

  <!-- Conditional Fields Based on Type -->
  {#if button.type === 'cc'}
    <label>
      CC Number:
      <input type="number" bind:value={button.cc} min="0" max="127" />
    </label>
    <label>
      CC On:
      <input type="number" bind:value={button.cc_on} min="0" max="127" />
    </label>
    <label>
      CC Off:
      <input type="number" bind:value={button.cc_off} min="0" max="127" />
    </label>
  {:else if button.type === 'note'}
    <label>
      Note Number:
      <input type="number" bind:value={button.note} min="0" max="127" />
    </label>
    <label>
      Velocity On:
      <input type="number" bind:value={button.velocity_on} min="0" max="127" />
    </label>
    <label>
      Velocity Off:
      <input type="number" bind:value={button.velocity_off} min="0" max="127" />
    </label>
  {:else if button.type === 'pc'}
    <label>
      Program Number:
      <input type="number" bind:value={button.program} min="0" max="127" />
    </label>
  {:else if button.type === 'pc_inc' || button.type === 'pc_dec'}
    <label>
      Step Value:
      <input type="number" bind:value={button.pc_step} min="1" max="127" />
    </label>
  {/if}

  <!-- Common fields: label, color, mode, channel, etc. -->
  <!-- ... existing code ... -->
</div>

<script>
  function handleTypeChange() {
    // Set appropriate defaults when type changes
    if (button.type === 'cc') {
      button.cc = button.cc || 20;
      button.cc_on = button.cc_on || 127;
      button.cc_off = button.cc_off || 0;
    } else if (button.type === 'note') {
      button.note = button.note || 60;
      button.velocity_on = button.velocity_on || 127;
      button.velocity_off = button.velocity_off || 0;
    } else if (button.type === 'pc') {
      button.program = button.program || 0;
    } else if (button.type === 'pc_inc' || button.type === 'pc_dec') {
      button.pc_step = button.pc_step || 1;
    }
  }
</script>
```

### Step 2.6: Testing

**Test suite updates needed:**

#### File: `tests/test_config.py`

Add tests for all 5 types:

```python
def test_all_message_types():
    """All 5 message types validate correctly."""
    
    # CC type
    cc_btn = validate_button({"type": "cc", "cc": 20})
    assert cc_btn["type"] == "cc"
    assert "cc" in cc_btn
    
    # Note type
    note_btn = validate_button({"type": "note", "note": 60})
    assert note_btn["type"] == "note"
    assert "note" in note_btn
    
    # PC type
    pc_btn = validate_button({"type": "pc", "program": 5})
    assert pc_btn["type"] == "pc"
    assert "program" in pc_btn
    
    # PC increment
    pc_inc_btn = validate_button({"type": "pc_inc", "pc_step": 1})
    assert pc_inc_btn["type"] == "pc_inc"
    assert "pc_step" in pc_inc_btn
    
    # PC decrement
    pc_dec_btn = validate_button({"type": "pc_dec", "pc_step": 5})
    assert pc_dec_btn["type"] == "pc_dec"
    assert "pc_step" in pc_dec_btn


def test_types_with_keytimes():
    """All types work with keytimes."""
    for msg_type in ["cc", "note", "pc", "pc_inc", "pc_dec"]:
        btn = validate_button({
            "type": msg_type,
            "keytimes": 3,
            "states": [{}, {}, {}]
        })
        assert btn["keytimes"] == 3
        assert len(btn["states"]) == 3
```

**Manual test checklist:**

- [ ] GUI loads without errors
- [ ] Type selector shows all 5 options
- [ ] Switching types shows correct input fields
- [ ] Config saves with all types
- [ ] Firmware loads config successfully
- [ ] Each type sends correct MIDI messages
- [ ] Keytimes work with each type
- [ ] Toggle/momentary modes work (where applicable)
- [ ] Bidirectional sync works for CC, Note, PC

### Step 2.7: Documentation Updates

**What @copilot will do:**

Update these docs to reflect unified type system:
- `docs/pc-messages.md` - PC message usage
- `docs/note-messages.md` - Note message usage (if exists from PR #53)
- `README.md` - Feature list
- Example configs showing mixed types

### Step 2.8: Create Pull Request

**For YOU:**

```bash
# Push integration branch
git push origin feature/unified-type-system

# Create PR via GitHub UI or gh CLI
gh pr create \
  --title "Unified Type System: CC, Note, PC, PC_inc, PC_dec" \
  --body "Integrates PR #51 and PR #53 into unified type system with full GUI support. Based on PR #50 ButtonState foundation." \
  --base main
```

**PR description should include:**
- Summary of what's being integrated
- Testing performed
- Breaking changes (if any)
- Migration guide (if needed)

---

## Phase 3: Integration Testing

**Duration:** ~2-3 hours  
**Risk:** LOW - Verification phase

### Step 3.1: Automated Testing

**For YOU:**

```bash
# Checkout integration PR branch
git checkout feature/unified-type-system

# Run full test suite
pytest tests/ -v

# Expected: All tests pass
```

### Step 3.2: GUI Testing

**For YOU:**

```bash
# Build and run GUI Config Editor
cd config-editor
npm install
npm run tauri dev

# Manual testing:
# 1. Load example config
# 2. Create button with each type
# 3. Verify correct fields show
# 4. Save config
# 5. Verify saved JSON is correct
```

### Step 3.3: Hardware Testing

**For YOU:**

```bash
# Deploy to device
./tools/deploy.sh --install

# Test each message type:
# - CC: Toggle on/off, verify LED and host sync
# - Note: Press button, verify Note On/Off sent
# - PC: Press button, verify program change sent
# - PC_inc: Press multiple times, verify increments
# - PC_dec: Press multiple times, verify decrements

# Test keytimes with each type
# Test mixed configs (different types per button)
```

### Step 3.4: Performance Testing

**For YOU:**

Monitor for:
- Firmware startup time (should be similar to before)
- Button response latency (should be <10ms)
- No memory issues or crashes
- No unexpected resets

---

## Phase 4: Merge and Close

**Duration:** ~1 hour  
**Risk:** LOW

### Step 4.1: Final Review

**For YOU:**

- [ ] All tests pass
- [ ] Hardware testing complete
- [ ] Documentation updated
- [ ] No performance regressions
- [ ] Code review complete

### Step 4.2: Merge Integration PR

```bash
git checkout main
git pull origin main
git merge --no-ff feature/unified-type-system
git push origin main
```

### Step 4.3: Close Original PRs

**For YOU:**

Comment on each original PR:

**On PR #50:**
```
✅ Merged to main as part of unified type system integration.
Keytimes feature is now available in main branch.
```

**On PR #51:**
```
✅ Integrated into unified type system (feature/unified-type-system).
PC message support now available with full GUI configuration.
Note: Original PR lacked GUI support; this has been added in integration.
```

**On PR #53:**
```
✅ Integrated into unified type system (feature/unified-type-system).
Note message support now available alongside PC messages.
Thank you @jjeff for this contribution!
```

Then close all three PRs.

### Step 4.4: Create Release (Optional)

**For YOU:**

If this warrants a release:

```bash
# Tag the release
git tag v1.1.0-alpha.1
git push origin v1.1.0-alpha.1

# GitHub Actions will create release automatically
```

---

## Troubleshooting

### If Merge Conflicts Occur

**During Step 2.2:**

```bash
# If cherry-picking causes conflicts
git status  # See conflicted files
# Manually resolve conflicts in each file
git add <resolved-files>
git cherry-pick --continue

# Or abort and try different approach
git cherry-pick --abort
```

**Alternative:** Ask @copilot to create integration PR from scratch.

### If Tests Fail

**During Step 3.1:**

1. Identify failing test
2. Check if it's new functionality or regression
3. Fix the issue
4. Re-run tests
5. If stuck, ask @copilot for help with specific test failure

### If Hardware Testing Reveals Issues

**During Step 3.3:**

1. Document the issue clearly
2. Check firmware logs via serial console
3. Test on different device if available
4. Ask @copilot to investigate specific behavior

---

## What @copilot Can Do vs What YOU Must Do

### @copilot CAN:
- ✅ Create integration branch and PR
- ✅ Write unified validation function
- ✅ Update ButtonState class
- ✅ Implement message sending logic
- ✅ Update GUI components
- ✅ Write and update tests
- ✅ Update documentation
- ✅ Resolve merge conflicts (with guidance)

### YOU MUST:
- ⚠️ Review and approve code changes
- ⚠️ Perform hardware testing on physical devices
- ⚠️ Test GUI Config Editor end-to-end
- ⚠️ Make final merge decisions
- ⚠️ Coordinate with @jjeff
- ⚠️ Close original PRs
- ⚠️ Create releases

---

## Timeline Summary

| Phase | Duration | Who |
|-------|----------|-----|
| Phase 1: Merge PR #50 | 2 hours | YOU (with @copilot review) |
| Phase 2: Create Integration | 8-10 hours | @copilot (with YOUR review) |
| Phase 3: Testing | 2-3 hours | YOU (with @copilot support) |
| Phase 4: Merge & Close | 1 hour | YOU |
| **TOTAL** | **13-16 hours** | **Collaborative** |

---

## Risk Mitigation

### Keep Working State
- Each phase leaves code in working state
- Can pause between phases
- Easy to roll back if needed

### Incremental Testing
- Test after each phase
- Catch issues early
- Reduce debugging complexity

### Clear Communication
- Keep @jjeff informed
- Document decisions
- Update PRs with status

---

## Success Criteria

Integration is successful when:

- ✅ All 5 message types work (CC, Note, PC, PC_inc, PC_dec)
- ✅ GUI supports all types with appropriate fields
- ✅ Keytimes work with all types
- ✅ All automated tests pass
- ✅ Hardware testing shows no regressions
- ✅ Documentation is complete
- ✅ No performance issues
- ✅ Original PRs are closed
- ✅ Main branch is stable

---

## Next Steps

**Immediate:**
1. Review this guide
2. Ask questions if anything is unclear
3. Decide when to start Phase 1

**To start Phase 1:**
```
@copilot review PR #50 and let me know if it's ready to merge
```

**To start Phase 2:**
```
@copilot create the unified type system integration PR based on docs/pr-integration-step-by-step.md
```

---

## Questions or Issues?

If you encounter problems or need clarification:
- Tag @copilot with specific questions
- Reference this guide and specific step number
- Provide error messages or logs if applicable

**Example:**
```
@copilot I'm at Step 2.4 and seeing this error in validate_button():
<error message>
How should I fix this?
```
