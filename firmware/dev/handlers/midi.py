"""
MIDI Captain MAX - MIDI I/O Handlers

MIDI send/receive functions with multi-transport support (USB + TRS/serial).

Author: Max Cascone
Date: 2026-03-15
Extracted from code.py for better organization.
"""


def send_midi_message(msg, channel, midi_usb, midi_trs, transport):
    """Send a MIDI message to USB, TRS, or both transports on specified channel.

    Transport is controlled by the 'midi_transport' config key:
      "usb"  - USB MIDI only (default)
      "trs"  - TRS/serial MIDI only
      "both" - send to both transports simultaneously

    RX (host → device) always comes from USB only via midi_usb.receive().

    Args:
        msg: MIDI message object (ControlChange, NoteOn, ProgramChange, etc.)
        channel: MIDI channel 0-15 (wire channels, displayed as 1-16 in UI)
        midi_usb: USB MIDI transport object
        midi_trs: TRS/serial MIDI transport object
        transport: Transport mode string ("usb", "trs", or "both")

    Note: adafruit_midi doesn't support per-message channels on send - the channel
    parameter on message constructors is for RX only. We temporarily set the
    transport's out_channel before each send.
    """
    if transport in ("usb", "both"):
        try:
            midi_usb.out_channel = channel
            midi_usb.send(msg)
        except Exception as e:
            print(f"[WARN] USB MIDI send failed: {e}")
    if transport in ("trs", "both"):
        try:
            midi_trs.out_channel = channel
            midi_trs.send(msg)
        except Exception as e:
            print(f"[WARN] TRS MIDI send failed: {e}")


def clamp_pc_value(value):
    """Clamp PC value to valid MIDI range (0-127)."""
    return max(0, min(127, value))


def get_button_expected_cc_value(btn_config):
    """Extract expected CC number, channel, and value from button's press action.

    Returns tuple: (cc, channel, value) or None if button doesn't send CC on press.
    Used for bidirectional MIDI sync with value-based scene switching (Quad Cortex style).

    Args:
        btn_config: Button configuration dict

    Returns:
        Tuple of (cc, channel, value) or None
    """
    press_cfg = btn_config.get("press")
    if not press_cfg:
        return None

    # Normalize to list
    if isinstance(press_cfg, dict):
        commands = [press_cfg]
    elif isinstance(press_cfg, list):
        commands = press_cfg
    else:
        return None

    # Find first CC command
    for cmd in commands:
        if not isinstance(cmd, dict):
            continue
        if cmd.get("type", "cc") == "cc":
            cc = cmd.get("cc")
            channel = cmd.get("channel", btn_config.get("channel", 0))
            value = cmd.get("value", cmd.get("cc_on", 127))
            if cc is not None:
                return (cc, channel, value)

    return None
