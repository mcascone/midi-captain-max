//! Configuration validation logic
//!
//! Validates MIDI Captain configuration against device constraints and MIDI spec.

use super::models::*;
use super::types::*;

impl MidiCaptainConfig {
    /// Validate the configuration
    pub fn validate(&self) -> Result<(), Vec<String>> {
        let mut errors = Vec::new();

        // Validate global channel (0-15 internally, display as 1-16)
        if let Some(ch) = self.global_channel {
            if ch > 15 {
                errors.push(format!(
                    "Global channel value {} is invalid (must be 1-16, stored as 0-15)",
                    ch + 1
                ));
            }
        }

        // Check button count matches device
        let expected_buttons = match self.device {
            DeviceType::Std10 => 10,
            DeviceType::Mini6 => 6,
        };

        if self.buttons.len() != expected_buttons {
            errors.push(format!(
                "Expected {} buttons for {:?}, found {}",
                expected_buttons,
                self.device,
                self.buttons.len()
            ));
        }

        // Validate CC numbers (0-127) and button-specific fields
        for (i, button) in self.buttons.iter().enumerate() {
            if let Some(cc) = button.cc {
                if cc > 127 {
                    errors.push(format!("Button {} CC {} exceeds 127", i + 1, cc));
                }
            }
            if button.label.len() > 6 {
                errors.push(format!(
                    "Button {} label '{}' exceeds 6 chars",
                    i + 1,
                    button.label
                ));
            }
            if let Some(ref long_label) = button.long_press_label {
                if long_label.len() > 6 {
                    errors.push(format!(
                        "Button {} long_press_label '{}' exceeds 6 chars",
                        i + 1,
                        long_label
                    ));
                }
            }
            if let Some(ch) = button.channel {
                if ch > 15 {
                    errors.push(format!(
                        "Button {} channel {} is invalid (must be 1-16)",
                        i + 1,
                        ch + 1
                    ));
                }
            }
            if let Some(val) = button.cc_on {
                if val > 127 {
                    errors.push(format!("Button {} cc_on {} exceeds 127", i + 1, val));
                }
            }
            if let Some(val) = button.cc_off {
                if val > 127 {
                    errors.push(format!("Button {} cc_off {} exceeds 127", i + 1, val));
                }
            }
            if let Some(ms) = button.flash_ms {
                if ms < 50 || ms > 5000 {
                    errors.push(format!(
                        "Button {} flash_ms {} out of range (50-5000)",
                        i + 1,
                        ms
                    ));
                }
            }
            if let Some(brightness) = button.dim_brightness {
                if brightness > 100 {
                    errors.push(format!(
                        "Button {} dim_brightness {} exceeds 100 (must be 0-100)",
                        i + 1,
                        brightness
                    ));
                }
            }

            // Validate event command arrays (press, release, long_press, long_release)
            let validate_command = |cmd: &MidiCommand, event_name: &str, cmd_idx: usize| {
                let mut cmd_errors = Vec::new();
                if let Some(ch) = cmd.channel {
                    if ch > 15 {
                        cmd_errors.push(format!(
                            "Button {} {}.{} channel {} invalid (must be 0-15)",
                            i + 1,
                            event_name,
                            cmd_idx,
                            ch
                        ));
                    }
                }
                if let Some(cc) = cmd.cc {
                    if cc > 127 {
                        cmd_errors.push(format!(
                            "Button {} {}.{} cc {} exceeds 127",
                            i + 1,
                            event_name,
                            cmd_idx,
                            cc
                        ));
                    }
                }
                if let Some(val) = cmd.value {
                    if val > 127 {
                        cmd_errors.push(format!(
                            "Button {} {}.{} value {} exceeds 127",
                            i + 1,
                            event_name,
                            cmd_idx,
                            val
                        ));
                    }
                }
                if let Some(note) = cmd.note {
                    if note > 127 {
                        cmd_errors.push(format!(
                            "Button {} {}.{} note {} exceeds 127",
                            i + 1,
                            event_name,
                            cmd_idx,
                            note
                        ));
                    }
                }
                if let Some(vel) = cmd.velocity {
                    if vel > 127 {
                        cmd_errors.push(format!(
                            "Button {} {}.{} velocity {} exceeds 127",
                            i + 1,
                            event_name,
                            cmd_idx,
                            vel
                        ));
                    }
                }
                if let Some(prog) = cmd.program {
                    if prog > 127 {
                        cmd_errors.push(format!(
                            "Button {} {}.{} program {} exceeds 127",
                            i + 1,
                            event_name,
                            cmd_idx,
                            prog
                        ));
                    }
                }
                if let Some(step) = cmd.pc_step {
                    if step < 1 || step > 127 {
                        cmd_errors.push(format!(
                            "Button {} {}.{} pc_step {} out of range (1-127)",
                            i + 1,
                            event_name,
                            cmd_idx,
                            step
                        ));
                    }
                }
                if let Some(thresh) = cmd.threshold_ms {
                    if thresh < 50 || thresh > 10000 {
                        cmd_errors.push(format!(
                            "Button {} {}.{} threshold_ms {} out of range (50-10000)",
                            i + 1,
                            event_name,
                            cmd_idx,
                            thresh
                        ));
                    }
                }
                cmd_errors
            };

            if let Some(ref cmds) = button.press {
                for (idx, cmd) in cmds.iter().enumerate() {
                    errors.extend(validate_command(cmd, "press", idx));
                }
            }
            if let Some(ref cmds) = button.release {
                for (idx, cmd) in cmds.iter().enumerate() {
                    errors.extend(validate_command(cmd, "release", idx));
                }
            }
            if let Some(ref cmds) = button.long_press {
                for (idx, cmd) in cmds.iter().enumerate() {
                    errors.extend(validate_command(cmd, "long_press", idx));
                }
            }
            if let Some(ref cmds) = button.long_release {
                for (idx, cmd) in cmds.iter().enumerate() {
                    errors.extend(validate_command(cmd, "long_release", idx));
                }
            }

            // Validate per-state event arrays (states[*].press/release/long_press/long_release)
            if let Some(ref states) = button.states {
                for (state_idx, state) in states.iter().enumerate() {
                    let state_num = state_idx + 1;

                    if let Some(ref cmds) = state.press {
                        for (cmd_idx, cmd) in cmds.iter().enumerate() {
                            errors.extend(validate_command(
                                cmd,
                                &format!("states[{}].press", state_num),
                                cmd_idx,
                            ));
                        }
                    }
                    if let Some(ref cmds) = state.release {
                        for (cmd_idx, cmd) in cmds.iter().enumerate() {
                            errors.extend(validate_command(
                                cmd,
                                &format!("states[{}].release", state_num),
                                cmd_idx,
                            ));
                        }
                    }
                    if let Some(ref cmds) = state.long_press {
                        for (cmd_idx, cmd) in cmds.iter().enumerate() {
                            errors.extend(validate_command(
                                cmd,
                                &format!("states[{}].long_press", state_num),
                                cmd_idx,
                            ));
                        }
                    }
                    if let Some(ref cmds) = state.long_release {
                        for (cmd_idx, cmd) in cmds.iter().enumerate() {
                            errors.extend(validate_command(
                                cmd,
                                &format!("states[{}].long_release", state_num),
                                cmd_idx,
                            ));
                        }
                    }
                }
            }

            // select_group rules: not allowed with momentary, tap, or keytimes > 1
            if let Some(_) = button.select_group {
                if button.mode == ButtonMode::Momentary {
                    errors.push(format!(
                        "Button {} select_group not supported for momentary mode",
                        i + 1
                    ));
                }
                if button.mode == ButtonMode::Tap {
                    errors.push(format!(
                        "Button {} select_group not supported for tap mode",
                        i + 1
                    ));
                }
                if let Some(kt) = button.keytimes {
                    if kt > 1 {
                        errors.push(format!(
                            "Button {} select_group not supported with keytimes > 1",
                            i + 1
                        ));
                    }
                }
            }
            if let Some(ds) = button.default_selected {
                // no extra check here; normalization performed elsewhere
                let _ = ds;
            }
        }

        // Validate encoder if present
        if let Some(ref enc) = self.encoder {
            // Mini6 does not support encoder
            if self.device == DeviceType::Mini6 {
                errors.push("Mini6 does not support encoder".to_string());
            }
            if enc.cc > 127 {
                errors.push(format!("Encoder CC {} exceeds 127", enc.cc));
            }
            if enc.label.len() > 8 {
                errors.push(format!("Encoder label '{}' exceeds 8 chars", enc.label));
            }
            if enc.max < enc.min {
                errors.push(format!(
                    "Encoder max ({}) must be >= min ({})",
                    enc.max, enc.min
                ));
            }
            if enc.initial < enc.min || enc.initial > enc.max {
                errors.push(format!(
                    "Encoder initial ({}) must be between min ({}) and max ({})",
                    enc.initial, enc.min, enc.max
                ));
            }
            if let Some(ch) = enc.channel {
                if ch > 15 {
                    errors.push(format!(
                        "Encoder channel {} is invalid (must be 1-16)",
                        ch + 1
                    ));
                }
            }
            if let Some(ref push) = enc.push {
                if push.cc > 127 {
                    errors.push(format!("Encoder push CC {} exceeds 127", push.cc));
                }
                if push.label.len() > 8 {
                    errors.push(format!(
                        "Encoder push label '{}' exceeds 8 chars",
                        push.label
                    ));
                }
                if let Some(ch) = push.channel {
                    if ch > 15 {
                        errors.push(format!(
                            "Encoder push channel {} is invalid (must be 1-16)",
                            ch + 1
                        ));
                    }
                }
                if let Some(val) = push.cc_on {
                    if val > 127 {
                        errors.push(format!("Encoder push cc_on {} exceeds 127", val));
                    }
                }
                if let Some(val) = push.cc_off {
                    if val > 127 {
                        errors.push(format!("Encoder push cc_off {} exceeds 127", val));
                    }
                }
            }
        }

        // Validate expression pedals if present
        if let Some(ref exp) = self.expression {
            // Mini6 does not support expression pedals
            if self.device == DeviceType::Mini6 {
                errors.push("Mini6 does not support expression pedals".to_string());
            }
            if exp.exp1.cc > 127 {
                errors.push(format!("EXP1 CC {} exceeds 127", exp.exp1.cc));
            }
            if exp.exp1.label.len() > 8 {
                errors.push(format!("EXP1 label '{}' exceeds 8 chars", exp.exp1.label));
            }
            if exp.exp1.max < exp.exp1.min {
                errors.push(format!(
                    "EXP1 max ({}) must be >= min ({})",
                    exp.exp1.max, exp.exp1.min
                ));
            }
            if let Some(ch) = exp.exp1.channel {
                if ch > 15 {
                    errors.push(format!("EXP1 channel {} is invalid (must be 1-16)", ch + 1));
                }
            }
            if exp.exp2.cc > 127 {
                errors.push(format!("EXP2 CC {} exceeds 127", exp.exp2.cc));
            }
            if exp.exp2.label.len() > 8 {
                errors.push(format!("EXP2 label '{}' exceeds 8 chars", exp.exp2.label));
            }
            if exp.exp2.max < exp.exp2.min {
                errors.push(format!(
                    "EXP2 max ({}) must be >= min ({})",
                    exp.exp2.max, exp.exp2.min
                ));
            }
            if let Some(ch) = exp.exp2.channel {
                if ch > 15 {
                    errors.push(format!("EXP2 channel {} is invalid (must be 1-16)", ch + 1));
                }
            }
        }

        if errors.is_empty() {
            Ok(())
        } else {
            Err(errors)
        }
    }
}
