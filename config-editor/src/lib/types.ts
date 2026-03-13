// MIDI Captain config types - mirrors Rust structs

export type ButtonColor =
  | 'red' | 'green' | 'blue' | 'yellow'
  | 'cyan' | 'magenta' | 'orange' | 'purple' | 'white';

export type ButtonMode = 'toggle' | 'momentary' | 'select' | 'tap';
export type OffMode = 'dim' | 'off';
export type MessageType = 'cc' | 'note' | 'pc' | 'pc_inc' | 'pc_dec';
export type Polarity = 'normal' | 'inverted';
export type DeviceType = 'std10' | 'mini6';

// Multi-command per action support
export interface MidiCommand {
  type: MessageType;
  channel?: number;    // 0-15 (optional, defaults to button channel or global_channel)
  // CC fields
  cc?: number;
  value?: number;      // CC value (replaces cc_on for simplicity)
  // Note fields
  note?: number;
  velocity?: number;   // Note velocity (replaces velocity_on for simplicity)
  // PC fields
  program?: number;
  // PC inc/dec fields
  pc_step?: number;
  // Optional threshold for long-press detection (on first command only)
  threshold_ms?: number;
}

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
  
  // ===== NEW: Multi-command event arrays =====
  // These take precedence over legacy type-based fields
  press?: MidiCommand[];      // Commands dispatched on button press
  release?: MidiCommand[];    // Commands dispatched on button release (short press)
  long_press?: MidiCommand[]; // Commands dispatched when hold threshold crossed
  long_release?: MidiCommand[]; // Commands dispatched on release after long press
  
  // ===== LEGACY: Single-type fields (for backwards compatibility) =====
  // These are automatically migrated to event arrays by the firmware
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
  
  // ===== COMMON FIELDS =====
  // Keytimes cycling
  keytimes?: number;         // States to cycle through on press (1-99); 1 = no cycling
  states?: StateOverride[];  // Per-state overrides; length should match keytimes
  // Optional select-group for mutually exclusive buttons (radio-group)
  // v1: supported for toggle-mode only and keytimes == 1
  select_group?: string;
  default_selected?: boolean;
  // Optional LED mode for visual feedback (e.g., 'tap' for blinking while active)
  led_mode?: 'tap';
  // Blink/tap rate in milliseconds when `led_mode` is 'tap'
  tap_rate_ms?: number;
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
  usb_drive_name?: string;  // Custom USB drive label (max 11 chars, alphanumeric + underscore)
  dev_mode?: boolean;       // true = USB always mounts; false (default) = switch-gated
  // Optional global default threshold for long-press in milliseconds
  long_press_threshold_ms?: number;
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
