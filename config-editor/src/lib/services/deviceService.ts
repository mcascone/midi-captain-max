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
  validationErrors, statusMessage, isLoading, devices, showToast
} from '$lib/stores';
import {
  readConfigRaw, writeConfigRaw, ejectDevice, triggerDeviceReload
} from '$lib/api';
import { loadConfig, validate, normalizeConfig, config } from '$lib/formStore';
import type { DetectedDevice } from '$lib/types';

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
  
  if (!validate()) {
    showToast('Please fix validation errors before saving', 'error');
    return false;
  }
  
  isLoading.set(true);
  let saveSucceeded = false;
  
  try {
    const configObj = normalizeConfig(get(config));
    const configJson = JSON.stringify(configObj, null, 2);
    await writeConfigRaw(device.config_path, configJson);
    currentConfigRaw.set(configJson);
    hasUnsavedChanges.set(false);
    saveSucceeded = true;

    // Brief delay to ensure FAT32 flush reaches device before triggering reload
    await new Promise(resolve => setTimeout(resolve, 300));

    // Attempt serial reload — non-fatal; falls back to manual restart message
    try {
      await triggerDeviceReload(device.path);
      statusMessage.set('Config saved — device reloading\u2026');
      showToast('Config saved — device reloading\u2026', 'success');
    } catch {
      statusMessage.set('Config saved — restart device to apply changes');
      showToast('Config saved — restart device to apply changes', 'success');
    }
  } catch (e: any) {
    const errorMsg = `Error saving config: ${e.message || e}`;
    statusMessage.set(errorMsg);
    showToast(errorMsg, 'error', 5000);
  } finally {
    isLoading.set(false);
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
