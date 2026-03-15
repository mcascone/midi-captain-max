// Device Profile Registry
import type { DeviceProfile } from './types';
import { quadCortexProfile } from './quad-cortex';
import { helixProfile } from './helix';
import { hxStompProfile } from './hx-stomp';
import { kemperProfile } from './kemper';
import { abletonLiveProfile } from './ableton-live';
import { mainStageProfile } from './mainstage';

export * from './types';
export * from './quad-cortex';
export * from './helix';
export * from './hx-stomp';
export * from './kemper';
export * from './ableton-live';
export * from './mainstage';
export * from './resolver';

/**
 * All available device profiles
 */
export const profiles: DeviceProfile[] = [
  quadCortexProfile,
  helixProfile,
  hxStompProfile,
  kemperProfile,
  abletonLiveProfile,
  mainStageProfile
];

/**
 * Profile lookup by ID
 */
export const profilesById: Record<string, DeviceProfile> = {
  [quadCortexProfile.id]: quadCortexProfile,
  [helixProfile.id]: helixProfile,
  [hxStompProfile.id]: hxStompProfile,
  [kemperProfile.id]: kemperProfile,
  [abletonLiveProfile.id]: abletonLiveProfile,
  [mainStageProfile.id]: mainStageProfile
};

/**
 * Get a profile by ID
 */
export function getProfile(id: string): DeviceProfile | undefined {
  return profilesById[id];
}

/**
 * Get all profiles for a specific type
 */
export function getProfilesByType(type: 'fixed' | 'hybrid' | 'template'): DeviceProfile[] {
  return profiles.filter(p => p.type === type);
}
