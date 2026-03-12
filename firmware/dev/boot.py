"""
MIDI Captain boot.py

Runs once at device power-on/reset, before code.py.

CRITICAL: Autoreload is DISABLED for rock-solid live performance.
The device must NEVER reset unexpectedly during a gig. File changes
on the USB drive will not trigger reloads.

USB DRIVE — two modes, controlled by config.json:

  Performance Mode (default, dev_mode: false):
    Drive is hidden unless Switch 1 is held during boot.
    - Hold switch 1 (top-left) while powering on → USB drive appears
    - Release switch and reboot normally → USB hidden again

  Development Mode (dev_mode: true):
    Drive always mounts on boot — no switch needed.
    Convenient when iterating on firmware locally.

To reload after config/code changes:
- Send Ctrl+D over serial console
- Or power-cycle the device
"""

import board
import digitalio
import storage
import supervisor

# DISABLED for live performance stability - no unexpected resets
# CP 7.x uses supervisor.disable_autoreload(), not runtime.autoreload
supervisor.disable_autoreload()

# Load config settings needed at boot time (drive name + dev mode).
# boot.py runs before normal module search paths are established,
# so we add /core to sys.path explicitly.
usb_drive_name = "MIDICAPTAIN"  # Default fallback
dev_mode = False                # Default: performance mode
try:
    import sys
    sys.path.insert(0, "/core")
    from config import load_config, get_usb_drive_name, get_dev_mode

    cfg = load_config("/config.json")
    usb_drive_name = get_usb_drive_name(cfg)
    dev_mode = get_dev_mode(cfg)
except Exception:
    # If config fails to load, use safe defaults (performance mode)
    pass

# Check if user is holding switch 1 (GP1) during boot.
# With pull-up: LOW (False) = pressed, HIGH (True) = not pressed.
switch_1 = digitalio.DigitalInOut(board.GP1)
switch_1.direction = digitalio.Direction.INPUT
switch_1.pull = digitalio.Pull.UP

switch_held = not switch_1.value          # True when switch is pressed
enable_usb_drive = dev_mode or switch_held  # dev_mode overrides switch gate

# CRITICAL: disable_usb_drive() must be called BEFORE any USB initialization.
# Always check the disable condition first; remount() would initialize USB.
if not enable_usb_drive:
    # Performance mode - hide USB drive completely
    # Drive won't appear on computer, preventing remount issues
    try:
        storage.disable_usb_drive()
        print("🔒 USB drive disabled (hold switch 1 during boot to enable)")
    except Exception as e:
        print(f"⚠️  USB disable failed: {e}")

# If USB is enabled, apply the custom drive label.
# This runs AFTER the disable check so USB only initializes when needed.
if enable_usb_drive:
    mode_label = "DEV MODE" if dev_mode else "switch held"
    print(f"🔓 USB DRIVE ENABLED as '{usb_drive_name}' ({mode_label})")
    if not dev_mode:
        print("   Release switch and reboot to hide drive")
    try:
        storage.remount("/", readonly=False, label=usb_drive_name)
    except Exception as e:
        print(f"⚠️  Drive label warning: {e}")

# Clean up - switch will be available again in code.py
switch_1.deinit()
