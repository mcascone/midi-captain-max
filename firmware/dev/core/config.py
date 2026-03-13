"""
Configuration loading and validation for MIDI Captain firmware.

Handles JSON config file parsing with fallback defaults.
"""

try:
    import json
except ImportError:
    # CircuitPython has json built-in, but just in case
    json = None

VALID_TYPES = ("cc", "note", "pc", "pc_inc", "pc_dec")
STATE_OVERRIDE_FIELDS = ("cc", "cc_on", "cc_off", "note", "velocity_on", "velocity_off", "program", "pc_step", "color", "label")


def load_config(config_path="/config.json", button_count=10):
    """Load button configuration from JSON file.

    Args:
        config_path: Path to config file (default: /config.json)
        button_count: Number of buttons for fallback defaults

    Returns:
        Configuration dict with 'buttons' array and optional other keys
    """
    if json is None:
        return _default_config(button_count)

    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)
            return cfg
    except Exception:
        pass

    return _default_config(button_count)


def _default_config(button_count):
    """Generate default configuration."""
    return {
        "buttons": [
            {"label": str(i + 1), "cc": 20 + i, "color": "white"}
            for i in range(button_count)
        ]
    }


_MIDI_BYTE_FIELDS = ("cc", "cc_on", "cc_off", "note", "velocity_on", "velocity_off", "program")

def _clamp_state_field(field, value):
    """Clamp numeric state override fields to valid MIDI ranges. Non-numeric fields pass through."""
    if field in _MIDI_BYTE_FIELDS:
        if not isinstance(value, int):
            return 0
        return max(0, min(127, value))
    if field == "pc_step":
        if not isinstance(value, int):
            return 1
        return max(1, min(127, value))
    return value  # color, label — pass through as-is


def validate_button(btn, index=0, global_channel=None):
    """Validate a button config dict, filling in defaults.

    Args:
        btn: Button config dict
        index: Button index (for default CC calculation)
        global_channel: Global MIDI channel (0-15), used if button doesn't specify channel

    Returns:
        Validated button config with all required fields

    Button Types:
        - "cc": Control Change (default)
        - "note": MIDI Note On/Off
        - "pc": Program Change fixed
        - "pc_inc": Program Change increment
        - "pc_dec": Program Change decrement
    """
    if global_channel is not None:
        default_channel = global_channel
    else:
        default_channel = 0

    # Keytimes: default to 1 (no cycling), clamp to 1-99
    keytimes = btn.get("keytimes", 1)
    if not isinstance(keytimes, int):
        keytimes = 1
    keytimes = max(1, min(99, keytimes))

    # Determine message type, fall back to cc if invalid
    msg_type = btn.get("type", "cc")
    if msg_type not in VALID_TYPES:
        msg_type = "cc"

    validated = {
        "label": btn.get("label", str(index + 1)),
        "color": btn.get("color", "white"),
        "mode": btn.get("mode", "toggle"),
        "off_mode": btn.get("off_mode", "dim"),
        "channel": btn.get("channel", default_channel),
        "type": msg_type,
        "keytimes": keytimes,
    }

    # Type-specific fields
    if msg_type == "cc":
        validated["cc"] = btn.get("cc", 20 + index)
        validated["cc_on"] = btn.get("cc_on", 127)
        validated["cc_off"] = btn.get("cc_off", 0)
    elif msg_type == "note":
        validated["note"] = btn.get("note", 60)
        validated["velocity_on"] = btn.get("velocity_on", 127)
        validated["velocity_off"] = btn.get("velocity_off", 0)
    elif msg_type == "pc":
        validated["program"] = btn.get("program", 0)
    elif msg_type in ("pc_inc", "pc_dec"):
        validated["pc_step"] = btn.get("pc_step", 1)

    # Long-press / hold actions (optional)
    # Accepts dicts with shape similar to a button action: type = cc|note|pc and type-specific fields.
    def _validate_action_field(field_name):
        action = btn.get(field_name)
        if not isinstance(action, dict):
            return None
        # Basic action validation
        a_type = action.get("type", "cc")
        if a_type not in ("cc", "note", "pc"):
            a_type = "cc"
        a = {"type": a_type, "channel": action.get("channel", default_channel)}
        if a_type == "cc":
            a["cc"] = _clamp_state_field("cc", action.get("cc", 20 + index))
            # 'value' used as the CC value for the action; fall back to cc_on if present
            a["value"] = _clamp_state_field("cc_on", action.get("value", action.get("cc_on", 127)))
        elif a_type == "note":
            a["note"] = _clamp_state_field("note", action.get("note", 60))
            a["value"] = _clamp_state_field("velocity_on", action.get("value", action.get("velocity_on", 127)))
        elif a_type == "pc":
            a["program"] = _clamp_state_field("program", action.get("program", 0))
        # Optional threshold in milliseconds
        thresh = action.get("threshold_ms", action.get("threshold", None))
        if isinstance(thresh, int) and thresh > 0:
            a["threshold_ms"] = thresh
        return a

    lp = _validate_action_field("long_press")
    if lp is not None:
        validated["long_press"] = lp

    lr = _validate_action_field("long_release")
    if lr is not None:
        validated["long_release"] = lr

    # Select-group (optional) - mutually exclusive group name for toggle-style buttons
    # v1: only support for non-momentary (toggle/select) buttons and keytimes == 1
    select_group = btn.get("select_group")
    default_selected = bool(btn.get("default_selected", False))
    if isinstance(select_group, str) and select_group:
        # Reject momentary or multi-keytimes configurations for select_group in v1
        if validated.get("mode") == "momentary" or keytimes > 1:
            # Not supported: ignore the select_group and default_selected, caller will be warned
            print(f"Warning: button {index+1} select_group ignored (momentary or keytimes>1)")
        else:
            validated["select_group"] = select_group
            if default_selected:
                validated["default_selected"] = True

    # For keytimes > 1, validate and pass through states array
    if keytimes > 1:
        states = btn.get("states", [])
        if isinstance(states, list):
            validated_states = []
            for state in states:
                if isinstance(state, dict):
                    validated_state = {}
                    for field in STATE_OVERRIDE_FIELDS:
                        if field in state:
                            validated_state[field] = _clamp_state_field(field, state[field])
                    validated_states.append(validated_state)
            if validated_states:
                validated["states"] = validated_states

    return validated


