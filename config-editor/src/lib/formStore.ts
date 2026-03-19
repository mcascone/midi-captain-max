import { writable, derived, get } from 'svelte/store';
import type { MidiCaptainConfig, ButtonConfig, EncoderConfig, DeviceType } from './types';
import { validateConfig } from './validation';

interface FormState {
  config: MidiCaptainConfig;
  history: MidiCaptainConfig[];
  historyIndex: number;
  validationErrors: Map<string, string>;
  isDirty: boolean;
  _hiddenButtons?: ButtonConfig[];
  _hiddenEncoder?: EncoderConfig;
}

const HISTORY_LIMIT = 50;
const DEBOUNCE_MS = 500;

// Initialize with first checkpoint
const initialConfig: MidiCaptainConfig = {
  device: 'std10',
  buttons: [],
  encoder: undefined,
  expression: undefined,
};

const initialState: FormState = {
  config: initialConfig,
  history: [initialConfig],  // Start with checkpoint
  historyIndex: 0,           // At first checkpoint
  validationErrors: new Map(),
  isDirty: false,
};

const formState = writable<FormState>(initialState);

export { formState };
export const config = derived(formState, $state => $state.config);
export const isDirty = derived(formState, $state => $state.isDirty);
export const validationErrors = derived(formState, $state => $state.validationErrors);
export const canUndo = derived(formState, $state => $state.historyIndex > 0);
export const canRedo = derived(formState, $state =>
  $state.historyIndex < $state.history.length - 1
);

let debounceTimer: ReturnType<typeof setTimeout> | null = null;

export function loadConfig(newConfig: MidiCaptainConfig) {
  // Ensure display always exists so DisplaySection can traverse into it
  let config = { ...newConfig, display: newConfig.display ?? {} };

  // Auto-migrate legacy single-bank format to multi-bank
  if (!config.banks && config.buttons) {
    const buttons = config.buttons;
    config.banks = [{
      name: 'Bank 1',
      buttons: structuredClone(buttons),
    }];
    config.active_bank = 0;
    delete config.buttons;
  }

  // Initialize activeBankIndex from config
  const initialBank = config.active_bank ?? 0;
  activeBankIndex.set(initialBank);

  formState.update(_state => ({
    config: structuredClone(config),
    history: [structuredClone(config)],
    historyIndex: 0,
    validationErrors: new Map(),
    isDirty: false,
  }));
}

function pushHistory(state: FormState): FormState {
  // Clear any future history if we're not at the end
  const newHistory = state.history.slice(0, state.historyIndex + 1);

  // Add current config to history
  newHistory.push(structuredClone(state.config));

  // Limit history size
  if (newHistory.length > HISTORY_LIMIT) {
    newHistory.shift();
  }

  return {
    ...state,
    history: newHistory,
    historyIndex: newHistory.length - 1,
    isDirty: true,
  };
}

export function undo() {
  formState.update(state => {
    if (state.historyIndex <= 0) return state;

    const newIndex = state.historyIndex - 1;
    return {
      ...state,
      config: structuredClone(state.history[newIndex]),
      historyIndex: newIndex,
      isDirty: newIndex !== 0,
    };
  });
}

export function redo() {
  formState.update(state => {
    if (state.historyIndex >= state.history.length - 1) return state;

    const newIndex = state.historyIndex + 1;
    return {
      ...state,
      config: structuredClone(state.history[newIndex]),
      historyIndex: newIndex,
      isDirty: true,
    };
  });
}

