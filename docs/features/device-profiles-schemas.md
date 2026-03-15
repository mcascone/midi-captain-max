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
      channel: int  # Optional, 0-15 (corresponds to MIDI channels 1-16)
      
      # Type-specific fields:
      # For type: cc
      cc: int       # CC number (0-127)
      value: int    # CC value (0-127)
      
      # For type: note
      note: int     # Note number (0-127)
      velocity: int # Velocity (0-127)
      
      # For type: pc
      program: int  # Program number (0-127)
      
      # For type: pc_inc | pc_dec
      pc_step: int  # Step size (default: 1)

> Note: `channel` is zero-based (0-15) and optional (defaults to button/global channel). In the UI, these are shown as MIDI channels 1-16.

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
