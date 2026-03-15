# MIDI Captain MAX
# Product Requirements Document

## Overview

MIDI Captain MAX is evolving from a firmware replacement into a programmable controller platform.

The goal is to move beyond OEM parity and provide a programmable MIDI control environment.

Core features:

1. Visual Button Editor
2. Device Profiles
3. Conditional / Smart Actions

---

# Feature 1 — Visual Button Editor

## Summary

Replace the current form-based configuration UI with a visual representation of the MIDI Captain hardware.

Users interact directly with buttons on a graphical layout.

## Example Layout

Device Layout

[1] [2] [3] [4] [5]
[6] [7] [8] [9] [10]

Button Settings Panel

- Label
- Color
- Action
- LED behavior
- Advanced options

## Requirements

- Buttons rendered in hardware layout
- Click button to edit
- Selected button highlighted
- Immediate visual feedback

## Acceptance Criteria

- Users configure buttons visually
- Layout matches hardware
- Labels and colors visible

---

# Feature 2 — Device Profiles

## Summary

Device profiles convert high-level musician actions into MIDI commands.

Example:

Device: Quad Cortex
Action: Scene B

Resolved MIDI:

CC 43 Value 1

## Profile Types

Fixed Profiles

- Quad Cortex

Hybrid Profiles

- Helix
- Kemper

Template Profiles

- Ableton Live
- MainStage
- Gig Performer

---

# Editor Integration

Profiles should appear as a layer above raw MIDI configuration.

Each action supports two sources:

Source:

- Profile Action
- Custom MIDI

Example UI:

Action Source
[ Profile ▼ ]

Device Profile
[ Quad Cortex ▼ ]

Action
[ Scene B ▼ ]

Resolved MIDI
CC 43 • Value 1 • Channel 1

If Custom MIDI is selected:

Type
CC

Channel
1

Controller
43

Value
1

---

# Feature 3 — Conditional Actions

## Summary

Buttons can change behavior depending on state.

Example:

IF drive_active
send CC20 value 0

ELSE
send CC20 value 127

## Requirements

- conditional evaluation engine
- access to button state
- nested conditions

## Acceptance Criteria

- conditional actions execute reliably
- works with multi-command actions
