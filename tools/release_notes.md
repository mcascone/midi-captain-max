${NOTES}

## Installation

**Before doing any of this, if you haven't already, please back up your existing config and firmware in a safe place** for recovery or if you just want to go back to OEM code.

### GUI Config Editor

Download the appropriate installer file from the `Assets` section below.

### Device Firmware

1. Download the firmware zip: [midi-captain-max-latest.zip](https://github.com/mcascone/midi-captain-max/releases/latest/download/midi-captain-max-latest.zip).
1. Connect your MIDI Captain via USB to your computer:
    1. Connect the USB cables.
    1. Hold down Button 1, the upper-left-most switch, while powering on the device with the power switch.
    1. If you plugged in and it started without holding, just power off and on the device, this time holding the switch down.
1. Extract the zip and copy all files and folders to the device drive (CIRCUITPY or MIDICAPTAIN), replacing existing files.
    - If you have a custom `config.json` with your own button mappings, keep your existing one.
1. **Important Note**: For first-time install on Mini6 devices, follow these steps:
    - Delete `config.json` on the device.
    - Rename `config-mini6.json` to `config.json`.
1. To restart the device, power cycle it with the on/off button, or unplug and replug the USB cable.
1. Your new code should be running. If not, please reach out to me with any issues!

ℹ️  Even if the device ends up in a bad state, it's fully recoverable: mount the device again, erase the contents, and copy your backed-up files to the device.