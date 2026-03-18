Long-Press / Hold Actions

Summary

The firmware supports configurable long-press (hold) actions per button to enable a secondary action when a footswitch is held for a configurable threshold. Long press also supports visual feedback through LED color overrides and custom display labels.

Why use it

- Assign two distinct actions to one physical switch (short press vs long press).
- Useful for tuner, bank changes, alternate presets, or transient effects.
- Visual feedback helps performers know when the long-press has triggered.

Schema

Per-button fields (optional):

- `long_press`: Array of commands dispatched when the hold threshold is crossed.
  - Each command object supports: `type`, `cc`, `value`, `note`, `velocity`, `program`, `pc_step`, `channel`
  - First command can include `threshold_ms` to override default threshold for this button
  
- `long_release`: Array of commands dispatched on release after a long-press.
  - Same command structure as `long_press` (no `threshold_ms`)

- `long_press_label`: Custom text shown on display during long press (max 6 chars). Example: `"TUNER"`

- `long_press_color`: LED color override during long press. Any named color: `red`, `green`, `blue`, `yellow`, `cyan`, `magenta`, `orange`, `purple`, `white`, `pink`, etc.
  - **Toggle/Select modes**: Color persists after release if button ends in ON state
  - **Momentary mode**: Color returns to off state after release

Global default:

- `long_press_threshold_ms`: Optional top-level integer (ms) used when a button's first `long_press` command has no `threshold_ms`. Typical values: 300, 500, 700. Default: 600.

Example

```json
{
  "buttons": [
    {
      "label": "LEAD",
      "color": "yellow",
      "mode": "toggle",
      "long_press_color": "pink",
      "long_press_label": "TUNE",
      "press": [
        {"type": "cc", "cc": 43, "value": 5, "channel": 0}
      ],
      "long_press": [
        {"type": "cc", "cc": 68, "value": 127, "channel": 0, "threshold_ms": 700}
      ],
      "long_release": [
        {"type": "cc", "cc": 68, "value": 0, "channel": 0}
      ]
    }
  ],
  "long_press_threshold_ms": 600
}
```

Behavior

- **Short press**: existing behavior (momentary/toggle/keytimes) remains.
- **Long press**: when a button is held longer than its `threshold_ms` (or the global default), the `long_press` action array is dispatched.
  - If `long_press_color` is configured, LED changes to that color
  - If `long_press_label` is configured, display shows that text
  - Serial console prints: `[LONG_PRESS] Button N: Applying color override 'pink' RGB=(255, 105, 180)...`
- **Long release**: when releasing after a triggered long-press, the `long_release` action array is dispatched.
  - **Toggle/Select modes**: If button is ON, LED stays in `long_press_color` (visual indicator that long action triggered)
  - **Momentary mode**: LED always returns to off state (standard momentary behavior)

Multi-Command Support

Each `long_press` and `long_release` event supports multiple commands in sequence:

```json
"long_press": [
  {"type": "cc", "cc": 68, "value": 127, "channel": 0, "threshold_ms": 600},
  {"type": "cc", "cc": 69, "value": 100, "channel": 1}
]
```

Commands execute sequentially with a 2ms inter-command delay for reliable MIDI transmission.

Notes

- If you do not set `long_press` or `long_release`, button behavior is unchanged.
- For momentary-type buttons, the firmware still sends an immediate "on" for responsive feedback; secondary long-press actions are then dispatched when threshold is reached.
- Visual feedback fields (`long_press_color`, `long_press_label`) work independently—you can use one, both, or neither.
- The color persists after release only for toggle/select modes, providing visual confirmation that the long action was triggered.

See also: firmware/circuitpython/core/config.py and firmware/circuitpython/code.py for implementation details.
