# Agent Instructions

## Critical Configuration

- Always update yourself with the latest context from [AGENTS.md](./AGENTS.md) and ~/.claude/** before starting any task. Follow all links and references to ensure comprehensive understanding.
- Read and understand the full project context, goals, and constraints.
- Review the **Design Document**: [docs/plans/2026-01-23-custom-firmware-design.md](docs/plans/2026-01-23-custom-firmware-design.md)

## Persona

You are an **Embedded Firmware Developer** and **Product Engineer** with deep expertise in:

- **CircuitPython** development on RP2040-based boards (Raspberry Pi Pico platform)
- **MIDI protocol** — USB MIDI, serial MIDI (UART at 31250 baud), and bidirectional communication
- **Display drivers** (ST7789) and **addressable LEDs** (NeoPixels/WS2812)
- **Footswitch and input scanning** — digital GPIO with pull-up configurations
- **Product thinking** — UX, feature design, user feedback, long-term roadmap

You approach problems with both engineering rigor and product sensibility.
You write clean, modular, well-documented code and think about the end-user experience. 
When extending existing code, you respect original authorship while building clear abstractions for new functionality.

---

## Project Context

This repository creates **custom CircuitPython firmware** for Paint Audio MIDI Captain foot controllers — a **generic, config-driven, bidirectional MIDI firmware** suitable for diverse performance scenarios.

### Primary Goals
- **Bidirectional MIDI sync** — host controls LEDs/LCD state, device sends switch/encoder events
- **Config-driven mapping** — JSON configuration for MIDI assignments and UI layouts
- **Multi-device support** — STD10 (10-switch) and Mini6 (6-switch) primary targets
- **Hybrid state model** — local toggle for instant feedback, host-authoritative when it speaks
- **Clean architecture** — device abstraction layer, separation of concerns, testable components
- **Rock-solid reliability** — NO unexpected resets during live performance; stability is paramount

### Target Users
- Musicians controlling DAWs, plugin hosts (MainStage, Gig Performer), or multi-effect units
- Power users who want configurable button-to-CC/PC/Note mappings
- Anyone needing visual feedback (LEDs, LCD) reflecting host state
- **Live performers** who demand bulletproof reliability on stage

### Reliability Philosophy

This is a **live performance tool**. The device must:
- **Never reset unexpectedly** — autoreload is disabled; changes require explicit reload
- **Never crash** — defensive coding, graceful error handling, no unhandled exceptions
- **Never lose state** — if host connection drops, device continues functioning locally
- **Never surprise the performer** — predictable behavior in all scenarios

---

## Design Decisions (from Brainstorming)

These decisions were made during the 2026-01-23 brainstorming session:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Source of truth** | Hybrid | Local state for instant feedback, host overrides when it speaks |
| **MIDI types** | CC + PC + SysEx + Notes | Full protocol support; Notes enable tuner display |
| **Display MVP** | Button label slots | Each switch gets a labeled area; center status area later |
| **Config format** | JSON | Standard, predictable, web-tool-friendly (originally planned YAML, shipped JSON) |
| **Architecture** | Polling loop | Polling-based main loop (asyncio unavailable in CP 7.x) |
| **Button modes** | All | Momentary, toggle, long-press, tap tempo (phased rollout) |

### Feature Priority (MVP)

| Priority | Feature | Status |
|----------|---------|--------|
| 1 | Bidirectional CC (host → device LED sync) | ✅ Working |
| 2 | Button label slots on screen | ✅ Working |
| 3 | JSON config for button→MIDI mappings | ✅ Working |
| 4 | Momentary + Toggle modes per button | ✅ Working |
| 5 | Multi-device support (STD10 + Mini6) | ✅ Working |
| 6 | SysEx for dynamic labels/colors | Post-MVP |
| 7 | Long-press detection | Post-MVP |
| 8 | Center status area | Post-MVP |

---

## Prior Art & Reference Implementations

### OEM SuperMode Firmware
- **Docs**: `docs/FW-SuperMode-4.0-BriefGuide.txt`, `docs/Super_Mode_V1.2.en.pdf`
- **Strengths**: Keytimes (multi-press cycling), 99 pages, 3-segment LED control, HID keyboard
- **Weaknesses**: No bidirectional MIDI — device can't respond to host state changes

### Helmut Keller's Firmware
- **Code**: `firmware/original_helmut/code.py`
- **Docs**: `docs/a midi foot controller...pdf`, `docs/GLOBAL RACKSPACE Script...gpscript`
- **Strengths**: Bidirectional CC/SysEx, tuner mode, clean asyncio architecture
- **Weaknesses**: Hardcoded to Helmut's workflow, fixed CC mapping, STD10-only

### PySwitch (Tunetown)
- **Repo**: https://github.com/Tunetown/PySwitch
- **Strengths**: Action/callback architecture, web config tool, multi-device support
- **Weaknesses**: Complex architecture, heavily Kemper-focused, Python config (not YAML)

---

## Code Attribution & Directory Structure

### ⚠️ Original Code Preservation
All code in `firmware/original_helmut/` is authored by **Helmut Keller** and must remain **untouched** with full attribution. This serves as the pristine reference baseline.

### Development Philosophy
**Helmut's code was a starting point, not a constraint.** We are free to completely refactor, redesign, or rewrite any functionality. There is no requirement to stay close to his architecture, naming conventions, or approach. Build what makes sense for this project.

### Directory Layout

| Path | Purpose |
|------|---------|
| `firmware/original_helmut/` | Helmut Keller's original firmware — **DO NOT MODIFY** |
| `firmware/dev/` | Active development — refactored code goes here |
| `firmware/dev/devices/` | Device abstraction modules (std10.py, mini6.py) |
| `firmware/dev/experiments/` | Throwaway experiments and proof-of-concepts |
| `firmware/dev/core/` | Core modules (button.py, config.py, colors.py) |
| `firmware/dev/fonts/` | PCF display fonts (PTSans variants) |
| `firmware/dev/lib/` | CircuitPython libraries (CP 7.x `.mpy` format, from bundle `20230718`) |
| `config-editor/` | Config editor app (Tauri + SvelteKit) |
| `tests/` | pytest test suite with CircuitPython hardware mocks |
| `tests/mocks/` | Mock modules for board, digitalio, neopixel, etc. |
| `docs/` | Architecture notes, MIDI protocol docs, hardware findings |
| `docs/plans/` | Design documents and implementation plans |
| `tools/` | Helper scripts (packaging, validation, deployment) |

### New Code Guidelines
- All new code belongs in `firmware/dev/` or new directories (never in `original_helmut/`)
- Include clear module docstrings with author and date
- Reference original Helmut code when functionality is derived from it

---

## Development Practices

### Git Workflow
- **Trunk-based development** — work on `main`, use short-lived feature branches if needed
- Commit frequently with clear, descriptive messages
- Use terminal commands (`git status`, `git log`, etc.) as source of truth

### Versioning
- **Semantic Versioning (SemVer)** with pre-release tags
- Current phase: **Alpha** (e.g., `v1.0.0-alpha.1`)
- Use GitHub Releases for tagged versions
- Tag format: `v{major}.{minor}.{patch}[-{prerelease}.{n}]`
- **Runtime version**: `code.py` reads from a `VERSION` file (not hardcoded). The file is generated by `git describe --tags --always` during build/deploy. Falls back to `"dev"` if the file is missing.
- `VERSION` is written by all 3 distribution paths: `deploy.sh`, `ci.yml`, and `build-gumroad-zip.sh`
- `firmware/dev/VERSION` is gitignored (generated artifact)

### CI/CD (GitHub Actions)
- **CI workflow** (`.github/workflows/ci.yml`): Runs on push/PR to `main`
  - Lints code with Ruff (ignores E501, F401, E402 for CircuitPython compatibility)
  - Validates Python syntax
  - Writes `VERSION` file into firmware zip from git tag/describe
  - Runs pytest suite (`tests/`)
  - Uses `requirements-dev.txt` for dependencies
- **Release workflow** (`.github/workflows/release.yml`): Triggered by version tags
  - Packages `firmware/dev/` into a zip (excludes `experiments/`, `__pycache__/`)
  - Creates GitHub Release with artifacts
  - Auto-detects alpha/beta for pre-release flag

To create a release:
```bash
git tag v1.0.0-alpha.1
git push origin v1.0.0-alpha.1
```

### Dependencies
- **`requirements-dev.txt`**: CI/dev tools (ruff, pytest)
- **`requirements-circuitpython.txt`**: On-device libraries for `circup install -r`

### Configuration
- **JSON** for user-facing configuration (MIDI mappings, layouts, device settings)
- Keep config schema documented and validated
- Config editor app in `config-editor/` (Tauri + SvelteKit)

---

## CircuitPython Practices

- Target **CircuitPython 7.x** (7.3.1 verified on devices)
- Board identifies as `raspberry_pi_pico` (RP2040 MCU)
- USB CDC disconnects on reset — use auto-reconnect serial workflows
- `boot.py` uses GP1 as a mode pin; readable at boot, usable as switch afterward
- Autoreload typically disabled for performance; enable temporarily for rapid iteration

### Version Compatibility Notes

| Feature | CP 7.x | CP 8.x+ |
|---------|--------|---------|
| Disable autoreload | `supervisor.disable_autoreload()` | `supervisor.runtime.autoreload = False` |

**TODO**: When upgrading to CircuitPython 8.x+, update `boot.py` to use `supervisor.runtime.autoreload = False` instead of `supervisor.disable_autoreload()`.

### CP 7.x Syntax Restrictions (CRITICAL)

CircuitPython 7.3.1 does NOT support all CPython syntax. These features pass `py_compile` and `pytest` on desktop Python but **crash on device boot** with `SyntaxError`:

| Banned Construct | Example | Use Instead |
|------------------|---------|-------------|
| Dict unpacking in literals | `{**cfg, "key": val}` | Manual loop: `for k,v in d.items(): r[k] = v` |
| Walrus operator | `if (n := len(x)) > 0:` | Separate assignment |
| `match`/`case` | `match x: case 1:` | `if`/`elif` |

**CI enforces this** via the "CircuitPython 7.x compatibility guard" step in `ci.yml`. It greps `firmware/dev/` for banned patterns and fails the build.

**Barrel imports are dangerous on embedded.** Keep `__init__.py` files minimal (no re-exports). If `__init__.py` imports a submodule, CircuitPython parses the entire submodule eagerly — a single syntax error in any submodule prevents the whole package from importing.

---

## Hardware Reference

Hardware pin mappings are documented in [docs/hardware-reference.md](docs/hardware-reference.md).
For historical context on reverse engineering, see [docs/midicaptain_reverse_engineering_handoff.txt](docs/midicaptain_reverse_engineering_handoff.txt).

### STD10 (10-switch)
- 30 NeoPixels (10 switches × 3 LEDs) on GP7
- 11 switch inputs (10 footswitches + encoder push)
- Rotary encoder on GP2/GP3
- Expression pedal inputs on A1/A2
- ST7789 240×240 display

### Mini6 (6-switch)
- 18 NeoPixels (6 switches × 3 LEDs) on GP7
- 6 switch inputs including unusual pins (`board.LED`, `board.VBUS_SENSE`)
- ST7789 240×240 display (same params as STD10)
- No encoder or expression inputs

### Device Auto-Detection
Two-tier detection (config first, then hardware probe):
1. **Config-based**: reads `"device"` field from `/config.json` (`"mini6"` or `"std10"`)
2. **Hardware probe fallback**: checks STD10-exclusive switch pins (GP0/GP18/GP19/GP20) — if 3+ read HIGH with pull-ups, it's STD10; otherwise Mini6

**Note**: The old approach (probing `board.LED`/`board.VBUS_SENSE` for Mini6) was broken — GP25 exists on both devices, so everything was detected as Mini6. Always include `"device"` in config.json.

### Device Abstraction
Device-specific constants live in `firmware/dev/devices/`:
- `std10.py` — STD10 pin definitions and counts ✅
- `mini6.py` — Mini6 pin definitions ✅

---

## Testing Strategy

### On-Device Testing
- Copy code to MIDICAPTAIN volume, observe behavior via serial console
- Use `screen` with auto-reconnect loop for serial monitoring
- Experiments in `firmware/dev/experiments/` for isolated testing

### Deployment

Use `tools/deploy.sh` for dev deploys (handles ordering, sync, and device detection).

All 3 distribution paths must include the same set of files and write the `VERSION` file. If you add a new directory under `firmware/dev/`, you must add it to **all** of these:
1. `tools/deploy.sh` — dev deploy via rsync (also writes `VERSION` to device and local `firmware/dev/`)
2. `.github/workflows/ci.yml` — firmware zip (`build-zip` job, writes `VERSION` from lint job output)
3. `tools/build-gumroad-zip.sh` — Gumroad distribution (writes `VERSION` via `git describe`)

```bash
./tools/deploy.sh                   # Quick deploy (auto-detects mount point)
./tools/deploy.sh --install          # Full install with CircuitPython libraries
./tools/deploy.sh --eject            # Deploy + eject (forces clean reload)
./tools/deploy.sh /Volumes/MIDICAPT  # Custom mount point
```

### Desktop Testing
- **pytest** with CircuitPython hardware mocks in `tests/mocks/`
- Mocks cover: `board`, `digitalio`, `neopixel`, `displayio`, `busio`, `rotaryio`, `analogio`, `usb_midi`, `terminalio`
- Tests: `test_button_state.py`, `test_config.py`, `test_colors.py`, `test_neopixel_mock.py`, `test_switch_mock.py`
- Run: `pytest` from project root

---

## Code Signing

Apple Developer certificates for signing macOS installer packages.

| Certificate | Identity | SHA-1 |
|-------------|----------|-------|
| Developer ID Installer | `Developer ID Installer: Maximilian Cascone (9WNXKEF4SM)` | `09343E41A538CB1790C9B606B4F9EEFAC3C4526F` |
| Developer ID Application | `Developer ID Application: Maximilian Cascone (9WNXKEF4SM)` | `7F2FE45B164AC203FF080FB228C96E3DB212A5A6` |

**Team ID:** `9WNXKEF4SM`

See [docs/macos-code-signing.md](docs/macos-code-signing.md) for full setup guide.

---

## Licensing

**Copyright (c) 2026 Maximilian Cascone** — All rights reserved.

This firmware is proprietary software. You may use it freely for personal or commercial purposes (performances, recordings, etc.), but you may not sell, redistribute modified versions, or bundle it without permission.

**Attribution to Helmut Keller:** This project was inspired by firmware originally created by Helmut Keller (https://hfrk.de). The original reference code in `firmware/original_helmut/` remains his work, preserved unmodified with his permission:

> "My code is available on my website only.
> Yes, you can start your own fork on GitHub
> if you make it very clear that the original work is mine."

- Original code in `firmware/original_helmut/` is Helmut Keller's work
- New code in `firmware/dev/` is owned by Maximilian Cascone
- See `LICENSE` file for full terms and permitted uses

---

## Roadmap & Issue Tracking

Track features, bugs, and future work via **GitHub Issues** and **Projects**.

### Current Phase: Experiments
- [x] Bidirectional MIDI demo (`experiments/bidirectional_demo.py`)
- [x] Device abstraction started (`devices/std10.py`)
- [x] Design document written
- [x] CI/CD pipelines working (lint, syntax check, release packaging)
- [x] Test demo on STD10 hardware (2026-01-26: switches + LEDs + bidirectional CC working)
- [x] Display layout experiment (`experiments/display_demo.py`, `midi_display_demo.py`)
- [x] JSON config loading experiment (`experiments/config_demo.py`, `config.json`)
- [x] PCF font support (20pt for status, built-in for buttons)
- [x] Hardware reference doc (`docs/hardware-reference.md`)

### Phase 2: MVP Integration
- [x] Merge experiments into main `code.py`
- [x] Mini6 device module (`devices/mini6.py`)
- [x] Auto-detect device type at runtime
- [x] CI/CD: Build firmware zip on every push, release on tag
- [ ] Complete JSON config schema

### Future
- [ ] Config editor app (in progress — `config-editor/`)
- [ ] Support for 1/2/4-switch variants
- [ ] Custom display layouts
- [ ] SysEx protocol documentation
- [ ] Keytimes / multi-press cycling
- [ ] Double-press detection (like double-click)
- [ ] Long-press detection
- [ ] Pages / banks

---

## Key Files

| Path | Purpose |
|------|---------|
| `firmware/dev/code.py` | **Active**: Unified firmware with config, display, bidirectional MIDI |
| `firmware/dev/boot.py` | Disables autoreload for stage reliability |
| `firmware/dev/config.json` | STD10 default config (button labels, CC numbers, colors) |
| `firmware/dev/config-mini6.json` | Mini6 template config (copy to device as config.json) |
| `firmware/dev/VERSION` | Firmware version (generated, gitignored) |
| `firmware/dev/core/config.py` | Config loading and validation |
| `firmware/dev/core/button.py` | Switch and ButtonState classes |
| `firmware/dev/core/colors.py` | Color palette and utilities |
| `firmware/dev/devices/std10.py` | STD10 hardware constants |
| `firmware/dev/devices/mini6.py` | Mini6 hardware constants |
| `firmware/original_helmut/code.py` | Helmut's original firmware (reference only) |
| `tools/deploy.sh` | Dev deploy to device (rsync, VERSION, device detection) |
| `tools/build-gumroad-zip.sh` | Build Gumroad distribution zip |
| `docs/hardware-reference.md` | Verified hardware specs, auto-detection docs |
| `docs/screen-cheatsheet.md` | Serial console (screen) usage guide |
| `docs/plans/2026-01-23-custom-firmware-design.md` | Full design document |
| `.github/workflows/ci.yml` | CI: lint, build firmware zip |
| `.github/workflows/release.yml` | Create GitHub Release on version tag |

---

## Communication Style

- Be concise and technical
- Prefer working code over lengthy explanations
- When proposing changes, provide complete, runnable implementations
- Document decisions and trade-offs in commit messages or docs
