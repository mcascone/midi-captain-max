# Hardware Testing Guide: Custom USB Drive Names

This document provides instructions for manually testing the custom USB drive name feature on physical MIDI Captain devices.

## Prerequisites

- MIDI Captain STD10 or Mini6 device
- USB cable
- Access to serial console (optional, for debugging)

## Test Scenarios

### Test 0: USB Disable (Critical Bug Fix)

**Goal:** Verify USB drive is properly hidden when switch 1 is NOT held during boot.

**Background:** Previous versions had a bug where USB drive always mounted. This test verifies the fix.

1. Power on device **WITHOUT** holding Switch 1
2. **Expected:** 
   - No USB drive appears on computer
   - Device operates normally for MIDI
3. Check serial console (if available):
   - Should see: `🔒 USB drive disabled (hold switch 1 during boot to enable)`
4. Power off, then power on WITH Switch 1 held
5. **Expected:** Drive appears (confirms switch is working)
6. Power off, then power on WITHOUT Switch 1
7. **Expected:** Drive hidden again (confirms disable works consistently)

**⚠️ CRITICAL:** If this test fails, the USB disable fix did not work. Report immediately.

### Test 1: Default Name (Baseline)

**Goal:** Verify the default name "MIDICAPTAIN" appears when no custom name is set.

1. Deploy firmware to device with default config.json
2. Power cycle device while holding Switch 1 (to enable USB)
3. **Expected:** Drive mounts as "MIDICAPTAIN"

### Test 2: Simple Custom Name

**Goal:** Verify basic custom name functionality.

1. Edit config.json:
   ```json
   {
     "device": "std10",
     "usb_drive_name": "CAPTAIN_A",
     ...
   }
   ```
2. Save and power cycle device while holding Switch 1
3. **Expected:** Drive mounts as "CAPTAIN_A"

### Test 3: Name Persistence

**Goal:** Verify name survives power cycles and USB disconnects.

1. With custom name set (from Test 2)
2. Power off device (unplug USB)
3. Power on again while holding Switch 1
4. **Expected:** Drive still mounts as "CAPTAIN_A"

### Test 4: Name Validation - Lowercase

**Goal:** Verify lowercase names are auto-converted to uppercase.

1. Edit config.json:
   ```json
   "usb_drive_name": "mycaptain"
   ```
2. Power cycle while holding Switch 1
3. **Expected:** Drive mounts as "MYCAPTAIN"

### Test 5: Name Validation - Special Characters

**Goal:** Verify special characters are removed.

1. Edit config.json:
   ```json
   "usb_drive_name": "MY-CAPTAIN!"
   ```
2. Power cycle while holding Switch 1
3. **Expected:** Drive mounts as "MYCAPTAIN"

### Test 6: Name Validation - Truncation

**Goal:** Verify names longer than 11 chars are truncated.

1. Edit config.json:
   ```json
   "usb_drive_name": "VERYLONGCAPTAINNAME"
   ```
2. Power cycle while holding Switch 1
3. **Expected:** Drive mounts as "VERYLONGCAP" (first 11 chars)

### Test 7: Name Validation - Invalid Characters Only

**Goal:** Verify fallback to default when all characters are invalid.

1. Edit config.json:
   ```json
   "usb_drive_name": "!!!"
   ```
2. Power cycle while holding Switch 1
3. **Expected:** Drive mounts as "MIDICAPTAIN" (fallback)

### Test 8: Multiple Devices

**Goal:** Verify multiple devices can have unique names.

**Requires:** 2+ MIDI Captain devices

1. Device 1: Set `"usb_drive_name": "CAPTAIN_1"`
2. Device 2: Set `"usb_drive_name": "CAPTAIN_2"`
3. Connect both devices simultaneously
4. **Expected:** Both devices visible with different names

### Test 9: Config Load Failure

**Goal:** Verify firmware boots even if config is corrupted.

1. Corrupt config.json (add invalid JSON syntax)
2. Power cycle while holding Switch 1
3. **Expected:** Drive mounts as "MIDICAPTAIN" (fallback)
4. Device still boots and operates normally

### Test 10: Performance Mode (USB Disabled)

**Goal:** Verify custom name doesn't interfere with USB-disabled mode.

1. With custom name set in config.json
2. Power on WITHOUT holding Switch 1
3. **Expected:** USB drive is hidden (performance mode)
4. Device operates normally for MIDI

## Serial Console Monitoring (Optional)

If you have access to serial console, you can see boot messages:

**USB Enabled (Switch 1 held):**
```
🔓 USB DRIVE ENABLED as 'MYCAPTAIN'
   Release switch and reboot to hide drive
```

**USB Disabled (normal boot):**
```
🔒 USB drive disabled (hold switch 1 during boot to enable)
```

**Config Load Error:**
```
🔓 USB DRIVE ENABLED as 'MIDICAPTAIN'
   Release switch and reboot to hide drive
```

## Test Results Template

Copy and fill in:

```
Date: ___________
Device: STD10 / Mini6
Firmware Version: ___________

Test 0 (USB Disable): PASS / FAIL ⚠️ CRITICAL
Test 1 (Default): PASS / FAIL
Test 2 (Custom): PASS / FAIL
Test 3 (Persistence): PASS / FAIL
Test 4 (Lowercase): PASS / FAIL
Test 5 (Special Chars): PASS / FAIL
Test 6 (Truncation): PASS / FAIL
Test 7 (Invalid): PASS / FAIL
Test 8 (Multiple): PASS / FAIL / N/A
Test 9 (Config Failure): PASS / FAIL
Test 10 (USB Disabled): PASS / FAIL

Notes:
_________________________________
_________________________________
_________________________________
```

## Common Issues

**Issue:** Drive name didn't change
- Verify config.json is saved correctly
- Check for JSON syntax errors
- Ensure you power-cycled (not just soft reset)

**Issue:** Drive shows "MIDICAPTAIN" instead of custom name
- Check serial console for errors
- Verify name follows validation rules
- Test with a simple name like "TEST"

**Issue:** Device won't boot
- Restore default config.json
- Check serial console for error messages
- This should NOT happen - report if it does

## Success Criteria

✅ **Test 0 (USB Disable) MUST pass** - Critical bug fix verification
✅ All 10 tests pass
✅ Device boots reliably in all scenarios
✅ Custom names persist across power cycles
✅ Invalid names fall back gracefully
✅ Performance mode works correctly (USB disabled)
✅ USB shows/hides based on switch 1 state

## Reporting Results

When hardware testing is complete, add results to PR comment:

```markdown
## Hardware Test Results

Tested on: STD10 / Mini6
Firmware: [version]
Date: [date]

- [x] All 10 test scenarios passed
- [x] Device boots reliably
- [x] No unexpected behavior observed

Notes: [any observations]
```
