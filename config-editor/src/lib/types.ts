// MIDI Captain config types - mirrors Rust structs

export type ButtonColor =
  | 'red' | 'green' | 'blue' | 'yellow'
  | 'cyan' | 'magenta' | 'orange' | 'purple' | 'white'
  | 'pink' | 'lime' | 'amber' | 'teal' | 'violet' | 'gold';

export type ButtonMode = 'toggle' | 'normal' | 'momentary' | 'select' | 'tap';
export type OffMode = 'dim' | 'off';
export type MessageType = 'cc' | 'note' | 'pc' | 'pc_inc' | 'pc_dec';
export type Polarity = 'normal' | 'inverted';
export type DeviceType = 'std10' | 'mini6';

// ===== CONDITIONAL ACTIONS SUPPORT =====

export type ConditionOperator = '==' | '!=' | '>' | '<' | '>=' | '<=';

// Button state condition - checks if a button is ON or OFF
export interface ButtonStateCondition {
  type: 'button_state';
  button: number;      // Button index (0-based)
  state: 'on' | 'off';
}

// Button keytime condition - checks which keytime state a button is in
export interface ButtonKeytimeCondition {
  type: 'button_keytime';
  button: number;      // Button index (0-based)
  keytime: number;     // Keytime index (0-based)
}

// Received MIDI condition - checks last received CC value from host
export interface ReceivedMidiCondition {
  type: 'received_midi';
  cc: number;          // CC number (0-127)
  channel: number;     // MIDI channel (0-15)
  operator: ConditionOperator;
  value: number;       // Value to compare (0-127)
}

// Expression pedal condition - checks pedal position
export interface ExpressionCondition {
  type: 'expression';
  pedal: 1 | 2;        // Expression pedal 1 or 2
  operator: ConditionOperator;
  value: number;       // Value to compare (0-127)
}

// Encoder condition - checks encoder position
export interface EncoderCondition {
  type: 'encoder';
  operator: ConditionOperator;
  value: number;       // Value to compare (0-127)
}

// Union of all condition types
export type Condition = 
  | ButtonStateCondition 
  | ButtonKeytimeCondition 
  | ReceivedMidiCondition
  | ExpressionCondition
  | EncoderCondition;

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

// Conditional command wrapper - allows if/then/else logic
export interface ConditionalCommand {
  type: 'conditional';
  if: Condition;                    // Condition to evaluate
  then: CommandOrConditional[];     // Commands to execute if condition is true
  else?: CommandOrConditional[];    // Optional commands to execute if condition is false
}

// Union type for command arrays - can be regular MIDI commands or conditional wrappers
export type CommandOrConditional = MidiCommand | ConditionalCommand;

export interface StateOverride {
  // ===== Multi-command event arrays (per-state actions) =====
  press?: MidiCommand[];      // Commands dispatched on button press for this state
  release?: MidiCommand[];    // Commands dispatched on button release for this state
  long_press?: MidiCommand[]; // Commands dispatched on long press for this state
  long_release?: MidiCommand[]; // Commands dispatched on long release for this state

  // ===== Legacy single-type field overrides =====
  cc?: number;
  cc_on?: number;
  cc_off?: number;
  note?: number;
  velocity_on?: number;
  velocity_off?: number;
  program?: number;
  pc_step?: number;

  // ===== Visual overrides =====
  color?: ButtonColor;
  label?: string;
}

export interface ButtonConfig {
  label: string;
  long_press_label?: string;  // Optional label to display when long press triggers
  long_press_color?: ButtonColor; // Optional color to display when long press triggers
  long_press_label_persist?: boolean; // Whether to keep long_press_label visible (default: true)
  color: ButtonColor;

  // ===== DEVICE PROFILE SUPPORT =====
  // When set, the editor resolves the action to MIDI commands before saving
  profile_id?: string;        // Device profile ID (e.g., 'quad-cortex', 'helix')
  action_id?: string;         // Action within profile (e.g., 'scene_b', 'snapshot_3')

