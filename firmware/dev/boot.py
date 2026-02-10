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

# Check if user is holding switch 1 (GP1) during boot
# If held LOW, enable USB drive for updates
# If not held, disable USB drive completely (performance mode)
switch_1 = digitalio.DigitalInOut(board.GP1)
switch_1.direction = digitalio.Direction.INPUT
switch_1.pull = digitalio.Pull.UP

# Read switch state (LOW = pressed with pull-up)
enable_usb_drive = not switch_1.value

if enable_usb_drive:
    # USB enabled - drive will appear on computer for file updates
    print("🔓 USB DRIVE ENABLED: Release switch and reboot to hide drive")
    # Leave USB drive enabled (default CircuitPython behavior)
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
