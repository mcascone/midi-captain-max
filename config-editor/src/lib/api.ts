// Tauri command wrappers

import { invoke } from '@tauri-apps/api/core';
import { listen } from '@tauri-apps/api/event';
import type { MidiCaptainConfig, DetectedDevice } from './types';

// Config operations
export async function readConfig(path: string): Promise<MidiCaptainConfig> {
  return invoke('read_config', { path });
}

export async function readConfigRaw(path: string): Promise<string> {
  return invoke('read_config_raw', { path });
}

export async function writeConfig(path: string, config: MidiCaptainConfig): Promise<void> {
  return invoke('write_config', { path, config });
}

export async function writeConfigRaw(path: string, json: string): Promise<void> {
  return invoke('write_config_raw', { path, json });
}

export async function validateConfig(json: string): Promise<void> {
  return invoke('validate_config', { json });
}

// Device operations
export async function scanDevices(): Promise<DetectedDevice[]> {
  return invoke('scan_devices');
}

export async function startDeviceWatcher(): Promise<void> {
  return invoke('start_device_watcher');
}

// Event listeners
export function onDeviceConnected(callback: (device: DetectedDevice) => void) {
  return listen<DetectedDevice>('device-connected', (event) => {
    callback(event.payload);
  });
}

export function onDeviceDisconnected(callback: (name: string) => void) {
  return listen<string>('device-disconnected', (event) => {
    callback(event.payload);
  });
}
