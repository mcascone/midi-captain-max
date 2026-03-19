"""
Bank Manager for MIDI Captain firmware.

Handles bank switching, state persistence, and bank configuration.
"""

import time


class BankManager:
    """Manages multiple banks of button configurations with state persistence."""

    def __init__(self, banks, button_states, active_bank=0):
        """Initialize BankManager.

        Args:
            banks: List of bank config dicts (from config['banks'])
            button_states: List of ButtonState objects for current bank
            active_bank: Initial active bank index (0-indexed)
        """
        self.banks = banks
        self.current_bank_index = active_bank if 0 <= active_bank < len(banks) else 0
        self.button_count = len(button_states)

        # Per-bank button state storage: bank_index -> list of ButtonState objects
        # Store state for all banks so switching is instant (no config reload)
        self.bank_states = {}
        for i in range(len(banks)):
            self.bank_states[i] = []

        # Initialize current bank's states
        self.bank_states[self.current_bank_index] = button_states

        # Bank switch cooldown (prevent rapid switches)
        # Initialize to -1.0 so first switch always succeeds
        self.last_switch_time = -1.0
        self.switch_cooldown_ms = 200  # 200ms minimum between switches

    def get_current_bank_index(self):
        """Get 0-indexed current bank number."""
        return self.current_bank_index

    def get_current_bank_config(self):
        """Get current bank's configuration dict."""
        if 0 <= self.current_bank_index < len(self.banks):
            return self.banks[self.current_bank_index]
        return None

    def get_current_bank_name(self):
        """Get current bank's name."""
        bank_cfg = self.get_current_bank_config()
        if bank_cfg:
            return bank_cfg.get("name", f"Bank {self.current_bank_index + 1}")
        return f"Bank {self.current_bank_index + 1}"

    def get_bank_count(self):
        """Get total number of banks."""
        return len(self.banks)

    def get_button_states(self):
        """Get current bank's button states."""
        return self.bank_states.get(self.current_bank_index, [])

    def switch_bank(self, new_bank_index):
        """Switch to a different bank.

        Args:
            new_bank_index: Target bank index (0-indexed)

        Returns:
            True if switch succeeded, False if invalid index or on cooldown
        """
        # Validate index
        if not isinstance(new_bank_index, int) or new_bank_index < 0 or new_bank_index >= len(self.banks):
            return False

        # Already on this bank
        if new_bank_index == self.current_bank_index:
            return False

        # Check cooldown
        now = time.monotonic()
        if (now - self.last_switch_time) < (self.switch_cooldown_ms / 1000.0):
            return False

        # Save current bank's state (already in bank_states dict, just reference)
        # No explicit save needed since button_states list is stored by reference

        # Switch to new bank
        old_bank = self.current_bank_index
        self.current_bank_index = new_bank_index
        self.last_switch_time = now

        # Initialize new bank's states if not yet created
        if new_bank_index not in self.bank_states or not self.bank_states[new_bank_index]:
            # Import ButtonState here to avoid circular import
            from .button import ButtonState
            new_bank_cfg = self.banks[new_bank_index]
            buttons = new_bank_cfg.get("buttons", [])
            states = []
            for i in range(self.button_count):
                if i < len(buttons):
                    btn_config = buttons[i]
                    cc = btn_config.get("cc", 0)
                    mode = btn_config.get("mode", "toggle")
                    keytimes = btn_config.get("keytimes", 1)
                    initial_on = False
                    states.append(ButtonState(cc=cc, mode=mode, initial_state=initial_on, keytimes=keytimes))
                else:
                    # Fallback for missing button configs
                    states.append(ButtonState(cc=0, mode="toggle", initial_state=False, keytimes=1))
            self.bank_states[new_bank_index] = states

        print(f"[BANK] Switched from bank {old_bank + 1} to bank {new_bank_index + 1}: {self.get_current_bank_name()}")
        return True

    def next_bank(self):
        """Switch to next bank (wrap around)."""
        if len(self.banks) == 0:
            return False
        next_idx = (self.current_bank_index + 1) % len(self.banks)
        return self.switch_bank(next_idx)

    def previous_bank(self):
        """Switch to previous bank (wrap around)."""
        if len(self.banks) == 0:
            return False
        prev_idx = (self.current_bank_index - 1) % len(self.banks)
        return self.switch_bank(prev_idx)

    def get_bank_switch_trigger(self, bank_switch_config, message_type=None, value=None):
        """Determine target bank based on bank switch trigger.

        Args:
            bank_switch_config: Bank switch config dict (method, button, cc, pc_base, channel)
            message_type: MIDI message type ('cc' or 'pc') or None for button trigger
            value: MIDI value (for CC/PC switching)

        Returns:
            Target bank index (0-indexed) or None if no switch triggered
        """
        if not bank_switch_config:
            return None

        method = bank_switch_config.get("method", "button")

        if method == "button" and message_type is None:
            # Button trigger (handled externally by caller)
            return None

        elif method == "cc" and message_type == "cc":
            # CC-based bank switching: CC value maps to bank index
            if value is not None and 0 <= value < len(self.banks):
                return value
            return None

        elif method == "pc" and message_type == "pc":
            # PC-based bank switching: PC number - pc_base = bank index
            pc_base = bank_switch_config.get("pc_base", 0)
            if value is not None:
                bank_idx = value - pc_base
                if 0 <= bank_idx < len(self.banks):
                    return bank_idx
            return None

        return None
