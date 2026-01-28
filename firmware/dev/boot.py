"""
MIDI Captain boot.py

Runs once at device power-on/reset, before code.py.

CRITICAL: Autoreload is DISABLED for rock-solid live performance.
The device must NEVER reset unexpectedly during a gig. File changes
on the USB drive will not trigger reloads.

To reload after config/code changes:
- Send Ctrl+C then Ctrl+D over serial (deploy.sh does this)
- Or power-cycle the device
"""

import supervisor

# DISABLED for live performance stability - no unexpected resets
# CP 7.x uses supervisor.disable_autoreload(), not runtime.autoreload
supervisor.disable_autoreload()
