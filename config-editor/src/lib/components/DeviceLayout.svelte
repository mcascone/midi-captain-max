<script lang="ts">
  import { config } from '$lib/formStore';
  import { selectedButtonIndex } from '$lib/stores';
  import { BUTTON_COLORS } from '$lib/types';
  import type { ButtonConfig } from '$lib/types';

  let buttons = $derived($config.buttons);
  let deviceType = $derived($config.device ?? 'std10');
  let totalSlots = $derived(deviceType === 'mini6' ? 6 : 10);

  // SVG dimensions based on device type
  let viewBox = $derived(deviceType === 'mini6' ? '0 0 520 400' : '0 0 800 400');
  let cols = $derived(deviceType === 'mini6' ? 3 : 5);
  let rows = 2;

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

  // Get LED color for button
  function getLedColor(btn: ButtonConfig | null): string {
    if (!btn) return '#6b7280'; // Gray for empty
    return BUTTON_COLORS[btn.color] ?? '#ffffff';
  }

  // Get button label
  function getButtonLabel(btn: ButtonConfig | null, index: number): string {
    if (!btn) return `${index + 1}`;
    const label = btn.label || `${index + 1}`;
    // Truncate to 6 chars with ellipsis
    return label.length > 6 ? label.slice(0, 5) + '…' : label;
  }

  // Get button mode display
  function getButtonMode(btn: ButtonConfig | null): string {
    if (!btn) return '';
    const mode = btn.mode || 'toggle';
    switch (mode) {
      case 'toggle': return 'T';
      case 'momentary': return 'M';
      case 'select': return 'S';
      case 'tap': return 'TAP';
      default: return 'T';
    }
  }

  // Get mode badge color
  function getModeBadgeColor(btn: ButtonConfig | null): string {
    if (!btn) return '#6b7280';
    const mode = btn.mode || 'toggle';
    switch (mode) {
      case 'toggle': return '#3b82f6'; // blue
      case 'momentary': return '#10b981'; // green
      case 'select': return '#f59e0b'; // amber
      case 'tap': return '#ec4899'; // pink
      default: return '#6b7280';
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
      if (t === 'cc') return `CC${c.cc}=${c.value}`;
      if (t === 'note') return `Note${c.note} vel${c.velocity}`;
      if (t === 'pc') return `PC${c.program}`;
      if (t === 'pc_inc') return `PC+${c.pc_step ?? 1}`;
      if (t === 'pc_dec') return `PC-${c.pc_step ?? 1}`;
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

  // Handle button click
  function handleButtonClick(index: number) {
    $selectedButtonIndex = index;
  }

  // Check if button is selected
  function isSelected(index: number): boolean {
    return $selectedButtonIndex === index;
  }
</script>

<div class="device-layout-container">
  <svg {viewBox} class="device-svg">
    {#each Array(totalSlots) as _, index}
      {@const pos = getButtonPosition(index)}
      {@const btn = getButton(index)}
      {@const ledColor = getLedColor(btn)}
      {@const label = getButtonLabel(btn, index)}
      {@const selected = isSelected(index)}
      {@const multiCmd = isMultiCommand(btn)}
      {@const cmdCount = getCommandCount(btn)}
      {@const tooltip = getTooltip(btn, index)}
      {@const mode = getButtonMode(btn)}
      {@const modeColor = getModeBadgeColor(btn)}

      <!-- Button Group -->
      <g
        class="button-group"
        class:selected
        role="button"
        tabindex={0}
        aria-label="Button {index + 1}"
        aria-selected={selected}
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
    background: #111827;
  }

  .device-svg {
    width: 100%;
    height: auto;
    max-width: 800px;
  }

  .button-group {
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .button-group:hover .button-rect {
    fill: #374151;
    stroke: #6b7280;
  }

  .button-group:focus {
    outline: none;
  }

  .button-group:focus .button-rect {
    stroke: #8b5cf6;
    stroke-width: 3;
  }

  .button-rect {
    fill: #1f2937;
    stroke: #4b5563;
    stroke-width: 2;
    transition: all 0.2s ease;
  }

  .button-rect.selected {
    fill: #2d1b4e;
    stroke: #8b5cf6;
    stroke-width: 3;
  }

  .button-rect.multi-command {
    fill: linear-gradient(135deg, #1f2937 0%, #2d1b4e 100%);
  }

  .

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
  }button-label {
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
    fill: #8b5cf6;
  }

  .badge-text {
    fill: #ffffff;
    font-size: 11px;
    font-weight: 700;
  }

  /* Keyboard accessibility */
  .button-group:focus-visible .button-rect {
    stroke: #8b5cf6;
    stroke-width: 3;
    outline: 2px solid #8b5cf6;
    outline-offset: 2px;
  }
</style>
