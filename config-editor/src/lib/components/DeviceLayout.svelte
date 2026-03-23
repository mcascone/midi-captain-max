<script lang="ts">
  import { config, getButtonErrors, activeBank, isMultiBankMode } from '$lib/formStore';
  import { selectedButtonIndex, buttonStates, selectedMidiPort, midiPorts, showToast } from '$lib/stores';
  import { sendMidiMessage, listMidiPorts } from '$lib/api';
  import { get } from 'svelte/store';
  import { BUTTON_COLORS } from '$lib/types';
  import type { ButtonConfig, CommandOrConditional, MidiCommand } from '$lib/types';

  // Debug: watch buttonStates changes
  $effect(() => {
    console.log('[DeviceLayout] buttonStates changed:', $buttonStates);
  });

  // Get buttons from active bank if multi-bank mode, otherwise from top-level
  let buttons = $derived(
    $isMultiBankMode && $activeBank
      ? $activeBank.buttons
      : $config.buttons ?? []
  );

  let deviceType = $derived($config.device ?? 'std10');
  let totalSlots = $derived(deviceType === 'mini6' ? 6 : 10);

  // SVG dimensions based on device type
  let viewBox = $derived(deviceType === 'mini6' ? '0 0 560 400' : '0 0 800 400');
  let maxWidth = $derived(deviceType === 'mini6' ? 560 : 800);
  let cols = $derived(deviceType === 'mini6' ? 3 : 5);

  // Button layout constants
  const BUTTON_SIZE = 120;
  const BUTTON_SPACING = 40;
  const BUTTON_RADIUS = 12;
  const LED_SIZE = 20;
  const LED_OFFSET = -30; // Above button

  // Calculate button position
  function getButtonPosition(index: number): { x: number; y: number } {
    const row = Math.floor(index / cols);
    const col = index % cols;
    return {
      x: BUTTON_SPACING + col * (BUTTON_SIZE + BUTTON_SPACING),
      y: 60 + row * (BUTTON_SIZE + BUTTON_SPACING + 20)
    };
  }

  // Get button config safely
  function getButton(index: number): ButtonConfig | null {
    return buttons[index] ?? null;
  }

  // Get LED color for button (responds to button state)
  function getLedColor(btn: ButtonConfig | null, index: number): string {
    if (!btn) return '#555555'; // Neutral gray for empty

    const baseColor = BUTTON_COLORS[btn.color] ?? '#ffffff';
    const isOn = $buttonStates[index] ?? false;
    const mode = btn.mode ?? 'toggle';

    // For toggle/select buttons, show full brightness when on, dim when off
    if ((mode === 'toggle' || mode === 'select') && !isOn) {
      // Dim the color by reducing opacity
      return baseColor + '40'; // Add 25% opacity
    }

    return baseColor;
  }

  // Get button label
  function getButtonLabel(btn: ButtonConfig | null, index: number): string {
    if (!btn) return `${index + 1}`;
    const label = btn.label || `${index + 1}`;
    // Truncate to 6 chars with ellipsis
    return label.length > 6 ? label.slice(0, 5) + '…' : label;
  }

  // Check if button has validation errors
  function hasButtonErrors(index: number): boolean {
    const errors = getButtonErrors(index);
    return errors.size > 0;
  }

  // Get button mode display
  function getButtonMode(btn: ButtonConfig | null): string {
    if (!btn) return '';
    const mode = btn.mode || 'toggle';
    switch (mode) {
      case 'normal': return 'N';
      case 'toggle': return 'T';
      case 'momentary': return 'M';
      case 'select': return 'S';
      case 'tap': return 'TAP';
      default: return 'T';
    }
  }

  // Get mode badge color
  function getModeBadgeColor(btn: ButtonConfig | null): string {
    if (!btn) return '#6b6b6b';
    const mode = btn.mode || 'toggle';
    switch (mode) {
      case 'normal': return '#6b6b6b'; // neutral gray
      case 'toggle': return '#3b82f6'; // blue
      case 'momentary': return '#10b981'; // green
      case 'select': return '#f59e0b'; // amber
      case 'tap': return '#f97316'; // orange
      default: return '#6b6b6b';
    }
  }

  // Check if button has multiple commands
  function isMultiCommand(btn: ButtonConfig | null): boolean {
    if (!btn) return false;
    const keytimes = btn.keytimes ?? 1;
    if (keytimes > 1) return true;
    return (btn.press?.length ?? 0) > 1 ||
           (btn.release?.length ?? 0) > 0 ||
           (btn.long_press?.length ?? 0) > 0 ||
           (btn.long_release?.length ?? 0) > 0;
  }

  // Get command count for badge
  function getCommandCount(btn: ButtonConfig | null): number {
    if (!btn) return 0;
    return (btn.press?.length ?? 0) +
           (btn.release?.length ?? 0) +
           (btn.long_press?.length ?? 0) +
           (btn.long_release?.length ?? 0);
  }

  // Get tooltip text
  function getTooltip(btn: ButtonConfig | null, index: number): string {
    if (!btn) return `Button ${index + 1} (not configured)`;

    const keytimes = btn.keytimes ?? 1;

    // For multi-state buttons
    if (keytimes > 1 && btn.states) {
      const lines: string[] = [`Button ${index + 1}: ${getButtonLabel(btn, index)}`, `${keytimes} States:`];
      btn.states.forEach((state, i) => {
        const stateLabel = state.label || `State ${i + 1}`;
        const stateColor = state.color || btn.color;
        lines.push(`${stateLabel} (${stateColor})`);
      });
      return lines.join('\n');
    }

    const formatCmd = (c: any) => {
      const t = c.type ?? 'cc';
      const ch = c.channel !== undefined ? ` Ch${c.channel + 1}` : '';
      if (t === 'cc') return `CC${c.cc}=${c.value}${ch}`;
      if (t === 'note') return `Note${c.note} vel${c.velocity}${ch}`;
      if (t === 'pc') return `PC${c.program}${ch}`;
      if (t === 'pc_inc') return `PC+${c.pc_step ?? 1}${ch}`;
      if (t === 'pc_dec') return `PC-${c.pc_step ?? 1}${ch}`;
      return t;
    };

    const lines: string[] = [`Button ${index + 1}: ${getButtonLabel(btn, index)}`];
    if (btn.press?.length) {
      lines.push(`Press: ${btn.press.map(formatCmd).join(', ')}`);
    }
    if (btn.release?.length) {
      lines.push(`Release: ${btn.release.map(formatCmd).join(', ')}`);
    }
    if (btn.long_press?.length) {
      lines.push(`Long: ${btn.long_press.map(formatCmd).join(', ')}`);
    }
    if (btn.long_release?.length) {
      lines.push(`Long Release: ${btn.long_release.map(formatCmd).join(', ')}`);
    }
    return lines.join('\n');
  }

  // Type guard to check if a command is a MIDI command (not conditional)
  function isMidiCommand(cmd: CommandOrConditional | undefined | null): cmd is MidiCommand {
    return cmd !== undefined && cmd !== null && cmd.type !== 'conditional';
  }

  // Get primary press command for MIDI sending
  function getPrimaryPressCommand(btn: ButtonConfig) {
    const keytimes = btn.keytimes ?? 1;
    if (keytimes > 1 && btn.states && btn.states.length > 0) {
      const state = btn.states[0];
      const pressCommands = (Array.isArray(state.press) && state.press.length > 0)
        ? state.press
        : btn.press;
      return Array.isArray(pressCommands) && pressCommands.length > 0 ? pressCommands[0] : null;
    }

    if (btn.cc !== undefined) {
      return { type: 'cc', cc: btn.cc, value: btn.value_on ?? 127, channel: btn.channel } as any;
    }
    if (btn.note !== undefined) {
      return { type: 'note', note: btn.note, velocity: btn.velocity_on ?? 127, channel: btn.channel } as any;
    }

    const firstCmd = Array.isArray(btn.press) && btn.press.length > 0 ? btn.press[0] : null;
    return firstCmd;
  }

  // Handle button click - send MIDI and update selection
  async function handleButtonClick(index: number) {
    $selectedButtonIndex = index;

    const btn = getButton(index);
    if (!btn) return;

    // Determine primary press MIDI command
    const cmd: any = getPrimaryPressCommand(btn);
    if (!cmd) return;

    // Optimistic state update for toggle/select buttons
    const mode = btn.mode ?? 'toggle';
    if (mode === 'toggle' || mode === 'select') {
      const currentStates = get(buttonStates);
      const newState = !currentStates[index];
      currentStates[index] = newState;
      buttonStates.set([...currentStates]);
      console.log(`[DeviceLayout] Button ${index} state changed to:`, newState);
    }

    // Choose MIDI output port
    let port = get(selectedMidiPort);
    if (!port) {
      const ports = await listMidiPorts();
      if (ports.length === 0) {
        showToast('No MIDI output ports available', 'error');
        return;
      }
      port = ports[0];
      selectedMidiPort.set(port);
    }

    const cmdType = cmd.type ?? 'cc';
    const channel = (cmd.channel ?? btn.channel ?? $config.global_channel ?? 0) & 0x0f;
    let bytes: number[] = [];
    if (cmdType === 'cc') {
      const cc = cmd.cc;
      const val = cmd.value ?? cmd.value_on ?? 127;
      bytes = [0xB0 | channel, cc, val];
    } else if (cmdType === 'note') {
      const note = cmd.note;
      const vel = cmd.velocity ?? cmd.velocity_on ?? 127;
      bytes = [0x90 | channel, note, vel];
    } else if (cmdType === 'pc') {
      const program = cmd.program ?? cmd.program_change ?? 0;
      bytes = [0xC0 | channel, program];
    } else {
      // Unsupported command types (conditionals handled by firmware)
      return;
    }

    try {
      await sendMidiMessage(port, bytes);
      console.log('[DeviceLayout] MIDI sent:', bytes, `[${bytes.map(b => '0x' + b.toString(16)).join(', ')}]`);
    } catch (e) {
      console.error('[DeviceLayout] MIDI send failed', e);
      showToast('MIDI send failed', 'error');
    }
  }

  // Check if button is selected
  function isSelected(index: number): boolean {
    return $selectedButtonIndex === index;
  }
