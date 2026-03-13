# Multi-Command Per Action Design Document

**Date:** 2026-03-13  
**Status:** Planning  
**Branch:** `feature/multi-command-per-action`

## Summary

Allow a single button action (press, release, long_press, long_release) to trigger multiple MIDI commands in sequence. This brings feature parity with OEM MIDI Captain Super Mode and enables complex macros.

## Motivation

The OEM firmware allows each action phase to execute several commands. Current firmware limitation to one command per action restricts advanced workflows like:
- Changing amp channel and delay preset simultaneously
- Selecting scene and toggling expression mapping  
- Selecting preset and resetting tap tempo
- Controlling multiple devices from a single footswitch

## Current Architecture

### Firmware (`firmware/dev/code.py`)

**Existing Functions:**
- `_send_action_from_cfg(action_cfg, btn_num, idx)` - sends a single MIDI command from config dict
- `handle_switches()` - main button press/release loop with inline command dispatch
- Long-press/long-release already use `_send_action_from_cfg()`
- Short press/release have inline MIDI dispatch mixed with state management

**Current Config Structure:**
```json
{
  "label": "DRIVE",
  "type": "cc",
  "cc": 20,
  "cc_on": 127,
  "long_press": {
    "type": "pc",
    "program": 5
  }
}
```

### Config Editor (`config-editor/`)

**TypeScript Types (`src/lib/types.ts`):**
- `ButtonConfig` interface with optional `long_press` and `long_release` objects
- Single command per action event

**Rust Structs (`src-tauri/src/config.rs`):**
- Mirror TypeScript types
- Serde serialization/deserialization

## Proposed Design

### 1. Config Schema Changes

#### New Event-Based Structure

Replace the current type-centric config with event-based arrays:

```json
{
  "label": "DRIVE",
  "press": [
    { "type": "cc", "cc": 20, "value": 127, "channel": 0 },
    { "type": "pc", "program": 5, "channel": 0 }
  ],
  "release": [
    { "type": "cc", "cc": 20, "value": 0, "channel": 0 }
  ],
  "long_press": [
    { "type": "cc", "cc": 40, "value": 127, "channel": 0 },
    { "type": "cc", "cc": 41, "value": 127, "channel": 0 }
  ],
  "long_release": [
    { "type": "cc", "cc": 40, "value": 0, "channel": 0 }
  ]
}
```

#### Command Object Structure

Each command is a dict with:
- `type`: `'cc' | 'note' | 'pc' | 'pc_inc' | 'pc_dec'`
- `channel`: 0-15 (optional, defaults to global_channel)
- Type-specific fields:
  - **CC**: `cc`, `value` (or `cc_on`/`cc_off` for compatibility)
  - **Note**: `note`, `velocity` (or `velocity_on`/`velocity_off`)
  - **PC**: `program`
  - **PC Inc/Dec**: `pc_step`

#### Backwards Compatibility

Support both old and new formats:

**Old format (single type + fields):**
```json
{
  "label": "DRIVE",
  "type": "cc",
  "cc": 20,
  "cc_on": 127,
  "cc_off": 0,
  "mode": "toggle"
}
```

**Internally converted to:**
```json
{
  "label": "DRIVE",
  "mode": "toggle",
  "press": [{ "type": "cc", "cc": 20, "value": 127 }],
  "release": [{ "type": "cc", "cc": 20, "value": 0 }]
}
```

Legacy `long_press` object format also supported and converted to array.

### 2. Firmware Changes

#### Updated `_send_action_from_cfg()` Function

