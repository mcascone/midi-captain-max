// Device Profile Registry
import type { DeviceProfile } from './types';
import { quadCortexProfile } from './quad-cortex';
import { helixProfile } from './helix';
import { kemperProfile } from './kemper';

export * from './types';
export * from './quad-cortex';
export * from './helix';
export * from './kemper';
export * from './resolver';

/**
 * All available device profiles
 */
export const profiles: DeviceProfile[] = [
  quadCortexProfile,
  helixProfile,
  kemperProfile
];

/**
 * Profile lookup by ID
 */
export const profilesById: Record<string, DeviceProfile> = {
  [quadCortexProfile.id]: quadCortexProfile,
  [helixProfile.id]: helixProfile,
  [kemperProfile.id]: kemperProfile
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
