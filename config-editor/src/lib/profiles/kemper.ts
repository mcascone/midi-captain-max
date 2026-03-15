// Kemper Profiler Device Profile
import type { DeviceProfile } from './types';

export const kemperProfile: DeviceProfile = {
  id: 'kemper',
  name: 'Kemper',
  manufacturer: 'Kemper',
  type: 'hybrid',
  description: 'Kemper Profiler guitar amp modeler',
  actions: [
    // Performance Slots (PC 0-4)
    {
      id: 'slot_1',
      label: 'Slot 1',
      description: 'Performance Slot 1',
      midi: { type: 'pc', program: 0, channel: 0 }
    },
    {
      id: 'slot_2',
      label: 'Slot 2',
      description: 'Performance Slot 2',
      midi: { type: 'pc', program: 1, channel: 0 }
    },
    {
      id: 'slot_3',
      label: 'Slot 3',
      description: 'Performance Slot 3',
      midi: { type: 'pc', program: 2, channel: 0 }
    },
    {
      id: 'slot_4',
      label: 'Slot 4',
      description: 'Performance Slot 4',
      midi: { type: 'pc', program: 3, channel: 0 }
    },
    {
      id: 'slot_5',
      label: 'Slot 5',
      description: 'Performance Slot 5',
      midi: { type: 'pc', program: 4, channel: 0 }
    },
    // Tap Tempo
    {
      id: 'tap_tempo',
      label: 'Tap Tempo',
      description: 'Tap tempo input',
      midi: { type: 'cc', cc: 30, value: 127, channel: 0 }
    },
    // Tuner
    {
      id: 'tuner',
      label: 'Tuner',
      description: 'Toggle tuner',
      midi: { type: 'cc', cc: 31, value: 1, channel: 0 }
    },
    // Effect Toggles (CC17-20)
    {
      id: 'effect_button_i',
      label: 'Effect I',
      description: 'Toggle Effect Button I',
      midi: { type: 'cc', cc: 17, value: 127, channel: 0 }
    },
    {
      id: 'effect_button_ii',
      label: 'Effect II',
      description: 'Toggle Effect Button II',
      midi: { type: 'cc', cc: 18, value: 127, channel: 0 }
    },
    {
      id: 'effect_button_iii',
      label: 'Effect III',
      description: 'Toggle Effect Button III',
      midi: { type: 'cc', cc: 19, value: 127, channel: 0 }
    },
    {
      id: 'effect_button_iv',
      label: 'Effect IV',
      description: 'Toggle Effect Button IV',
      midi: { type: 'cc', cc: 20, value: 127, channel: 0 }
    }
  ]
};
