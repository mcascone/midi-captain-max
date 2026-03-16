"""
MIDI Captain MAX - Button State Management

Functions for managing button LED states, initialization, and display updates.

Author: Max Cascone
Date: 2026-03-15
Extracted from code.py for better organization.
"""

import time
from core.colors import get_off_color, get_off_color_for_display, rgb_to_hex
from core.constants import LED_DEFAULT_OFF_MODE, LED_DEFAULT_DIM_BRIGHTNESS


def set_button_state(
    switch_idx,
    on,
    buttons,
    button_states,
    button_labels,
    button_boxes,
    pixels,
    led_count,
    blink_state,
    blink_next_toggle,
    switch_to_led_func,
    get_button_color_func
):
    """Update LED and display for a button (1-indexed).

    Manages NeoPixel LEDs, button label colors, and tap mode blink state.

    Args:
        switch_idx: Button number (1-indexed)
        on: True to turn on, False to turn off
        buttons: List of button config dicts
        button_states: List of ButtonState objects
        button_labels: List of displayio.Label objects for button text
        button_boxes: List of (tilegrid, palette) tuples for button boxes
        pixels: NeoPixel object
        led_count: Total number of LEDs
        blink_state: List tracking current blink LED state for each button
        blink_next_toggle: List tracking next blink toggle time for each button
        switch_to_led_func: Function to map switch index to LED index
        get_button_color_func: Function to get button color for current keytime

    Returns:
        tuple: (blink_state, blink_next_toggle) - updated state lists
    """
    idx = switch_idx - 1

    # Use button_states length as bounds check (physical button count)
    if idx < 0 or idx >= len(button_states):
        return blink_state, blink_next_toggle

    btn_state = button_states[idx]
    # Provide fallback config if button is beyond config array
    btn_config = buttons[idx] if idx < len(buttons) else {"color": "white"}

    # Get color for current keytime state
    color_rgb = get_button_color_func(btn_config, btn_state.get_keytime())
    off_mode = btn_config.get("off_mode", LED_DEFAULT_OFF_MODE)  # "dim" or "off"
    dim_brightness = btn_config.get("dim_brightness", LED_DEFAULT_DIM_BRIGHTNESS)  # 0-100

    # Update LED
    led_idx = switch_to_led_func(switch_idx)
    if led_idx is not None:
        rgb = color_rgb if on else get_off_color(color_rgb, off_mode, dim_brightness)
        base = led_idx * 3
        for j in range(3):
            if base + j < led_count:
                pixels[base + j] = rgb
        pixels.show()

    # If this button uses 'tap' led_mode, manage blink state/timers
    try:
        btn_cfg = buttons[idx] if idx < len(buttons) else {}
        if btn_cfg.get("led_mode") == "tap":
            # Turning on: start blinking with short flash
            if on:
                blink_state[idx] = True
                blink_next_toggle[idx] = time.monotonic() + 0.1  # 100ms flash
            else:
                # Turning off: ensure LED shows off state and stop blinking
                blink_state[idx] = False
                blink_next_toggle[idx] = 0.0
    except (IndexError, KeyError) as e:
        print(f"Tap mode state update error for button {idx}: {e}")
    except Exception as e:
        print(f"Unexpected tap mode error: {e}")

    # Update display
    if idx < len(button_labels):
        color_hex = rgb_to_hex(color_rgb if on else get_off_color_for_display(color_rgb, off_mode))
        button_labels[idx].color = color_hex
        if idx < len(button_boxes):
            _, box_palette = button_boxes[idx]
            box_palette[1] = color_hex

    return blink_state, blink_next_toggle


def init_leds(button_count, set_button_state_func):
    """Initialize all LEDs to off/dim state.

    Args:
        button_count: Number of buttons to initialize
        set_button_state_func: Function to call to set button state
    """
    for i in range(1, button_count + 1):
        set_button_state_func(i, False)


def flash_pc_button(button_idx, flash_ms, pc_flash_timers, set_button_state_func):
    """Light LED briefly for PC button press feedback.

    Args:
        button_idx: 1-indexed button number (matches set_button_state convention)
        flash_ms: Flash duration in milliseconds
        pc_flash_timers: List of PC flash timer expiry times
        set_button_state_func: Function to call to turn button LED on

    Returns:
        Updated pc_flash_timers list
    """
    set_button_state_func(button_idx, True)
    pc_flash_timers[button_idx - 1] = time.monotonic() + flash_ms / 1000.0
    return pc_flash_timers
