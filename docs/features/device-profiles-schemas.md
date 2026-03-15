# Device Profile Schema

Profiles define how high-level actions map to MIDI commands.

## Structure

profile:
  id: string
  name: string
  type: fixed | hybrid | template

actions:
  - id: string
    label: string
    midi:
      type: cc | note | pc | pc_inc | pc_dec
      channel: int  # 0-15 (corresponds to MIDI channels 1-16)
      cc: int
      value: int
      pc_step: int  # For pc_inc/pc_dec types

> Note: `channel` is zero-based (0-15). In the UI, these are shown as MIDI channels 1-16.

---

# Example

profile:
  id: quad_cortex
  name: Neural DSP Quad Cortex
  type: fixed

actions:

  - id: scene_a
    label: Scene A
    midi:
      type: cc
      channel: 0
      cc: 43
      value: 0

  - id: scene_b
    label: Scene B
    midi:
      type: cc
      channel: 0
      cc: 43
      value: 1
