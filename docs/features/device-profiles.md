# Device Profiles

Device profiles translate musician-friendly actions into MIDI commands.

Example:

User selects

Device: Quad Cortex
Action: Scene B

System resolves to:

CC 43 value 1

---

# Supported Profiles

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

# Quad Cortex

Scene Recall

CC43

0 Scene A
1 Scene B
2 Scene C
3 Scene D
4 Scene E
5 Scene F
6 Scene G
7 Scene H

Tap Tempo

CC44

Tuner

CC45

Gig View

CC46

Mode Select

CC47

Preset Recall

CC0 bank select
CC32 setlist
Program Change preset

---

# Helix

Snapshot Recall

CC69

0 Snapshot 1
1 Snapshot 2
2 Snapshot 3
3 Snapshot 4
4 Snapshot 5
5 Snapshot 6
6 Snapshot 7
7 Snapshot 8

---

# Kemper

Program Change used for slot recall

PC1 Slot1
PC2 Slot2
PC3 Slot3
PC4 Slot4
PC5 Slot5

---

# Template Platforms

These rely on MIDI learn rather than fixed mappings.

- Ableton Live
- MainStage
- Gig Performer