def validate_config(cfg, button_count=10):
    """Validate entire config, filling in defaults.

    Args:
        cfg: Raw config dict
        button_count: Expected number of buttons

    Returns:
        Validated config with all required fields
    """
    buttons = cfg.get("buttons", [])

    # Get global channel (0-15 = MIDI Ch 1-16), default to 0
    global_channel = cfg.get("global_channel", 0)
    # Clamp to valid range
    if not isinstance(global_channel, int) or global_channel < 0 or global_channel > 15:
        global_channel = 0

    # Extend buttons array if needed
    while len(buttons) < button_count:
        buttons.append({})

    # Validate each button with global channel context
    validated_buttons = [
        validate_button(btn, i, global_channel) for i, btn in enumerate(buttons[:button_count])
    ]

    result = {}
    for k, v in cfg.items():
        result[k] = v
    result["buttons"] = validated_buttons
    result["global_channel"] = global_channel
    # Preserve optional global long-press threshold (ms)
    if isinstance(cfg.get("long_press_threshold_ms"), int):
        result["long_press_threshold_ms"] = cfg.get("long_press_threshold_ms")

    # Normalize select_group default selections: ensure at most one default per group
    groups = {}
    for i, b in enumerate(result["buttons"]):
        g = b.get("select_group")
        if not g:
            continue
        if g not in groups:
            groups[g] = []
        if b.get("default_selected"):
            groups[g].append(i)

    for g, indices in groups.items():
        if len(indices) > 1:
            # Keep the first default-selected, clear others
            first = indices[0]
            for idx in indices[1:]:
                result["buttons"][idx].pop("default_selected", None)
            print(f"Warning: multiple default_selected in group '{g}'; keeping button {first+1}")
    return result


def get_button_state_config(btn_config, keytime_index):
    """Get button config merged with per-state overrides for a given keytime position.

    Args:
        btn_config: Validated button config dict
        keytime_index: Current keytime position (1-indexed)

    Returns:
        Dict with base values overridden by per-state values where present.
        Overridable fields: cc, cc_on, cc_off, note, velocity_on, velocity_off, program, pc_step, color, label.
    """
    # Start with base config
    result = {}
    for field in STATE_OVERRIDE_FIELDS:
        if field in btn_config:
            result[field] = btn_config[field]

    # Apply per-state overrides if keytime_index is in range
    states = btn_config.get("states", [])
    if states and 0 < keytime_index <= len(states):
        state = states[keytime_index - 1]
        for field in STATE_OVERRIDE_FIELDS:
            if field in state:
                result[field] = state[field]

    return result


