"""
MIDI Captain boot.py

Runs once at device power-on/reset, before code.py.

CRITICAL: Autoreload is DISABLED for rock-solid live performance.
The device must NEVER reset unexpectedly during a gig. File changes
on the USB drive will not trigger reloads.

USB DRIVE: DISABLED by default for stability. This prevents:
- Drive remounting notifications on every power cycle
- Accidental file corruption during performance
- Unexpected drive ejects/remounts
- File system errors from improper USB disconnect

To update firmware:
1. Hold switch 1 (top-left) while powering on → USB drive appears
2. Copy new files via deploy.sh or manually
3. Eject drive and power-cycle normally (without holding switch) → USB hidden

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

# Load config to get custom USB drive name
# This happens early in boot, before USB is fully configured
usb_drive_name = "MIDICAPTAIN"  # Default fallback
try:
    # Import config module to read drive name
    # boot.py runs before normal module search paths are established,
    # so we need to explicitly add /core to sys.path
    import sys
    sys.path.insert(0, "/core")
    from config import load_config, get_usb_drive_name
    
    cfg = load_config("/config.json")
    usb_drive_name = get_usb_drive_name(cfg)
except Exception:
    # If config fails to load, use default name
    pass

# Check if user is holding switch 1 (GP1) during boot
# If held LOW, enable USB drive for updates
# If not held, disable USB drive completely (performance mode)
switch_1 = digitalio.DigitalInOut(board.GP1)
switch_1.direction = digitalio.Direction.INPUT
switch_1.pull = digitalio.Pull.UP

# Read switch state (LOW = pressed with pull-up)
enable_usb_drive = not switch_1.value

if enable_usb_drive:
    # USB enabled - apply custom drive name and make read-write
    print(f"🔓 USB DRIVE ENABLED as '{usb_drive_name}'")
    print("   Release switch and reboot to hide drive")
    try:
        # Remount with custom label (read-write by default)
        storage.remount("/", readonly=False, label=usb_drive_name)
    except Exception as e:
        # If remount fails, log but continue
        print(f"⚠️  Drive label warning: {e}")
else:
    # Performance mode - hide USB drive completely
    # Drive won't appear on computer, preventing remount issues
    try:
        storage.disable_usb_drive()
        print("🔒 USB drive disabled (hold switch 1 during boot to enable)")
    except Exception as e:
        # If disable fails, continue anyway
        print(f"⚠️  USB disable warning: {e}")

# Clean up - switch will be available again in code.py
switch_1.deinit()
