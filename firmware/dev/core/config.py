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
STATE_OVERRIDE_FIELDS = ("press", "release", "long_press", "long_release", "cc", "cc_on", "cc_off", "note", "velocity_on", "velocity_off", "program", "pc_step", "color", "label")


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


def _validate_channel(channel, default_channel=0):
    """Validate and clamp MIDI channel to 0-15 range.

    Args:
        channel: Input channel value (any type)
        default_channel: Fallback value if invalid (0-15)

    Returns:
        Valid MIDI channel (0-15)
    """
    if not isinstance(channel, (int, float)):
        return default_channel
    channel_int = int(channel)
    return max(0, min(15, channel_int))


def _validate_command_array(action, index=0, default_channel=0):
    """Validate and normalize a command action (single dict or array).

    Args:
        action: Single command dict, array of dicts, or None
        index: Button index (for default values)
        default_channel: Default MIDI channel (0-15)

    Returns:
        Validated array of command dicts, or None if invalid/empty
    """
    if action is None:
        return None

    # Handle array of commands (new format)
    if isinstance(action, list):
        validated_cmds = []
        for cmd in action:
            if not isinstance(cmd, dict):
                continue
            # Basic action validation
            a_type = cmd.get("type", "cc")
            if a_type not in ("cc", "note", "pc", "pc_inc", "pc_dec"):
                a_type = "cc"
            a = {"type": a_type, "channel": _validate_channel(cmd.get("channel", default_channel), default_channel)}
            if a_type == "cc":
                a["cc"] = _clamp_state_field("cc", cmd.get("cc", 20 + index))
                a["value"] = _clamp_state_field("cc_on", cmd.get("value", cmd.get("cc_on", 127)))
            elif a_type == "note":
                a["note"] = _clamp_state_field("note", cmd.get("note", 60))
                a["velocity"] = _clamp_state_field("velocity_on", cmd.get("velocity", cmd.get("velocity_on", 127)))
            elif a_type == "pc":
                a["program"] = _clamp_state_field("program", cmd.get("program", 0))
            elif a_type in ("pc_inc", "pc_dec"):
                a["pc_step"] = _clamp_state_field("pc_step", cmd.get("pc_step", 1))
            # Optional threshold in milliseconds (for long_press events)
            thresh = cmd.get("threshold_ms", cmd.get("threshold", None))
            if isinstance(thresh, int) and thresh > 0:
                a["threshold_ms"] = thresh
            validated_cmds.append(a)
        return validated_cmds if validated_cmds else None

    # Handle single command dict (legacy format)
    elif isinstance(action, dict):
        a_type = action.get("type", "cc")
        if a_type not in ("cc", "note", "pc", "pc_inc", "pc_dec"):
            a_type = "cc"
        a = {"type": a_type, "channel": _validate_channel(action.get("channel", default_channel), default_channel)}
        if a_type == "cc":
            a["cc"] = _clamp_state_field("cc", action.get("cc", 20 + index))
            a["value"] = _clamp_state_field("cc_on", action.get("value", action.get("cc_on", 127)))
        elif a_type == "note":
            a["note"] = _clamp_state_field("note", action.get("note", 60))
            a["velocity"] = _clamp_state_field("velocity_on", action.get("velocity", action.get("velocity_on", 127)))
        elif a_type == "pc":
            a["program"] = _clamp_state_field("program", action.get("program", 0))
        elif a_type in ("pc_inc", "pc_dec"):
            a["pc_step"] = _clamp_state_field("pc_step", action.get("pc_step", 1))
        # Optional threshold in milliseconds
        thresh = action.get("threshold_ms", action.get("threshold", None))
        if isinstance(thresh, int) and thresh > 0:
            a["threshold_ms"] = thresh
        return [a]  # Convert to array for consistency

    return None


