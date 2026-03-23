// Svelte stores for state management
import { writable, derived } from 'svelte/store';
import type { DetectedDevice } from './types';

// Connected devices
export const devices = writable<DetectedDevice[]>([]);

// Currently selected device
export const selectedDevice = writable<DetectedDevice | null>(null);

// Current config as raw JSON (for text editor)
export const currentConfigRaw = writable<string>('');

// Whether config has unsaved changes
export const hasUnsavedChanges = writable<boolean>(false);

// Validation errors
export const validationErrors = writable<string[]>([]);

// UI state
export const isLoading = writable<boolean>(false);
export const statusMessage = writable<string>('');
export const isReloadingDevice = writable<boolean>(false);

// Currently selected button index (for the right-panel settings editor)
export const selectedButtonIndex = writable<number>(0);

// Toast notifications - using Skeleton's toaster
import { toaster } from './toaster';

export function showToast(message: string, type: 'success' | 'error' | 'info' = 'success', duration = 3000) {
  toaster.create({
    type,
    title: message,
    description: '',
    duration
  });
}

// Button clipboard for copy/paste
import type { ButtonConfig } from './types';
export const buttonClipboard = writable<ButtonConfig | null>(null);

// MIDI UI state
export const midiPorts = writable<string[]>([]);
export const selectedMidiPort = writable<string | null>(null);

// Button runtime states (on/off tracking for visual feedback)
export const buttonStates = writable<boolean[]>([]);

// Derived: is a device selected and has config
export const canEdit = derived(
  [selectedDevice, currentConfigRaw],
  ([$device, $configRaw]) => $device !== null && $configRaw !== ''
);

// Status bar enhancements
export const lastSavedTimestamp = writable<Date | null>(null);
export const firmwareVersion = writable<string>('');
export const saveFeedback = writable<'idle' | 'saving' | 'success' | 'error'>('idle');
