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

// Toast notifications
export interface ToastNotification {
  id: number;
  message: string;
  type: 'success' | 'error' | 'info';
  duration?: number;
}

export const toasts = writable<ToastNotification[]>([]);

let toastId = 0;

export function showToast(message: string, type: 'success' | 'error' | 'info' = 'success', duration = 3000) {
  const id = toastId++;
  toasts.update(t => [...t, { id, message, type, duration }]);
}

export function removeToast(id: number) {
  toasts.update(t => t.filter(toast => toast.id !== id));
}

// Button clipboard for copy/paste
import type { ButtonConfig } from './types';
export const buttonClipboard = writable<ButtonConfig | null>(null);

// Derived: is a device selected and has config
export const canEdit = derived(
  [selectedDevice, currentConfigRaw],
  ([$device, $configRaw]) => $device !== null && $configRaw !== ''
);
