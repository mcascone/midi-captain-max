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
  channel?: number;  // Stored as 0-15, displayed as 1-16
  cc_on?: number;    // CC value when button is ON (default: 127)
  cc_off?: number;   // CC value when button is OFF (default: 0)
}

export interface EncoderPush {
  enabled: boolean;
  cc: number;
  label: string;
  mode?: ButtonMode;
  channel?: number;  // Stored as 0-15, displayed as 1-16
  cc_on?: number;    // CC value when button is ON (default: 127)
  cc_off?: number;   // CC value when button is OFF (default: 0)
}

export interface EncoderConfig {
  enabled: boolean;
  cc: number;
  label: string;
  min?: number;
  max?: number;
  initial?: number;
  steps?: number | null;
  channel?: number;  // Stored as 0-15, displayed as 1-16
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
  channel?: number;  // Stored as 0-15, displayed as 1-16
}

export interface ExpressionPedals {
  exp1: ExpressionConfig;
  exp2: ExpressionConfig;
}

export interface DisplayConfig {
  button_text_size?: 'small' | 'medium' | 'large';
  status_text_size?: 'small' | 'medium' | 'large';
  expression_text_size?: 'small' | 'medium' | 'large';
}

export interface MidiCaptainConfig {
  device?: DeviceType;
  global_channel?: number;  // Stored as 0-15, displayed as 1-16
  buttons: ButtonConfig[];
  encoder?: EncoderConfig;
  expression?: ExpressionPedals;
  display?: DisplayConfig;
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
