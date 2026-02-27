# USB Drive Disable Bug Fix

## Problem Report

User reported that the USB drive **always mounts**, even when switch 1 is NOT held during boot. The intended behavior was:
- Hold switch 1 → USB drive appears (update mode)
- Don't hold switch 1 → USB drive hidden (performance mode)

## Root Cause

### The Issue: Execution Order in CircuitPython boot.py

CircuitPython's `storage.disable_usb_drive()` has a **critical timing requirement**: it must be called **BEFORE any USB subsystem initialization occurs**.

**Original buggy code structure:**
```python
if enable_usb_drive:
    storage.remount("/", label="NAME")  # ⚠️ This initializes USB!
else:
    storage.disable_usb_drive()  # ❌ Too late - USB already initialized
```

### Why This Fails

In CircuitPython boot.py execution:

1. Python evaluates the `if` statement first
2. If the condition is true, `storage.remount()` is called
3. **`remount()` initializes the USB mass storage subsystem**
4. Once USB is initialized, `disable_usb_drive()` **cannot** disable it

Even worse: In some CircuitPython versions, simply **having `remount()` in the code** (even in a non-executed branch) can cause the USB subsystem to initialize, making `disable_usb_drive()` ineffective.

### The Fix

**Check the disable condition FIRST**, before any USB-related calls:

```python
# STEP 1: Disable USB if needed (must be FIRST)
if not enable_usb_drive:
    storage.disable_usb_drive()  # ✅ Called before USB init

# STEP 2: Configure USB if enabled (runs after disable check)
if enable_usb_drive:
    storage.remount("/", label="NAME")  # USB only initializes here
```

This ensures:
- `disable_usb_drive()` runs **before** any USB initialization
- USB only initializes when explicitly needed (enable path)
- The disable path completes **before** USB subsystem starts

## Code Changes

### Before (buggy):
```python
enable_usb_drive = not switch_1.value

if enable_usb_drive:
    print(f"🔓 USB DRIVE ENABLED as '{usb_drive_name}'")
    storage.remount("/", readonly=False, label=usb_drive_name)
else:
    storage.disable_usb_drive()  # ❌ Too late
    print("🔒 USB drive disabled")
```

### After (fixed):
```python
enable_usb_drive = not switch_1.value

# CRITICAL: Check disable condition FIRST
if not enable_usb_drive:
    storage.disable_usb_drive()  # ✅ Runs before USB init
    print("🔒 USB drive disabled")

# Then configure USB if enabled
if enable_usb_drive:
    print(f"🔓 USB DRIVE ENABLED as '{usb_drive_name}'")
    storage.remount("/", readonly=False, label=usb_drive_name)
```

## Why This Pattern Works

1. **Sequential evaluation**: Boot.py runs top-to-bottom
2. **First check** evaluates `not enable_usb_drive` → if true, disables USB
3. **USB disable happens** before reaching any `remount()` call
4. **Second check** evaluates `enable_usb_drive` → only initializes USB when needed

## Testing

To verify the fix works:

**Test 1: USB Disabled (default)**
1. Power on device **without** holding switch 1
2. **Expected:** No USB drive appears on computer
3. Check serial console: Should see "🔒 USB drive disabled"

**Test 2: USB Enabled (update mode)**
1. Hold switch 1 while powering on
2. **Expected:** USB drive appears as custom name (e.g., "MIDICAPTAIN")
3. Check serial console: Should see "🔓 USB DRIVE ENABLED as 'MIDICAPTAIN'"

**Test 3: Toggle behavior**
1. Power on without switch 1 → no drive
2. Power off
3. Power on WITH switch 1 → drive appears
4. Power off
5. Power on without switch 1 → no drive

## Technical Background

### CircuitPython USB Subsystem Initialization

When CircuitPython boots:

1. **boot.py runs first** (before USB enumeration)
2. During boot.py execution, it decides USB configuration
3. **After boot.py completes**, USB enumeration occurs
4. **Key rule:** `disable_usb_drive()` must run **before** any call that touches USB (including `remount()`)

### Why `if/else` Order Matters

In Python (including CircuitPython), an `if/else` block:
- Evaluates the `if` condition first
- Executes the `if` body if true
- Executes the `else` body if false

But **importing storage module** and **defining functions** can trigger subsystem initialization. The safest pattern:
- Always check the "disable" case first
- Use separate `if` statements, not `if/else`
- Ensure disable runs before any enable operations

## Additional Notes

- This bug would manifest as "USB drive always visible" regardless of switch state
- The fix maintains backward compatibility (same external behavior when working correctly)
- No changes needed to config.json or other files
- The custom drive name feature still works correctly in enable mode

## Related Documentation

- CircuitPython storage module: https://docs.circuitpython.org/en/latest/shared-bindings/storage/
- Boot.py execution order: https://learn.adafruit.com/welcome-to-circuitpython/boot_out-txt
- MIDI Captain boot behavior: docs/hardware-reference.md
