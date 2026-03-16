# Deploying Experiments to MIDI Captain

## Bidirectional Demo

This minimal experiment proves bidirectional MIDI communication.

### What it does:
- Press any footswitch → sends CC (CC20-30)
- Receive CC20-29 → updates corresponding LED (value > 63 = ON, else OFF)
- Local toggle: pressing a switch also toggles its LED locally

### Deploy to STD10:

1. Connect MIDI Captain via USB while holding switch 1 (enters USB mode)
2. Copy these files to CIRCUITPY:

```
# From firmware/dev/ copy:
experiments/bidirectional_demo.py  →  CIRCUITPY/code.py
devices/                           →  CIRCUITPY/devices/
```

Or use this command from the repo root:
```bash
# Assuming CIRCUITPY is mounted
cp firmware/dev/experiments/bidirectional_demo.py /Volumes/CIRCUITPY/code.py
cp -r firmware/dev/devices /Volumes/CIRCUITPY/
```

3. Eject CIRCUITPY safely
4. Power cycle the device

### Testing:

**Test outgoing MIDI:**
- Use a MIDI monitor (e.g., MIDI Monitor on macOS, or your DAW)
- Press footswitches, you should see CC20-30 messages

**Test incoming MIDI:**
- Send CC20 with value 127 → Switch 0 LED turns ON (green)
- Send CC20 with value 0 → Switch 0 LED turns OFF (dim)
- Works for CC20-29 (switches 0-9)

### Serial Console:

To see debug output:
```bash
screen /dev/tty.usbmodem* 115200
```
Or use Mu Editor's serial console.
