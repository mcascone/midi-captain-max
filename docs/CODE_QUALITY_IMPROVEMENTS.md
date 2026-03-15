# Code Quality Improvements Tracker

**Created:** March 15, 2026  
**Branch:** `refactor/code-quality-improvements`  
**Status:** Planning Phase

This document tracks identified code quality improvements and refactoring opportunities for the MIDI Captain MAX project.

---

## 📊 Project Metrics

- **Total Lines of Code:** ~110,236 (Python, TypeScript, Rust)
- **Firmware (`code.py`):** 1,678 lines ⚠️ *Needs modularization*
- **Rust Config Module:** 1,601 lines ⚠️ *Needs splitting*
- **Button Settings Panel:** 960 lines ⚠️ *Complex component*
- **Main Route Component:** 653 lines ⚠️ *Too much logic*

---

## 🔴 Critical Priority Issues

### 1. Overly Large Files

**Problem:** Several files exceed 600 lines, making them difficult to maintain and test.

| File | Lines | Recommendation |
|------|-------|----------------|
| `firmware/dev/code.py` | 1,678 | Extract to handlers/ modules |
| `config-editor/src-tauri/src/config.rs` | 1,601 | Split into types/validation/deserialize |
| `config-editor/src/lib/components/ButtonSettingsPanel.svelte` | 960 | Break into sub-components |
| `config-editor/src/routes/+page.svelte` | 653 | Extract business logic |

**Action Items:**
- [ ] Create `firmware/dev/handlers/` directory
  - [ ] `handlers/midi.py` - MIDI I/O functions
  - [ ] `handlers/display.py` - Display/label functions
  - [ ] `handlers/button.py` - Button state management
  - [ ] `handlers/encoder.py` - Encoder/expression handling
- [ ] Split `config.rs` into:
  - [ ] `config/types.rs` - Struct definitions
  - [ ] `config/validation.rs` - Validation logic
  - [ ] `config/deserialize.rs` - Serde helpers
- [ ] Break down `ButtonSettingsPanel.svelte`:
  - [ ] Extract event editor sub-component
  - [ ] Extract keytimes editor sub-component
  - [ ] Extract profile selector logic

**Estimated Effort:** 2-3 weeks

---

### 2. Broad Exception Handling (13 occurrences)

**Problem:** Silent failure patterns make debugging difficult and mask critical bugs.

**Locations:**
- `firmware/dev/boot.py`: Line 49
- `firmware/dev/code.py`: Lines 92, 116, 176, 231, 494, 530, 934, 1025, 1116, 1227, 1636
- `firmware/dev/core/config.py`: Line 34

**Current Pattern:**
```python
try:
    risky_operation()
except Exception:
    pass  # Silent failure
```

**Should Be:**
```python
try:
    risky_operation()
except FileNotFoundError:
    print("Config file not found, using defaults")
    return default_config
except json.JSONDecodeError as e:
    print(f"Invalid JSON in config: {e}")
    return default_config
```

**Action Items:**
- [ ] Audit all 13 occurrences
- [ ] Replace with specific exception types
- [ ] Add logging for all exceptions
- [ ] Create error recovery strategies
- [ ] Update tests to verify error paths

**Estimated Effort:** 1 week

---

## 🟡 Medium Priority Issues

### 3. Circular Import Risk

**Problem:** Main `code.py` imports from `core/` modules, but dependencies are fragile.

**Action Items:**
- [ ] Create `firmware/dev/utils/` directory for shared utilities
- [ ] Move pure functions (no hardware deps) to utils
- [ ] Establish clear import hierarchy: `utils → core → handlers → main`
- [ ] Document import rules in `firmware/dev/README.md`

**Estimated Effort:** 3-4 days

---

### 4. Magic Numbers Throughout Code

**Problem:** Hardcoded values make code difficult to tune and understand.

**Examples:**
```python
PC_FLASH_DURATION_MS = 200  # Hardcoded in code.py
LABEL_RETURN_TIMEOUT_SEC = 3.0  # Hardcoded in code.py
LED_DIM_BRIGHTNESS = 0.3  # Scattered throughout
```

**Action Items:**
- [ ] Create `firmware/dev/core/constants.py`
- [ ] Extract all magic numbers with descriptive names
- [ ] Group constants by category (display, LEDs, MIDI, timing)
- [ ] Update all references to use constants

**Example Structure:**
```python
# firmware/dev/core/constants.py

# Display Timeouts (seconds)
LABEL_RETURN_TIMEOUT_SEC = 3.0
STATUS_MESSAGE_TIMEOUT_SEC = 2.0

# LED Behavior (milliseconds)
PC_FLASH_DURATION_MS = 200
LED_BLINK_INTERVAL_MS = 500

# LED Brightness (0.0 - 1.0)
LED_DIM_BRIGHTNESS = 0.3
LED_FULL_BRIGHTNESS = 1.0
LED_OFF_BRIGHTNESS = 0.0

# MIDI Configuration
DEFAULT_MIDI_CHANNEL = 0
MAX_MIDI_VALUE = 127
MIN_MIDI_VALUE = 0
```

