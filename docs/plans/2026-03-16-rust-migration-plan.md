# Rust + Embassy Firmware Migration Plan

**Date:** 2026-03-16  
**Status:** Planning / Proof of Concept

## Motivation

Migrate from CircuitPython to native Rust + Embassy firmware for:

1. **MIDI clock sync** — Zero GC pauses enable <1ms timing jitter for 24 PPQ clock generation
2. **Dual-core utilization** — RP2040 has 2 cores; CircuitPython uses only 1
3. **Type-safe config** — Share config structs between firmware and editor via Cargo workspace
4. **Memory safety** — Compile-time checks eliminate buffer overflows and null pointer bugs
5. **True async** — Embassy tasks (MIDI I/O, display, input) run concurrently instead of polling loop

## Non-Goals

- **Not a rewrite** — Same hardware, same config format, same user-facing behavior
- **Not abandoning CircuitPython** — CP version remains supported until Rust reaches parity
- **Not a new product** — Users choose which firmware to flash; both live in same repo

---

## Repository Structure

```
midi-captain-max/
├── Cargo.toml                    # NEW: Workspace root
├── firmware/
│   ├── circuitpython/            # RENAMED: from dev/
│   │   ├── code.py
│   │   ├── boot.py
│   │   ├── core/
│   │   ├── devices/
│   │   └── original_helmut/      # MOVED: from firmware/original_helmut
│   └── rust/                     # NEW: Rust + Embassy firmware
│       ├── Cargo.toml
│       ├── memory.x
│       ├── .cargo/config.toml
│       └── src/main.rs
├── config-editor/                # Shares config types with rust firmware
│   └── src-tauri/
│       └── src/config/           # Re-used by firmware/rust via workspace
└── tests/
    ├── circuitpython/            # CP-specific tests (existing)
    └── rust/                     # NEW: Rust firmware tests
```

---

## Cargo Workspace

Root `Cargo.toml` defines workspace:
```toml
[workspace]
members = ["firmware/rust", "config-editor/src-tauri"]
resolver = "2"
```

Firmware imports editor's config types:
```toml
[dependencies]
config_editor_lib = { path = "../../config-editor/src-tauri" }
```

**Zero duplication** — Same `MidiCaptainConfig`, `ButtonConfig`, etc. structs used by both firmware and editor.

---

## Feature Parity Roadmap

### Phase 1: Skeleton (This PR)
- [x] Cargo workspace setup
- [x] Directory structure
- [x] Basic main.rs with Embassy executor
- [x] Build configuration for RP2040

### Phase 2: Core Hardware
- [ ] Device detection (STD10 vs Mini6 via GPIO probe)
- [ ] Config loading from Flash (serde_json_core)
- [ ] USB MIDI class device (embassy-usb)
- [ ] GPIO switch scanning with debounce
- [ ] NeoPixel LED control via PIO

### Phase 3: Display & Input
- [ ] ST7789 display driver (embassy-rp SPI)
- [ ] Display layout rendering (button labels, status)
- [ ] Rotary encoder (embassy-rp rotaryio alternative)
- [ ] Expression pedal ADC reading

### Phase 4: MIDI Protocol
- [ ] Bidirectional MIDI CC/Note/PC
- [ ] Button modes (toggle/momentary/select)
- [ ] Keytimes cycling
- [ ] Select groups
- [ ] Long-press detection

### Phase 5: Advanced Features (CircuitPython can't do)
- [ ] MIDI clock generation (24 PPQ at configurable BPM)
- [ ] Tap tempo with hardware timer accuracy
- [ ] MIDI clock input → BPM display
- [ ] Dual-core: Core 0 = MIDI/logic, Core 1 = display/LEDs
- [ ] Smooth LED animations without MIDI latency impact

---

## Config Format — No Changes

The same `config.json` works for both firmwares:
```json
{
  "device": "std10",
  "buttons": [
    {"label": "Scene A", "press": [{"type": "cc", "cc": 20, "value": 127}]}
  ],
  "encoder": { "enabled": true, "cc": 11 }
}
```

Rust firmware uses `serde_json_core` (no_std JSON parser) to read this from Flash.

---

## Development Workflow

### Dual-firmware releases
GitHub Releases include both:
- `firmware-circuitpython-v1.5.0.zip`
- `firmware-rust-v0.1.0.zip`

### User choice
Users flash whichever firmware meets their needs:
- **CircuitPython**: Proven, stable, easy to modify
- **Rust**: Performance, MIDI clock, dual-core

### Deprecation timeline
Once Rust firmware reaches feature parity + 3 months of field testing:
1. Mark CircuitPython firmware as "legacy" in documentation
2. Stop adding new features to CircuitPython version
3. Continue bug fixes for CircuitPython for 6 months
4. Eventually archive `firmware/circuitpython/` with final stable release

---

## Testing Strategy

### Rust firmware tests
```bash
cd firmware/rust
cargo test
```

Embassy tasks can be tested with `embassy-executor` test features.

### Hardware-in-loop
- Same test devices (STD10, Mini6)
- Same config files
- Same MIDI protocol verification

### Parity checklist
Before declaring Rust "stable":
- [ ] All CircuitPython features implemented
- [ ] Config files from CircuitPython work in Rust
- [ ] 100% MIDI protocol compatibility
- [ ] Field-tested by 5+ users for 1+ month

---

## Migration Trigger

**When to actually start this:**
- A user requests MIDI clock sync
- Display animations cause noticeable MIDI latency (haven't hit this yet)
- CircuitPython 7.x syntax restrictions become painful (already annoying)
- We want to add a feature that needs tight timing (tap tempo accuracy)

**Not before:**
- CircuitPython firmware is stable and working
- No critical bugs or performance issues in production
- Config editor is stable
- Device profiles feature is implemented (if desired)

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Rust learning curve | Slower development | Phase 1 is just skeleton; can pause anytime |
| Embassy breaking changes | Firmware doesn't compile | Pin Embassy versions in Cargo.toml |
| Hardware incompatibility | Feature doesn't work | Extensive testing on both STD10 and Mini6 |
| User confusion | "Which firmware do I use?" | Clear documentation, default to CircuitPython |
| Abandoned rewrite | Wasted effort | Keep CircuitPython working; Rust is optional |

---

## References

- Embassy Book: https://embassy.dev/book/
- RP2040 Datasheet: https://datasheets.raspberrypi.com/rp2040/rp2040-datasheet.pdf
- MIDI Specification: https://www.midi.org/specifications
- This project's CircuitPython firmware: `firmware/circuitpython/code.py`