```python
def _send_action_from_cfg(action_cfg, btn_num, idx):
    """Send MIDI from action config (single dict or list of dicts).
    
    Supports:
    - Single command: {"type":"cc","cc":20,"value":127}
    - Multiple commands: [{"type":"cc",...}, {"type":"pc",...}]
    """
    # Normalize to list
    if isinstance(action_cfg, dict):
        commands = [action_cfg]
    elif isinstance(action_cfg, list):
        commands = action_cfg
    else:
        return
    
    # Execute each command in sequence
    for cmd in commands:
        if not isinstance(cmd, dict):
            print(f"[WARN] Invalid command in action (button {btn_num}): {cmd}")
            continue
        
        msg_type = cmd.get("type", "cc")
        channel = cmd.get("channel", 0)
        
        try:
            if msg_type == "cc":
                cc = cmd.get("cc", 20 + idx)
                val = cmd.get("value", cmd.get("cc_on", 127))
                midi.send(ControlChange(cc, val, channel=channel))
                print(f"[MIDI TX] Ch{channel+1} CC{cc}={val} (switch {btn_num})")
                
            elif msg_type == "note":
                note = cmd.get("note", 60)
                vel = cmd.get("velocity", cmd.get("velocity_on", 127))
                midi.send(NoteOn(note, vel, channel=channel))
                print(f"[MIDI TX] Ch{channel+1} NoteOn{note} vel{vel} (switch {btn_num})")
                
            elif msg_type == "pc":
                program = cmd.get("program", 0)
                midi.send(ProgramChange(program, channel=channel))
                print(f"[MIDI TX] Ch{channel+1} PC{program} (switch {btn_num})")
                
            elif msg_type == "pc_inc":
                step = cmd.get("pc_step", 1)
                pc_values[channel] = clamp_pc_value(pc_values[channel] + step)
                midi.send(ProgramChange(pc_values[channel], channel=channel))
                print(f"[MIDI TX] Ch{channel+1} PC{pc_values[channel]} +{step} (switch {btn_num})")
                
            elif msg_type == "pc_dec":
                step = cmd.get("pc_step", 1)
                pc_values[channel] = clamp_pc_value(pc_values[channel] - step)
                midi.send(ProgramChange(pc_values[channel], channel=channel))
                print(f"[MIDI TX] Ch{channel+1} PC{pc_values[channel]} -{step} (switch {btn_num})")
            else:
                print(f"[WARN] Unknown command type '{msg_type}' (button {btn_num})")
                
        except Exception as e:
            print(f"[ERROR] Failed to send command (button {btn_num}): {e}")
            # Continue to next command
            continue
```

#### Refactor `handle_switches()` to Use Event Arrays

Current inline dispatch code needs to be extracted into reusable event handlers:

1. **Extract press event builders** - functions that construct press/release command arrays based on mode (toggle/momentary/select/tap)
2. **Unify dispatch path** - all events (press/release/long_press/long_release) use `_send_action_from_cfg()`
3. **State management separation** - keep LED/display updates separate from command dispatch

#### Config Loading with Backwards Compatibility

In `core/config.py`, add migration logic:

```python
def normalize_button_config(btn):
    """Convert old single-type config to new event-array format."""
    # If already has 'press' key, assume new format
    if 'press' in btn or 'release' in btn:
        return btn
    
    # Old format: convert based on type and mode
    msg_type = btn.get('type', 'cc')
    mode = btn.get('mode', 'toggle')
    channel = btn.get('channel', 0)
    
    press_cmds = []
    release_cmds = []
    
    if msg_type == 'cc':
        cc = btn.get('cc', 0)
        cc_on = btn.get('cc_on', 127)
        cc_off = btn.get('cc_off', 0)
        press_cmds = [{'type': 'cc', 'cc': cc, 'value': cc_on, 'channel': channel}]
        if mode == 'momentary':
            release_cmds = [{'type': 'cc', 'cc': cc, 'value': cc_off, 'channel': channel}]
        # toggle mode: release doesn't send (state change on press only)
        
    elif msg_type == 'note':
        note = btn.get('note', 60)
        vel_on = btn.get('velocity_on', 127)
        vel_off = btn.get('velocity_off', 0)
        press_cmds = [{'type': 'note', 'note': note, 'velocity': vel_on, 'channel': channel}]
        if mode == 'momentary':
            release_cmds = [{'type': 'note', 'note': note, 'velocity': vel_off, 'channel': channel}]
            
    elif msg_type == 'pc':
        program = btn.get('program', 0)
        press_cmds = [{'type': 'pc', 'program': program, 'channel': channel}]
        
    # ... handle pc_inc, pc_dec
    
    # Migrate long_press/long_release if present
    if 'long_press' in btn and isinstance(btn['long_press'], dict):
        btn['long_press'] = [btn['long_press']]
    if 'long_release' in btn and isinstance(btn['long_release'], dict):
        btn['long_release'] = [btn['long_release']]
    
    btn['press'] = press_cmds
    if release_cmds:
        btn['release'] = release_cmds
    
    return btn
```

### 3. Config Editor Changes

#### TypeScript Type Updates

```typescript
// Command structure for multi-command arrays
export interface MidiCommand {
  type: 'cc' | 'note' | 'pc' | 'pc_inc' | 'pc_dec';
  channel?: number;  // 0-15, optional
  // CC fields
  cc?: number;
  value?: number;    // Generic value field (cc_on, velocity_on, etc.)
  // Note fields
  note?: number;
  velocity?: number;
  // PC fields
  program?: number;
  // PC inc/dec
  pc_step?: number;
}

export interface ButtonConfig {
  label: string;
  color: ButtonColor;
  mode?: ButtonMode;
  off_mode?: OffMode;
  
  // Event-based command arrays (new format)
  press?: MidiCommand[];
  release?: MidiCommand[];
  long_press?: MidiCommand[];
  long_release?: MidiCommand[];
  
  // Legacy fields for backwards compatibility (optional, auto-migrated)
  type?: MessageType;
  channel?: number;
  cc?: number;
  cc_on?: number;
  cc_off?: number;
  note?: number;
  velocity_on?: number;
  velocity_off?: number;
  program?: number;
  pc_step?: number;
  flash_ms?: number;
  
  // Other fields unchanged
  keytimes?: number;
  states?: StateOverride[];
  select_group?: string;
  default_selected?: boolean;
  led_mode?: 'tap';
  tap_rate_ms?: number;
}
```

