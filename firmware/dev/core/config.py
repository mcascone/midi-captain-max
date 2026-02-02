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


def validate_button(btn, index=0):
    """Validate a button config dict, filling in defaults.
    
    Args:
        btn: Button config dict
        index: Button index (for default CC calculation)
        
    Returns:
        Validated button config with all required fields
    """
    return {
        "label": btn.get("label", str(index + 1)),
        "cc": btn.get("cc", 20 + index),
        "color": btn.get("color", "white"),
        "mode": btn.get("mode", "toggle"),
        "off_mode": btn.get("off_mode", "dim"),
    }


def validate_config(cfg, button_count=10):
    """Validate entire config, filling in defaults.
    
    Args:
        cfg: Raw config dict
        button_count: Expected number of buttons
        
    Returns:
        Validated config with all required fields
    """
    buttons = cfg.get("buttons", [])
    
    # Extend buttons array if needed
    while len(buttons) < button_count:
        buttons.append({})
    
    # Validate each button
    validated_buttons = [
        validate_button(btn, i) for i, btn in enumerate(buttons[:button_count])
    ]
    
    return {
        **cfg,
        "buttons": validated_buttons,
    }


def get_encoder_config(cfg):
    """Extract encoder configuration with defaults.
    
    Args:
        cfg: Full config dict
        
    Returns:
        Encoder config dict
    """
    enc = cfg.get("encoder", {})
    push = enc.get("push", {})
    
    return {
        "enabled": enc.get("enabled", True),
        "cc": enc.get("cc", 11),
        "label": enc.get("label", "ENC"),
        "min": enc.get("min", 0),
        "max": enc.get("max", 127),
        "initial": enc.get("initial", 64),
        "steps": enc.get("steps", None),
        "push": {
            "enabled": push.get("enabled", True),
            "cc": push.get("cc", 14),
            "label": push.get("label", "PUSH"),
            "mode": push.get("mode", "momentary"),
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
    
    return {
        "exp1": {
            "enabled": exp1.get("enabled", True),
            "cc": exp1.get("cc", 12),
            "label": exp1.get("label", "EXP1"),
            "min": exp1.get("min", 0),
            "max": exp1.get("max", 127),
            "polarity": exp1.get("polarity", "normal"),
            "threshold": exp1.get("threshold", 2),
        },
        "exp2": {
            "enabled": exp2.get("enabled", True),
            "cc": exp2.get("cc", 13),
            "label": exp2.get("label", "EXP2"),
            "min": exp2.get("min", 0),
            "max": exp2.get("max", 127),
            "polarity": exp2.get("polarity", "normal"),
            "threshold": exp2.get("threshold", 2),
        },
    }
