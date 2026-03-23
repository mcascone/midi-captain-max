/**
 * Device Management Service
 *
 * Encapsulates device selection, config loading/saving, and eject logic.
 * Separated from +page.svelte for better organization and testability.
 */

import { get } from 'svelte/store';
import { message } from '@tauri-apps/plugin-dialog';
import {
  selectedDevice, currentConfigRaw, hasUnsavedChanges,
  validationErrors, statusMessage, isLoading, devices, showToast, isReloadingDevice,
  lastSavedTimestamp, saveFeedback, selectedMidiPort
} from '$lib/stores';
import {
  readConfigRaw, writeConfigRaw, ejectDevice, triggerDeviceReload,
  listMidiPorts
} from '$lib/api';
import { loadConfig, validate, normalizeConfig, config } from '$lib/formStore';
import type { DetectedDevice } from '$lib/types';

// Track reload timeout to allow cancellation on subsequent saves
let reloadTimeoutId: ReturnType<typeof setTimeout> | null = null;

/**
 * Select a device and load its configuration
 */
export async function selectDevice(device: DetectedDevice) {
  if (get(hasUnsavedChanges) && !confirm('You have unsaved changes. Discard them?')) return;

  selectedDevice.set(device);
  isLoading.set(true);

  try {
    if (device.has_config) {
      const configRaw = await readConfigRaw(device.config_path);
      loadConfig(JSON.parse(configRaw));
      currentConfigRaw.set(configRaw);
      hasUnsavedChanges.set(false);
      validationErrors.set([]);
      statusMessage.set('Config loaded successfully');
    } else {
      currentConfigRaw.set('');
      statusMessage.set('No config.json found on device');
    }
  } catch (e: any) {
    statusMessage.set(`Error reading config: ${e.message || e}`);
  } finally {
    isLoading.set(false);
  }
}

/**
 * Save current configuration to device
 * Returns true if save succeeded, false otherwise
 */
export async function saveToDevice(): Promise<boolean> {
  const device = get(selectedDevice);
  if (!device) return false;

  const validationResult = validate();
  if (!validationResult.isValid) {
    // Get validation errors directly from result (avoids timing issues with derived stores)
    const errors = validationResult.errors;
    if (errors.size > 0) {
      const errorList = Array.from(errors.entries())
        .slice(0, 5) // Show first 5 errors
        .map(([field, message]) => `• ${field}: ${message}`)
        .join('\n');
      const remaining = errors.size > 5 ? `\n... and ${errors.size - 5} more errors` : '';
      showToast(`Validation errors:\n${errorList}${remaining}`, 'error');
    } else {
      showToast('Please fix validation errors before saving', 'error');
    }
    return false;
  }

  isLoading.set(true);
  saveFeedback.set('saving');
  let saveSucceeded = false;

  try {
    // Read dev_mode from config BEFORE normalization
    const currentConfig = get(config);
    const devMode = currentConfig.dev_mode ?? false;

    const configObj = normalizeConfig(currentConfig);

    // Debug: log buttons with conditional commands
    const buttons = configObj.banks ? configObj.banks[0]?.buttons : configObj.buttons;
    if (buttons) {
      buttons.forEach((btn: any, idx: number) => {
        if (btn.press) {
          btn.press.forEach((cmd: any, cmdIdx: number) => {
            if (cmd.type === 'conditional') {
              console.log(`[SAVE] Button ${idx}, Press[${cmdIdx}]:`, {
                type: cmd.type,
                then_label: cmd.then_label,
                else_label: cmd.else_label
              });
            }
          });
        }
      });
    }

    const configJson = JSON.stringify(configObj, null, 2);
    console.log('[SAVE] Config JSON length:', configJson.length);
    
    // Write to filesystem for persistence
    await writeConfigRaw(device.config_path, configJson);
    currentConfigRaw.set(configJson);
    console.log('[SAVE] Written to filesystem');
    
    // Reload method depends on dev_mode setting
    if (devMode) {
      // Dev mode: trigger serial reload (device restarts automatically)
      try {
        statusMessage.set('Reloading device config...');
        await triggerDeviceReload(device.path);
        isReloadingDevice.set(true);
        
        if (reloadTimeoutId !== null) {
          clearTimeout(reloadTimeoutId);
        }
        reloadTimeoutId = setTimeout(() => {
          isReloadingDevice.set(false);
          reloadTimeoutId = null;
        }, 5000);
        
        lastSavedTimestamp.set(new Date());
        saveFeedback.set('success');
        hasUnsavedChanges.set(false);
        saveSucceeded = true;
        statusMessage.set('Config saved — device restarting…');
        showToast('Config saved! Device will restart.', 'success');
      } catch (e: any) {
        console.warn('[SAVE] Serial reload failed:', e);
        statusMessage.set('Config saved to disk — restart device manually to apply');
        lastSavedTimestamp.set(new Date());
        saveFeedback.set('success');
        hasUnsavedChanges.set(false);
        saveSucceeded = true;
        showToast('Config saved! Restart device to apply.', 'info');
      }
    } else {
      // Performance mode: config saved, manual restart required
      statusMessage.set('Config saved to disk — unplug and reconnect device to apply');
      lastSavedTimestamp.set(new Date());
      saveFeedback.set('success');
      hasUnsavedChanges.set(false);
      saveSucceeded = true;
      showToast('Config saved! Reconnect device to apply changes.', 'info');
    }
  } catch (e: any) {
    const errorMsg = `Error saving config: ${e.message || e}`;
    statusMessage.set(errorMsg);
    showToast(errorMsg, 'error', 5000);
    saveFeedback.set('error');
  } finally {
    isLoading.set(false);
    // Reset feedback after animation
    setTimeout(() => saveFeedback.set('idle'), 2000);
  }

  return saveSucceeded;
}

