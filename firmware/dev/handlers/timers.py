"""
MIDI Captain MAX - Timer Management

Functions for managing various timing-based updates (PC flash, LED blink, label timeout).

Author: Max Cascone
Date: 2026-03-15
Extracted from code.py for better organization.
"""

import time


def update_pc_flash_timers(pc_flash_timers, button_count, set_button_state_func):
    """Turn off LEDs whose flash period has expired. Call each main loop.

    Args:
        pc_flash_timers: List of expiry times (0.0 = inactive, >0 = monotonic time)
        button_count: Number of buttons
        set_button_state_func: Function to call to turn button LED off

    Returns:
        Updated pc_flash_timers list
    """
    now = time.monotonic()
    for i in range(button_count):
        if pc_flash_timers[i] > 0 and now >= pc_flash_timers[i]:
            pc_flash_timers[i] = 0.0
            set_button_state_func(i + 1, False)
    return pc_flash_timers


def update_blink_timers(
    buttons,
    button_count,
    button_states,
    blink_next_toggle,
    blink_state,
    blink_rate_ms,
    tap_active_until,
    set_button_state_func
):
    """Toggle blink states for buttons configured with led_mode 'tap'.

    Blinking is non-blocking and driven by monotonic time checks.
    When a button is active (logical state True) and has led_mode 'tap',
    its LED alternates between ON color and OFF color at `tap_rate_ms`.

    Args:
        buttons: List of button config dicts
        button_count: Number of buttons
        button_states: List of ButtonState objects
        blink_next_toggle: List of next toggle times
        blink_state: List of current blink LED states (True=ON, False=OFF)
        blink_rate_ms: List of blink rates in milliseconds
        tap_active_until: List of tap active window expiry times
        set_button_state_func: Function to call to set button LED state

    Returns:
        tuple: (blink_next_toggle, blink_state) - updated state lists
    """
    now = time.monotonic()
    for i in range(button_count):
        try:
            btn_cfg = buttons[i] if i < len(buttons) else {}
            if btn_cfg.get("led_mode") != "tap":
                # ensure any lingering blink timers are cleared
                blink_next_toggle[i] = 0.0
                blink_state[i] = False
                continue

            # Blink while logical state is active OR while within the recent
            # tap active window (user tapped recently).
            active_window = now < tap_active_until[i]
            if not (button_states[i].state or active_window):
                if blink_state[i]:
                    blink_state[i] = False
                    set_button_state_func(i + 1, False)
                    blink_next_toggle[i] = 0.0
                continue

            # Active and tap mode: initialize timer if needed
            if blink_next_toggle[i] == 0.0:
                blink_state[i] = True
                set_button_state_func(i + 1, True)
                blink_next_toggle[i] = now + 0.1  # Start with 100ms flash
                continue

            if now >= blink_next_toggle[i]:
                blink_state[i] = not blink_state[i]
                set_button_state_func(i + 1, blink_state[i])
                
                # Use different durations for on vs off to match tempo
                # ON = short flash (100ms), OFF = rest of beat interval
                if blink_state[i]:
                    # Just turned ON - flash briefly
                    blink_next_toggle[i] = now + 0.1  # 100ms flash
                else:
                    # Just turned OFF - wait for next beat
                    beat_interval = blink_rate_ms[i] / 1000.0
                    flash_duration = 0.1
                    blink_next_toggle[i] = now + max(0.05, beat_interval - flash_duration)
        except (IndexError, ZeroDivisionError, TypeError) as e:
            # Defensive: don't let blinking crash the loop
            print(f"[WARN] Blink timing failed for button {i}: {e}")

    return blink_next_toggle, blink_state
