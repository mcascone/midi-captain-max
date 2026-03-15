// Neural DSP Quad Cortex Device Profile
import type { DeviceProfile } from './types';

export const quadCortexProfile: DeviceProfile = {
  id: 'quad_cortex',
  name: 'Quad Cortex',
  manufacturer: 'Neural DSP',
  type: 'fixed',
  description: 'Neural DSP Quad Cortex multi-effects processor',
  actions: [
    // Scene Recall (CC43)
    {
      id: 'scene_a',
      label: 'Scene A',
      description: 'Recall Scene A',
      midi: { type: 'cc', cc: 43, value: 0, channel: 0 }
    },
    {
      id: 'scene_b',
      label: 'Scene B',
      description: 'Recall Scene B',
      midi: { type: 'cc', cc: 43, value: 1, channel: 0 }
    },
    {
      id: 'scene_c',
      label: 'Scene C',
      description: 'Recall Scene C',
      midi: { type: 'cc', cc: 43, value: 2, channel: 0 }
    },
    {
      id: 'scene_d',
      label: 'Scene D',
      description: 'Recall Scene D',
      midi: { type: 'cc', cc: 43, value: 3, channel: 0 }
    },
    {
      id: 'scene_e',
      label: 'Scene E',
      description: 'Recall Scene E',
      midi: { type: 'cc', cc: 43, value: 4, channel: 0 }
    },
    {
      id: 'scene_f',
      label: 'Scene F',
      description: 'Recall Scene F',
      midi: { type: 'cc', cc: 43, value: 5, channel: 0 }
    },
    {
      id: 'scene_g',
      label: 'Scene G',
      description: 'Recall Scene G',
      midi: { type: 'cc', cc: 43, value: 6, channel: 0 }
    },
    {
      id: 'scene_h',
      label: 'Scene H',
      description: 'Recall Scene H',
      midi: { type: 'cc', cc: 43, value: 7, channel: 0 }
    },
    // Other Controls
    {
      id: 'tap_tempo',
      label: 'Tap Tempo',
      description: 'Tap tempo input',
      midi: { type: 'cc', cc: 44, value: 127, channel: 0 }
    },
    {
      id: 'tuner',
      label: 'Tuner',
      description: 'Toggle tuner',
      midi: { type: 'cc', cc: 45, value: 127, channel: 0 }
    },
    {
      id: 'gig_view',
      label: 'Gig View',
      description: 'Toggle gig view',
      midi: { type: 'cc', cc: 46, value: 127, channel: 0 }
    },
    {
      id: 'mode_select',
      label: 'Mode Select',
      description: 'Cycle modes',
      midi: { type: 'cc', cc: 47, value: 127, channel: 0 }
    }
  ]
};