**Estimated Effort:** 2-3 days

---

### 5. No Frontend Testing

**Problem:** Config editor has zero automated tests for critical logic.

**Missing Coverage:**
- Form validation logic (`formStore.ts`)
- State management (`stores.ts`)
- Component rendering
- API integration (`api.ts`)

**Action Items:**
- [ ] Install test dependencies:
  ```bash
  npm install -D vitest @testing-library/svelte @testing-library/jest-dom
  ```
- [ ] Create `config-editor/src/lib/__tests__/` directory
- [ ] Write unit tests for:
  - [ ] `formStore.ts` - validation, undo/redo, normalizeConfig
  - [ ] `validation.ts` - all validation functions
  - [ ] `api.ts` - API wrappers (with mocks)
- [ ] Add test scripts to `package.json`:
  ```json
  "scripts": {
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage"
  }
  ```
- [ ] Set up CI test job in `.github/workflows/ci.yml`
- [ ] Target: >80% coverage on critical modules

**Estimated Effort:** 1 week

---

### 6. Inconsistent Validation (Frontend vs Backend)

**Problem:** TypeScript validation doesn't match Rust validation, leading to bugs.

**Recent Example:** Channel validation was missing in TypeScript but present in Rust.

**Action Items:**
- [ ] Install `ts-rs` in Rust project:
  ```toml
  [dependencies]
  ts-rs = "7.0"
  ```
- [ ] Add `#[derive(TS)]` to all config structs
- [ ] Generate TypeScript bindings
- [ ] Replace manual type definitions in `types.ts`
- [ ] Update validation to consume generated types
- [ ] Add CI check to ensure bindings are up-to-date

**Estimated Effort:** 3-4 days

---

## 🟢 Nice to Have

### 7. Documentation Reorganization

**Current Structure:**
```
docs/
├── Various .md files (scattered)
├── plans/ (design docs)
├── features/ (feature specs)
└── reports/
```

**Proposed Structure:**
```
docs/
├── README.md (overview, getting started)
├── architecture/ (high-level design, ADRs)
├── api/ (auto-generated API reference)
├── guides/ (how-to guides)
└── decisions/ (Architecture Decision Records)
```

**Action Items:**
- [ ] Reorganize existing docs into new structure
- [ ] Set up auto-generated API docs:
  - [ ] Python: `pdoc` or `sphinx`
  - [ ] Rust: `cargo doc`
  - [ ] TypeScript: `typedoc`
- [ ] Create `ADR-001-device-detection.md` (example ADR)
- [ ] Add navigation index to `docs/README.md`

**Estimated Effort:** 4-5 days

---

### 8. Performance Monitoring

**Problem:** No instrumentation to detect slow operations in main loop.

**Action Items:**
- [ ] Create `firmware/dev/utils/timing.py`:
  ```python
  import time
  
  def measure_time(func, name, threshold_ms=10):
      """Measure function execution time and warn if over threshold."""
      start = time.monotonic()
      result = func()
      elapsed = (time.monotonic() - start) * 1000  # Convert to ms
      if elapsed > threshold_ms:
          print(f"⚠️ {name} took {elapsed:.1f}ms")
      return result
  ```
- [ ] Add timing to critical main loop operations
- [ ] Monitor MIDI handling, display updates, button scanning
- [ ] Document performance budgets in `docs/architecture/performance.md`

**Estimated Effort:** 2-3 days

---

### 9. CI/CD Enhancements

**Problem:** Slow builds, no caching, no coverage reporting.

**Action Items:**
- [ ] Add dependency caching to CI:
  ```yaml
  - uses: actions/cache@v4
    with:
      path: |
        ~/.cache/pip
        ~/.cargo
        config-editor/node_modules
      key: ${{ runner.os }}-deps-${{ hashFiles('**/requirements*.txt', 'Cargo.lock', 'package-lock.json') }}
  ```
- [ ] Add code coverage reporting:
  ```yaml
  - name: Run tests with coverage
    run: pytest --cov=firmware/dev --cov-report=xml
  
  - name: Upload coverage
    uses: codecov/codecov-action@v4
  ```
- [ ] Add matrix testing for multiple Python versions
- [ ] Add frontend test job
- [ ] Add Rust test job

**Estimated Effort:** 1 day

---

## 🏗️ Architectural Improvements

### Firmware Modularization Plan

**Phase 1: Extract Handlers (Week 1)**
1. Create `firmware/dev/handlers/` directory
2. Move MIDI functions from `code.py` → `midi_handler.py`
3. Move display functions → `display_handler.py`
4. Move button functions → `button_handler.py`
5. Move encoder/expression → `encoder_handler.py`
6. Update imports in `code.py`
7. Run full test suite

**Phase 2: Improve Error Handling (Week 2)**
1. Audit all exception handling
2. Replace broad exceptions with specific types
3. Add logging throughout
4. Create error recovery strategies
5. Update tests for error paths

**Phase 3: Add Frontend Tests (Week 3)**
1. Set up Vitest
2. Write tests for `formStore.ts`
3. Write tests for `validation.ts`
4. Write tests for `api.ts`
5. Achieve >80% coverage