def normalize_button_config(btn, index=0, global_channel=0):
    """Convert old single-type config to new event-array format.

    Detects old format (has 'type' but no 'press'/'release') and migrates to
    event-based arrays. New format passes through unchanged.

    Args:
        btn: Button config dict (old or new format)
        index: Button index (for default values)
        global_channel: Global MIDI channel (0-15)

    Returns:
        Button config in new event-array format
    """
    # If already has event arrays, assume new format
    if 'press' in btn or 'release' in btn:
        # Migrate old-style long_press/long_release dicts to arrays
        if 'long_press' in btn and isinstance(btn['long_press'], dict):
            btn['long_press'] = [btn['long_press']]
        if 'long_release' in btn and isinstance(btn['long_release'], dict):
            btn['long_release'] = [btn['long_release']]
        return btn

    # Old format: convert based on type and mode
    msg_type = btn.get('type', 'cc')
    mode = btn.get('mode', 'toggle')
    channel = btn.get('channel', global_channel)

    press_cmds = []
    release_cmds = []

    if msg_type == 'cc':
        cc = btn.get('cc', 20 + index)
        cc_on = btn.get('cc_on', 127)
        cc_off = btn.get('cc_off', 0)
        press_cmds = [{'type': 'cc', 'cc': cc, 'value': cc_on, 'channel': channel}]
        if mode == 'momentary':
            release_cmds = [{'type': 'cc', 'cc': cc, 'value': cc_off, 'channel': channel}]
        # toggle/select/tap modes: state change on press only, release does nothing

    elif msg_type == 'note':
        note = btn.get('note', 60)
        vel_on = btn.get('velocity_on', 127)
        vel_off = btn.get('velocity_off', 0)
        press_cmds = [{'type': 'note', 'note': note, 'velocity': vel_on, 'channel': channel}]
        if mode == 'momentary':
            # NoteOff on release
            release_cmds = [{'type': 'note', 'note': note, 'velocity': vel_off, 'channel': channel}]

    elif msg_type == 'pc':
        program = btn.get('program', 0)
        press_cmds = [{'type': 'pc', 'program': program, 'channel': channel}]
        # PC has no release action

    elif msg_type == 'pc_inc':
        pc_step = btn.get('pc_step', 1)
        press_cmds = [{'type': 'pc_inc', 'pc_step': pc_step, 'channel': channel}]

    elif msg_type == 'pc_dec':
        pc_step = btn.get('pc_step', 1)
        press_cmds = [{'type': 'pc_dec', 'pc_step': pc_step, 'channel': channel}]

    # Migrate long_press/long_release if present
    if 'long_press' in btn and isinstance(btn['long_press'], dict):
        btn['long_press'] = [btn['long_press']]
    if 'long_release' in btn and isinstance(btn['long_release'], dict):
        btn['long_release'] = [btn['long_release']]

    # Add event arrays to button config
    if press_cmds:
        btn['press'] = press_cmds
    if release_cmds:
        btn['release'] = release_cmds

    return btn


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
        # Accept 'tap' and 'normal' modes alongside the legacy set
        "mode": btn.get("mode", "toggle"),
        "off_mode": btn.get("off_mode", "dim"),
        "channel": _validate_channel(btn.get("channel", default_channel), default_channel),
        "type": msg_type,
        "keytimes": keytimes,
    }

    # Normalise mode: unknown values fall back to 'toggle'
    if validated["mode"] not in ("toggle", "normal", "momentary", "select", "tap"):
        validated["mode"] = "toggle"

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
    # Accepts dicts OR arrays of dicts with shape: type = cc|note|pc|pc_inc|pc_dec and type-specific fields.
    def _validate_action_field(field_name):
        action = btn.get(field_name)
        if action is None:
            return None

        # Handle array of commands (new format)
        if isinstance(action, list):
            validated_cmds = []
            for cmd in action:
                if not isinstance(cmd, dict):
                    continue
                # Basic action validation
                a_type = cmd.get("type", "cc")
                if a_type not in ("cc", "note", "pc", "pc_inc", "pc_dec"):
                    a_type = "cc"
                a = {"type": a_type, "channel": cmd.get("channel", default_channel)}
                if a_type == "cc":
                    a["cc"] = _clamp_state_field("cc", cmd.get("cc", 20 + index))
                    a["value"] = _clamp_state_field("cc_on", cmd.get("value", cmd.get("cc_on", 127)))
                elif a_type == "note":
                    a["note"] = _clamp_state_field("note", cmd.get("note", 60))
                    a["velocity"] = _clamp_state_field("velocity_on", cmd.get("velocity", cmd.get("velocity_on", 127)))
                elif a_type == "pc":
                    a["program"] = _clamp_state_field("program", cmd.get("program", 0))
                elif a_type in ("pc_inc", "pc_dec"):
                    a["pc_step"] = _clamp_state_field("pc_step", cmd.get("pc_step", 1))
                # Optional threshold in milliseconds (for long_press events)
                thresh = cmd.get("threshold_ms", cmd.get("threshold", None))
                if isinstance(thresh, int) and thresh > 0:
                    a["threshold_ms"] = thresh
                validated_cmds.append(a)
            return validated_cmds if validated_cmds else None

        # Handle single command dict (legacy format)
        elif isinstance(action, dict):
            a_type = action.get("type", "cc")
            if a_type not in ("cc", "note", "pc", "pc_inc", "pc_dec"):
                a_type = "cc"
            a = {"type": a_type, "channel": action.get("channel", default_channel)}
            if a_type == "cc":
                a["cc"] = _clamp_state_field("cc", action.get("cc", 20 + index))
                a["value"] = _clamp_state_field("cc_on", action.get("value", action.get("cc_on", 127)))
            elif a_type == "note":
                a["note"] = _clamp_state_field("note", action.get("note", 60))
                a["velocity"] = _clamp_state_field("velocity_on", action.get("value", action.get("velocity_on", 127)))
            elif a_type == "pc":
                a["program"] = _clamp_state_field("program", action.get("program", 0))
            elif a_type in ("pc_inc", "pc_dec"):
                a["pc_step"] = _clamp_state_field("pc_step", action.get("pc_step", 1))
            # Optional threshold in milliseconds
            thresh = action.get("threshold_ms", action.get("threshold", None))
            if isinstance(thresh, int) and thresh > 0:
                a["threshold_ms"] = thresh
            return [a]  # Convert to array for consistency

        return None

    # Validate event arrays: press, release, long_press, long_release
    for event_name in ("press", "release", "long_press", "long_release"):
        validated_event = _validate_action_field(event_name)
        if validated_event is not None:
            validated[event_name] = validated_event

    # Select-group (optional) - mutually exclusive group name for toggle-style buttons
    # v1: only support for non-momentary (toggle/select) buttons and keytimes == 1
    select_group = btn.get("select_group")
    default_selected = bool(btn.get("default_selected", False))
    if isinstance(select_group, str) and select_group:
        # Reject momentary or multi-keytimes configurations for select_group in v1
        # Also reject tap mode: tap is visual-only and incompatible with select_group
        if validated.get("mode") == "momentary" or validated.get("mode") == "tap" or keytimes > 1:
            # Not supported: ignore the select_group and default_selected, caller will be warned
            print(f"Warning: button {index+1} select_group ignored (momentary or keytimes>1)")
        else:
            validated["select_group"] = select_group
            if default_selected:
                validated["default_selected"] = True

    # If mode is 'tap', map that to led_mode 'tap' for runtime
    if validated.get("mode") == "tap":
        validated["led_mode"] = "tap"
        # Tap mode tempo is determined by taps at runtime; do not accept a fixed tap_rate_ms

    # For keytimes > 1, validate and pass through states array
    if keytimes > 1:
        states = btn.get("states", [])
        if isinstance(states, list):
            validated_states = []
            for state in states:
                if isinstance(state, dict):
                    validated_state = {}
                    # Process event arrays with full validation using the helper function
                    for event_field in ("press", "release", "long_press", "long_release"):
                        if event_field in state:
                            validated_event = _validate_command_array(state[event_field], index, default_channel)
                            if validated_event is not None:
                                validated_state[event_field] = validated_event
                    # Process numeric/legacy fields with clamping
                    for field in STATE_OVERRIDE_FIELDS:
                        if field not in ("press", "release", "long_press", "long_release") and field in state:
                            validated_state[field] = _clamp_state_field(field, state[field])
                    validated_states.append(validated_state)
            if validated_states:
                validated["states"] = validated_states

    # LED mode: optional (e.g., "tap") with optional per-button tap rate in ms
    led_mode = btn.get("led_mode")
    if isinstance(led_mode, str) and led_mode == "tap":
        validated["led_mode"] = "tap"
        # Legacy: ignore any provided tap_rate_ms; tempo is derived from user taps

    # Dim brightness: optional percentage (0-100) for dim LED brightness, defaults to 15
    dim_brightness = btn.get("dim_brightness")
    if dim_brightness is not None:
        if isinstance(dim_brightness, (int, float)):
            # Clamp to 0-100 range
            validated["dim_brightness"] = max(0, min(100, int(dim_brightness)))

    # Simplified toggle fields: value_on, value_off, default_on (only meaningful for mode='toggle')
    if validated.get("mode") == "toggle":
        value_on = btn.get("value_on")
        value_off = btn.get("value_off")
        if value_on is not None:
            try:
                validated["value_on"] = max(0, min(127, int(value_on)))
            except (TypeError, ValueError):
                pass
        if value_off is not None:
            try:
                validated["value_off"] = max(0, min(127, int(value_off)))
            except (TypeError, ValueError):
                pass
        default_on = btn.get("default_on")
        if default_on is not None:
            validated["default_on"] = bool(default_on)

    # Long press label: optional custom label shown on long press (max 6 chars)
    long_press_label = btn.get("long_press_label")
    if long_press_label is not None and isinstance(long_press_label, str) and long_press_label:
        validated["long_press_label"] = long_press_label[:6]

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

    # Normalize old-format configs to new event-based format, then validate
    normalized_buttons = [
        normalize_button_config(btn, i, global_channel) for i, btn in enumerate(buttons[:button_count])
    ]
    validated_buttons = [
        validate_button(btn, i, global_channel) for i, btn in enumerate(normalized_buttons)
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
    button_name_size = display.get("button_name_text_size", "large")

    # Fallback to defaults if invalid
    if button_size not in valid_sizes:
        button_size = "medium"
    if status_size not in valid_sizes:
        status_size = "medium"
    if expression_size not in valid_sizes:
        expression_size = "medium"
    if button_name_size not in valid_sizes:
        button_name_size = "large"

    return {
        "button_text_size": button_size,
        "status_text_size": status_size,
        "expression_text_size": expression_size,
        "button_name_text_size": button_name_size,
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
