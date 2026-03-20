import type { MidiCaptainConfig } from './types';

export interface ValidationResult {
  isValid: boolean;
  errors: Map<string, string>;
}

export interface FieldValidator {
  (value: any, config?: MidiCaptainConfig): string | null;
}

export const validators = {
  label: (value: string): string | null => {
    if (!value || value.trim() === '') {
      return 'Label is required';
    }
    if (value.length > 6) {
      return 'Label must be 6 characters or less';
    }
    if (!/^[\w\s-]+$/.test(value)) {
      return 'Label contains invalid characters';
    }
    return null;
  },

  cc: (value: number, config?: MidiCaptainConfig): string | null => {
    if (value < 0 || value > 127) {
      return 'CC must be between 0 and 127';
    }
    if (!Number.isInteger(value)) {
      return 'CC must be an integer';
    }
    return null;
  },

  range: (min: number, max: number): string | null => {
    if (min >= max) {
      return 'Min must be less than max';
    }
    return null;
  },

  withinRange: (value: number, min: number, max: number): string | null => {
    if (value < min || value > max) {
      return `Value must be between ${min} and ${max}`;
    }
    return null;
  },

  note: (value: number): string | null => {
    if (value < 0 || value > 127) return 'Note must be between 0 and 127';
    if (!Number.isInteger(value)) return 'Note must be an integer';
    return null;
  },

  velocity: (value: number): string | null => {
    if (value < 0 || value > 127) return 'Velocity must be between 0 and 127';
    if (!Number.isInteger(value)) return 'Velocity must be an integer';
    return null;
  },

  program: (value: number): string | null => {
    if (value < 0 || value > 127) return 'Program must be between 0 and 127';
    if (!Number.isInteger(value)) return 'Program must be an integer';
    return null;
  },

  pcStep: (value: number): string | null => {
    if (!Number.isInteger(value)) return 'Step must be an integer';
    if (value < 1 || value > 127) return 'Step must be between 1 and 127';
    return null;
  },

  keytimes: (value: number): string | null => {
    if (!Number.isInteger(value)) return 'Keytimes must be an integer';
    if (value < 1 || value > 99) return 'Keytimes must be between 1 and 99';
    return null;
  },

  flashMs: (value: number): string | null => {
    if (!Number.isInteger(value)) return 'Flash duration must be an integer';
    if (value < 50 || value > 5000) return 'Flash duration must be between 50 and 5000 ms';
    return null;
  },

  // value is stored as 0-15 (displayed as 1-16)
  channel: (value: number): string | null => {
    if (!Number.isInteger(value)) return 'Channel must be an integer';
    if (value < 0 || value > 15) return 'Channel must be between 1 and 16';
    return null;
  },
};

/**
 * Validate an array of buttons (helper for single-bank and multi-bank configs)
 * @param buttons - Array of button configurations
 * @param pathPrefix - Path prefix for error keys (e.g., "buttons" or "banks[0].buttons")
 * @param errors - Map to accumulate errors
 */
