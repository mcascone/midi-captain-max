#!/usr/bin/env python3
"""
Config migration tool for MIDI Captain firmware upgrades.

Reads existing config.json from device, migrates to latest format,
preserves user customizations, and writes back the upgraded config.

Usage:
    python3 migrate_config.py <device_mount_point> <template_config_path>

Example:
    python3 migrate_config.py /Volumes/CIRCUITPY firmware/circuitpython/config.json
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def migrate_button_to_event_format(btn: Dict[str, Any], index: int = 0, global_channel: int = 0) -> Dict[str, Any]:
    """
    Convert old single-type button config to new event-array format.
    
    Detects old format (has 'type' but no 'press'/'release') and migrates.
    New format passes through unchanged.
    
    Based on normalize_button_config() in firmware/circuitpython/core/config.py
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

    elif msg_type == 'note':
        note = btn.get('note', 60)
        vel_on = btn.get('velocity_on', 127)
        vel_off = btn.get('velocity_off', 0)
        press_cmds = [{'type': 'note', 'note': note, 'velocity': vel_on, 'channel': channel}]
        if mode == 'momentary':
            release_cmds = [{'type': 'note', 'note': note, 'velocity': vel_off, 'channel': channel}]

    elif msg_type == 'pc':
        program = btn.get('program', 0)
        press_cmds = [{'type': 'pc', 'program': program, 'channel': channel}]

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

    # Remove legacy single-type fields
    for field in ['type', 'cc_on', 'cc_off', 'velocity_on', 'velocity_off', 'program', 'pc_step']:
        btn.pop(field, None)

    return btn


def migrate_config(old_config: Dict[str, Any], template_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Migrate old config to new format, preserving user customizations.
    
    Args:
        old_config: Existing config from device
        template_config: Latest template config with new fields
    
    Returns:
        Migrated config with user values preserved
    """
    migrated = {}
    
    # Copy device type (required)
    migrated['device'] = old_config.get('device', template_config.get('device', 'std10'))
    
    # Add new top-level fields with defaults from template
    migrated['usb_drive_name'] = old_config.get('usb_drive_name', template_config.get('usb_drive_name', 'MIDICAPTAIN'))
    migrated['dev_mode'] = old_config.get('dev_mode', template_config.get('dev_mode', False))
    
    # Migrate display settings
    if 'display' not in old_config:
        migrated['display'] = template_config.get('display', {
            'button_text_size': 'medium',
            'status_text_size': 'medium',
            'expression_text_size': 'medium'
        })
    else:
        # Merge with template to add any new display fields
        migrated['display'] = {**template_config.get('display', {}), **old_config['display']}
    
    # Migrate buttons
    global_channel = old_config.get('global_channel', 0)
    migrated['global_channel'] = global_channel
    
    if 'buttons' in old_config:
        migrated['buttons'] = []
        for idx, btn in enumerate(old_config['buttons']):
            migrated_btn = migrate_button_to_event_format(btn.copy(), idx, global_channel)
            migrated['buttons'].append(migrated_btn)
    else:
        # No buttons in old config, use template
        migrated['buttons'] = template_config.get('buttons', [])
    
    # Copy long_press_threshold_ms if present
    if 'long_press_threshold_ms' in old_config:
        migrated['long_press_threshold_ms'] = old_config['long_press_threshold_ms']
    elif 'long_press_threshold_ms' in template_config:
        migrated['long_press_threshold_ms'] = template_config['long_press_threshold_ms']
    
    # Copy encoder config (preserve user settings)
    if 'encoder' in old_config:
        migrated['encoder'] = old_config['encoder']
    elif 'encoder' in template_config:
        migrated['encoder'] = template_config['encoder']
    
    # Copy expression config (preserve user settings)
    if 'expression' in old_config:
        migrated['expression'] = old_config['expression']
    elif 'expression' in template_config:
        migrated['expression'] = template_config['expression']
    
    return migrated


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 migrate_config.py <device_mount_point> <template_config_path>", file=sys.stderr)
        print("", file=sys.stderr)
        print("Example:", file=sys.stderr)
        print("  python3 migrate_config.py /Volumes/CIRCUITPY firmware/circuitpython/config.json", file=sys.stderr)
        sys.exit(1)
    
    device_mount = Path(sys.argv[1])
    template_path = Path(sys.argv[2])
    
    config_path = device_mount / "config.json"
    
    # Check if device config exists
    if not config_path.exists():
        print(f"No config.json found on device at {config_path}", file=sys.stderr)
        print("Skipping migration - deploy will install fresh config", file=sys.stderr)
        sys.exit(0)
    
    # Check if template exists
    if not template_path.exists():
        print(f"Template config not found at {template_path}", file=sys.stderr)
        sys.exit(1)
    
    try:
        # Read existing config
        with open(config_path, 'r') as f:
            old_config = json.load(f)
        
        # Read template config
        with open(template_path, 'r') as f:
            template_config = json.load(f)
        
        # Check if migration needed
        needs_migration = False
        
        # Check for old format buttons
        if 'buttons' in old_config:
            for btn in old_config['buttons']:
                if 'type' in btn and 'press' not in btn and 'release' not in btn:
                    needs_migration = True
                    break
                if 'long_press' in btn and isinstance(btn['long_press'], dict):
                    needs_migration = True
                    break
        
        # Check for missing new fields
        if 'display' not in old_config:
            needs_migration = True
        if 'usb_drive_name' not in old_config:
            needs_migration = True
        if 'dev_mode' not in old_config:
            needs_migration = True
        
        if not needs_migration:
            print("✓ Config is already up-to-date, no migration needed")
            sys.exit(0)
        
        # Perform migration
        print("📝 Migrating config to latest format...")
        migrated_config = migrate_config(old_config, template_config)
        
        # Write backup
        backup_path = device_mount / "config.json.backup"
        with open(backup_path, 'w') as f:
            json.dump(old_config, f, indent=2)
        print(f"✓ Backed up old config to {backup_path.name}")
        
        # Write migrated config
        with open(config_path, 'w') as f:
            json.dump(migrated_config, f, indent=2)
        print(f"✓ Wrote migrated config to {config_path.name}")
        
        # Show what changed
        changes = []
        if 'display' not in old_config:
            changes.append("Added display settings")
        if 'usb_drive_name' not in old_config:
            changes.append("Added usb_drive_name")
        if 'dev_mode' not in old_config:
            changes.append("Added dev_mode")
        
        migrated_buttons = 0
        if 'buttons' in old_config:
            for btn in old_config['buttons']:
                if 'type' in btn and 'press' not in btn:
                    migrated_buttons += 1
        if migrated_buttons > 0:
            changes.append(f"Migrated {migrated_buttons} button(s) to event-array format")
        
        if changes:
            print("\nMigration changes:")
            for change in changes:
                print(f"  • {change}")
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error during migration: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