def get_encoder_config(cfg):
    """Extract encoder configuration with defaults.

    Args:
        cfg: Full config dict

    Returns:
        Encoder config dict
    """
    enc = cfg.get("encoder", {})
    push = enc.get("push", {})
    global_channel = cfg.get("global_channel", 0)

    return {
        "enabled": enc.get("enabled", True),
        "cc": enc.get("cc", 11),
        "label": enc.get("label", "ENC"),
        "min": enc.get("min", 0),
        "max": enc.get("max", 127),
        "initial": enc.get("initial", 64),
        "steps": enc.get("steps", None),
        "channel": enc.get("channel", global_channel),
        "push": {
            "enabled": push.get("enabled", True),
            "cc": push.get("cc", 14),
            "label": push.get("label", "PUSH"),
            "mode": push.get("mode", "momentary"),
            "channel": push.get("channel", global_channel),
            "cc_on": push.get("cc_on", 127),
            "cc_off": push.get("cc_off", 0),
        },
    }


def get_expression_config(cfg):
    """Extract expression pedal configuration with defaults.

    Args:
        cfg: Full config dict

    Returns:
        Expression config dict with exp1 and exp2
    """
    exp = cfg.get("expression", {})
    exp1 = exp.get("exp1", {})
    exp2 = exp.get("exp2", {})
    global_channel = cfg.get("global_channel", 0)

    return {
        "exp1": {
            "enabled": exp1.get("enabled", True),
            "cc": exp1.get("cc", 12),
            "label": exp1.get("label", "EXP1"),
            "min": exp1.get("min", 0),
            "max": exp1.get("max", 127),
            "polarity": exp1.get("polarity", "normal"),
            "threshold": exp1.get("threshold", 2),
            "channel": exp1.get("channel", global_channel),
        },
        "exp2": {
            "enabled": exp2.get("enabled", True),
            "cc": exp2.get("cc", 13),
            "label": exp2.get("label", "EXP2"),
            "min": exp2.get("min", 0),
            "max": exp2.get("max", 127),
            "polarity": exp2.get("polarity", "normal"),
            "threshold": exp2.get("threshold", 2),
            "channel": exp2.get("channel", global_channel),
        },
    }


def get_display_config(cfg):
    """Extract display configuration with defaults.

    Args:
        cfg: Full config dict

    Returns:
        Display config dict with text size settings
    """
    display = cfg.get("display", {})

    # Validate size names
    valid_sizes = ["small", "medium", "large"]
    button_size = display.get("button_text_size", "medium")
    status_size = display.get("status_text_size", "medium")
    expression_size = display.get("expression_text_size", "medium")

    # Fallback to defaults if invalid
    if button_size not in valid_sizes:
        button_size = "medium"
    if status_size not in valid_sizes:
        status_size = "medium"
    if expression_size not in valid_sizes:
        expression_size = "medium"

    return {
        "button_text_size": button_size,
        "status_text_size": status_size,
        "expression_text_size": expression_size,
    }


def get_dev_mode(cfg):
    """Extract development mode setting from config.

    In development mode the USB drive mounts on every boot without needing
    to hold Switch 1.  In performance mode (the default) the drive is hidden
    unless Switch 1 is held during boot.

    Args:
        cfg: Full config dict

    Returns:
        True if development mode is enabled, False otherwise
    """
    return bool(cfg.get("dev_mode", False))


def validate_usb_drive_name(name):
    """Validate USB drive name for FAT32 compatibility.

    FAT32 volume labels have strict requirements:
    - Maximum 11 characters
    - Uppercase alphanumeric + underscore only
    - No spaces or special characters

    Args:
        name: Proposed drive name string

    Returns:
        Valid drive name (sanitized) or "MIDICAPTAIN" if invalid
    """
    if not name or not isinstance(name, str):
        return "MIDICAPTAIN"

    # Convert to uppercase and strip whitespace
    name = name.upper().strip()

    # Filter to valid characters (alphanumeric + underscore).
    # Avoid str.isalnum() — not available in CircuitPython 7.x.
    # name is already uppercased, so only A-Z, 0-9, and _ are valid.
    name = "".join(c for c in name if ('A' <= c <= 'Z') or ('0' <= c <= '9') or c == '_')

    # Truncate to 11 characters
    if len(name) > 11:
        name = name[:11]

    # Must have at least 1 character
    if len(name) == 0:
        return "MIDICAPTAIN"

    return name


def get_usb_drive_name(cfg):
    """Extract and validate USB drive name from config.

    Args:
        cfg: Full config dict

    Returns:
        Validated USB drive name string
    """
    name = cfg.get("usb_drive_name", "MIDICAPTAIN")
    return validate_usb_drive_name(name)
