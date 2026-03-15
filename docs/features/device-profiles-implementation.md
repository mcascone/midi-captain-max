# Device Profile Implementation

This document describes how device profiles integrate with the editor and firmware.

---

# Resolution Pipeline

User Action
→ Profile Lookup
→ MIDI Command Generation
→ Send via Transport

Transport options:

- USB
- TRS
- Both

---

# Editor Behavior

The editor stores both semantic actions and resolved MIDI.

Example config

{
"source": "profile",
"profile": "quad_cortex",
"action": "scene_b",
"resolved": {
"type": "cc",
"channel": 1,
"cc": 43,
"value": 1
}
}

Recommended architecture:

Editor resolves profiles → raw MIDI
Firmware only sends MIDI

---

# Dispatch Logic

dispatch_action(action):

1 lookup profile
2 resolve midi mapping
3 send midi message

Pseudo logic

midi = profile[action]

send_midi(
type=midi.type,
controller=midi.controller,
value=midi.value,
channel=midi.channel
)
