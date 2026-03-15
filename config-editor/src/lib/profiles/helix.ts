// Line 6 Helix Device Profile
import type { DeviceProfile } from './types';

export const helixProfile: DeviceProfile = {
  id: 'helix',
  name: 'Helix',
  manufacturer: 'Line 6',
  type: 'hybrid',
  description: 'Line 6 Helix guitar processor',
  actions: [
    // Snapshot Recall (CC69)
    {
      id: 'snapshot_1',
      label: 'Snapshot 1',
      description: 'Recall Snapshot 1',
      midi: { type: 'cc', cc: 69, value: 0, channel: 0 }
    },
    {
      id: 'snapshot_2',
      label: 'Snapshot 2',
      description: 'Recall Snapshot 2',
      midi: { type: 'cc', cc: 69, value: 1, channel: 0 }
    },
    {
      id: 'snapshot_3',
      label: 'Snapshot 3',
      description: 'Recall Snapshot 3',
      midi: { type: 'cc', cc: 69, value: 2, channel: 0 }
    },
    {
      id: 'snapshot_4',
      label: 'Snapshot 4',
      description: 'Recall Snapshot 4',
      midi: { type: 'cc', cc: 69, value: 3, channel: 0 }
    },
    {
      id: 'snapshot_5',
      label: 'Snapshot 5',
      description: 'Recall Snapshot 5',
      midi: { type: 'cc', cc: 69, value: 4, channel: 0 }
    },
    {
      id: 'snapshot_6',
      label: 'Snapshot 6',
      description: 'Recall Snapshot 6',
      midi: { type: 'cc', cc: 69, value: 5, channel: 0 }
    },
    {
      id: 'snapshot_7',
      label: 'Snapshot 7',
      description: 'Recall Snapshot 7',
      midi: { type: 'cc', cc: 69, value: 6, channel: 0 }
    },
    {
      id: 'snapshot_8',
      label: 'Snapshot 8',
      description: 'Recall Snapshot 8',
      midi: { type: 'cc', cc: 69, value: 7, channel: 0 }
    },
    // Tap Tempo
    {
      id: 'tap_tempo',
      label: 'Tap Tempo',
      description: 'Tap tempo input',
      midi: { type: 'cc', cc: 64, value: 127, channel: 0 }
    },
    // Tuner
    {
      id: 'tuner',
      label: 'Tuner',
      description: 'Toggle tuner',
      midi: { type: 'cc', cc: 68, value: 127, channel: 0 }
    }
  ]
};
