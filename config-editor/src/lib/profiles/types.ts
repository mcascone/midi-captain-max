// Device Profile Types for MIDI Captain MAX

export type ProfileType = 'fixed' | 'hybrid' | 'template';

export interface ProfileMidiCommand {
  type: 'cc' | 'note' | 'pc';
  channel?: number;  // 0-15 (optional, defaults to button channel)
  // CC fields
  cc?: number;
  value?: number;
  // Note fields
  note?: number;
  velocity?: number;
  // PC fields
  program?: number;
}

export interface ProfileAction {
  id: string;
  label: string;
  description?: string;
  midi: ProfileMidiCommand | ProfileMidiCommand[];  // Single command or array for multi-command
}

export interface DeviceProfile {
  id: string;
  name: string;
  manufacturer?: string;
  type: ProfileType;
  description?: string;
  actions: ProfileAction[];
}

// Profile-based button configuration
export interface ProfileButtonConfig {
  source: 'profile';
  profile_id: string;
  action_id: string;
  // Resolved MIDI (cached for firmware)
  resolved?: ProfileMidiCommand | ProfileMidiCommand[];
}
