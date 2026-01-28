"""
MIDI Captain boot.py

Runs once at device power-on/reset, before code.py.
Disables autoreload so file copies don't cause multiple resets.

To reload after deploy, either:
- Eject and reconnect the device
- Send Ctrl+D over serial (deploy.sh does this automatically)
- Press the reset button on the device
"""

import supervisor

# Disable autoreload - device won't reset on every file change
supervisor.runtime.autoreload = False
