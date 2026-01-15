# MIDI Captain HK Firmware

This repository starts from Helmut Keller’s CircuitPython firmware for the
Paint Audio MIDI Captain and evolves it into a more generic, configurable,
multi-device firmware (STD 10-switch, Mini6, etc.).

## Layout
- `firmware/original_helmut/` — pristine snapshot of Helmut’s original drop-in (do not edit)
- `firmware/dev/` — working area for refactors and new features
- `docs/` — architecture notes, MIDI protocol, config schema
- `tools/` — helper scripts (packaging, sanity checks)

## Goals
- Bidirectional MIDI sync (host → LEDs/LCD)
- Config-driven mapping and UI layouts
- Hardware abstraction for multiple MIDI Captain models
