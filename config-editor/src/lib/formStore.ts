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
