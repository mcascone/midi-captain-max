Long-Press / Hold Actions

Summary

The firmware supports configurable long-press (hold) actions per button to enable a secondary action when a footswitch is held for a configurable threshold.

Why use it

- Assign two distinct actions to one physical switch (short press vs long press).
- Useful for tuner, bank changes, alternate presets, or transient effects.

Schema

Per-button fields (optional):

- `long_press`: Action dispatched when the hold threshold is crossed.
  - `type`: `cc` | `note` | `pc` (required)
  - `cc`: CC controller number (0-127) — for `type: cc`
  - `value`: CC value or note velocity (0-127)
  - `note`: MIDI note (0-127) — for `type: note`
  - `program`: Program number (0-127) — for `type: pc`
  - `channel`: MIDI channel (0-15)
  - `threshold_ms`: Optional per-button threshold in milliseconds (overrides global default)

- `long_release`: Optional action dispatched on release after a long-press. Same sub-fields as `long_press` (no `threshold_ms`).

Global default:

- `long_press_threshold_ms`: Optional top-level integer (ms) used when a button has no `threshold_ms`. Typical values: 300, 500, 700.

Example

{
  "buttons": [
    {
      "label": "EDGE",
      "cc": 30,
      "color": "white",
      "long_press": {"type": "cc", "cc": 31, "value": 127, "threshold_ms": 700},
      "long_release": {"type": "cc", "cc": 32, "value": 0}
    }
  ],
  "long_press_threshold_ms": 600
}

Behavior

- Short press: existing behavior (momentary/toggle/keytimes) remains.
- Long press: when a button is held longer than its `threshold_ms` (or the global default), the `long_press` action is dispatched once.
- Long release: when releasing after a triggered long-press, an optional `long_release` action is dispatched.

Notes

- If you do not set `long_press` or `long_release`, button behavior is unchanged.
- For momentary-type buttons, the firmware still sends an immediate "on" for responsive feedback; secondary long-press actions are then dispatched when threshold is reached.

See also: firmware/dev/core/config.py and firmware/dev/code.py for implementation details.