#### Rust Config Struct Updates

Mirror TypeScript changes in `config-editor/src-tauri/src/config.rs`:

```rust
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MidiCommand {
    #[serde(rename = "type")]
    pub command_type: String,  // "cc", "note", "pc", "pc_inc", "pc_dec"
    #[serde(skip_serializing_if = "Option::is_none")]
    pub channel: Option<u8>,   // 0-15
    #[serde(skip_serializing_if = "Option::is_none")]
    pub cc: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub value: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub note: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub velocity: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub program: Option<u8>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub pc_step: Option<u8>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ButtonConfig {
    pub label: String,
    pub color: String,
    // Event arrays (new format)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub press: Option<Vec<MidiCommand>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub release: Option<Vec<MidiCommand>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub long_press: Option<Vec<MidiCommand>>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub long_release: Option<Vec<MidiCommand>>,
    
    // Legacy fields (backwards compat)
    #[serde(skip_serializing_if = "Option::is_none")]
    pub r#type: Option<String>,
    #[serde(skip_serializing_if = "Option::is_none")]
    pub channel: Option<u8>,
    // ... other legacy fields
}
```

#### UI Component for Multi-Command Editing

Add new component: `ButtonCommandsEditor.svelte`

```svelte
<script lang="ts">
  import type { MidiCommand } from '$lib/types';
  
  interface Props {
    label: string;  // "Press", "Release", "Long Press", "Long Release"
    commands: MidiCommand[];
    onChange: (commands: MidiCommand[]) => void;
  }
  
  let { label, commands, onChange }: Props = $props();
  
  function addCommand() {
    onChange([...commands, { type: 'cc', cc: 20, value: 127, channel: 0 }]);
  }
  
  function removeCommand(index: number) {
    onChange(commands.filter((_, i) => i !== index));
  }
  
  function updateCommand(index: number, field: string, value: any) {
    const updated = [...commands];
    updated[index] = { ...updated[index], [field]: value };
    onChange(updated);
  }
</script>

<div class="commands-section">
  <div class="section-header">
    <span>{label}</span>
    <button class="add-btn" onclick={addCommand}>+ Add Command</button>
  </div>
  
  {#each commands as cmd, i}
    <div class="command-row">
      <span class="command-index">{i + 1}.</span>
      <select value={cmd.type} onchange={(e) => updateCommand(i, 'type', e.currentTarget.value)}>
        <option value="cc">CC</option>
        <option value="note">Note</option>
        <option value="pc">PC</option>
        <option value="pc_inc">PC+</option>
        <option value="pc_dec">PC-</option>
      </select>
      
      {#if cmd.type === 'cc'}
        <input type="number" placeholder="CC" min="0" max="127"
          value={cmd.cc} onchange={(e) => updateCommand(i, 'cc', parseInt(e.currentTarget.value))} />
        <input type="number" placeholder="Value" min="0" max="127"
          value={cmd.value} onchange={(e) => updateCommand(i, 'value', parseInt(e.currentTarget.value))} />
      {:else if cmd.type === 'note'}
        <input type="number" placeholder="Note" min="0" max="127"
          value={cmd.note} onchange={(e) => updateCommand(i, 'note', parseInt(e.currentTarget.value))} />
        <input type="number" placeholder="Velocity" min="0" max="127"
          value={cmd.velocity} onchange={(e) => updateCommand(i, 'velocity', parseInt(e.currentTarget.value))} />
      {:else if cmd.type === 'pc'}
        <input type="number" placeholder="Program" min="0" max="127"
          value={cmd.program} onchange={(e) => updateCommand(i, 'program', parseInt(e.currentTarget.value))} />
      {/if}
      
      <input type="number" placeholder="Ch" min="1" max="16"
        value={(cmd.channel ?? 0) + 1} onchange={(e) => updateCommand(i, 'channel', parseInt(e.currentTarget.value) - 1)} />
      
      <button class="remove-btn" onclick={() => removeCommand(i)}>✕</button>
    </div>
  {/each}
</div>
```

Integrate into `ButtonSettingsPanel.svelte` with collapsible sections for each event type.

