"""
Configuration loading and validation for MIDI Captain firmware.

Handles JSON config file parsing with fallback defaults.
"""

try:
    import json
except ImportError:
    # CircuitPython has json built-in, but just in case
    json = None


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


def validate_button(btn, index=0, global_channel=None):
    """Validate a button config dict, filling in defaults.
    
    Args:
        btn: Button config dict
        index: Button index (for default CC calculation)
        global_channel: Global MIDI channel (0-15), used if button doesn't specify channel
        
    Returns:
        Validated button config with all required fields
    """
    # Channel: per-button override or global channel or default to 0 (MIDI Ch 1)
    if global_channel is not None:
        default_channel = global_channel
    else:
        default_channel = 0
    
    # Keytimes: default to 1 (no cycling), clamp to 1-9
    keytimes = btn.get("keytimes", 1)
    if not isinstance(keytimes, int):
        keytimes = 1
    keytimes = max(1, min(9, keytimes))
    
    validated = {
        "label": btn.get("label", str(index + 1)),
        "cc": btn.get("cc", 20 + index),
        "color": btn.get("color", "white"),
        "mode": btn.get("mode", "toggle"),
        "off_mode": btn.get("off_mode", "dim"),
        "channel": btn.get("channel", default_channel),
        "cc_on": btn.get("cc_on", 127),
        "cc_off": btn.get("cc_off", 0),
        "keytimes": keytimes,
    }
    
    # For keytimes > 1, support per-state configuration
    if keytimes > 1:
        # Optional: states array with per-state overrides
        states = btn.get("states", [])
        if isinstance(states, list) and len(states) > 0:
            validated["states"] = states
    
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