**Phase 4: Type Safety (Week 4)**
1. Add `ts-rs` to Rust
2. Generate TypeScript bindings
3. Replace manual type definitions
4. Update validation to use generated types
5. Add CI check for type consistency

---

## 📈 Performance Optimizations

### Firmware Optimizations

**Batch LED Updates**
- [ ] Current: Updates each LED individually
- [ ] Proposed: Batch all LED updates, call `pixels.show()` once per loop
- [ ] Expected impact: Reduce loop time by ~30%

**Cache Font Objects**
- [ ] Current: Loads fonts on every label update
- [ ] Proposed: Load once at startup, cache references
- [ ] Expected impact: Reduce display update latency

**Optimize MIDI Parsing**
- [ ] Current: Creates new message objects for each parse
- [ ] Proposed: Use bytearray views to avoid allocations
- [ ] Expected impact: Reduce memory pressure in tight loops

### Config Editor Optimizations

**Already Good:**
- ✅ Debounced form updates (500ms)
- ✅ Efficient state management with Svelte stores

**Future Considerations:**
- [ ] Virtual scrolling (only if >20 buttons become common)
- [ ] Lazy load profiles (load on-demand vs upfront)

---

## 🛡️ Security & Maintenance

### Security Enhancements

**Action Items:**
- [ ] Create `SECURITY.md` with vulnerability reporting process
- [ ] Set up Dependabot for automated dependency updates:
  ```yaml
  # .github/dependabot.yml
  version: 2
  updates:
    - package-ecosystem: "pip"
      directory: "/"
      schedule:
        interval: "weekly"
    - package-ecosystem: "npm"
      directory: "/config-editor"
      schedule:
        interval: "weekly"
    - package-ecosystem: "cargo"
      directory: "/config-editor/src-tauri"
      schedule:
        interval: "weekly"
  ```
- [ ] Add security linting to CI (Bandit for Python, cargo-audit for Rust)
- [ ] Create `CHANGELOG.md` for tracking security patches

**Estimated Effort:** 1 day

---

## 📝 Quick Wins (High Impact, Low Effort)

These can be done immediately for quick improvements:

### 1. Update `.gitignore`
**Current Issues:**
- Missing `node_modules/`
- Missing `*.log`
- Missing editor swap files

**Add:**
```gitignore
# Logs
*.log
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Node
node_modules/

# Editor files
*.swp
*.swo
*~
.idea/

# OS
.DS_Store
Thumbs.db
```

**Status:** ⬜ Not Started

---

### 2. Add Test Scripts to `package.json`

**Add:**
```json
"scripts": {
  "test": "vitest",
  "test:ui": "vitest --ui",
  "test:coverage": "vitest --coverage",
  "lint": "eslint src --ext .ts,.svelte"
}
```

**Status:** ⬜ Not Started

---

### 3. Create `CONTRIBUTING.md`

**Include:**
- Code style guidelines (Ruff for Python, eslint for TS)
- PR process
- Testing requirements
- Commit message conventions
- How to run tests locally

**Status:** ⬜ Not Started

---

### 4. Extract Constants

**Create:** `firmware/dev/core/constants.py`

**Status:** ⬜ Not Started

---

## 📊 Progress Tracking

### Overall Status

| Priority | Category | Completed | In Progress | Not Started | Total |
|----------|----------|-----------|-------------|-------------|-------|
| 🔴 Critical | Modularization | 0 | 0 | 4 | 4 |
| 🔴 Critical | Error Handling | 0 | 0 | 1 | 1 |
| 🟡 Medium | Architecture | 0 | 0 | 4 | 4 |
| 🟢 Nice to Have | Documentation | 0 | 0 | 3 | 3 |
| **Total** | | **0** | **0** | **12** | **12** |

### Estimated Timeline

- **Quick Wins:** 1-2 days
- **Phase 1 (Handlers):** 1 week
- **Phase 2 (Error Handling):** 1 week
- **Phase 3 (Frontend Tests):** 1 week
- **Phase 4 (Type Safety):** 1 week
- **Total:** 4-5 weeks for all critical and medium priority items

---

## 📋 Next Steps

1. ✅ Create feature branch: `refactor/code-quality-improvements`
2. ⬜ Start with Quick Wins (`.gitignore`, constants, etc.)
3. ⬜ Begin Phase 1: Extract handlers from `code.py`
4. ⬜ Run tests after each refactor to ensure no breakage
5. ⬜ Create PRs for each phase with clear descriptions

---

## 🔗 References

- [Original Investigation Analysis](../AGENTS.md)
- [Python Style Guide (PEP 8)](https://pep8.org/)
- [CircuitPython Best Practices](https://learn.adafruit.com/circuitpython-essentials)
- [Svelte Component Best Practices](https://svelte.dev/docs/svelte/best-practices)
- [Rust API Guidelines](https://rust-lang.github.io/api-guidelines/)

---

**Last Updated:** March 15, 2026  
**Maintained By:** Development Team