## Implementation Phases

### Phase 1: Firmware Core (MVP)
- [x] Analyze current code structure
- [ ] Update `_send_action_from_cfg()` to handle arrays
- [ ] Add `normalize_button_config()` migration in `core/config.py`
- [ ] Extract press/release command builders
- [ ] Refactor `handle_switches()` to use event arrays
- [ ] Test with existing single-command configs
- [ ] Test with new multi-command configs

### Phase 2: Config Editor Backend
- [ ] Update TypeScript types (`MidiCommand`, `ButtonConfig`)
- [ ] Update Rust structs and validation
- [ ] Add round-trip tests for new format
- [ ] Add migration logic for old→new format on load

### Phase 3: Config Editor UI
- [ ] Create `ButtonCommandsEditor.svelte` component
- [ ] Integrate into `ButtonSettingsPanel.svelte`
- [ ] Add UI toggle for "simple" vs "advanced" mode
- [ ] Simple mode: single command per event (like current UI)
- [ ] Advanced mode: multi-command editor
- [ ] Update form validation

### Phase 4: Testing & Docs
- [ ] Test on STD10 hardware
- [ ] Test on Mini6 hardware
- [ ] Test backwards compatibility with existing configs
- [ ] Add example configs to `firmware/dev/`
- [ ] Update `AGENTS.md` with new schema
- [ ] Update `README.md` with examples

## Example Configs

### Example 1: Dual Device Control
```json
{
  "label": "BOTH",
  "mode": "toggle",
  "press": [
    { "type": "cc", "cc": 20, "value": 127, "channel": 0 },
    { "type": "cc", "cc": 30, "value": 127, "channel": 1 }
  ],
  "release": [
    { "type": "cc", "cc": 20, "value": 0, "channel": 0 },
    { "type": "cc", "cc": 30, "value": 0, "channel": 1 }
  ]
}
```

### Example 2: Scene Change + Tempo Reset
```json
{
  "label": "CLEAN",
  "press": [
    { "type": "pc", "program": 2, "channel": 0 },
    { "type": "cc", "cc": 80, "value": 120, "channel": 0 }
  ]
}
```

### Example 3: Long-Press Macro
```json
{
  "label": "PANIC",
  "press": [
    { "type": "cc", "cc": 123, "value": 0, "channel": 0 }
  ],
  "long_press": [
    { "type": "cc", "cc": 123, "value": 0, "channel": 0 },
    { "type": "cc", "cc": 123, "value": 0, "channel": 1 },
    { "type": "cc", "cc": 123, "value": 0, "channel": 2 },
    { "type": "pc", "program": 0, "channel": 0 }
  ]
}
```

## Acceptance Criteria

- [ ] Button events can trigger 1-N commands (tested with 1, 2, 5, 10 commands)
- [ ] Commands execute in defined order
- [ ] Existing single-command configs work without modification
- [ ] Invalid commands skip gracefully with warning (no crash)
- [ ] Works with all button modes (toggle, momentary, select, tap)
- [ ] Works with long-press/long-release
- [ ] Works with keytimes cycling
- [ ] Works with select groups
- [ ] GUI provides intuitive multi-command editing
- [ ] Config validation catches malformed commands
- [ ] Round-trip save/load preserves command order

## Open Questions

1. **Delay between commands?** Should we add optional `delay_ms` field per command for sequential timing?
   - **Decision:** Not in MVP. Can add later if needed.

2. **PC flash feedback with multi-command?** How should LED flash work when multiple PC commands in one event?
   - **Decision:** Flash only once at end of command sequence if any command is PC type.

3. **Conditional commands?** E.g., "send CC20=127 only if button 2 is on"
   - **Decision:** Out of scope for this feature. Would require expression language.

4. **Maximum commands per event?** Should there be a limit?
   - **Decision:** Soft limit of 10 commands per event for UI sanity. Firmware has no hard limit (within memory constraints).

## Performance Considerations

- Commands execute synchronously in main loop (non-blocking to hardware)
- Typical command takes <1ms to send
- 10 commands = ~10ms total
- Acceptable for button press (human reaction time ~100-200ms)
- No sleep/delay between commands in MVP

## Backwards Compatibility Strategy

1. **Config loading:** Auto-detect old vs new format
   - If button has `type` field but no `press` → old format, migrate
   - If button has `press`/`release` → new format, use directly
2. **GUI:** Show migration prompt on first load of old config
3. **Firmware:** Accept both formats, normalize at load time
4. **Validation:** Warn about deprecated fields, don't error

## Success Metrics

- Zero breaking changes to existing configs
- <5% performance overhead for single-command configs
- GUI supports both simple and advanced editing modes
- End-to-end latency <50ms for 5-command macro