</script>

<div class="device-layout-container">
  <svg {viewBox} class="device-svg" style="max-width: {maxWidth}px;">
    {#each Array(totalSlots) as _, index}
      {@const pos = getButtonPosition(index)}
      {@const btn = getButton(index)}
      {@const label = getButtonLabel(btn, index)}
      {@const selected = isSelected(index)}
      {@const multiCmd = isMultiCommand(btn)}
      {@const cmdCount = getCommandCount(btn)}
      {@const tooltip = getTooltip(btn, index)}
      {@const mode = getButtonMode(btn)}
      {@const modeColor = getModeBadgeColor(btn)}
      {@const hasErrors = hasButtonErrors(index)}

      <!-- Compute LED color reactively in template (always full brightness) -->
      {@const ledColor = btn ? (BUTTON_COLORS[btn.color] ?? '#ffffff') : '#555555'}

      <!-- Button Group -->
      <g
        class="button-group"
        class:selected
        role="button"
        tabindex={0}
        aria-label="Button {index + 1}"
        aria-pressed={selected}
        onclick={() => handleButtonClick(index)}
        onkeydown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            handleButtonClick(index);
          }
        }}
      >
        <title>{tooltip}</title>

        <!-- LED Indicator -->
        <circle
          cx={pos.x + BUTTON_SIZE / 2}
          cy={pos.y + LED_OFFSET}
          r={LED_SIZE / 2}
          class="led"
          fill={ledColor}
          style="filter: drop-shadow(0 0 4px {ledColor});"
        />

        <!-- Button Rectangle -->
        <rect
          x={pos.x}
          y={pos.y}
          width={BUTTON_SIZE}
          height={BUTTON_SIZE}
          rx={BUTTON_RADIUS}
          ry={BUTTON_RADIUS}
          class="button-rect"
          class:selected
          class:multi-command={multiCmd}
        />

        <!-- Button Label -->
        <text
          x={pos.x + BUTTON_SIZE / 2}
          y={pos.y + BUTTON_SIZE / 2}
          class="button-label"
          text-anchor="middle"
          dominant-baseline="middle"
        >
          {label}
        </text>

        <!-- Multi-command Badge (top-right) -->
        {#if multiCmd && cmdCount > 0}
          <g class="badge-group">
            <title>{tooltip}</title>
            <rect
              x={pos.x + BUTTON_SIZE - 35}
              y={pos.y + 5}
              width="30"
              height="20"
              rx="4"
              class="badge-bg"
            />
            <text
              x={pos.x + BUTTON_SIZE - 20}
              y={pos.y + 15}
              class="badge-text"
              text-anchor="middle"
              dominant-baseline="middle"
            >
              ×{cmdCount}
            </text>
          </g>
        {/if}

        <!-- Error Indicator (top-left) -->
        {#if hasErrors}
          <g class="error-indicator">
            <circle
              cx={pos.x + 15}
              cy={pos.y + 15}
              r="10"
              fill="#dc2626"
            />
            <text
              x={pos.x + 15}
              y={pos.y + 15}
              class="error-icon"
              text-anchor="middle"
              dominant-baseline="middle"
            >
              !
            </text>
          </g>
        {/if}

        <!-- Mode Badge (bottom-left) -->
        {#if mode}
          <g class="mode-badge-group">
            <rect
              x={pos.x + 5}
              y={pos.y + BUTTON_SIZE - 25}
              width={mode === 'TAP' ? 35 : 24}
              height="20"
              rx="4"
              class="mode-badge-bg"
              fill={modeColor}
            />
            <text
              x={pos.x + (mode === 'TAP' ? 22.5 : 17)}
              y={pos.y + BUTTON_SIZE - 15}
              class="mode-badge-text"
              text-anchor="middle"
              dominant-baseline="middle"
            >
              {mode}
            </text>
          </g>
        {/if}
      </g>
    {/each}
  </svg>
</div>

<style>
  .device-layout-container {
    width: 100%;
    height: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 24px;
    background: transparent;
  }

  .device-svg {
    width: 100%;
    height: auto;
  }

  .button-group {
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .button-group:hover .button-rect {
    fill: #1e1e1e;
    stroke: var(--accent-primary);
  }

  .button-group:focus {
    outline: none;
  }

  .button-group:focus .button-rect {
    stroke: var(--accent-primary);
    stroke-width: 3;
  }

  .button-rect {
    fill: var(--bg-card);
    stroke: var(--border-default);
    stroke-width: 2;
    transition: all 0.2s ease;
  }

  .button-rect.selected {
    fill: var(--bg-input);
    stroke: var(--accent-primary);
    stroke-width: 3;
  }

  .button-label {
    fill: #ffffff;
    font-size: 14px;
    font-weight: 600;
    pointer-events: none;
    user-select: none;
  }

  .led {
    transition: fill 0.2s ease;
  }

  .badge-group {
    pointer-events: none;
  }

  .badge-bg {
    fill: var(--accent-primary);
  }

  .badge-text {
    fill: #ffffff;
    font-size: 11px;
    font-weight: 700;
  }

  .mode-badge-group {
    pointer-events: none;
  }

  .mode-badge-bg {
    opacity: 0.9;
  }

  .mode-badge-text {
    fill: #ffffff;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
  }

  .error-indicator {
    pointer-events: none;
  }

  .error-icon {
    fill: #ffffff;
    font-size: 14px;
    font-weight: 900;
  }

  /* Keyboard accessibility */
  .button-group:focus-visible .button-rect {
    stroke: var(--accent-primary);
    stroke-width: 3;
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
  }
</style>
