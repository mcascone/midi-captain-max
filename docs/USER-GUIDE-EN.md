# MIDI Captain MAX - Config Editor User Guide

**Version:** 1.0  
**Language:** English

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Main Interface](#main-interface)
4. [Device Settings](#device-settings)
5. [Button Configuration](#button-configuration)
6. [Device Profiles](#device-profiles)
7. [Multi-State Buttons (Keytimes)](#multi-state-buttons-keytimes)
8. [Encoder Configuration](#encoder-configuration)
9. [Expression Pedals](#expression-pedals)
10. [Display Settings](#display-settings)
11. [Keyboard Shortcuts](#keyboard-shortcuts)
12. [Tips and Best Practices](#tips-and-best-practices)
13. [Troubleshooting](#troubleshooting)

---

## Introduction

The **MIDI Captain MAX Config Editor** is a desktop application that allows you to customize your Paint Audio MIDI Captain foot controller (STD10 or Mini6 models). With this editor, you can:

- Configure button labels, colors, and MIDI commands
- Set up complex multi-command actions
- Use device profiles for popular gear (Quad Cortex, Helix, Kemper, etc.)
- Configure encoders and expression pedals
- Customize the device display
- Work in development or performance mode

---

## Getting Started

### Connecting Your Device

1. **Connect** your MIDI Captain to your computer via USB
2. **Enable USB Drive Mode** (if not in dev mode):
   - Power off the device
   - Hold **Switch 1** (top-left button)
   - Power on while holding Switch 1
   - Release when the USB drive appears
3. The editor will automatically detect your device

### First Launch

When you launch the editor:

1. Your connected device(s) will appear in the **device dropdown** at the top
2. Select your device to load its current configuration
3. The device layout will appear showing all buttons
4. Any unsaved changes will be marked with a yellow dot indicator

---

## Main Interface

The editor is divided into three main areas:

### Left Panel - Device Overview

- **Device Layout**: Interactive visual representation of your foot controller
  - Click any button to select it for editing
  - Button colors and labels reflect current configuration
  - Multi-command buttons show badge indicators
  - LED preview shows button appearance
- **Device Grid** (optional view): List-style view of all buttons
- **Status Bar**: Shows save status and validation errors

### Center Panel - Button Settings

Detailed configuration for the selected button:

- **Button ID & Label**: Identify and name your button
- **Color**: Choose LED color from preset palette
- **Behavior**: Configure mode and channel settings
- **Actions**: Set up MIDI commands for different events
- **State Overrides**: Configure multi-state behavior (keytimes)
- **Advanced Settings**: Select groups, off mode, dim brightness

### Right Side - Global Settings

- Device type and general settings
- USB drive name
- Development mode toggle
- Display text size settings

### Toolbar

- **Undo/Redo**: Navigate configuration history (⌘Z / ⌘⇧Z)
- **View JSON**: Inspect raw configuration
- **Save**: Write changes to device (⌘S)
- **Reload**: Discard changes and reload from device
- **Reset**: Restore factory default configuration

---

## Device Settings

### Device Type

Select your hardware model:
- **STD10**: 10-button foot controller with encoder
- **Mini6**: 6-button compact controller

### Global MIDI Channel

Default MIDI channel for all buttons (1-16). Individual buttons can override this.

### USB Drive Name

Customize the volume name when USB drive mode is enabled:
- Maximum 11 characters
- Only letters, numbers, and underscores
- Automatically converted to uppercase

**Example**: `MIDICAPTAIN`, `MYCONTROL`, `FOOT_SW_01`

### Development Mode

- **OFF** (Performance Mode): USB drive hidden by default. Hold Switch 1 during power-on to enable temporarily.
- **ON** (Dev Mode): USB drive always mounts automatically. Useful during configuration but may impact boot time.

---

## Button Configuration

### Button Identity

**Button ID**  
Unique identifier for referencing this button (e.g., `btn1`, `scene_a`)

**Label**  
Display name shown on device screen (max 6 characters)

**Color**  
LED color from preset palette:
- Red, Green, Blue
- Yellow, Cyan, Magenta
- Orange, Purple, White

### Behavior Settings

#### Mode

- **Toggle**: Button alternates between ON and OFF states
  - Press → turns ON, sends Press commands
  - Press again → turns OFF, sends Release commands
  - LED stays lit when ON

- **Momentary**: Button is ON only while held
  - Press → turns ON, sends Press commands
  - Release → turns OFF, sends Release commands
  - Like a sustain pedal

- **Select**: Button turns ON when pressed, stays ON
  - Used with select groups for radio-button behavior
  - Press → turns ON, sends Press commands
  - Other buttons in same group turn OFF automatically

- **Tap**: Advanced mode for tap tempo (future feature)

#### Off Mode

Controls LED appearance when button is OFF:
- **Dim**: LED visible at reduced brightness (configurable %)
- **Off**: LED completely dark

#### Dim Brightness

When Off Mode is "Dim", set the brightness percentage (0-100%):
- **0%**: Completely off
- **15%**: Default subtle glow
- **50%**: Half brightness
- **100%**: Full brightness (appears always on)

Real-time preview shows the dimmed color next to the slider.

#### Select Group

Group multiple buttons for radio-button behavior:
- Assign same group name to related buttons
- When one button turns ON, others in group turn OFF
- Deselected buttons send their Release commands
- Useful for: scene selection, mode switching

**Example**: Group buttons 1-4 as `"scenes"`. Pressing button 2 turns OFF buttons 1, 3, and 4.

#### Default Selected

Mark this button to activate on device startup:
- Button turns ON when device boots
- Sends Press commands at startup
- Only one button per select group should be default

### Channel Override

Override global MIDI channel for this button (1-16). Leave blank to use global channel.

---

## Actions (MIDI Commands)

Each button can send different MIDI commands for four events:

### Event Types

1. **Press**: Sent when button is pressed
2. **Release**: Sent when button is released (or toggled OFF)
3. **Long Press**: Sent when button is held beyond threshold
4. **Long Release**: Sent when button is released after long press

### Action Sources

#### Profile Action (Recommended)

Use built-in profiles for common devices:
- Select device profile (Quad Cortex, Helix, Kemper, etc.)
- Choose action from dropdown
- MIDI commands auto-configured
- Preview shows resolved MIDI

See [Device Profiles](#device-profiles) section for details.

#### Custom MIDI

Configure MIDI commands manually:

**Multiple Commands Per Event**  
Each event (Press, Release, etc.) can send multiple MIDI commands in sequence.

Click **+ Add Command** to add more commands to an event.

### Command Types

#### Control Change (CC)

Most common MIDI message type.

**Parameters:**
- **Type**: CC
- **Controller**: CC number (0-127)
- **Value**: CC value (0-127)
- **Channel**: MIDI channel (1-16, optional)

**Example**: Send CC 20 with value 127 on channel 1

**Common Uses:**
- Toggle effects (value 127 = on, 0 = off)
- Control parameters (0-127 range)
- Switch scenes/snapshots

#### Note On/Off (Note)

Send MIDI note messages.

**Parameters:**
- **Type**: Note
- **Note**: MIDI note number (0-127)
- **Velocity**: Note velocity (0-127)
- **Channel**: MIDI channel (1-16, optional)

**Note**: Velocity 0 = Note Off, Velocity > 0 = Note On

**Common Uses:**
- Trigger drum pads
- Toggle tuner (some devices)
- Trigger samples

#### Program Change (PC)

Change presets/patches.

**Parameters:**
- **Type**: PC
- **Program**: Program number (0-127)
- **Channel**: MIDI channel (1-16, optional)

**Common Uses:**
- Switch presets
- Change patches
- Select banks

#### Program Change Inc (PC+)

Increment program number by step value.

**Parameters:**
- **Type**: PC Inc
- **Step**: Increment amount (default 1)
- **Channel**: MIDI channel (1-16, optional)

**Common Use**: Next preset/patch button

#### Program Change Dec (PC-)

Decrement program number by step value.

**Parameters:**
- **Type**: PC Dec
- **Step**: Decrement amount (default 1)
- **Channel**: MIDI channel (1-16, optional)

**Common Use**: Previous preset/patch button

### Long Press Threshold

For Long Press commands, set the hold duration in milliseconds:
- Default: **500ms** (half second)
- Range: 100-5000ms
- Only applies to first Long Press command

**Example**: Set 1000ms to require 1-second hold before triggering

### Flash Duration (PC Commands)

For Program Change buttons with no persistent state:
- Set LED flash duration in milliseconds
- Default: **200ms**
- Provides visual feedback for momentary press

---

## Device Profiles

Device profiles simplify configuration by converting high-level actions into MIDI commands.

### Available Profiles

#### Neural DSP Quad Cortex
- Scene A/B/C/D selection
- Stomp and Row bypass
- Tuner control
- Preset navigation

#### Line 6 Helix
- Snapshot selection (1-8)
- Footswitch assignments
- Looper controls
- Tuner toggle

#### Line 6 HX Stomp
- Snapshot selection (1-3)
- Footswitch emulation
- Expression pedal control

#### Kemper Profiler
- Rig selection
- Effect bypass
- Tuner control
- Looper functions

#### Ableton Live (Template)
- Scene launch
- Track mute/solo
- Transport control
- Device control

#### Apple MainStage (Template)
- Patch changes
- Bypass controls
- Expression mapping

### Using Profiles

1. **Select Event**: Choose Press, Release, Long Press, or Long Release
2. **Change Source**: Select "Profile Action"
3. **Choose Device**: Pick target device profile
4. **Select Action**: Choose action from dropdown
5. **Preview MIDI**: View resolved commands
6. **Channel Override**: Optionally override MIDI channel

### Channel Overrides

Each profile action can override its default MIDI channel:
- Leave blank to use profile default
- Set specific channel (1-16) for custom routing

### Combining Profile and Custom Commands

You can mix profile and custom commands in the same event:
- Add profile action
- Click **+ Add Command** 
- Add custom CC, Note, or PC commands
- Commands execute in sequence

### Auto-Detection

When you select a button, the editor shows if existing MIDI commands match a known profile:
- **Badge indicator**: Shows matching profile
- **Tooltip**: Displays detected profile name
- Makes it easy to identify preconfigured buttons

---

## Multi-State Buttons (Keytimes)

Keytimes allow buttons to cycle through multiple states, sending different MIDI commands each time pressed.

### Enabling Keytimes

1. Select a button
2. Find **Keytimes** field under Behavior
3. Set number of states (2-8)
4. State tabs appear below Actions

### State Configuration

Each state can override:
- **CC Number**: Different controller per state
- **CC On Value**: Different value when active
- **Color**: Different LED color per state
- **Label**: Different display name per state

### State Cycling

**Toggle/Select Mode:**
- First press → State 1 (sends Press commands)
- Second press → turns OFF (sends Release commands)
- Third press → State 2 (sends Press commands)
- Fourth press → turns OFF (sends Release commands)
- And so on...

**Example - Scene Cycling:**

Button labeled "SCENES" with 3 keytimes:
- **State 1**: CC 20, Red LED, "CLEAN"
- **State 2**: CC 21, Green LED, "CRUNCH"
- **State 3**: CC 22, Blue LED, "LEAD"

Each press cycles through clean → crunch → lead → off → clean...

### State Tabs

When keytimes > 1, tabs appear for each state:
- Click tab to edit that state's overrides
- Active state highlighted in color
- Leave fields empty to use base button settings

---

## Encoder Configuration

*Available on STD10 model only*

The rotary encoder provides continuous control and push-button functionality.

### Encoder Rotation

**Enable/Disable**  
Toggle encoder functionality on/off

**CC Number**  
MIDI controller to send (0-127)

**Label**  
Display name (max 8 characters)

**Range (Min/Max)**  
- Min: Starting value (0-127)
- Max: Ending value (0-127)
- Initial: Starting position on boot

**Steps**  
Number of discrete steps (leave blank for continuous)

**Channel**  
MIDI channel (1-16), uses global channel if blank

### Encoder Push Button

The encoder has a built-in push button with full button capabilities:

**Enable/Disable**  
Toggle push button functionality

**Mode**  
- Toggle
- Momentary

**CC Numbers**  
- CC On: Value sent when turned on (0-127)
- CC Off: Value sent when turned off (0-127)

**Display Settings**
- Label: Button name (max 8 characters)
- Channel: MIDI channel override (1-16)

---

## Expression Pedals

*Available on STD10 model only*

Configure up to two expression pedal inputs (EXP1 and EXP2).

### Expression Settings

**Enable/Disable**  
Toggle expression pedal input

**CC Number**  
MIDI controller to send (0-127)

**Label**  
Display name (max 8 characters)

**Range (Min/Max)**  
- Min: Value at heel position (0-127)
- Max: Value at toe position (0-127)

**Polarity**  
- Normal: Min at heel, Max at toe
- Inverted: Max at heel, Min at toe

**Threshold**  
Minimum movement to register change (reduces jitter)

**Channel**  
MIDI channel (1-16), uses global channel if blank

---

## Display Settings

Customize text sizes on the device screen.

### Text Size Options

**Button Text**  
Labels displayed for each button slot
- Small: Compact (~8px)
- Medium: Standard (20px)
- Large: Bold (60px)

**Status Text**  
Center status line (MIDI messages, system info)
- Small: Compact (~8px)
- Medium: Standard (20px)
- Large: Bold (60px)

**Expression Text**  
Expression pedal value display
- Small: Compact (~8px)
- Medium: Standard (20px)
- Large: Bold (60px)

**Note**: Very large text may overflow display for long labels. Use Medium for balanced appearance.

---

## Keyboard Shortcuts

### Global

- **⌘S** / **Ctrl+S**: Save configuration to device
- **⌘Z** / **Ctrl+Z**: Undo last change
- **⌘⇧Z** / **Ctrl+Shift+Z**: Redo change
- **⌘R** / **Ctrl+R**: Reload configuration from device
- **Esc**: Close modal dialogs

### Button Selection

- **↑** / **↓**: Select previous/next button
- **1-9, 0**: Quick select button by number

### Copy/Paste

- **⌘C** / **Ctrl+C**: Copy selected button (when focused)
- **⌘V** / **Ctrl+V**: Paste button configuration

---

## Tips and Best Practices

### Configuration Workflow

1. **Start with profiles** when possible - they handle complex MIDI correctly
2. **Use select groups** for mutually exclusive buttons (scenes, modes)
3. **Test one button at a time** before configuring entire board
4. **Save frequently** (⌘S) - changes are only written on save
5. **Use descriptive labels** - 6 characters is enough to identify function

### Button Modes

- **Toggle**: Best for on/off effects (delay, reverb, looper)
- **Momentary**: Best for hold-while-active (sustain, freeze, tap tempo)
- **Select**: Best for scenes, presets, or mode selection

### MIDI Channels

- Use **global channel** unless you need multiple devices
- **Override channel** per button for multi-device setups
- Remember: Channel displayed as 1-16, stored as 0-15 internally

### Multi-Command Actions

- Order matters - commands execute in sequence
- Keep Press commands simple for instant response
- Use Release commands to cleanly disable effects
- Long Press for "alternate function" on same button

### Performance Tips

- **Disable dev mode** for live use (faster boot, no USB delay)
- **Use Off Mode: Dim** to see button layout in dark
- **Set default_selected** for startup scene/mode
- **Test select groups** thoroughly - wrong config can cause conflicts

### Expression Pedals

- **Calibrate range** using Min/Max to match your pedal's sweep
- **Increase threshold** if values jump erratically
- **Invert polarity** if pedal responds backward

---

## Troubleshooting

### Device Not Detected

**Problem**: Device doesn't appear in dropdown

**Solutions**:
1. **Enable USB drive mode**:
   - Power off device
   - Hold Switch 1 (top-left)
   - Power on while holding
   - Release after 2 seconds
2. **Enable dev mode** in existing config.json:
   - Add `"dev_mode": true` to config file
   - Device will always mount USB
3. **Check USB cable** - must be data cable, not charge-only
4. **Try different USB port** - some ports may have issues
5. **Restart editor** after connecting device

### Configuration Not Saving

**Problem**: Changes don't persist after save

**Solutions**:
1. Check **validation errors** in status bar
2. Ensure device is **not write-protected**
3. Verify **USB drive has space** (unlikely but possible)
4. Try **Reload** then save again
5. Check console for error messages

### Button Not Responding

**Problem**: Button presses don't send MIDI

**Solutions**:
1. Verify **MIDI commands** are configured for Press event
2. Check **MIDI channel** matches receiving device
3. Ensure **CC/Note numbers** are correct for target device
4. Test with **MIDI monitor** to verify messages are sent
5. Try **simple CC command** first to isolate issue

### Wrong LED Color or Behavior

**Problem**: LED doesn't match configuration

**Solutions**:
1. **Save configuration** first (changes don't apply until saved)
2. **Power cycle device** after saving
3. Check **Off Mode** - Dim vs Off affects appearance
4. Verify **color name** is in preset palette
5. Check for **state overrides** if using keytimes

### Encoder Not Working

**Problem**: Encoder doesn't send MIDI

**Solutions**:
1. Verify **encoder is enabled** in config
2. Check **CC number** doesn't conflict with buttons
3. Ensure **Min/Max range** is correct (Min < Max)
4. Test with **MIDI monitor** software
5. **STD10 only** - Mini6 has no encoder

### Expression Pedal Issues

**Problem**: Pedal sends wrong values or jumps

**Solutions**:
1. **Calibrate Min/Max** to match pedal's actual range
2. **Increase threshold** to reduce noise/jitter
3. Try **Inverted polarity** if range is backward
4. Verify **pedal is TRS** expression pedal (not TS)
5. Test **pedal with multimeter** to check resistance sweep

### Display Shows Wrong Text

**Problem**: Device screen doesn't match configuration

**Solutions**:
1. **Save and power cycle** device
2. Check **label max length** (6 chars for buttons, 8 for encoder)
3. Verify **text size settings** aren't too large
4. **ASCII characters only** - special chars may not render
5. Check for **firmware version** compatibility

### Keytimes Not Cycling

**Problem**: Multi-state button doesn't advance states

**Solutions**:
1. Verify **keytimes > 1** in configuration
2. Check **mode is Toggle or Select** (not Momentary)
3. Ensure **state overrides** are configured
4. **Save configuration** before testing
5. Watch **device screen** for state changes

### Unsaved Changes Warning

**Problem**: Editor warns about unsaved changes

**Solutions**:
1. **Intentional**: Click Save to write changes
2. **False positive**: Reload to discard unwanted changes
3. **Persistent warning**: Check if any field has validation error
4. **After reload**: Wait 2-3 seconds for device to reconnect

---

## Support and Resources

- **GitHub Issues**: [Report bugs or request features](https://github.com/MC-Music-Workshop/midi-captain-max/issues)
- **Documentation**: [Technical docs](https://github.com/MC-Music-Workshop/midi-captain-max/tree/main/docs)
- **Firmware Updates**: [Latest releases](https://github.com/MC-Music-Workshop/midi-captain-max/releases)

---

**Copyright © 2026 Maximilian Cascone. All rights reserved.**