function setNestedValue(obj: any, path: string, value: any) {
  const parts = path.split('.');
  let current = obj;

  for (let i = 0; i < parts.length - 1; i++) {
    const part = parts[i];
    const arrayMatch = part.match(/(\w+)\[(\d+)\]/);

    if (arrayMatch) {
      const [, key, index] = arrayMatch;
      const idx = parseInt(index);

      // Check array exists and is valid
      if (!current[key]) {
        throw new Error(`Invalid path "${path}": ${key} does not exist`);
      }
      if (!Array.isArray(current[key])) {
        throw new Error(`Invalid path "${path}": ${key} is not an array`);
      }
      if (idx < 0 || idx >= current[key].length) {
        throw new Error(`Invalid path "${path}": index ${idx} out of bounds for ${key} (length ${current[key].length})`);
      }

      current = current[key][idx];
    } else {
      // If an intermediate object property is missing, create it so nested
      // fields (e.g. `long_press`) can be added via the form without having
      // to pre-initialize every nested object. Arrays must already exist.
      if (current[part] === undefined || current[part] === null) {
        current[part] = {};
      }
      current = current[part];
    }
  }

  // Same checks for the last part
  const lastPart = parts[parts.length - 1];
  const arrayMatch = lastPart.match(/(\w+)\[(\d+)\]/);

  if (arrayMatch) {
    const [, key, index] = arrayMatch;
    const idx = parseInt(index);

    if (!current[key]) {
      throw new Error(`Invalid path "${path}": ${key} does not exist`);
    }
    if (!Array.isArray(current[key])) {
      throw new Error(`Invalid path "${path}": ${key} is not an array`);
    }
    if (idx < 0 || idx >= current[key].length) {
      throw new Error(`Invalid path "${path}": index ${idx} out of bounds for ${key} (length ${current[key].length})`);
    }

    current[key][idx] = value;
  } else {
    current[lastPart] = value;
  }
}

export function updateField(path: string, value: any) {
  // Clear existing debounce
  if (debounceTimer) {
    clearTimeout(debounceTimer);
  }

  // Update value immediately
  formState.update(state => {
    const newConfig = structuredClone(state.config);
    setNestedValue(newConfig, path, value);

    return {
      ...state,
      config: newConfig,
      isDirty: true,
    };
  });

  // Validate after update
  validate();

  // Debounce history push
  debounceTimer = setTimeout(() => {
    formState.update(state => pushHistory(state));
  }, DEBOUNCE_MS);
}

export function syncButtonStates(buttonIndex: number, keytimes: number) {
  if (debounceTimer) {
    clearTimeout(debounceTimer);
    debounceTimer = null;
  }

  formState.update(state => {
    const newConfig = structuredClone(state.config);

    // Get buttons array - from active bank or top-level
    const buttons = newConfig.banks?.[get(activeBankIndex)]?.buttons ?? newConfig.buttons;
    if (!buttons) return state;

    const btn = buttons[buttonIndex];
    if (!btn) return state;

    if (keytimes <= 1) {
      delete btn.keytimes;
      delete btn.states;
    } else {
      btn.keytimes = keytimes;
      const current = btn.states ?? [];
      if (current.length < keytimes) {
        while (current.length < keytimes) current.push({});
      } else if (current.length > keytimes) {
        current.length = keytimes;
      }
      btn.states = current;
    }

    return { ...state, config: newConfig, isDirty: true };
  });

  validate();
  formState.update(state => pushHistory(state));
}

function createDefaultButton(index: number): ButtonConfig {
  return {
    label: `BTN${index}`,
    cc: 20 + index,
    color: 'white',
    mode: 'toggle',
    off_mode: 'dim',
  };
}

function createDefaultButtons(startIndex: number, endIndex: number): ButtonConfig[] {
  const defaults: ButtonConfig[] = [];
  for (let i = startIndex; i <= endIndex; i++) {
    defaults.push(createDefaultButton(i));
  }
  return defaults;
}

