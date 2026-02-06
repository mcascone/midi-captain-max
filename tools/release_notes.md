${NOTES}

## Installation

### macOS (Recommended)
**Before doing any of this, if you haven't already, please back up your existing config and firmware in a safe place** for recovery or if you just want to go back to OEM code.

- Always make your changes on your local copy and copy them over to the device. 
- Don't edit on the device if you can avoid it. It's possible, but it's better to have a copy. 
- Use of [git](https://github.com/) or any other version control system is highly recommended!

1. Download the installer: [midi-captain-max-latest.pkg](https://github.com/mcascone/midi-captain-max/releases/latest/download/midi-captain-max-latest.pkg)
1. Connect your MIDI Captain via USB to your computer:
    1. Connect the USB cables.
    1. Hold down Button 1, the upper-left-most switch, while powering on the device with the power switch.
    1. If the switch was already engaged when you plugged in and it started without holding, just power off and on the device, this time holding the switch down.
1. Extract and run the installer.
1. Click Continue on the welcome screen.
1. Click Install.
1. The firmware will install, and you'll see a screen like this when it's done:

    > The device will restart automatically.
    > If it doesn't, disconnect and reconnect USB.

    I haven't actually seen it do that yet, so if you don't either, you must eject the disk cleanly before restarting! It's not guaranteed that doing so bricks the device*, but I have seen it happen personally.

    - Even in this case, the device is still fully recoverable: mount the device again and erase all the contents, then copy your source files again.
1. Your new code should be running. If not, please reach out to me with any issues!

### All Platforms (Manual)
1. Download `midicaptain-firmware-${VERSION}.zip`
2. Extract to your CIRCUITPY drive
3. See README for configuration options

## Stable download URLs

- [midi-captain-max-latest.zip](https://github.com/mcascone/midi-captain-max/releases/latest/download/midi-captain-max-latest.zip)
- [midi-captain-max-latest.pkg](https://github.com/mcascone/midi-captain-max/releases/latest/download/midi-captain-max-latest.pkg)
