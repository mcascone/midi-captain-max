def handle_switches():
    """Handle footswitch presses using event-based dispatch.
    
    Refactored to use the new multi-command event system:
    - "press" event: dispatched when button is pressed
    - "release" event: dispatched when button is released (short press)
    - "long_press" event: dispatched when hold threshold is exceeded
    - "long_release" event: dispatched when button released after long press
    
    State management (toggle, momentary, keytimes, select_group) is handled
    here, while MIDI dispatch is delegated to _send_action_from_cfg().
    """
    # STD10: index 0 is encoder push, 1-10 are footswitches
    # Mini6: indices 0-5 are footswitches (no encoder)
    start_idx = 1 if HAS_ENCODER else 0
    now = time.monotonic()
    
    for i in range(start_idx, len(switches)):
        sw = switches[i]
        changed, pressed = sw.changed()

        # Convert to 1-indexed button number and index
        btn_num = i if HAS_ENCODER else i + 1
        idx = btn_num - 1
        btn_state = button_states[idx]
        btn_config = buttons[idx] if idx < len(buttons) else {"cc": 20 + idx}

        mode = btn_config.get("mode", "toggle")
        
        # Check for long-press configuration
        long_press_cfg = btn_config.get("long_press")
        long_release_cfg = btn_config.get("long_release")
        long_enabled = bool(long_press_cfg or long_release_cfg)

        # --- Handle edge events ---
        if changed:
            if pressed:
                # PRESSED: Initialize press timing
                if not press_start_times[idx]:
                    press_start_times[idx] = now
                    long_press_triggered[idx] = False
                    short_action_executed[idx] = False

                # Handle tap tempo recording
                if mode == "tap":
                    record_tap_tempo(idx, now)
                    # Start blinking for tap mode
                    blink_state[idx] = True
                    blink_next_toggle[idx] = now + (blink_rate_ms[idx] / 1000.0)

                # Dispatch press event
                if not long_enabled:
                    # No long-press: execute press action immediately
                    if mode in ("toggle", "select", "tap"):
                        # Advance keytime for toggle modes
                        btn_state.advance_keytime()
                        # For toggle/select: update state and LED
                        if mode in ("toggle", "select"):
                            new_state = True if btn_state.keytimes > 1 else (not btn_state.state if mode == "toggle" else True)
                            btn_state.state = new_state
                            set_button_state(btn_num, new_state)
                            # Handle select_group exclusivity
                            if new_state and mode == "select":
                                sg = btn_config.get("select_group")
                                if sg:
                                    _deselect_group(sg, idx)
                    
                    # Dispatch press event
                    press_cfg = btn_config.get("press")
                    if press_cfg:
                        _send_action_from_cfg(press_cfg, btn_num, idx)
                        short_action_executed[idx] = True
                    
                    # For momentary mode, also set LED on
                    if mode == "momentary":
                        set_button_state(btn_num, True)
                
                else:
                    # Long-press configured: for momentary, dispatch press immediately
                    # For toggle modes, defer until we know if it's short or long
                    if mode == "momentary":
                        btn_state.advance_keytime()
                        press_cfg = btn_config.get("press")
                        if press_cfg:
                            _send_action_from_cfg(press_cfg, btn_num, idx)
                        set_button_state(btn_num, True)

            else:
                # RELEASED: Dispatch appropriate release event
                press_start_times[idx] = 0.0
                was_long = long_press_triggered[idx]
                long_press_triggered[idx] = False

                if was_long:
                    # Long-press completed: dispatch long_release if configured
                    if long_release_cfg:
                        _send_action_from_cfg(long_release_cfg, btn_num, idx)
                else:
                    # Short press: handle deferred actions
                    if long_enabled:
                        # Deferred press action (for toggle modes with long-press configured)
                        if mode in ("toggle", "select", "tap") and not short_action_executed[idx]:
                            btn_state.advance_keytime()
                            if mode in ("toggle", "select"):
                                new_state = True if btn_state.keytimes > 1 else (not btn_state.state if mode == "toggle" else True)
                                btn_state.state = new_state
                                set_button_state(btn_num, new_state)
                                if new_state and mode == "select":
                                    sg = btn_config.get("select_group")
                                    if sg:
                                        _deselect_group(sg, idx)
                            press_cfg = btn_config.get("press")
                            if press_cfg:
                                _send_action_from_cfg(press_cfg, btn_num, idx)
                                short_action_executed[idx] = True
                    
                    # Dispatch release event
                    release_cfg = btn_config.get("release")
                    if release_cfg:
                        _send_action_from_cfg(release_cfg, btn_num, idx)
                    
                    # For momentary mode, set LED off
                    if mode == "momentary":
                        set_button_state(btn_num, False)

        # --- Handle held buttons for long-press threshold crossing ---
        if pressed and long_enabled and not long_press_triggered[idx] and press_start_times[idx]:
            # Determine threshold (ms)
            threshold_ms = DEFAULT_LONG_PRESS_MS
            if long_press_cfg and isinstance(long_press_cfg, dict):
                threshold_ms = long_press_cfg.get("threshold_ms", threshold_ms)
            elif isinstance(long_press_cfg, list) and len(long_press_cfg) > 0:
                # If it's an array, check first command for threshold
                first_cmd = long_press_cfg[0]
                if isinstance(first_cmd, dict):
                    threshold_ms = first_cmd.get("threshold_ms", threshold_ms)

            if (now - press_start_times[idx]) >= (threshold_ms / 1000.0):
                # Trigger long-press action
                long_press_triggered[idx] = True
                if long_press_cfg:
                    _send_action_from_cfg(long_press_cfg, btn_num, idx)