export function setDevice(deviceType: DeviceType) {
  formState.update(state => {
    const newState = { ...state };
    const currentDevice = state.config.device;

    // Helper: get buttons array from config (handles both banks and legacy)
    const getButtons = (bankIdx?: number) => {
      if (bankIdx !== undefined && state.config.banks) {
        return state.config.banks[bankIdx]?.buttons ?? [];
      }
      return state.config.banks?.[get(activeBankIndex)]?.buttons ?? state.config.buttons ?? [];
    };

    // Helper: set buttons array in config (handles both banks and legacy)
    const setButtons = (buttons: ButtonConfig[], bankIdx?: number) => {
      if (newState.config.banks) {
        const idx = bankIdx !== undefined ? bankIdx : get(activeBankIndex);
        if (newState.config.banks[idx]) {
          newState.config.banks[idx].buttons = buttons;
        }
      } else {
        newState.config.buttons = buttons;
      }
    };

    // Apply device change to ALL banks (if in multi-bank mode)
    if (newState.config.banks) {
      for (let bankIdx = 0; bankIdx < newState.config.banks.length; bankIdx++) {
        const buttons = getButtons(bankIdx);
        
        if (deviceType === 'mini6' && currentDevice === 'std10') {
          // Truncate to 6 buttons
          setButtons(buttons.slice(0, 6), bankIdx);
        } else if (deviceType === 'std10' && currentDevice === 'mini6') {
          // Expand to 10 buttons
          const expandedButtons = [...buttons.slice(0, 6)];
          while (expandedButtons.length < 10) {
            expandedButtons.push(createDefaultButton(expandedButtons.length));
          }
          setButtons(expandedButtons, bankIdx);
        }
      }

      // Update encoder for device type
      if (deviceType === 'mini6' && newState.config.encoder) {
        newState.config.encoder = { ...newState.config.encoder, enabled: false };
      }
      newState.config.device = deviceType;
    }
    // Legacy single-bank mode
    else {
      const buttons = getButtons();

      // Switching TO Mini6: preserve STD10-only features
      if (deviceType === 'mini6' && currentDevice === 'std10') {
        // Preserve buttons 7-10
        if (buttons.length > 6) {
          newState._hiddenButtons = buttons.slice(6);
        }

        // Preserve encoder config
        if (state.config.encoder) {
          newState._hiddenEncoder = structuredClone(state.config.encoder);
        }

        // Truncate buttons array and disable encoder
        setButtons(buttons.slice(0, 6));
        newState.config.device = 'mini6';
        if (newState.config.encoder) {
          newState.config.encoder = { ...newState.config.encoder, enabled: false };
        }
      }

      // Switching TO STD10: restore preserved features
      else if (deviceType === 'std10' && currentDevice === 'mini6') {
        // Ensure we have exactly 6 Mini6 buttons before appending 7-10
        const mini6Buttons = buttons.slice(0, 6);
        while (mini6Buttons.length < 6) {
          mini6Buttons.push(createDefaultButton(mini6Buttons.length));
        }

        const allButtons = [
          ...mini6Buttons,
          ...(state._hiddenButtons || createDefaultButtons(6, 9)),
        ];

        // Restore preserved encoder
        if (state._hiddenEncoder) {
          newState.config.encoder = structuredClone(state._hiddenEncoder);
          delete newState._hiddenEncoder;
        } else if (newState.config.encoder) {
          newState.config.encoder = { ...newState.config.encoder, enabled: true };
        }

        setButtons(allButtons);
        newState.config.device = 'std10';
      }

      // First-time Mini6 initialization
      else if (deviceType === 'mini6' && !currentDevice) {
        const currentButtons = buttons.slice(0, 6);
        while (currentButtons.length < 6) {
          currentButtons.push(createDefaultButton(currentButtons.length));
        }
        setButtons(currentButtons);
        newState.config.device = 'mini6';
        if (newState.config.encoder) {
          newState.config.encoder = { ...newState.config.encoder, enabled: false };
        }
      }

      // First-time STD10 initialization
      else if (deviceType === 'std10' && !currentDevice) {
        const currentButtons = [...buttons];
        while (currentButtons.length < 10) {
          currentButtons.push(createDefaultButton(currentButtons.length));
        }
        setButtons(currentButtons);
        newState.config.device = 'std10';
      }

      // Same device: no-op
      else {
        newState.config = { ...state.config, device: deviceType };
      }
    }

    return pushHistory(newState);
  });
}

// Convert action objects to arrays and strip legacy single-action fields
// Since we always use multi-command arrays now, remove obsolete fields
function normalizeButton(btn: ButtonConfig): ButtonConfig {
  const ensureArray = (field: any): any[] | undefined => {
    if (!field) return undefined;
    if (Array.isArray(field)) return field;
    return [field]; // Convert single object to array
  };

  // Auto-migrate: old-style 'toggle' with explicit press/release arrays or keytimes > 1
  // → becomes 'normal' (explicit/advanced toggle) so it keeps working as before.
  const hasExplicitEvents = (btn.press?.length ?? 0) > 0 || (btn.release?.length ?? 0) > 0;
  const hasMultiStates = (btn.keytimes ?? 1) > 1;
  if ((btn.mode === 'toggle' || btn.mode === undefined) && (hasExplicitEvents || hasMultiStates)) {
    btn = { ...btn, mode: 'normal' };
  }

  if (btn.mode === 'toggle') {
    // Simplified toggle: keep cc, channel, value_on, value_off, default_on.
    // Strip event arrays, states, keytimes, and all legacy type-based fields.
    // long_press is kept as an optional advanced escape hatch.
    const {
      type, cc_on, cc_off, note, velocity_on, velocity_off,
      program, pc_step, flash_ms,
      press, release, long_release, states, keytimes,
      ...rest
    } = btn as any;
    const result: any = { ...rest };
    if (btn.long_press && (btn.long_press as any[]).length > 0) {
      result.long_press = ensureArray(btn.long_press);
    } else {
      delete result.long_press;
    }
    return result as ButtonConfig;
  }

  // 'normal', 'momentary', 'select', 'tap':
  // Strip legacy single-type fields AND simplified-toggle-only fields.
  const {
    type, cc, cc_on, cc_off, note, velocity_on, velocity_off,
    program, pc_step, flash_ms,
    value_on, value_off, default_on,
    ...cleanButton
  } = btn as any;

  return {
    ...cleanButton,
    press: ensureArray(btn.press) as any,
    release: ensureArray(btn.release) as any,
    long_press: ensureArray(btn.long_press) as any,
    long_release: ensureArray(btn.long_release) as any,
  };
}

