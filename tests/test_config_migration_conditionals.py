"""Test that config migration preserves conditional actions."""

import sys
from pathlib import Path

# Add tools directory to path for migration script import
sys.path.insert(0, str(Path(__file__).parent.parent / 'tools'))

from migrate_config import migrate_button_to_event_format


def test_migration_preserves_conditional_actions():
    """Verify that conditional actions pass through migration unchanged."""
    
    # Button config with conditional action (new format)
    btn_with_conditional = {
        'label': 'Test',
        'color': 'red',
        'channel': 0,
        'press': [
            {
                'type': 'conditional',
                'if': {'type': 'button_state', 'button': 1, 'state': 'on'},
                'then': [{'type': 'cc', 'cc': 20, 'value': 127}],
                'else': [{'type': 'cc', 'cc': 20, 'value': 0}]
            }
        ],
        'release': [
            {'type': 'cc', 'cc': 21, 'value': 0}
        ]
    }
    
    # Migrate - should pass through unchanged
    result = migrate_button_to_event_format(btn_with_conditional.copy(), index=0, global_channel=0)
    
    # Verify conditional structure preserved
    assert 'press' in result
    assert len(result['press']) == 1
    assert result['press'][0]['type'] == 'conditional'
    assert result['press'][0]['if']['type'] == 'button_state'
    assert result['press'][0]['if']['button'] == 1
    assert len(result['press'][0]['then']) == 1
    assert result['press'][0]['then'][0]['type'] == 'cc'
    assert len(result['press'][0]['else']) == 1
    
    # Verify release preserved
    assert 'release' in result
    assert len(result['release']) == 1
    assert result['release'][0]['type'] == 'cc'


def test_migration_preserves_mixed_commands():
    """Verify that button with both MIDI and conditional commands is preserved."""
    
    btn_mixed = {
        'label': 'Mixed',
        'color': 'blue',
        'press': [
            {'type': 'cc', 'cc': 10, 'value': 127},  # Regular MIDI command
            {
                'type': 'conditional',
                'if': {'type': 'expression', 'pedal': 'exp1', 'operator': 'gt', 'value': 64},
                'then': [{'type': 'pc', 'program': 5}]
            }
        ]
    }
    
    result = migrate_button_to_event_format(btn_mixed.copy(), index=0, global_channel=0)
    
    # Both commands should be preserved
    assert len(result['press']) == 2
    assert result['press'][0]['type'] == 'cc'
    assert result['press'][1]['type'] == 'conditional'


def test_migration_converts_old_format():
    """Verify that old single-type format is still converted correctly."""
    
    # Old format button (no press/release, has legacy type field)
    old_btn = {
        'label': 'Old',
        'color': 'green',
        'type': 'cc',
        'cc': 25,
        'cc_on': 127,
        'cc_off': 0,
        'mode': 'momentary',
        'channel': 2
    }
    
    result = migrate_button_to_event_format(old_btn.copy(), index=5, global_channel=0)
    
    # Should be converted to new event-array format
    assert 'press' in result
    assert 'release' in result
    assert result['press'][0]['type'] == 'cc'
    assert result['press'][0]['cc'] == 25
    assert result['press'][0]['value'] == 127
    assert result['release'][0]['value'] == 0
    
    # Legacy fields removed
    assert 'type' not in result
    assert 'cc_on' not in result
    assert 'cc_off' not in result


if __name__ == '__main__':
    test_migration_preserves_conditional_actions()
    test_migration_preserves_mixed_commands()
    test_migration_converts_old_format()
    print("✅ All migration tests passed!")