/**
 * Prompt user to eject device after successful save
 */
export async function promptEjectDevice() {
  const device = get(selectedDevice);
  if (!device) return;

  const shouldEject = confirm(
    'Config saved! Would you like to safely eject the device?\n\n' +
    'After ejecting:\n' +
    '1. Press the power button on the BACK of the device to turn it off\n' +
    '2. Wait 2 seconds\n' +
    '3. Press the power button again to turn it back on\n\n' +
    'The new config will be loaded on startup.'
  );

  if (!shouldEject) return;

  try {
    const devicePath = device.path.toString();
    const deviceName = device.name;

    const result = await ejectDevice(devicePath);
    showToast(result, 'success');

    // Clear current device selection
    selectedDevice.set(null);
    statusMessage.set(`${deviceName} ejected - waiting for reconnection...`);

    // Auto-select next available device if any
    const allDevices = get(devices);
    if (allDevices.length > 1) {
      const nextDevice = allDevices.find(d => d.path.toString() !== devicePath);
      if (nextDevice) {
        await new Promise(resolve => setTimeout(resolve, 500));
        await selectDevice(nextDevice);
      }
    }
  } catch (e: any) {
    // On Windows or if eject fails, show manual instructions
    await message(
      e.message || 'Could not eject device automatically.\n\nPlease eject manually using your system\'s device manager.',
      { title: 'Eject Device', kind: 'info' }
    );
  }
}

/**
 * Reload configuration from currently selected device
 */
export async function reloadFromDevice() {
  const device = get(selectedDevice);
  if (!device) return;

  isLoading.set(true);

  try {
    if (device.has_config) {
      const configRaw = await readConfigRaw(device.config_path);
      loadConfig(JSON.parse(configRaw));
      currentConfigRaw.set(configRaw);
      hasUnsavedChanges.set(false);
      validationErrors.set([]);
      statusMessage.set('Config reloaded from device');
    }
  } catch (e: any) {
    statusMessage.set(`Error reloading config: ${e.message || e}`);
  } finally {
    isLoading.set(false);
  }
}

/**
 * Show instructions for resetting the device
 */
export async function resetDevice() {
  const device = get(selectedDevice);
  if (!device) return;

  await message(
    'To apply config changes, restart your MIDI Captain:\n\n' +
    '1. Press the power button on the BACK of the device to turn it off\n' +
    '2. Wait 2 seconds\n' +
    '3. Press the power button again to turn it back on\n\n' +
    'The new config will be loaded on startup.',
    { title: 'Restart Device', kind: 'info' }
  );
  statusMessage.set('Restart device to apply config changes');
}

/**
 * Save current config and prompt for device eject
 */
export async function saveAndEject() {
  const saveSucceeded = await saveToDevice();
  if (saveSucceeded) {
    await promptEjectDevice();
  }
}