  // ===== NEW: Multi-command event arrays =====
  // These take precedence over legacy type-based fields
  // Now supports conditional commands in addition to regular MIDI commands
  press?: CommandOrConditional[];      // Commands dispatched on button press
  release?: CommandOrConditional[];    // Commands dispatched on button release (short press)
  long_press?: CommandOrConditional[]; // Commands dispatched when hold threshold crossed
  long_release?: CommandOrConditional[]; // Commands dispatched on release after long press

  // ===== LEGACY: Single-type fields (for backwards compatibility) =====
  // These are automatically migrated to event arrays by the firmware
  type?: MessageType;      // defaults to 'cc'
  mode?: ButtonMode;
  off_mode?: OffMode;
  dim_brightness?: number; // LED brightness when off_mode is 'dim' (0-100, default: 30)
  channel?: number;        // Stored as 0-15, displayed as 1-16
  // Simplified toggle fields (mode='toggle' only — no press/release arrays needed)
  value_on?: number;       // CC value sent when turning ON (0-127, default 127)
  value_off?: number;      // CC value sent when turning OFF (0-127, default 0)
  default_on?: boolean;    // Boot in ON state and send value_on at startup (default false)
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
  button_name_text_size?: 'small' | 'medium' | 'large';
}

export interface SplashScreenConfig {
  enabled?: boolean;     // Whether to show splash (default: true)
  duration_ms?: number;  // Display duration in milliseconds (default: 1500)
  idle_timeout_seconds?: number; // Show splash after N seconds idle (0 or undefined = disabled)
}

export type MidiTransport = 'usb' | 'trs' | 'both';

// ===== BANKS/PAGES SUPPORT =====

export interface BankConfig {
  name: string;              // Bank name (e.g., "Live Set 1", "Studio")
  buttons: ButtonConfig[];   // Button configs for this bank
}

export type BankSwitchMethod = 'button' | 'cc' | 'pc';

export interface BankSwitchConfig {
  method: BankSwitchMethod;  // How to switch banks
  button?: number;           // [Legacy] Single button cycles through banks (1-10 for STD10, 1-6 for Mini6)
  button_next?: number;      // Button for next bank (bank up) - if set, takes precedence over 'button'
  button_prev?: number;      // Button for previous bank (bank down)
  cc?: number;               // CC number (0-127) if method='cc'
  pc_base?: number;          // Base PC number (0-127) if method='pc' (bank 0 = pc_base, bank 1 = pc_base+1, etc.)
  channel?: number;          // MIDI channel for bank switching (0-15)
}

export interface MidiCaptainConfig {
  device?: DeviceType;
  global_channel?: number;  // Stored as 0-15, displayed as 1-16
  usb_drive_name?: string;  // Custom USB drive label (max 11 chars, alphanumeric + underscore)
  dev_mode?: boolean;       // true = USB always mounts; false (default) = switch-gated
  midi_transport?: MidiTransport; // "usb" (default) | "trs" | "both"
  // Optional global default threshold for long-press in milliseconds
  long_press_threshold_ms?: number;
  
  // ===== MULTI-BANK SUPPORT =====
  // If 'banks' is present, use multi-bank mode (preferred)
  // If 'buttons' is present without 'banks', use single-bank mode (legacy, auto-wrapped)
  banks?: BankConfig[];      // Array of banks (max 8)
  bank_switch?: BankSwitchConfig; // Bank switching configuration
  active_bank?: number;      // Active bank on boot (0-indexed, default: 0)
  
  // ===== SINGLE-BANK MODE (legacy, backward compatibility) =====
  buttons?: ButtonConfig[];  // Legacy: single bank of buttons (auto-wrapped in banks[0] on load)
  
  // ===== SHARED ACROSS ALL BANKS =====
  encoder?: EncoderConfig;
  expression?: ExpressionPedals;
  display?: DisplayConfig;
  splash_screen?: SplashScreenConfig;
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
  pink: '#ff69b4',
  lime: '#00ff80',
  amber: '#ffbf00',
  teal: '#008080',
  violet: '#6600cc',
  gold: '#ffd700',
};
