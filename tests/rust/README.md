# Rust Firmware Tests

Unit and integration tests for the Rust firmware live here.

## Running Tests

The firmware crate is a `no_std` binary (`[[bin]] test = false`), so standard `cargo test` won't work.

To build the firmware:
```bash
cd firmware/rust
cargo build --release
```

To flash to hardware (via probe-rs):
```bash
cargo run --release
```

## Future Testing Strategy

- Host-side simulation tests (once abstraction layers are in place)
- Hardware-in-the-loop tests with actual RP2040 devices
- Unit tests for config parsing and validation logic
