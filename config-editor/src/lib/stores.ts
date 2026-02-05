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

// Derived: is a device selected and has config
export const canEdit = derived(
  [selectedDevice, currentConfigRaw],
  ([$device, $configRaw]) => $device !== null && $configRaw !== ''
);
