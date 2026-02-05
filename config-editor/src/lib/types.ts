// MIDI Captain config types - mirrors Rust structs

export type ButtonColor = 
  | 'red' | 'green' | 'blue' | 'yellow' 
  | 'cyan' | 'magenta' | 'orange' | 'purple' | 'white';

export type ButtonMode = 'toggle' | 'momentary';
export type OffMode = 'dim' | 'off';
export type Polarity = 'normal' | 'inverted';
export type DeviceType = 'std10' | 'mini6';

export interface ButtonConfig {
  label: string;
  cc: number;
  color: ButtonColor;
  mode?: ButtonMode;
  off_mode?: OffMode;
}

export interface EncoderPush {
  enabled: boolean;
  cc: number;
  label: string;
  mode?: ButtonMode;
}

export interface EncoderConfig {
  enabled: boolean;
  cc: number;
  label: string;
  min?: number;
  max?: number;
  initial?: number;
  steps?: number | null;
  push?: EncoderPush;
}

export interface ExpressionConfig {
  enabled: boolean;
  cc: number;
  label: string;
  min?: number;
  max?: number;
  polarity?: Polarity;
  threshold?: number;
}

export interface ExpressionPedals {
  exp1: ExpressionConfig;
  exp2: ExpressionConfig;
}

export interface MidiCaptainConfig {
  device?: DeviceType;
  buttons: ButtonConfig[];
  encoder?: EncoderConfig;
  expression?: ExpressionPedals;
}

export interface DetectedDevice {
  name: string;
  path: string;
  config_path: string;
  has_config: boolean;
}

export interface ConfigError {
  message: string;
  details?: string[];
}

// Color mapping for UI
export const BUTTON_COLORS: Record<ButtonColor, string> = {
  red: '#ff0000',
  green: '#00ff00',
  blue: '#0000ff',
  yellow: '#ffff00',
  cyan: '#00ffff',
  magenta: '#ff00ff',
  orange: '#ff8000',
  purple: '#8000ff',
  white: '#ffffff',
};
