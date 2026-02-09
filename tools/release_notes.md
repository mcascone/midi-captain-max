${NOTES}

## Installation

**Before doing any of this, if you haven't already, please back up your existing config and firmware in a safe place** for recovery or if you just want to go back to OEM code.

- Always make your changes on your local copy and copy them over to the device.
- Don't edit on the device if you can avoid it. It's possible, but it's better to have a copy.
- Use of [git](https://github.com/) or any other version control system is highly recommended!

1. Download the firmware zip: [midi-captain-max-latest.zip](https://github.com/mcascone/midi-captain-max/releases/latest/download/midi-captain-max-latest.zip)
1. Connect your MIDI Captain via USB to your computer:
    1. Connect the USB cables.
    1. Hold down Button 1, the upper-left-most switch, while powering on the device with the power switch.
    1. If the switch was already engaged when you plugged in and it started without holding, just power off and on the device, this time holding the switch down.
1. Extract the zip and copy all files and folders to the device drive (CIRCUITPY or MIDICAPTAIN), replacing existing files.
    - If you have a custom `config.json` with your own button mappings, keep your existing one.
1. The device will restart automatically after the copy completes. If it doesn't, unplug and replug USB.
    - Even if the device ends up in a bad state, it's fully recoverable: mount the device again, erase the contents, and copy your source files again.
1. Your new code should be running. If not, please reach out to me with any issues!

## Stable download URL

- [midi-captain-max-latest.zip](https://github.com/mcascone/midi-captain-max/releases/latest/download/midi-captain-max-latest.zip)
