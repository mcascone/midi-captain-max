//! MIDI Captain Firmware - Rust + Embassy
//!
//! RP2040-based MIDI foot controller firmware using Embassy async runtime.
//! Replaces CircuitPython implementation with native Rust for:
//! - Zero GC pauses (deterministic timing for MIDI clock sync)
//! - True async tasks (concurrent MIDI I/O, display rendering, input scanning)
//! - Dual-core utilization (core 0: MIDI/logic, core 1: display/LEDs)
//! - Shared config types with the Tauri editor backend
//!
//! Target Hardware: Paint Audio MIDI Captain STD10 / Mini6
//! MCU: RP2040 (Raspberry Pi Pico platform)

#![no_std]
#![no_main]

use defmt::*;
use embassy_executor::Spawner;
use embassy_rp::gpio;
use embassy_time::Timer;
use {defmt_rtt as _, panic_probe as _};

/// Main entry point - runs on core 0
#[embassy_executor::main]
async fn main(_spawner: Spawner) {
    info!("MIDI Captain Firmware (Rust + Embassy)");
    info!("Initializing...");

    let p = embassy_rp::init(Default::default());

    // TODO: Device detection (STD10 vs Mini6)
    // TODO: Load config from Flash
    // TODO: Initialize USB MIDI
    // TODO: Initialize GPIO (switches, encoder, expression pedals)
    // TODO: Initialize SPI display (ST7789)
    // TODO: Initialize NeoPixels (WS2812)
    
    // Placeholder blink loop
    let mut led = gpio::Output::new(p.PIN_25, gpio::Level::Low);
    
    info!("Entering main loop");
    loop {
        led.set_high();
        Timer::after_millis(500).await;
        led.set_low();
        Timer::after_millis(500).await;
    }
}
