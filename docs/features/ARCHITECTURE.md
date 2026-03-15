# MIDI Captain MAX
# Firmware Architecture

## Overview

MIDI Captain MAX firmware is structured around an **event-driven control system** that converts button interactions into MIDI messages sent through one or more transports.

The firmware is designed to support:

- multi-command actions
- long press / release events
- device profiles
- conditional logic
- USB + TRS MIDI output

---

# Core Architecture

Controller Input
↓
Button Event Engine
↓
Action Resolver
↓
MIDI Dispatcher
↓
Transport Layer (USB / TRS)

---

# Main Components

## 1. Input Layer

Responsible for reading physical inputs from the hardware.

Examples:

- footswitch presses
- encoder rotation
- expression pedal
- tap tempo

Responsibilities:

- detect press
- detect release
- detect long press
- debounce inputs

Output:

Button Events

Example

button_press
button_release
button_long_press

---

## 2. Event Engine

The event engine converts raw input signals into high-level events.

Events supported:

- press
- release
- long_press
- long_release
- tap

Example

Button 3 pressed
→ event: press

Button 3 held > threshold
→ event: long_press

---

## 3. Action Resolver

The resolver determines which actions must be executed when an event occurs.

Example configuration

{
  "label": "EDGE",
  "press": [
    { "type": "cc", "cc": 20, "value": 127 }
  ]
}

Resolver responsibilities:

- read button config
- match event type
- evaluate conditional logic
- expand profile actions into MIDI commands

Output:

List of MIDI commands

---

## 4. Profile Resolver

If the action source is a **device profile**, it converts profile actions into MIDI messages.

Example

profile action

scene_b

resolved to

CC 43 value 1

---

## 5. MIDI Dispatcher

Responsible for converting resolved commands into MIDI messages.

Examples

- Control Change
- Program Change
- Note On
- Note Off

Dispatcher creates MIDI messages and forwards them to the transport layer.

---

## 6. Transport Layer

Handles the physical output of MIDI messages.

Supported transports:

- USB MIDI
- TRS / DIN MIDI
- Both simultaneously

Transport configuration example

{
  "midi_transport": "both"
}

---

# Event Flow Example

Button Press

User presses EDGE

1 Input layer detects press
2 Event engine emits "press"
3 Action resolver loads button config
4 Profile resolver expands action
5 MIDI dispatcher creates CC message
6 Transport layer sends message

Result

CC 20 value 127 sent to device

---

# Conditional Logic

Conditional actions allow dynamic button behavior.

Example

IF delay_active
send CC30 value 0
ELSE
send CC30 value 127

The resolver evaluates conditions before dispatching commands.

---

# Multi-Command Actions

A single event can trigger multiple MIDI messages.

Example

press event

[
  { "type": "cc", "cc": 20, "value": 127 },
  { "type": "pc", "program": 3 }
]

The dispatcher executes actions sequentially.

---

# Future Extensions

The architecture supports future features:

- MIDI routing engine
- scripting support
- external MIDI input processing
- device state tracking
- plugin device profiles
