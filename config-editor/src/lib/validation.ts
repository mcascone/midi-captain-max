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
    if (value < 1 || value > 127) return 'Step must be between 1 and 127';
    if (!Number.isInteger(value)) return 'Step must be an integer';
    return null;
  },

  keytimes: (value: number): string | null => {
    if (value < 1 || value > 99) return 'Keytimes must be between 1 and 99';
    if (!Number.isInteger(value)) return 'Keytimes must be an integer';
    return null;
  },
};

export function validateConfig(config: MidiCaptainConfig): ValidationResult {
  const errors = new Map<string, string>();
  
  // Device-specific validation
  if (config.device === 'mini6') {
    if (config.buttons.length > 6) {
      errors.set('device', 'Mini6 supports only 6 buttons');
    }
    if (config.encoder?.enabled) {
      errors.set('encoder.enabled', 'Mini6 does not support encoder');
    }
  } else if (config.device === 'std10') {
    if (config.buttons.length > 10) {
      errors.set('device', 'STD10 supports only 10 buttons');
    }
  }
  
  // Validate all buttons
  config.buttons.forEach((btn, idx) => {
    const labelError = validators.label(btn.label);
    if (labelError) errors.set(`buttons[${idx}].label`, labelError);

    const msgType = btn.type ?? 'cc';

    if (msgType === 'cc') {
      if (btn.cc !== undefined) {
        const ccError = validators.cc(btn.cc);
        if (ccError) errors.set(`buttons[${idx}].cc`, ccError);
      }
    } else if (msgType === 'note') {
      if (btn.note !== undefined) {
        const noteError = validators.note(btn.note);
        if (noteError) errors.set(`buttons[${idx}].note`, noteError);
      }
      if (btn.velocity_on !== undefined) {
        const velError = validators.velocity(btn.velocity_on);
        if (velError) errors.set(`buttons[${idx}].velocity_on`, velError);
      }
      if (btn.velocity_off !== undefined) {
        const velError = validators.velocity(btn.velocity_off);
        if (velError) errors.set(`buttons[${idx}].velocity_off`, velError);
      }
    } else if (msgType === 'pc') {
      if (btn.program !== undefined) {
        const progError = validators.program(btn.program);
        if (progError) errors.set(`buttons[${idx}].program`, progError);
      }
    } else if (msgType === 'pc_inc' || msgType === 'pc_dec') {
      if (btn.pc_step !== undefined) {
        const stepError = validators.pcStep(btn.pc_step);
        if (stepError) errors.set(`buttons[${idx}].pc_step`, stepError);
      }
    }

    if (btn.keytimes !== undefined) {
      const ktError = validators.keytimes(btn.keytimes);
      if (ktError) errors.set(`buttons[${idx}].keytimes`, ktError);

      if (btn.states) {
        btn.states.forEach((state, si) => {
          const sp = `buttons[${idx}].states[${si}]`;
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
        });
      }
    }
  });
  
  // Validate encoder
  if (config.encoder?.enabled) {
    const ccError = validators.cc(config.encoder.cc);
    if (ccError) {
      errors.set('encoder.cc', ccError);
    }
    
    if (config.encoder.min !== undefined && config.encoder.max !== undefined) {
      const rangeError = validators.range(config.encoder.min, config.encoder.max);
      if (rangeError) {
        errors.set('encoder.range', rangeError);
      }
    }
  }
  
  // Validate expression pedals
  if (config.expression?.exp1?.enabled) {
    const ccError = validators.cc(config.expression.exp1.cc);
    if (ccError) {
      errors.set('expression.exp1.cc', ccError);
    }
  }
  
  if (config.expression?.exp2?.enabled) {
    const ccError = validators.cc(config.expression.exp2.cc);
    if (ccError) {
      errors.set('expression.exp2.cc', ccError);
    }
  }
  
  return {
    isValid: errors.size === 0,
    errors,
  };
}