export function normalizeConfig(cfg: MidiCaptainConfig): MidiCaptainConfig {
  // Normalize buttons - handle both banks and legacy format
  let normalized: MidiCaptainConfig;

  if (cfg.banks) {
    // Multi-bank mode: normalize each bank's buttons
    normalized = {
      ...cfg,
      banks: cfg.banks.map(bank => ({
        ...bank,
        buttons: bank.buttons.map(normalizeButton),
      })),
    };
  } else if (cfg.buttons) {
    // Legacy mode: normalize top-level buttons
    normalized = { ...cfg, buttons: cfg.buttons.map(normalizeButton) };
  } else {
    // No buttons at all
    normalized = { ...cfg };
  }

  // Strip display if no fields were set (avoids writing `"display": {}` for untouched configs)
  if (normalized.display && Object.values(normalized.display).every(v => v === undefined)) {
    delete normalized.display;
  }

  // Normalize select_group default selections: ensure at most one default per group PER BANK
  if (normalized.banks) {
    // Multi-bank mode: normalize each bank independently
    normalized.banks.forEach((bank) => {
      const buttons = bank.buttons;
      const groups: Record<string, number[]> = {};
      buttons.forEach((b, i) => {
        const g = (b as any).select_group;
        const ds = (b as any).default_selected;
        if (g && typeof g === 'string') {
          if (!groups[g]) groups[g] = [];
          if (ds) groups[g].push(i);
        }
      });
      for (const g in groups) {
        const idxs = groups[g];
        if (idxs.length > 1) {
          // Keep the first, clear others
          for (let k = 1; k < idxs.length; k++) {
            delete (buttons[idxs[k]] as any).default_selected;
          }
        }
      }
    });
  } else if (normalized.buttons) {
    // Single-bank mode
    const buttons = normalized.buttons;
    const groups: Record<string, number[]> = {};
    buttons.forEach((b, i) => {
      const g = (b as any).select_group;
      const ds = (b as any).default_selected;
      if (g && typeof g === 'string') {
        if (!groups[g]) groups[g] = [];
        if (ds) groups[g].push(i);
      }
    });
    for (const g in groups) {
      const idxs = groups[g];
      if (idxs.length > 1) {
        // Keep the first, clear others
        for (let k = 1; k < idxs.length; k++) {
          delete (buttons[idxs[k]] as any).default_selected;
        }
      }
    }
  }

  return normalized;
}

export function validate() {
  const state = get(formState);
  const result = validateConfig(state.config);

  formState.update(s => ({
    ...s,
    validationErrors: result.errors,
  }));

  return result.isValid;
}

// Get error for a specific field path (e.g., "buttons[0].label")
export function getFieldError(fieldPath: string): string | null {
  const errors = get(validationErrors);
  return errors.get(fieldPath) ?? null;
}

// Get all errors for a button by index
export function getButtonErrors(buttonIndex: number): Map<string, string> {
  const errors = get(validationErrors);
  const buttonErrors = new Map<string, string>();

  // Build prefix based on multi-bank mode
  const state = get(formState);
  let prefix: string;
  if (state.config.banks) {
    const activeIdx = get(activeBankIndex);
    prefix = `banks[${activeIdx}].buttons[${buttonIndex}]`;
  } else {
    prefix = `buttons[${buttonIndex}]`;
  }

  errors.forEach((error, key) => {
    if (key.startsWith(prefix)) {
      buttonErrors.set(key, error);
    }
  });

  return buttonErrors;
}
// =============================================================================
// Bank Management Functions
// =============================================================================

