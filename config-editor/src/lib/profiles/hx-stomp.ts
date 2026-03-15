// Line 6 HX Stomp Device Profile
import type { DeviceProfile } from './types';

export const hxStompProfile: DeviceProfile = {
  id: 'hx-stomp',
  name: 'HX Stomp',
  manufacturer: 'Line 6',
  type: 'hybrid',
  description: 'Line 6 HX Stomp compact guitar processor',
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
    },
    // Looper Controls
    {
      id: 'looper_record',
      label: 'Looper Record',
      description: 'Looper record/overdub',
      midi: { type: 'cc', cc: 60, value: 127, channel: 0 }
    },
    {
      id: 'looper_play',
      label: 'Looper Play',
      description: 'Looper play/stop',
      midi: { type: 'cc', cc: 61, value: 127, channel: 0 }
    },
    {
      id: 'looper_undo',
      label: 'Looper Undo',
      description: 'Looper undo',
      midi: { type: 'cc', cc: 63, value: 127, channel: 0 }
    }
  ]
};
