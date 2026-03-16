# MIDI Captain Firmware - Rust + Embassy

**Status:** 🚧 In Development (Proof of Concept)

Native Rust firmware for Paint Audio MIDI Captain controllers using Embassy async runtime on RP2040.

## Why Rust?

Replaces CircuitPython with Rust for performance and reliability improvements:

| Feature | CircuitPython | Rust + Embassy |
|---------|--------------|----------------|
| Timing | GC pauses (jitter) | Zero GC (deterministic) |
| Concurrency | Polling loop | True async tasks |
| MIDI Clock Sync | ❌ Not viable | ✅ <1ms jitter |
| Dual-core | ❌ Single core only | ✅ Core 0: MIDI, Core 1: Display |
| Type Safety | Runtime checks | Compile-time checks |
| Config Types | JSON parsing in Python | Shared structs with editor |

## Prerequisites

```bash
# Install Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install ARM Cortex-M target
rustup target add thumbv6m-none-eabi

# Install tools
cargo install probe-rs flip-link
```

## Build

```bash
cd firmware/rust
cargo build --release
```

## Flash

Using probe-rs (via SWD debugger):
```bash
cargo run --release
```

Or via UF2 bootloader (drag-and-drop):
```bash
cargo objcopy --release -- -O binary target/thumbv6m-none-eabi/release/midi-captain-firmware.bin
elf2uf2-rs target/thumbv6m-none-eabi/release/midi-captain-firmware
# Drag .uf2 file to RPI-RP2 drive
```

## Architecture

```
src/
├── main.rs              # Entry point, core 0 executor
├── devices/
│   ├── mod.rs          # Device abstraction
│   ├── std10.rs        # STD10 pin definitions
│   └── mini6.rs        # Mini6 pin definitions
├── config.rs           # Config types (shared with editor via workspace)
├── midi/
│   ├── mod.rs
│   ├── usb.rs          # USB MIDI class device
│   └── serial.rs       # UART MIDI at 31250 baud
├── input/
│   ├── switches.rs     # GPIO footswitch scanning
│   ├── encoder.rs      # Rotary encoder
│   └── expression.rs   # Expression pedal ADC
├── output/
│   ├── leds.rs         # NeoPixel/WS2812 via PIO
│   └── display.rs      # ST7789 SPI display
└── core1.rs            # Core 1 tasks (display rendering, LED animations)
```

## Config Compatibility

The same `config.json` format works for both CircuitPython and Rust firmware.
Config types are shared via Cargo workspace from `config-editor/src-tauri`.

## Migration Status

- [x] Project structure
- [x] Cargo workspace setup
- [ ] Device detection (STD10 vs Mini6)
- [ ] Config loading from Flash
- [ ] USB MIDI class device
- [ ] GPIO switch scanning
- [ ] NeoPixel LED control
- [ ] ST7789 display driver
- [ ] Rotary encoder
- [ ] Expression pedals
- [ ] MIDI clock generation
- [ ] Dual-core task distribution
- [ ] Equivalent feature parity with CircuitPython firmware

## Development

CircuitPython firmware remains the stable, supported version until Rust firmware reaches feature parity.
Users can choose which firmware to flash based on their needs.

## License

Copyright (c) 2026 Maximilian Cascone — All rights reserved.

See [LICENSE](../../LICENSE) for full terms.
