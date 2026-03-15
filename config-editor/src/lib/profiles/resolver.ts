// Profile Resolution Logic
import type { MidiCommand } from '../types';
import type { ProfileMidiCommand, DeviceProfile } from './types';
import { getProfile } from './index';

/**
 * Resolve a profile action to MIDI commands
 * @param profileId - Device profile ID (e.g., 'quad-cortex')
 * @param actionId - Action ID within profile (e.g., 'scene_b')
 * @returns Array of MIDI commands, or undefined if resolution fails
 */
export function resolveProfileAction(
  profileId: string,
  actionId: string
): MidiCommand[] | undefined {
  const profile = getProfile(profileId);
  if (!profile) {
    console.warn(`[Profile Resolver] Profile not found: ${profileId}`);
    return undefined;
  }

  const action = profile.actions.find(a => a.id === actionId);
  if (!action) {
    console.warn(`[Profile Resolver] Action not found: ${actionId} in profile ${profileId}`);
    return undefined;
  }

  // Convert profile MIDI command(s) to editor MIDI command format
  const profileCommands = Array.isArray(action.midi) ? action.midi : [action.midi];
  const resolvedCommands: MidiCommand[] = profileCommands.map(cmd => 
    convertProfileCommand(cmd)
  );

  console.log(`[Profile Resolver] Resolved ${profileId}.${actionId}:`, resolvedCommands);
  return resolvedCommands;
}

/**
 * Convert a ProfileMidiCommand to editor MidiCommand format
 */
function convertProfileCommand(cmd: ProfileMidiCommand): MidiCommand {
  const base: MidiCommand = {
    type: cmd.type,
    channel: cmd.channel
  };

  switch (cmd.type) {
    case 'cc':
      return { ...base, cc: cmd.cc, value: cmd.value };
    case 'note':
      return { ...base, note: cmd.note, velocity: cmd.velocity };
    case 'pc':
      return { ...base, program: cmd.program };
    case 'pc_inc':
      return { ...base, type: 'pc_inc', pc_step: cmd.pc_step };
    case 'pc_dec':
      return { ...base, type: 'pc_dec', pc_step: cmd.pc_step };
    default:
      // Should never reach here with typed ProfileMidiCommand
      return base;
  }
}

/**
 * Get all actions for a profile
 * @param profileId - Device profile ID
 * @returns Array of action IDs and labels, or undefined if profile not found
 */
export function getProfileActions(profileId: string): Array<{ id: string; label: string; description?: string }> | undefined {
  const profile = getProfile(profileId);
  if (!profile) {
    return undefined;
  }

  return profile.actions.map(action => ({
    id: action.id,
    label: action.label,
    description: action.description
  }));
}

/**
 * Check if a button is using a device profile
 */
export function isProfileButton(button: { profile_id?: string; action_id?: string }): boolean {
  return Boolean(button.profile_id && button.action_id);
}

/**
 * Apply profile resolution to a button config (mutates press array)
 * Used before saving config to convert profile actions to raw MIDI
 * @returns true if resolution succeeded, false if it failed
 */
export function applyProfileResolution(button: {
  profile_id?: string;
  action_id?: string;
  press?: MidiCommand[];
}): boolean {
  if (!isProfileButton(button)) {
    return true; // Not a profile button, nothing to resolve
  }

  const commands = resolveProfileAction(button.profile_id!, button.action_id!);
  if (!commands) {
    return false; // Resolution failed
  }

  // Update button's press array with resolved commands
  button.press = commands;
  return true;
}
