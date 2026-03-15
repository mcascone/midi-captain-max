"""
MIDI Captain MAX - Display Management

Functions for managing displayio labels and center display content.

Author: Max Cascone  
Date: 2026-03-15
Extracted from code.py for better organization.
"""

from core.constants import LABEL_RETURN_TIMEOUT_SEC
import time


def set_label_text(lbl, text, label_prev_len):
    """Update a displayio.Label's text with space padding for clean overwrite.

    Pads with spaces to previous text length to ensure single bitmap update,
    avoiding flicker and GC churn from double-update (clear then set).

    Args:
        lbl: displayio.Label instance
        text: New text string to display
        label_prev_len: Dict tracking previous lengths keyed by label id()

    Returns:
        Updated label_prev_len dict
    """
    lbl_id = id(lbl)
    prev_len = label_prev_len.get(lbl_id, 0)

    # Pad with spaces if new text is shorter than previous
    if len(text) < prev_len:
        text = text + " " * (prev_len - len(text))

    lbl.text = text
    label_prev_len[lbl_id] = len(text.rstrip())  # Store unpadded length

    return label_prev_len


def arm_label_return_timeout(btn_config=None):
    """Arm or cancel the return-to-selected-button timeout.

    If btn_config is provided and has select_group, cancels the timeout (select buttons stay displayed).
    Otherwise, arms the timeout for non-select buttons/encoder to return after inactivity.

    Args:
        btn_config: Button configuration dict, or None for encoders/non-button events

    Returns:
        New timeout value (0.0 to cancel, future monotonic time to arm)
    """
    if btn_config and btn_config.get("select_group"):
        # Select button pressed - cancel timeout (stay on this button)
        return 0.0
    else:
        # Non-select button or encoder - arm timeout to return to selected
        return time.monotonic() + LABEL_RETURN_TIMEOUT_SEC


def find_selected_button(buttons, button_states):
    """Find the currently selected button (button with select_group and state=True).

    Args:
        buttons: List of button config dicts
        button_states: List of ButtonState objects

    Returns:
        tuple: (button_index, button_config) or (None, None) if no button is selected
    """
    for i, btn_config in enumerate(buttons):
        if btn_config.get("select_group") and button_states[i].state:
            return i, btn_config
    return None, None


def update_label_timeout(label_timeout, buttons, button_states, button_name_label, status_label, set_label_text_func, label_prev_len):
    """Check if label timeout has expired and return to showing selected button.

    Args:
        label_timeout: Current timeout value (0.0 = no timeout, >0 = monotonic time)
        buttons: List of button configs
        button_states: List of ButtonState objects
        button_name_label: displayio.Label for button name
        status_label: displayio.Label for status text
        set_label_text_func: Function to call for setting label text
        label_prev_len: Dict tracking previous label lengths

    Returns:
        Updated label_prev_len dict
    """
    if label_timeout == 0.0:
        return label_prev_len  # No timeout active

    now = time.monotonic()
    if now >= label_timeout:
        # Timeout expired - show selected button
        idx, btn_config = find_selected_button(buttons, button_states)
        if idx is not None:
            label_prev_len = set_label_text_func(button_name_label, btn_config.get("label", str(idx + 1)), label_prev_len)
            label_prev_len = set_label_text_func(status_label, "", label_prev_len)
        else:
            # No select button active - clear display to ready state
            label_prev_len = set_label_text_func(button_name_label, "", label_prev_len)
            label_prev_len = set_label_text_func(status_label, "Ready", label_prev_len)

    return label_prev_len