function validateButtons(
  buttons: any[],
  pathPrefix: string,
  errors: Map<string, string>
): void {
  buttons.forEach((btn, idx) => {
    const btnPath = `${pathPrefix}[${idx}]`;
    
    const labelError = validators.label(btn.label);
    if (labelError) errors.set(`${btnPath}.label`, labelError);

    const msgType = btn.type ?? 'cc';

    if (msgType === 'cc') {
      if (btn.cc !== undefined) {
        const ccError = validators.cc(btn.cc);
        if (ccError) errors.set(`${btnPath}.cc`, ccError);
      }
    } else if (msgType === 'note') {
      if (btn.note !== undefined) {
        const noteError = validators.note(btn.note);
        if (noteError) errors.set(`${btnPath}.note`, noteError);
      }
      if (btn.velocity_on !== undefined) {
        const velError = validators.velocity(btn.velocity_on);
        if (velError) errors.set(`${btnPath}.velocity_on`, velError);
      }
      if (btn.velocity_off !== undefined) {
        const velError = validators.velocity(btn.velocity_off);
        if (velError) errors.set(`${btnPath}.velocity_off`, velError);
      }
    } else if (msgType === 'pc') {
      if (btn.program !== undefined) {
        const progError = validators.program(btn.program);
        if (progError) errors.set(`${btnPath}.program`, progError);
      }
    } else if (msgType === 'pc_inc' || msgType === 'pc_dec') {
      if (btn.pc_step !== undefined) {
        const stepError = validators.pcStep(btn.pc_step);
        if (stepError) errors.set(`${btnPath}.pc_step`, stepError);
      }
    }

    if (btn.channel !== undefined) {
      const chError = validators.channel(btn.channel);
      if (chError) errors.set(`${btnPath}.channel`, chError);
    }

    if (btn.flash_ms !== undefined) {
      const fError = validators.flashMs(btn.flash_ms);
      if (fError) errors.set(`${btnPath}.flash_ms`, fError);
    }

    // LED tap mode validation
    if (btn.led_mode !== undefined) {
      if (btn.led_mode !== 'tap') {
        errors.set(`${btnPath}.led_mode`, 'led_mode must be "tap" if set');
      }
      if (btn.tap_rate_ms !== undefined) {
        const tError = validators.flashMs(btn.tap_rate_ms);
        if (tError) errors.set(`${btnPath}.tap_rate_ms`, tError);
      }
    }

    // Long-press / long-release actions validation
    const validateAction = (action: any, pathBase: string) => {
      if (!action) return;
      if (typeof action !== 'object') {
        errors.set(pathBase, 'Action must be an object');
        return;
      }
      const aType = action.type ?? 'cc';
      if (!['cc', 'note', 'pc'].includes(aType)) {
        errors.set(`${pathBase}.type`, 'Action type must be cc, note, or pc');
      }
      if (aType === 'cc') {
        if (action.cc !== undefined) {
          const e = validators.cc(action.cc);
          if (e) errors.set(`${pathBase}.cc`, e);
        }
        if (action.value !== undefined) {
          const e = validators.withinRange(action.value, 0, 127);
          if (e) errors.set(`${pathBase}.value`, e);
        }
      } else if (aType === 'note') {
        if (action.note !== undefined) {
          const e = validators.note(action.note);
          if (e) errors.set(`${pathBase}.note`, e);
        }
        if (action.value !== undefined) {
          const e = validators.velocity(action.value);
          if (e) errors.set(`${pathBase}.value`, e);
        }
      } else if (aType === 'pc') {
        if (action.program !== undefined) {
          const e = validators.program(action.program);
          if (e) errors.set(`${pathBase}.program`, e);
        }
      }
      if (action.channel !== undefined) {
        const ch = validators.channel(action.channel);
        if (ch) errors.set(`${pathBase}.channel`, ch);
      }
      if (action.threshold_ms !== undefined) {
        if (!Number.isInteger(action.threshold_ms) || action.threshold_ms < 50 || action.threshold_ms > 10000) {
          errors.set(`${pathBase}.threshold_ms`, 'threshold_ms must be integer 50-10000');
        }
      }
    };

    // Validate long_press and long_release arrays
    const validateActionArray = (actions: any, pathBase: string) => {
      if (!actions) return;
      if (Array.isArray(actions)) {
        actions.forEach((action, idx) => {
          validateAction(action, `${pathBase}[${idx}]`);
          // threshold_ms only valid on first command
          if (idx > 0 && action.threshold_ms !== undefined) {
            errors.set(`${pathBase}[${idx}].threshold_ms`, 'threshold_ms only allowed on first command');
          }
        });
      } else {
        // Backward compatibility: treat single object as array of one
        validateAction(actions, pathBase);
      }
    };

    validateActionArray(btn.long_press, `${btnPath}.long_press`);
    validateActionArray(btn.long_release, `${btnPath}.long_release`);

    // select_group validation
    if (btn.select_group !== undefined) {
      if (typeof btn.select_group !== 'string' || btn.select_group.trim() === '') {
        errors.set(`${btnPath}.select_group`, 'select_group must be a non-empty string');
      } else {
        if (btn.mode === 'momentary') {
          errors.set(`${btnPath}.select_group`, 'select_group not supported for momentary mode');
        }
        if (btn.mode === 'tap') {
          errors.set(`${btnPath}.select_group`, 'select_group not supported for tap mode');
        }
        if ((btn.keytimes ?? 1) > 1) {
          errors.set(`${btnPath}.select_group`, 'select_group not supported with keytimes > 1');
        }
      }
    }
    if (btn.default_selected !== undefined && typeof btn.default_selected !== 'boolean') {
      errors.set(`${btnPath}.default_selected`, 'default_selected must be boolean');
    }

    if (btn.states && (btn.keytimes === undefined || btn.keytimes <= 1)) {
      errors.set(`${btnPath}.states`, 'states requires keytimes > 1');
    }

    if (btn.keytimes !== undefined) {
      const ktError = validators.keytimes(btn.keytimes);
      if (ktError) errors.set(`${btnPath}.keytimes`, ktError);

      if (btn.states) {
        btn.states.forEach((state: any, si: number) => {
          const sp = `${btnPath}.states[${si}]`;
          if (state.cc !== undefined) {
            const e = validators.cc(state.cc);
            if (e) errors.set(`${sp}.cc`, e);
          }
          if (state.cc_on !== undefined) {
            const e = validators.withinRange(state.cc_on, 0, 127);
            if (e) errors.set(`${sp}.cc_on`, e);
          }
          if (state.cc_off !== undefined) {
            const e = validators.withinRange(state.cc_off, 0, 127);
            if (e) errors.set(`${sp}.cc_off`, e);
          }
          if (state.note !== undefined) {
            const e = validators.note(state.note);
            if (e) errors.set(`${sp}.note`, e);
          }
          if (state.velocity_on !== undefined) {
            const e = validators.velocity(state.velocity_on);
            if (e) errors.set(`${sp}.velocity_on`, e);
          }
          if (state.velocity_off !== undefined) {
            const e = validators.velocity(state.velocity_off);
            if (e) errors.set(`${sp}.velocity_off`, e);
          }
          if (state.program !== undefined) {
            const e = validators.program(state.program);
            if (e) errors.set(`${sp}.program`, e);
          }
          if (state.pc_step !== undefined) {
            const e = validators.pcStep(state.pc_step);
            if (e) errors.set(`${sp}.pc_step`, e);
          }
          if (state.label !== undefined) {
            const e = validators.label(state.label);
            if (e) errors.set(`${sp}.label`, e);
          }
        });
      }
    }
  });

  // Cross-button select_group validation within this button set
  const groupDefaults: Record<string, number[]> = {};
  buttons.forEach((btn, idx) => {
    if (btn.select_group && btn.default_selected) {
      if (!groupDefaults[btn.select_group]) groupDefaults[btn.select_group] = [];
      groupDefaults[btn.select_group].push(idx);
    }
  });
  for (const g in groupDefaults) {
    const idxs = groupDefaults[g];
    if (idxs.length > 1) {
      for (let i = 1; i < idxs.length; i++) {
        errors.set(`${pathPrefix}[${idxs[i]}].default_selected`, `Multiple default_selected in group '${g}'`);
      }
    }
  }
}

