# Program Change (PC) MIDI Message Configuration

This document describes how to configure buttons to send Program Change (PC) MIDI messages.

## Overview

Program Change messages are used to switch between different programs, patches, or presets on MIDI devices. The MIDI Captain firmware supports three types of PC message modes:

1. **`"pc"`** - Send a specific program number
2. **`"pc_inc"`** - Increment the current program number
3. **`"pc_dec"`** - Decrement the current program number

## Configuration

### Basic Program Change

To configure a button to send a specific program number, use `"type": "pc"`:

```json
{
  "label": "PATCH1",
  "type": "pc",
  "program": 0,
  "channel": 0,
  "color": "green"
}
```

**Fields:**
- `type`: Must be `"pc"`
- `program`: Program number to send (0-127)
- `channel`: MIDI channel (0-15 = MIDI Ch 1-16), inherits from `global_channel` if not specified
- `label`: Button label displayed on screen
- `color`: Button LED color

### Increment/Decrement Program Change

For inc/dec modes, the device tracks the current program number internally:

```json
{
  "label": "PC+",
  "type": "pc_inc",
  "pc_step": 1,
  "channel": 0,
  "color": "orange"
}
```

```json
{
  "label": "PC-",
  "type": "pc_dec",
  "pc_step": 1,
  "channel": 0,
  "color": "cyan"
}
```

**Fields:**
- `type`: Either `"pc_inc"` (increment) or `"pc_dec"` (decrement)
- `pc_step`: Step value for increment/decrement (default: 1)
- `channel`: MIDI channel (0-15 = MIDI Ch 1-16)
- `label`: Button label
- `color`: Button LED color

### Step Values

The `pc_step` parameter allows you to increment or decrement by any value:

```json
{"label": "PC+5", "type": "pc_inc", "pc_step": 5, "color": "white"}
{"label": "PC-10", "type": "pc_dec", "pc_step": 10, "color": "red"}
```

Program numbers are automatically clamped to the valid range (0-127):
- Increment stops at 127 (won't wrap)
- Decrement stops at 0 (won't wrap)

## Bidirectional Sync

When the device receives a PC message from the host on a given channel, it updates the internal PC value for all inc/dec buttons on that channel. This allows the host to set the current program externally.

Example flow:
1. Device sends PC 5 via inc/dec button
2. Host receives and processes it
3. Host sends PC 10 back to device
4. Device updates internal state to 10
5. Next inc press sends PC 11

## Behavior Notes

### Visual Feedback

PC buttons briefly light up when pressed to provide visual feedback, then turn off. This is different from toggle-mode CC buttons which stay lit to show on/off state.

### Mode Compatibility

The `"mode"` field ("toggle" or "momentary") is ignored for PC message types - PC messages are always sent on press only.

### Mixing CC and PC

You can mix CC and PC message types in the same configuration:

```json
"buttons": [
  {"label": "CC20", "type": "cc", "cc": 20, "color": "red"},
  {"label": "PATCH1", "type": "pc", "program": 0, "color": "green"},
  {"label": "PC+", "type": "pc_inc", "pc_step": 1, "color": "orange"}
]
```

## Complete Example

See `config-example-pc.json` for a full working example with a mix of PC and CC buttons.

## MIDI Protocol Details

- **Standard PC Message**: Status byte `0xCn` (where n = MIDI channel 0-15) followed by program number (0-127)
- **Channel Range**: 0-15 (displayed as MIDI Ch 1-16 in logs)
- **Program Range**: 0-127 (128 total programs)
- **Send Behavior**: Messages sent on button press only (not on release)
