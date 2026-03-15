// Apple MainStage Template Profile
import type { DeviceProfile } from './types';

export const mainStageProfile: DeviceProfile = {
  id: 'mainstage',
  name: 'MainStage',
  manufacturer: 'Apple',
  type: 'template',
  description: 'Apple MainStage live performance software',
  actions: [
    // Patch changes (PC)
    {
      id: 'patch_1',
      label: 'Patch 1',
      description: 'Select Patch 1',
      midi: { type: 'pc', program: 0, channel: 0 }
    },
    {
      id: 'patch_2',
      label: 'Patch 2',
      description: 'Select Patch 2',
      midi: { type: 'pc', program: 1, channel: 0 }
    },
    {
      id: 'patch_3',
      label: 'Patch 3',
      description: 'Select Patch 3',
      midi: { type: 'pc', program: 2, channel: 0 }
    },
    {
      id: 'patch_4',
      label: 'Patch 4',
      description: 'Select Patch 4',
      midi: { type: 'pc', program: 3, channel: 0 }
    },
    {
      id: 'patch_5',
      label: 'Patch 5',
      description: 'Select Patch 5',
      midi: { type: 'pc', program: 4, channel: 0 }
    },
    {
      id: 'patch_next',
      label: 'Next Patch',
      description: 'Next patch',
      midi: { type: 'pc_inc', pc_step: 1, channel: 0 }
    },
    {
      id: 'patch_prev',
      label: 'Prev Patch',
      description: 'Previous patch',
      midi: { type: 'pc_dec', pc_step: 1, channel: 0 }
    },
    // Common CC mappings
    {
      id: 'sustain',
      label: 'Sustain',
      description: 'Sustain pedal (CC64)',
      midi: { type: 'cc', cc: 64, value: 127, channel: 0 }
    },
    {
      id: 'expression',
      label: 'Expression',
      description: 'Expression pedal (CC11)',
      midi: { type: 'cc', cc: 11, value: 127, channel: 0 }
    },
    // Tuner
    {
      id: 'tuner',
      label: 'Tuner',
      description: 'Toggle tuner',
      midi: { type: 'cc', cc: 102, value: 127, channel: 0 }
    }
  ]
};
