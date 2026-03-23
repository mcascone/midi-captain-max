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

export async function ejectDevice(path: string): Promise<string> {
  return invoke('eject_device', { path });
}

export async function triggerDeviceReload(devicePath: string): Promise<string> {
  return invoke('trigger_device_reload', { devicePath });
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

// MIDI wrappers
export async function listMidiPorts(): Promise<string[]> {
  return invoke('list_midi_ports_cmd');
}

export async function sendMidiMessage(portName: string, data: number[]): Promise<void> {
  return invoke('send_midi_message_cmd', { portName, data });
}

export async function startMidiInputListener(portName: string): Promise<void> {
  return invoke('start_midi_input_listener_cmd', { portName });
}

export async function stopMidiInputListener(): Promise<void> {
  return invoke('stop_midi_input_listener_cmd');
}

// Frontend event: subscribe to MIDI events emitted by the backend
export function onMidiEvent(callback: (evt: { timestamp: number; data: number[]; port: string }) => void) {
  return listen<{ timestamp: number; data: number[]; port: string }>('midi-event', (event) => {
    callback(event.payload);
  });
}
