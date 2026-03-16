"""
MIDI Captain MAX - Encoder and Expression Pedal Handlers

Functions for handling rotary encoder, encoder push button, and expression pedals.

Author: Max Cascone
Date: 2026-03-15
Extracted from code.py for better organization.
"""

from adafruit_midi.control_change import ControlChange


def handle_encoder_button(
    switches,
    enc_push_enabled,
    enc_push_mode,
    encoder_push_state,
    enc_push_cc_on,
    enc_push_cc_off,
    cc_encoder_push,
    enc_push_channel,
    enc_push_label,
    send_midi_func,
    set_button_name_label_func,
    set_status_label_func,
    arm_timeout_func
):
    """Handle encoder push button.

    Args:
        switches: List of Switch objects (encoder push is index 0)
        enc_push_enabled: Whether encoder push is enabled
        enc_push_mode: "toggle" or "momentary"
        encoder_push_state: Current toggle state (for toggle mode)
        enc_push_cc_on: CC value for ON state
        enc_push_cc_off: CC value for OFF state
        cc_encoder_push: CC number for encoder push
        enc_push_channel: MIDI channel (0-15)
        enc_push_label: Label text for display
        send_midi_func: Function to send MIDI messages
        set_button_name_label_func: Function to update button name label
        set_status_label_func: Function to update status label
        arm_timeout_func: Function to arm label return timeout

    Returns:
        Updated encoder_push_state
    """
    if not enc_push_enabled:
        return encoder_push_state

    sw = switches[0]  # Encoder push is switch index 0
    changed, pressed = sw.changed()
    if changed:
        if enc_push_mode == "toggle":
            # Toggle mode: flip state on press only
            if pressed:
                encoder_push_state = not encoder_push_state
                cc_val = enc_push_cc_on if encoder_push_state else enc_push_cc_off
                send_midi_func(ControlChange(cc_encoder_push, cc_val), channel=enc_push_channel)
                print(f"[MIDI TX] Ch{enc_push_channel+1} CC{cc_encoder_push}={cc_val} (encoder push, toggle)")
                set_button_name_label_func(enc_push_label)
                set_status_label_func(f"TX CC{cc_encoder_push}={'ON' if encoder_push_state else 'OFF'}")
                arm_timeout_func()
        else:
            # Momentary mode: send on press and release
            cc_val = enc_push_cc_on if pressed else enc_push_cc_off
            send_midi_func(ControlChange(cc_encoder_push, cc_val), channel=enc_push_channel)
            print(f"[MIDI TX] Ch{enc_push_channel+1} CC{cc_encoder_push}={cc_val} (encoder push, momentary)")
            set_button_name_label_func(enc_push_label)
            set_status_label_func(f"TX CC{cc_encoder_push}={cc_val}")
            arm_timeout_func()

    return encoder_push_state


