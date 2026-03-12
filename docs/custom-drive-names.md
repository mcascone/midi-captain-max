# Custom USB Drive Name Examples

This document shows examples of how to set custom USB drive names for your MIDI Captain devices.

## Basic Example

To rename your device drive from "MIDICAPTAIN" to "MYCAPTAIN", edit `config.json`:

```json
{
  "device": "std10",
  "usb_drive_name": "MYCAPTAIN",
  "buttons": [
    ...
  ]
}
```

## Multiple Devices

If you have multiple MIDI Captain devices, give each one a unique name:

**Device 1 (config.json):**
```json
{
  "device": "std10",
  "usb_drive_name": "CAPTAIN_1",
  "buttons": [...]
}
```

**Device 2 (config.json):**
```json
{
  "device": "std10",
  "usb_drive_name": "CAPTAIN_2",
  "buttons": [...]
}
```

**Device 3 (config.json):**
```json
{
  "device": "mini6",
  "usb_drive_name": "MINI_A",
  "buttons": [...]
}
```

## Naming Rules

The USB drive name must follow FAT32 volume label requirements:

- **Maximum 11 characters** (longer names are truncated)
- **Letters and numbers only** (plus underscore `_`)
- **Automatically converted to uppercase**
- **Special characters removed** (spaces, hyphens, symbols)

### Valid Names

✅ `MYCAPTAIN` → `MYCAPTAIN`
✅ `PEDAL_1` → `PEDAL_1`
✅ `STUDIO` → `STUDIO`
✅ `BOSS` → `BOSS`
✅ `GT_AMP` → `GT_AMP`

### Invalid Names (Auto-Corrected)

❌ `my-captain` → ✅ `MYCAPTAIN` (uppercase, hyphen removed)
❌ `Super Long Name` → ✅ `SUPERLONGN` (truncated to 11 chars, space removed)
❌ `PEDAL #1` → ✅ `PEDAL1` (special char removed)
❌ ` test ` → ✅ `TEST` (whitespace trimmed)

### Empty/Invalid (Falls Back to Default)

❌ `""` → ✅ `MIDICAPTAIN`
❌ `"!!!"` → ✅ `MIDICAPTAIN`
❌ `null` → ✅ `MIDICAPTAIN`

## How It Works

When you power on your MIDI Captain:

1. **Boot.py reads config.json** to get your custom drive name
2. **Validates the name** according to FAT32 rules
3. **Applies the name** using CircuitPython's `storage.remount(label=...)`
4. **Name persists** in the FAT32 boot sector until changed

The name survives:
- ✅ Power cycles
- ✅ USB disconnects
- ✅ Firmware updates (as long as you keep your config.json)

## Changing the Name

To change your drive name:

1. Edit `config.json` and update `usb_drive_name`
2. Power-cycle the device (unplug and replug USB)
3. The drive will appear with the new name

## Troubleshooting

**Q: The drive name didn't change**
- Make sure you saved config.json
- Verify the name follows the rules above
- Power-cycle the device (not just soft reset)
- Check for typos in the JSON (use a JSON validator)

**Q: I get a blank drive name**
- Invalid characters were removed and nothing remained
- The firmware falls back to "MIDICAPTAIN"
- Check the serial console for error messages

**Q: The name is truncated**
- FAT32 limits volume labels to 11 characters
- Use shorter names or abbreviations

## Tooling Support

Both the deploy script and the GUI config editor automatically handle custom drive names.

### Deploy Script (`tools/deploy.sh`)

The script reads `usb_drive_name` from your local `config.json` and `config-mini6.json` files and
includes those names in its mount-point search. No extra flags are needed:

```bash
./tools/deploy.sh          # finds CIRCUITPY, MIDICAPTAIN, or any usb_drive_name in config
./tools/deploy.sh --eject  # same, plus eject after deploy
```

Candidate search order:
1. `/Volumes/CIRCUITPY` (CircuitPython default)
2. `/Volumes/MIDICAPTAIN`
3. `/Volumes/<usb_drive_name>` from `firmware/dev/config.json`
4. `/Volumes/<usb_drive_name>` from `firmware/dev/config-mini6.json`
5. Same paths under `/media/$USER/` and `/run/media/$USER/` (Linux)

If your device is not found, pass the mount point explicitly:

```bash
./tools/deploy.sh /Volumes/MYRIG
```

### GUI Config Editor

The config editor detects devices by both volume name and config content:

- **Known names** — always accepted: `CIRCUITPY`, `MIDICAPTAIN`
- **Custom names** — any mounted volume whose `config.json` contains a `"device": "std10"` or
  `"device": "mini6"` field is accepted automatically

This means you can rename your device and the editor will still find and open it without any
extra configuration.