export function validateConfig(config: MidiCaptainConfig): ValidationResult {
  const errors = new Map<string, string>();

  // Determine expected button count based on device
  const expectedButtons = config.device === 'mini6' ? 6 : 10;

  // Validate banks (multi-bank mode) or legacy buttons (single-bank mode)
  if (config.banks && config.banks.length > 0) {
    // Multi-bank mode validation
    if (config.banks.length > 8) {
      errors.set('banks', `Max 8 banks supported, found ${config.banks.length}`);
    }

    config.banks.forEach((bank, bankIdx) => {
      const bankPrefix = `banks[${bankIdx}]`;
      
      // Validate bank name
      if (!bank.name || bank.name.length === 0) {
        errors.set(`${bankPrefix}.name`, 'Bank name cannot be empty');
      } else if (bank.name.length > 20) {
        errors.set(`${bankPrefix}.name`, 'Bank name cannot exceed 20 chars');
      }

      // Validate button count
      if (!Array.isArray(bank.buttons)) {
        errors.set(`${bankPrefix}.buttons`, 'Bank buttons must be an array');
        return; // Skip further validation for this bank
      }
      if (bank.buttons.length !== expectedButtons) {
        errors.set(`${bankPrefix}.buttons`, `Expected ${expectedButtons} buttons for ${config.device}, found ${bank.buttons.length}`);
      }

      // Validate buttons for this bank
      validateButtons(bank.buttons, `${bankPrefix}.buttons`, errors);
    });

      // Validate each button in this bank
      validateButtons(bank.buttons, `${bankPrefix}.buttons`, errors);
    });

    // Validate bank_switch config if present
    if (config.bank_switch) {
      const bs = config.bank_switch;
      if (bs.channel !== undefined) {
        const chErr = validators.channel(bs.channel);
        if (chErr) errors.set('bank_switch.channel', chErr);
      }
      if (bs.cc !== undefined) {
        const ccErr = validators.cc(bs.cc);
        if (ccErr) errors.set('bank_switch.cc', ccErr);
      }
      if (bs.pc_base !== undefined) {
        const pcErr = validators.cc(bs.pc_base); // PC numbers use same range as CC
        if (pcErr) errors.set('bank_switch.pc_base', pcErr);
      }
      // Validate button numbers (1-indexed, must be within device button count)
      // STD10 can use buttons 1-10 or 11 (encoder push) for bank switching
      // Mini6 can use buttons 1-6 only (no encoder)
      const maxBankSwitchButton = config.device === 'mini6' ? 6 : 11;
      if (bs.button !== undefined) {
        if (bs.button < 1 || bs.button > maxBankSwitchButton) {
          errors.set('bank_switch.button', `Button must be between 1 and ${maxBankSwitchButton}`);
        }
      }
      if (bs.button_next !== undefined) {
        if (bs.button_next < 1 || bs.button_next > maxBankSwitchButton) {
          errors.set('bank_switch.button_next', `Button must be between 1 and ${maxBankSwitchButton}`);
        }
      }
      if (bs.button_prev !== undefined) {
        if (bs.button_prev < 1 || bs.button_prev > maxBankSwitchButton) {
          errors.set('bank_switch.button_prev', `Button must be between 1 and ${maxBankSwitchButton}`);
        }
      }
    }

    // Validate active_bank index
    if (config.active_bank !== undefined) {
      if (config.active_bank < 0 || config.active_bank >= config.banks.length) {
        errors.set('active_bank', `active_bank ${config.active_bank} out of range (max ${config.banks.length - 1})`);
      }
    }
  } else if (config.buttons) {
    // Legacy single-bank mode validation
    if (config.buttons.length !== expectedButtons) {
      errors.set('buttons', `Expected ${expectedButtons} buttons for ${config.device}, found ${config.buttons.length}`);
    }
    validateButtons(config.buttons, 'buttons', errors);
  }

  // Device-specific validation
  if (config.device === 'mini6') {
    if (config.encoder?.enabled) {
      errors.set('encoder.enabled', 'Mini6 does not support encoder');
    }
  }

  // Validate encoder
  if (config.encoder?.enabled) {
    const ccError = validators.cc(config.encoder.cc);
    if (ccError) errors.set('encoder.cc', ccError);

    if (config.encoder.channel !== undefined) {
      const chError = validators.channel(config.encoder.channel);
      if (chError) errors.set('encoder.channel', chError);
    }

    const min = config.encoder.min ?? 0;
    const max = config.encoder.max ?? 127;
    const rangeError = validators.range(min, max);
    if (rangeError) errors.set('encoder.range', rangeError);

    if (config.encoder.initial !== undefined) {
      const initError = validators.withinRange(config.encoder.initial, min, max);
      if (initError) errors.set('encoder.initial', `Initial ${initError.toLowerCase()}`);
    }

    if (config.encoder.push?.enabled) {
      const pushCcError = validators.cc(config.encoder.push.cc);
      if (pushCcError) errors.set('encoder.push.cc', pushCcError);

      if (config.encoder.push.channel !== undefined) {
        const chError = validators.channel(config.encoder.push.channel);
        if (chError) errors.set('encoder.push.channel', chError);
      }
      if (config.encoder.push.cc_on !== undefined) {
        const e = validators.cc(config.encoder.push.cc_on);
        if (e) errors.set('encoder.push.cc_on', e);
      }
      if (config.encoder.push.cc_off !== undefined) {
        const e = validators.cc(config.encoder.push.cc_off);
        if (e) errors.set('encoder.push.cc_off', e);
      }
    }
  }

  // Validate expression pedals
  for (const [key, exp] of [['exp1', config.expression?.exp1], ['exp2', config.expression?.exp2]] as const) {
    if (!exp?.enabled) continue;
    const p = `expression.${key}`;

    const ccError = validators.cc(exp.cc);
    if (ccError) errors.set(`${p}.cc`, ccError);

    if (exp.channel !== undefined) {
      const chError = validators.channel(exp.channel);
      if (chError) errors.set(`${p}.channel`, chError);
    }

    const min = exp.min ?? 0;
    const max = exp.max ?? 127;
    const rangeError = validators.range(min, max);
    if (rangeError) errors.set(`${p}.range`, rangeError);
  }

  return {
    isValid: errors.size === 0,
    errors,
  };
}
