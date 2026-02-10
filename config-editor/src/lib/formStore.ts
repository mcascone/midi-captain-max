import { writable, derived, get } from 'svelte/store';
import type { MidiCaptainConfig, ButtonConfig, EncoderConfig, DeviceType } from './types';

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
  formState.update(state => ({
    config: structuredClone(newConfig),
    history: [structuredClone(newConfig)],
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
      // Check object property exists
      if (current[part] === undefined || current[part] === null) {
        throw new Error(`Invalid path "${path}": ${part} does not exist`);
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
  
  // Debounce history push
  debounceTimer = setTimeout(() => {
    formState.update(state => pushHistory(state));
  }, DEBOUNCE_MS);
}
