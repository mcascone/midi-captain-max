"""
Bidirectional MIDI Demo for MIDI Captain STD10

Minimal experiment to prove:
1. Device abstraction (imports from devices/std10)
2. Outgoing MIDI (switch press → CC)
3. Incoming MIDI (CC → LED update)

Deploy: Copy this file to CIRCUITPY as code.py

Author: Max Cascone / GitHub Copilot
Date: 2026-01-23
"""

print("\n=== BIDIRECTIONAL MIDI DEMO ===\n")

import board
import neopixel
import digitalio
import usb_midi
import adafruit_midi
from adafruit_midi.control_change import ControlChange

# Import hardware constants from device abstraction
from devices.std10 import (
    LED_PIN,
    LED_COUNT,
    SWITCH_PINS,
)

# --- Configuration ---
MIDI_CHANNEL = 0  # Channel 1 (0-indexed)
CC_START = 20     # First switch sends CC20, second CC21, etc.
LED_BRIGHTNESS = 0.3

# --- Colors ---
COLOR_OFF = (10, 10, 10)      # Dim white when off
COLOR_ON = (0, 255, 0)        # Bright green when on

# --- Hardware Setup ---

# NeoPixels: 3 LEDs per switch, 10 switches = 30 LEDs
pixels = neopixel.NeoPixel(LED_PIN, LED_COUNT, brightness=LED_BRIGHTNESS, auto_write=False)

# Map switch index to its 3 LED indices
def get_led_indices(switch_idx):
    """Return the 3 LED indices for a given switch (0-9)."""
    base = switch_idx * 3
    return [base, base + 1, base + 2]

# Initialize all LEDs to off state
def init_leds():
    for i in range(10):
        set_switch_leds(i, COLOR_OFF)
    pixels.show()

def set_switch_leds(switch_idx, color):
    """Set all 3 LEDs for a switch to the given color."""
    for led_idx in get_led_indices(switch_idx):
        pixels[led_idx] = color

# --- Switch Setup ---

class Switch:
    """Simple debounced switch with state tracking."""
    def __init__(self, pin):
        self.io = digitalio.DigitalInOut(pin)
        self.io.direction = digitalio.Direction.INPUT
        self.io.pull = digitalio.Pull.UP
        self.last_state = True  # Pull-up: True = not pressed
    
    @property
    def pressed(self):
        """Returns True if switch is currently pressed."""
        return not self.io.value  # Inverted due to pull-up
    
    def changed(self):
        """Returns (changed, pressed) tuple."""
        current = self.pressed
        changed = current != self.last_state
        self.last_state = current
        return changed, current

# Initialize switches (skip encoder push at index 0 for this demo, use switches 1-10)
# Actually let's use all 11 switches but map them to CC20-30
switches = [Switch(pin) for pin in SWITCH_PINS]
print(f"Initialized {len(switches)} switches")

# --- MIDI Setup ---

midi_usb = adafruit_midi.MIDI(
    midi_in=usb_midi.ports[0],
    midi_out=usb_midi.ports[1],
    in_channel=MIDI_CHANNEL,
    out_channel=MIDI_CHANNEL,
)
print(f"MIDI initialized on channel {MIDI_CHANNEL + 1}")

# --- State ---

# Track LED states (True = on, False = off) for switches 0-9 (we have 10 LEDs)
led_states = [False] * 10

def update_led_from_state(switch_idx):
    """Update LED based on current state."""
    if switch_idx < 10:  # Only 10 switches have LEDs
        color = COLOR_ON if led_states[switch_idx] else COLOR_OFF
        set_switch_leds(switch_idx, color)
        pixels.show()

# --- Main Loop ---

def handle_incoming_midi():
    """Check for incoming MIDI and update LEDs."""
    msg = midi_usb.receive()
    if msg is not None:
        if isinstance(msg, ControlChange):
            cc_num = msg.control
            cc_val = msg.value
            
            # Map CC20-29 to switches 0-9
            switch_idx = cc_num - CC_START
            if 0 <= switch_idx < 10:
                # Value > 63 = on, else off
                led_states[switch_idx] = cc_val > 63
                update_led_from_state(switch_idx)
                print(f"RX: CC{cc_num}={cc_val} → Switch {switch_idx} {'ON' if cc_val > 63 else 'OFF'}")

def handle_switches():
    """Check switches and send MIDI on change."""
    for i, switch in enumerate(switches):
        changed, pressed = switch.changed()
        if changed:
            cc_num = CC_START + i
            cc_val = 127 if pressed else 0
            midi_usb.send(ControlChange(cc_num, cc_val))
            print(f"TX: Switch {i} {'pressed' if pressed else 'released'} → CC{cc_num}={cc_val}")
            
            # Also update local LED state on press (hybrid mode: local + host)
            if i < 10 and pressed:
                led_states[i] = not led_states[i]  # Toggle on press
                update_led_from_state(i)

# --- Startup ---

print("Starting main loop...")
print(f"Switches send CC{CC_START}-CC{CC_START + len(switches) - 1}")
print(f"LEDs respond to CC{CC_START}-CC{CC_START + 9}")
print("")

init_leds()

# Main loop
while True:
    handle_incoming_midi()
    handle_switches()
