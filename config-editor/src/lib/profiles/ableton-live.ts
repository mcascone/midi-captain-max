// Ableton Live Template Profile
import type { DeviceProfile } from './types';

export const abletonLiveProfile: DeviceProfile = {
  id: 'ableton-live',
  name: 'Ableton Live',
  manufacturer: 'Ableton',
  type: 'template',
  description: 'Ableton Live DAW - common MIDI mappings template',
  actions: [
    // Transport
    {
      id: 'transport_play',
      label: 'Play',
      description: 'Start/stop playback',
      midi: { type: 'note', note: 60, velocity: 127, channel: 0 }
    },
    {
      id: 'transport_record',
      label: 'Record',
      description: 'Toggle recording',
      midi: { type: 'note', note: 61, velocity: 127, channel: 0 }
    },
    {
      id: 'transport_stop',
      label: 'Stop',
      description: 'Stop playback',
      midi: { type: 'note', note: 62, velocity: 127, channel: 0 }
    },
    // Scenes
    {
      id: 'scene_1',
      label: 'Scene 1',
      description: 'Launch Scene 1',
      midi: { type: 'note', note: 64, velocity: 127, channel: 0 }
    },
    {
      id: 'scene_2',
      label: 'Scene 2',
      description: 'Launch Scene 2',
      midi: { type: 'note', note: 65, velocity: 127, channel: 0 }
    },
    {
      id: 'scene_3',
      label: 'Scene 3',
      description: 'Launch Scene 3',
      midi: { type: 'note', note: 66, velocity: 127, channel: 0 }
    },
    {
      id: 'scene_4',
      label: 'Scene 4',
      description: 'Launch Scene 4',
      midi: { type: 'note', note: 67, velocity: 127, channel: 0 }
    },
    // Metronome
    {
      id: 'metronome',
      label: 'Metronome',
      description: 'Toggle metronome',
      midi: { type: 'note', note: 63, velocity: 127, channel: 0 }
    },
    // Undo/Redo
    {
      id: 'undo',
      label: 'Undo',
      description: 'Undo last action',
      midi: { type: 'note', note: 70, velocity: 127, channel: 0 }
    },
    {
      id: 'redo',
      label: 'Redo',
      description: 'Redo last action',
      midi: { type: 'note', note: 71, velocity: 127, channel: 0 }
    }
  ]
};
