# MIDI Captain MAX
# Editor Architecture

## Overview

The MIDI Captain editor is a web-based interface for configuring the controller.

It allows users to:

- configure buttons visually
- assign MIDI actions
- use device profiles
- preview resolved MIDI commands

The editor should remain simple for beginners but powerful for advanced users.

---

# Technology Stack

Frontend Framework

Svelte

Optional UI libraries

- Skeleton UI
- Melt UI
- ShadCN Svelte

State Management

Svelte stores

Configuration Format

JSON

---

# Editor Layout

The editor is divided into three main areas.

Controller Layout Panel
Button Settings Panel
Configuration Panel

Example

Controller Layout

[1] [2] [3] [4] [5]
[6] [7] [8] [9] [10]

Right Panel

Button Settings

- label
- color
- action
- LED behavior

---

# Component Structure

App

ControllerLayout
ButtonTile
ButtonEditor
ActionEditor
ProfileSelector
MidiEditor

---

# Controller Layout

Displays the device buttons in their physical layout.

Responsibilities

- render button tiles
- highlight selected button
- show label and color
- show state indicator

ButtonTile props

- label
- color
- active state

---

# Button Editor

Allows editing properties of a selected button.

Fields

Label
Color
LED behavior
Actions

Events supported

press
release
long_press
long_release

---

# Action Editor

Each button event can contain multiple actions.

Example

press

[
  action1
  action2
]

Each action supports two sources.

Source

- Profile
- Custom MIDI

---

# Profile Selector

Displays device profiles.

Example

Profile

Quad Cortex

Action

Scene B

Resolved MIDI preview

CC 43 value 1

---

# Custom MIDI Editor

Allows manual MIDI configuration.

Fields

Type
Channel
Controller
Value

Supported types

- CC
- Program Change
- Note

---

# Resolved MIDI Preview

Even when using profiles, the editor should display the generated MIDI message.

Example

Resolved MIDI

CC 43 • Value 1 • Channel 1

This helps debugging and builds user trust.

---

# Config Data Model

Example button configuration

{
  "label": "EDGE",
  "press": [
    {
      "source": "profile",
      "profile": "quad_cortex",
      "action": "scene_b"
    }
  ]
}

When saving, the editor may optionally include resolved MIDI.

---

# Save Pipeline

User edits configuration
↓
Editor validates actions
↓
Profile actions resolved
↓
Config exported to JSON
↓
File saved to device

---

# Future Editor Features

Potential future improvements

- device simulator
- MIDI monitor
- preset sharing
- rig templates
- drag and drop button layout