// Active bank index (0-indexed)
export const activeBankIndex = writable<number>(0);

// Derived: get current bank config
export const activeBank = derived(
  [config, activeBankIndex],
  ([$config, $activeBankIndex]) => {
    const banks = $config.banks ?? [];
    return banks[$activeBankIndex] ?? null;
  }
);

// Derived: total number of banks
export const bankCount = derived(config, $config => {
  return $config.banks?.length ?? 0;
});

// Switch to a different bank
export function switchBank(index: number) {
  const state = get(formState);
  const banks = state.config.banks ?? [];

  if (index < 0 || index >= banks.length) {
    console.error(`Invalid bank index: ${index}`);
    return;
  }

  activeBankIndex.set(index);
}

// Add a new bank
export function addBank(name?: string) {
  const state = get(formState);
  const banks = state.config.banks ?? [];

  // Enforce 8-bank maximum
  if (banks.length >= 8) {
    console.error('Cannot add bank: maximum of 8 banks reached');
    return;
  }

  const currentDevice = state.config.device ?? 'std10';
  const buttonCount = currentDevice === 'mini6' ? 6 : 10;

  // Create default buttons for new bank
  const defaultButtons: ButtonConfig[] = Array.from({ length: buttonCount }, (_, i) => ({
    label: `${i + 1}`,
    color: 'white',
    mode: 'toggle' as const,
    channel: 0,
    press: [{ type: 'cc' as const, cc: 20 + i, value: 127 }],
    release: [{ type: 'cc' as const, cc: 20 + i, value: 0 }],
  }));

  const newBankName = name ?? `Bank ${banks.length + 1}`;

  const newBank: import('./types').BankConfig = {
    name: newBankName,
    buttons: defaultButtons,
  };

  updateField('banks', [...banks, newBank]);

  // Switch to the new bank
  activeBankIndex.set(banks.length);
}

// Duplicate an existing bank
export function duplicateBank(index: number) {
  const state = get(formState);
  const banks = state.config.banks ?? [];

  if (index < 0 || index >= banks.length) {
    console.error(`Invalid bank index: ${index}`);
    return;
  }

  const sourceBank = banks[index];
  const newBank: import('./types').BankConfig = {
    name: `${sourceBank.name} (Copy)`,
    buttons: structuredClone(sourceBank.buttons),
  };

  updateField('banks', [...banks, newBank]);

  // Switch to the new bank
  activeBankIndex.set(banks.length);
}

// Delete a bank
export function deleteBank(index: number) {
  const state = get(formState);
  const banks = state.config.banks ?? [];

  if (index < 0 || index >= banks.length) {
    console.error(`Invalid bank index: ${index}`);
    return;
  }

  // Prevent deleting the last bank
  if (banks.length <= 1) {
    console.error('Cannot delete the last bank');
    return;
  }

  const newBanks = banks.filter((_, i) => i !== index);
  updateField('banks', newBanks);

  // Adjust active bank index if needed
  const currentActive = get(activeBankIndex);
  if (currentActive >= newBanks.length) {
    activeBankIndex.set(newBanks.length - 1);
  } else if (currentActive > index) {
    activeBankIndex.set(currentActive - 1);
  }
}

// Rename a bank
export function renameBank(index: number, newName: string) {
  const state = get(formState);
  const banks = state.config.banks ?? [];

  if (index < 0 || index >= banks.length) {
    console.error(`Invalid bank index: ${index}`);
    return;
  }

  updateField(`banks[${index}].name`, newName);
}

// Convert single-bank config to multi-bank
export function convertToMultiBank() {
  const state = get(formState);

  // Already multi-bank
  if (state.config.banks) {
    return;
  }

  // Legacy single-bank format
  const buttons = state.config.buttons ?? [];
  const bank: import('./types').BankConfig = {
    name: 'Bank 1',
    buttons: structuredClone(buttons),
  };

  formState.update(_state => {
    const newConfig = { ..._state.config };
    newConfig.banks = [bank];
    newConfig.active_bank = 0;
    delete newConfig.buttons;

    return {
      ..._state,
      config: newConfig,
    };
  });

  activeBankIndex.set(0);
  validate();
}

// Check if config is in multi-bank mode
export const isMultiBankMode = derived(config, $config => {
  return !!$config.banks && $config.banks.length > 0;
});
