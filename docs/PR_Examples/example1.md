# Title: Add Per-Switch MIDI Channel and CC Value Configuration

# Description:

This PR adds comprehensive MIDI channel and CC value configuration, enabling independent control of MIDI routing and CC ranges for each button, encoder, and expression pedal.

# Features Added

## Global MIDI Channel Configuration

- Set a default MIDI channel (1-16) that applies to all controls
- Individual controls can override the global setting
- Simplifies multi-device setups where most controls use the same channel

## Per-Control Channel Override

- Each button can specify its own MIDI channel (1-16)
- Encoder, encoder push, and expression pedals also support channel configuration
- Enables routing different controls to different devices or software instances

## Custom CC Values

- Configure custom ON and OFF values for each button and encoder push (not limited to 127/0)
- `cc_on`: CC value sent when button/encoder push is activated (default: 127)
- `cc_off`: CC value sent when button/encoder push is deactivated (default: 0)
- Supports devices that expect specific CC value ranges

## Bidirectional MIDI with Channel Filtering

- Incoming MIDI messages are filtered by both CC number and channel
- Prevents cross-talk when using same CC numbers on different channels
- Host can control LED states per-channel

### Configuration

The GUI Config Editor supports all of the new functionality.

Under the hood JSON Schema:

```json
{
  "global_channel": 0,
  "buttons": [
    {
      "label": "REVERB",
      "cc": 20,
      "color": "blue"
    },
    {
      "label": "DELAY", 
      "cc": 20,
      "channel": 1,
      "cc_on": 100,
      "cc_off": 20,
      "color": "green"
    }
  ],
  "encoder": {
    "enabled": true,
    "cc": 11,
    "channel": 0,
    "push": {
      "enabled": true,
      "cc": 14,
      "mode": "momentary",
      "channel": 0,
      "cc_on": 127,
      "cc_off": 0
    }
  }
}
```


In this example:

- Button 1 uses global channel (Ch 1), sends CC20 with values 127/0
- Button 2 overrides to Ch 2, sends CC20 with values 100/20
- Both buttons can coexist without conflict

ℹ️ Note: Channels are stored as 0-15 in JSON (MIDI protocol standard) but displayed as 1-16 in the GUI and serial output for user convenience.

## GUI Configuration Editor

- Device Settings: Global MIDI Channel input (1-16)
- Button Configuration: Channel, ON value, OFF value inputs per button
- Encoder Configuration: Channel inputs for encoder rotation and encoder push button, plus ON/OFF values for push
- Expression Configuration: Channel input for each expression pedal
- Tooltips: Show effective channel (inherited or explicit)
- Validation: Ensures channels are 1-16, CC values are 0-127

## Implementation Details

### Backend (CircuitPython Firmware)

- `core/config.py`: Validates and applies defaults with global channel inheritance
- `code.py`: Uses channel parameter for all `ControlChange()` messages
- `code.py`: Filters incoming MIDI by matching both CC and channel
- Serial output shows channel numbers and values: `[MIDI TX] Ch2 CC20=100 (switch 1, toggle), [ENCODER] Ch1 CC11=65`

### Frontend (Tauri Config Editor)

- Rust backend (`config.rs`): Struct definitions with channel fields, validation
- Svelte components: Input fields with 1-16 display, 0-15 storage conversion
- TypeScript types: Updated interfaces with channel/CC value fields

#### Display Convention

- User-facing: Channels displayed as 1-16 in GUI, validation messages, serial output
- Internal storage: Channels stored as 0-15 in JSON for MIDI protocol compatibility
- Conversion: `Display = stored + 1`, `Storage = display - 1`


## Use Cases

### Multi-Device Control

Control multiple devices without CC conflicts:

- Guitar pedal on Ch 1
- Synthesizer on Ch 2
- DAW on Ch 3

### Multi-Instance Setup

Route to different tracks, plugins, or applications:

- Logic Pro on Ch 1
- Ableton on Ch 2
- Gig Performer on Ch 3
- Fine-Grained CC Control

### Send specific CC values for device requirements:

- Device expects 0-100 range: set `cc_on`: 100, `cc_off`: 0
- Device expects 20-80 range: set `cc_on`: 80, `cc_off`: 20
- Different switches on same CC/different channels with different value ranges

## Backward Compatibility

✅ Fully backward compatible

- All new fields are optional
- Existing configs work without modification

### Defaults

`global_channel: 0, channel: inherits global, cc_on: 127, cc_off: 0`

## Testing

✅ All unit tests pass (30 tests)
✅ Python syntax validation passes
✅ Config validation with new fields
✅ Channel inheritance and override logic
✅ GUI displays 1-16, stores 0-15 correctly

## Changes

**Config schema**
- `global_channel` (0-15): default MIDI channel for all controls
- Per-control `channel`: overrides global
- Per-button/encoder-push `cc_on`/`cc_off`: custom CC values (default 127/0)

**Backend** (`firmware/dev/`)
- `core/config.py`: validate and default new fields, inherit global channel
- `code.py`: pass `channel` to `ControlChange()`, filter incoming MIDI by channel

**Frontend** (`config-editor/`)
- Added channel/ON/OFF inputs to all control sections
- Display channels as 1-16, store as 0-15
- Channel input shows placeholder with effective channel (inherited or explicit)

**Example**
```json
{
  "global_channel": 0,
  "buttons": [
    {"label": "VERB", "cc": 20, "color": "blue"},
    {"label": "DELAY", "cc": 20, "channel": 1, "cc_on": 100, "cc_off": 20, "color": "green"}
  ]
}
```

Button 1 sends CC20=127/0 on Ch1 (global). Button 2 sends CC20=100/20 on Ch2 (override). Same CC number, different channels, no interference.

All fields optional. Existing configs unchanged.

<!-- START COPILOT ORIGINAL PROMPT -->



<details>
<summary>Original prompt</summary>

> 
> ----
> 
> *This section details on the original issue you should resolve*
> 
> <issue_title>Add Channel and CC Value config for any switch</issue_title>
> <issue_description># Current State
> 
> Switches can be set to any CC Number, but only CC values 0 (OFF) and 127 (ON) are supported, on MIDI Channel 1 only.
> 
> # Desired Outcome
> 
> 1. Any switch can be set to any MIDI Channel, CC Number, and CC Value.
> 1. The configuration options are added to the existing options in the JSON config file and the GUI config editor.
> 1. A "global channel" config option is available: this sets all switches to the chosen channel.
> 1. Any switch can override the global channel setting with its own channel setting
>
> </issue_description>
> 
> ## Comments on the Issue (you are @copilot in this section)
> 
> <comments>
> </comments>
> 


</details>



<!-- START COPILOT CODING AGENT SUFFIX -->

- Fixes MC-Music-Workshop/midi-captain-max#30

<!-- START COPILOT CODING AGENT TIPS -->
---

💬 We'd love your input! Share your thoughts on Copilot coding agent in our [2 minute survey](https://gh.io/copilot-coding-agent-survey).
