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
      type: cc | note | pc
      channel: int
      cc: int
      value: int

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
      channel: 1
      cc: 43
      value: 0

  - id: scene_b
    label: Scene B
    midi:
      type: cc
      channel: 1
      cc: 43
      value: 1
