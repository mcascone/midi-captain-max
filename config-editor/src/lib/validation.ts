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

  note: (value: number): string | null => {
    if (value < 0 || value > 127) {
      return 'Note must be between 0 and 127';
    }
    if (!Number.isInteger(value)) {
      return 'Note must be an integer';
    }
    return null;
  },

  velocity: (value: number): string | null => {
    if (value < 0 || value > 127) {
      return 'Velocity must be between 0 and 127';
    }
    if (!Number.isInteger(value)) {
      return 'Velocity must be an integer';
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
};

export function findDuplicateNotes(config: MidiCaptainConfig): Map<string, string> {
  const errors = new Map<string, string>();
  const noteMap = new Map<string, string[]>();

  config.buttons.forEach((btn, idx) => {
    if (btn.type === 'note' && btn.note !== undefined) {
      const ch = btn.channel ?? config.global_channel ?? 0;
      const key = `${btn.note}:${ch}`;
      const path = `buttons[${idx}].note`;
      if (!noteMap.has(key)) {
        noteMap.set(key, []);
      }
      noteMap.get(key)!.push(path);
    }
  });

  noteMap.forEach((paths, key) => {
    if (paths.length > 1) {
      const [note, ch] = key.split(':');
      paths.forEach(path => {
        const others = paths.filter(p => p !== path).join(', ');
        errors.set(path, `Note ${note} (Ch ${parseInt(ch) + 1}) is also used by: ${others}`);
      });
    }
  });

  return errors;
}

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
    if (labelError) {
      errors.set(`buttons[${idx}].label`, labelError);
    }

    if (btn.type === 'note') {
      // Validate note-specific fields
      if (btn.note !== undefined) {
        const noteError = validators.note(btn.note);
        if (noteError) {
          errors.set(`buttons[${idx}].note`, noteError);
        }
      }
      if (btn.velocity_on !== undefined) {
        const velError = validators.velocity(btn.velocity_on);
        if (velError) {
          errors.set(`buttons[${idx}].velocity_on`, velError);
        }
      }
      if (btn.velocity_off !== undefined) {
        const velError = validators.velocity(btn.velocity_off);
        if (velError) {
          errors.set(`buttons[${idx}].velocity_off`, velError);
        }
      }
    } else {
      // Validate CC fields (default)
      const ccError = validators.cc(btn.cc);
      if (ccError) {
        errors.set(`buttons[${idx}].cc`, ccError);
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

  // Check for duplicate notes (same note + same channel)
  const duplicateNotes = findDuplicateNotes(config);
  duplicateNotes.forEach((error, path) => {
    errors.set(path, error);
  });

  return {
    isValid: errors.size === 0,
    errors,
  };
}