def handle_encoder(
    encoder,
    enc_enabled,
    encoder_last_pos,
    encoder_value,
    encoder_slot,
    enc_steps,
    cc_encoder,
    enc_channel,
    enc_label,
    send_midi_func,
    set_button_name_label_func,
    set_status_label_func,
    arm_timeout_func
):
    """Handle rotary encoder.

    Args:
        encoder: Rotary encoder object
        enc_enabled: Whether encoder is enabled
        encoder_last_pos: Last recorded encoder position
        encoder_value: Current internal encoder value (0-127)
        encoder_slot: Current slot number (for stepped mode)
        enc_steps: Number of steps (None or >1 for stepped mode)
        cc_encoder: CC number for encoder
        enc_channel: MIDI channel (0-15)
        enc_label: Label text for display
        send_midi_func: Function to send MIDI messages
        set_button_name_label_func: Function to update button name label
        set_status_label_func: Function to update status label
        arm_timeout_func: Function to arm label return timeout

    Returns:
        tuple: (encoder_last_pos, encoder_value, encoder_slot) - updated state
    """
    if not enc_enabled:
        return encoder_last_pos, encoder_value, encoder_slot

    pos = encoder.position
    if pos != encoder_last_pos:
        delta = pos - encoder_last_pos
        encoder_last_pos = pos

        # Update internal value (always 0-127)
        encoder_value = max(0, min(127, encoder_value + delta))

        if enc_steps and enc_steps > 1:
            # Stepped mode: divide 0-127 into N discrete slots
            # Send CC value 0 to N-1 when crossing slot boundaries
            # Example: enc_steps=5 creates 5 slots, sends values 0-4
            # Slot boundaries: 0-25=slot0, 26-50=slot1, etc. for 5 slots
            # Clamp enc_steps to safe range (2..128) to prevent division by zero
            enc_steps_safe = max(2, min(enc_steps, 128))
            slot_size = 128 // enc_steps_safe
            new_slot = min(encoder_value // slot_size, enc_steps_safe - 1)

            if new_slot != encoder_slot:
                encoder_slot = new_slot
                # Output CC is the slot number (0 to steps-1)
                send_midi_func(ControlChange(cc_encoder, encoder_slot), channel=enc_channel)
                print(f"[ENCODER] Ch{enc_channel+1} CC{cc_encoder}={encoder_slot} (slot {new_slot+1}/{enc_steps_safe})")
                set_button_name_label_func(enc_label)
                set_status_label_func(f"ENC slot {encoder_slot}")
                arm_timeout_func()
        else:
            # Normal mode: send every change
            send_midi_func(ControlChange(cc_encoder, encoder_value), channel=enc_channel)
            print(f"[ENCODER] Ch{enc_channel+1} CC{cc_encoder}={encoder_value}")
            set_button_name_label_func(enc_label)
            set_status_label_func(f"ENC={encoder_value}")
            arm_timeout_func()

    return encoder_last_pos, encoder_value, encoder_slot


def handle_expression(
    exp1,
    exp2,
    has_expression,
    exp1_config,
    exp2_config,
    cc_exp1,
    cc_exp2,
    exp1_channel,
    exp2_channel,
    exp1_min,
    exp1_max,
    exp1_last,
    exp2_min,
    exp2_max,
    exp2_last,
    send_midi_func
):
    """Handle expression pedals.

    Args:
        exp1: AnalogIn object for expression pedal 1
        exp2: AnalogIn object for expression pedal 2
        has_expression: Whether expression pedals are available
        exp1_config: Expression 1 configuration dict
        exp2_config: Expression 2 configuration dict
        cc_exp1: CC number for expression pedal 1
        cc_exp2: CC number for expression pedal 2
        exp1_channel: MIDI channel for expression pedal 1 (0-15)
        exp2_channel: MIDI channel for expression pedal 2 (0-15)
        exp1_min: Minimum value seen for expression pedal 1
        exp1_max: Maximum value seen for expression pedal 1
        exp1_last: Last sent value for expression pedal 1
        exp2_min: Minimum value seen for expression pedal 2
        exp2_max: Maximum value seen for expression pedal 2
        exp2_last: Last sent value for expression pedal 2
        send_midi_func: Function to send MIDI messages

    Returns:
        tuple: (exp1_min, exp1_max, exp1_last, exp2_min, exp2_max, exp2_last) - updated state
    """
    if not has_expression:
        return exp1_min, exp1_max, exp1_last, exp2_min, exp2_max, exp2_last

    # Expression 1
    if exp1_config.get("enabled", True) and exp1 is not None:
        raw1 = exp1.value
        exp1_max = max(raw1, exp1_max)
        exp1_min = min(raw1, exp1_min)

        if exp1_max > exp1_min:
            # Map to 0-127, then apply config range
            normalized = (raw1 - exp1_min) / (exp1_max - exp1_min)
            if exp1_config.get("polarity", "normal") == "reverse":
                normalized = 1.0 - normalized
            out_min = exp1_config.get("min", 0)
            out_max = exp1_config.get("max", 127)
            val1 = int(out_min + normalized * (out_max - out_min))
            val1 = max(0, min(127, val1))  # Clamp to valid MIDI range

            # Hysteresis: only send if change exceeds threshold
            threshold = exp1_config.get("threshold", 2)
            if abs(val1 - exp1_last) >= threshold:
                exp1_last = val1
                send_midi_func(ControlChange(cc_exp1, val1), channel=exp1_channel)
                lbl = exp1_config.get("label", "EXP1")
                print(f"[{lbl}] Ch{exp1_channel+1} CC{cc_exp1}={val1}")

    # Expression 2
    if exp2_config.get("enabled", True) and exp2 is not None:
        raw2 = exp2.value
        exp2_max = max(raw2, exp2_max)
        exp2_min = min(raw2, exp2_min)

        if exp2_max > exp2_min:
            # Map to 0-127, then apply config range
            normalized = (raw2 - exp2_min) / (exp2_max - exp2_min)
            if exp2_config.get("polarity", "normal") == "reverse":
                normalized = 1.0 - normalized
            out_min = exp2_config.get("min", 0)
            out_max = exp2_config.get("max", 127)
            val2 = int(out_min + normalized * (out_max - out_min))
            val2 = max(0, min(127, val2))  # Clamp to valid MIDI range

            # Hysteresis: only send if change exceeds threshold
            threshold = exp2_config.get("threshold", 2)
            if abs(val2 - exp2_last) >= threshold:
                exp2_last = val2
                send_midi_func(ControlChange(cc_exp2, val2), channel=exp2_channel)
                lbl = exp2_config.get("label", "EXP2")
                print(f"[{lbl}] Ch{exp2_channel+1} CC{cc_exp2}={val2}")

    return exp1_min, exp1_max, exp1_last, exp2_min, exp2_max, exp2_last
