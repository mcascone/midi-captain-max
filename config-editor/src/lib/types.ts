// MIDI Captain config types - mirrors Rust structs

export type ButtonColor = 
  | 'red' | 'green' | 'blue' | 'yellow' 
  | 'cyan' | 'magenta' | 'orange' | 'purple' | 'white';

export type ButtonMode = 'toggle' | 'momentary';
export type OffMode = 'dim' | 'off';
export type MessageType = 'cc' | 'note' | 'pc' | 'pc_inc' | 'pc_dec';
export type Polarity = 'normal' | 'inverted';
export type DeviceType = 'std10' | 'mini6';

export interface StateOverride {
  cc?: number;
  cc_on?: number;
  cc_off?: number;
  note?: number;
  velocity_on?: number;
  velocity_off?: number;
  program?: number;
  pc_step?: number;
  color?: ButtonColor;
  label?: string;
}

export interface ButtonConfig {
  label: string;
  color: ButtonColor;
  type?: MessageType;      // defaults to 'cc'
  mode?: ButtonMode;
  off_mode?: OffMode;
  channel?: number;        // Stored as 0-15, displayed as 1-16
  // CC fields (type='cc')
  cc?: number;
  cc_on?: number;          // CC value when ON (default: 127)
  cc_off?: number;         // CC value when OFF (default: 0)
  // Note fields (type='note')
  note?: number;           // MIDI note number 0-127
  velocity_on?: number;    // Note velocity when ON (default: 127)
  velocity_off?: number;   // Note velocity when OFF (default: 0)
  // PC fields (type='pc')
  program?: number;        // Program number 0-127
  // PC inc/dec fields (type='pc_inc' | 'pc_dec')
  pc_step?: number;        // Step size (default: 1)
  // PC flash feedback (all PC types)
  flash_ms?: number;       // LED flash duration in ms (default: 200)
  // Keytimes cycling
  keytimes?: number;         // States to cycle through on press (1-99); 1 = no cycling
  states?: StateOverride[];  // Per-state overrides; length should match keytimes
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
