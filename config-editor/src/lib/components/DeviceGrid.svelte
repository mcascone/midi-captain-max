<script lang="ts">
  import { config, activeBank, isMultiBankMode } from '$lib/formStore';
  import { selectedButtonIndex } from '$lib/stores';
  import { BUTTON_COLORS } from '$lib/types';
  import type { ButtonConfig, CommandOrConditional, MidiCommand } from '$lib/types';

  // Type guard to check if a command is a MIDI command (not conditional)
  function isMidiCommand(cmd: CommandOrConditional | undefined | null): cmd is MidiCommand {
    return cmd !== undefined && cmd !== null && cmd.type !== 'conditional';
  }

  // Get buttons from active bank if multi-bank mode, otherwise from top-level
  let buttons = $derived(
    $isMultiBankMode && $activeBank
      ? $activeBank.buttons
      : $config.buttons ?? []
  );

  let deviceType = $derived($config.device ?? 'std10');
  let totalSlots = $derived(deviceType === 'mini6' ? 6 : 10);
  let cols = $derived(deviceType === 'mini6' ? 3 : 5);

  function typeLabel(btn: ButtonConfig): string {
    const keytimes = btn.keytimes ?? 1;

    // For multi-state buttons, check first state's press commands, fall back to button-level
    if (keytimes > 1 && btn.states && btn.states.length > 0) {
      const state = btn.states[0];
      // Check state override first, then fall back to button-level (matches firmware behavior)
      const pressCommands = (Array.isArray(state.press) && state.press.length > 0)
        ? state.press
        : btn.press;

      const firstCmd = Array.isArray(pressCommands) && pressCommands.length > 0 ? pressCommands[0] : null;
      if (!isMidiCommand(firstCmd)) return '—';

      const type = firstCmd.type ?? 'cc';
      const cmdCount = pressCommands?.length ?? 0;
      const countBadge = cmdCount > 1 ? ` ×${cmdCount}` : '';
      const stateBadge = ` [${keytimes}]`;

      if (type === 'cc')     return `CC${firstCmd.cc ?? '?'}${countBadge}${stateBadge}`;
      if (type === 'note')   return `Note${firstCmd.note ?? '?'}${countBadge}${stateBadge}`;
      if (type === 'pc')     return `PC${firstCmd.program ?? '?'}${countBadge}${stateBadge}`;
      if (type === 'pc_inc') return `PC+${countBadge}${stateBadge}`;
      if (type === 'pc_dec') return `PC-${countBadge}${stateBadge}`;
      return (type as string).toUpperCase() + countBadge + stateBadge;
    }

    // Check for simplified toggle format (direct cc/note fields)
    if (btn.cc !== undefined) {
      return `CC${btn.cc}`;
    }
    if (btn.note !== undefined) {
      return `Note${btn.note}`;
    }

    // Extract info from first press command (multi-command mode)
    const firstCmd = Array.isArray(btn.press) && btn.press.length > 0 ? btn.press[0] : null;
    if (!isMidiCommand(firstCmd)) return '—';

    const type = firstCmd.type ?? 'cc';
    const cmdCount = btn.press?.length ?? 0;
    const countBadge = cmdCount > 1 ? ` ×${cmdCount}` : '';

    if (type === 'cc')     return `CC${firstCmd.cc ?? '?'}${countBadge}`;
    if (type === 'note')   return `Note${firstCmd.note ?? '?'}${countBadge}`;
    if (type === 'pc')     return `PC${firstCmd.program ?? '?'}${countBadge}`;
    if (type === 'pc_inc') return `PC+${countBadge}`;
    if (type === 'pc_dec') return `PC-${countBadge}`;
    return (type as string).toUpperCase() + countBadge;
  }

  function colorHex(btn: ButtonConfig): string {
    return BUTTON_COLORS[btn.color] ?? '#ffffff';
  }

  function isMultiCommand(btn: ButtonConfig): boolean {
    const keytimes = btn.keytimes ?? 1;

    // If keytimes > 1, always show multi-command indicator
    if (keytimes > 1) return true;

    return (btn.press?.length ?? 0) > 1 ||
           (btn.release?.length ?? 0) > 0 ||
           (btn.long_press?.length ?? 0) > 0 ||
           (btn.long_release?.length ?? 0) > 0;
  }

  function commandTooltip(btn: ButtonConfig): string {
    const keytimes = btn.keytimes ?? 1;

    // For multi-state buttons, show state info
    if (keytimes > 1 && btn.states) {
      const lines: string[] = [`${keytimes} States:`];
      btn.states.forEach((state, i) => {
        const stateLabel = state.label || `State ${i + 1}`;
        const stateColor = state.color || btn.color;
        lines.push(`\n${stateLabel} (${stateColor}):`);

        const formatCmd = (c: any) => {
          const t = c.type ?? 'cc';
          if (t === 'cc') return `CC${c.cc}=${c.value}`;
          if (t === 'note') return `Note${c.note} vel${c.velocity}`;
          if (t === 'pc') return `PC${c.program}`;
          if (t === 'pc_inc') return `PC+${c.pc_step ?? 1}`;
          if (t === 'pc_dec') return `PC-${c.pc_step ?? 1}`;
          return t;
        };

        if (state.press?.length) lines.push(`  Press: ${state.press.map(formatCmd).join(', ')}`);
        if (state.release?.length) lines.push(`  Release: ${state.release.map(formatCmd).join(', ')}`);
        if (state.long_press?.length) lines.push(`  Long: ${state.long_press.map(formatCmd).join(', ')}`);
        if (state.long_release?.length) lines.push(`  Long Rel: ${state.long_release.map(formatCmd).join(', ')}`);
      });
      return lines.join('\n');
    }

    // Check for simplified toggle format
    if (btn.cc !== undefined && btn.value_on !== undefined) {
      return `Toggle: CC${btn.cc}\nOn: ${btn.value_on}\nOff: ${btn.value_off ?? 0}`;
    }
    if (btn.note !== undefined && btn.velocity_on !== undefined) {
      return `Toggle: Note${btn.note}\nOn vel: ${btn.velocity_on}\nOff vel: ${btn.velocity_off ?? 0}`;
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

    const lines: string[] = [];
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

  function onValues(btn: ButtonConfig): string {
    const keytimes = btn.keytimes ?? 1;

    // For multi-state buttons, check first state's press commands, fall back to button-level
    if (keytimes > 1 && btn.states && btn.states.length > 0) {
      const state = btn.states[0];
      // Check state override first, then fall back to button-level (matches firmware behavior)
      const pressCommands = (Array.isArray(state.press) && state.press.length > 0)
        ? state.press
        : btn.press;

      const firstCmd = Array.isArray(pressCommands) && pressCommands.length > 0 ? pressCommands[0] : null;
      if (!isMidiCommand(firstCmd)) return '—';

      const type = firstCmd.type ?? 'cc';
      const ch = (firstCmd.channel ?? btn.channel ?? $config.global_channel ?? 0) + 1;
      if (type === 'cc')   return `Ch:${ch}  On:${firstCmd.value ?? 127}`;
      if (type === 'note') return `Ch:${ch}  Vel:${firstCmd.velocity ?? 127}`;
      return `Ch:${ch}`;
    }

    // Check for simplified toggle format (direct value_on field)
    if (btn.value_on !== undefined) {
      const ch = (btn.channel ?? $config.global_channel ?? 0) + 1;
      return `Ch:${ch}  On:${btn.value_on}`;
    }
    if (btn.velocity_on !== undefined) {
      const ch = (btn.channel ?? $config.global_channel ?? 0) + 1;
      return `Ch:${ch}  Vel:${btn.velocity_on}`;
    }

    const firstCmd = Array.isArray(btn.press) && btn.press.length > 0 ? btn.press[0] : null;
    if (!isMidiCommand(firstCmd)) return '—';

    const type = firstCmd.type ?? 'cc';
    const ch = (firstCmd.channel ?? btn.channel ?? $config.global_channel ?? 0) + 1;
    if (type === 'cc')   return `Ch:${ch}  On:${firstCmd.value ?? 127}`;
    if (type === 'note') return `Ch:${ch}  Vel:${firstCmd.velocity ?? 127}`;
    return `Ch:${ch}`;
  }

  function offValues(btn: ButtonConfig): string {
    const keytimes = btn.keytimes ?? 1;
    const mode = btn.mode ?? 'toggle';

    // For multi-state buttons, check first state's release commands, fall back to button-level
    if (keytimes > 1 && btn.states && btn.states.length > 0) {
      const state = btn.states[0];
      // Check state override for release first, then fall back to button-level
      const releaseCommands = (Array.isArray(state.release) && state.release.length > 0)
        ? state.release
        : btn.release;

      const releaseCmd = Array.isArray(releaseCommands) && releaseCommands.length > 0 ? releaseCommands[0] : null;
      if (isMidiCommand(releaseCmd)) {
        const t = releaseCmd.type ?? 'cc';
        if (t === 'cc')   return `Off:${releaseCmd.value ?? 0}`;
        if (t === 'note') return `Vel:${releaseCmd.velocity ?? 0}`;
        return '—';  // PC types don't have an off value
      }

      // Multi-state buttons without explicit release don't show off value
      return '';
    }

    // Check for simplified toggle format (direct value_off field)
    if (btn.value_off !== undefined) {
      return `Off:${btn.value_off}`;
    }
    if (btn.velocity_off !== undefined) {
      return `Vel:${btn.velocity_off}`;
    }

    // Check release command first (for momentary mode or explicit release)
    const releaseCmd = Array.isArray(btn.release) && btn.release.length > 0 ? btn.release[0] : null;
    if (isMidiCommand(releaseCmd)) {
      const t = releaseCmd.type ?? 'cc';
      if (t === 'cc')   return `Off:${releaseCmd.value ?? 0}`;
      if (t === 'note') return `Vel:${releaseCmd.velocity ?? 0}`;
      return '—';  // PC types don't have an off value
    }

    // For select buttons without explicit release command, don't show off value
    if (mode === 'select') {
      return '';
    }

    // For toggle/momentary without explicit release, infer from press command
    if (mode === 'toggle' || mode === 'momentary') {
      const pressCmd = Array.isArray(btn.press) && btn.press.length > 0 ? btn.press[0] : null;
      if (!isMidiCommand(pressCmd)) return '';

      const type = pressCmd.type ?? 'cc';
      if (type === 'cc')   return 'Off:0';  // Default CC off value
      if (type === 'note') return 'Vel:0';  // Default note off velocity
    }

    return '';  // PC, tap, and other modes have no off value
  }
  function combinedValues(btn: ButtonConfig): string {
    const mode = btn.mode ?? 'toggle';
    const on = onValues(btn);
    const off = offValues(btn);

    // For toggle/momentary buttons, combine on/off into one display
    if ((mode === 'toggle' || mode === 'momentary') && on && off) {
      return `${on} ${off}`;
    }

    // For other modes, show separately or just on value
    return '';
  }
</script>

<div class="device-panel">
  <div class="panel-header">
    <span class="panel-title">MIDI CAPTAIN</span>
    <button class="dots-btn" title="Options">•••</button>
  </div>

  <div class="buttons-grid" style="--cols: {cols}">
    {#each buttons as btn, i}
      <button
        class="btn-card"
        class:selected={$selectedButtonIndex === i}
        class:multi-command={isMultiCommand(btn)}
        title={isMultiCommand(btn) ? commandTooltip(btn) : ''}
        onclick={() => selectedButtonIndex.set(i)}
      >
        <div class="btn-led" style="background: {colorHex(btn)}"></div>

        {#if isMultiCommand(btn)}
          <div class="multi-badge">×{(btn.press?.length ?? 0) || (btn.keytimes ?? 1)}</div>
        {/if}

        <div class="btn-label">{btn.label}</div>
        <div class="btn-type">{typeLabel(btn)}</div>

        <div class="btn-vals">
          {#if combinedValues(btn)}
            <span class="val-pill">{combinedValues(btn)}</span>
          {:else}
            {#if onValues(btn)}
              <span class="val-pill">{onValues(btn)}</span>
            {/if}
            {#if offValues(btn)}
              <span class="val-pill">{offValues(btn)}</span>
            {/if}
          {/if}
        </div>

        <div class="mode-badge" class:mode-toggle={btn.mode === 'toggle' || !btn.mode} class:mode-momentary={btn.mode === 'momentary'} class:mode-select={btn.mode === 'select'} class:mode-tap={btn.mode === 'tap'}>
          {#if btn.mode === 'momentary'}
            M
          {:else if btn.mode === 'select'}
            S
          {:else if btn.mode === 'tap'}
            TAP
          {:else}
            N
          {/if}
        </div>

        <div class="btn-num">{i + 1}</div>
      </button>
    {/each}

    <!-- Empty slots -->
    {#each Array(Math.max(0, totalSlots - buttons.length)) as _, i}
      <div class="btn-card empty">
        <div class="empty-plus">+</div>
        <div class="btn-num">{buttons.length + i + 1}</div>
      </div>
    {/each}
  </div>
</div>

<style>
  .device-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow-y: auto;
  }

  .panel-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px 10px;
    letter-spacing: 0.08em;
  }

  .panel-title {
    font-size: var(--text-sm);
    font-weight: 700;
    text-transform: uppercase;
    color: var(--text-secondary);
    letter-spacing: 0.1em;
  }

  .dots-btn {
    background: none;
    border: none;
    color: #6b7280;
    font-size: 16px;
    cursor: pointer;
    padding: 2px 6px;
    border-radius: 4px;
  }
  .dots-btn:hover { color: #d1d5db; }

  .buttons-grid {
    display: grid;
    grid-template-columns: repeat(var(--cols, 5), 1fr);
    gap: 20px;
    padding: 20px 28px 28px;
  }

  .btn-card {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    padding: 18px 16px 14px;
    background: #181818;
    border: 2px solid var(--border-default);
    border-radius: 14px;
    cursor: pointer;
    text-align: left;
    height: 175px;
    transition: all 0.2s ease;
    color: #e5e7eb;
    gap: 8px;
    box-shadow: var(--shadow-md);
  }

  .btn-card:hover {
    border-color: var(--accent-primary);
    background: var(--bg-input);
    box-shadow: var(--shadow-lg), var(--glow-cyan-sm);
    transform: translateY(-3px);
  }

  .btn-card.selected {
    border-color: var(--accent-primary);
    border-width: 3px;
    background: #1e1e1e;
    box-shadow: var(--shadow-lg), var(--glow-cyan), inset 0 0 20px rgba(0, 212, 170, 0.1);
    padding: 17px 15px 13px;
  }

  .btn-card.multi-command {
    border-color: #d97706;
    background: linear-gradient(135deg, var(--bg-card) 0%, #1c1c1c 100%);
    box-shadow: inset 0 0 0 1px rgba(217, 119, 6, 0.2), var(--shadow-md);
  }

  .btn-card.multi-command:hover {
    border-color: #f59e0b;
    background: linear-gradient(135deg, #1e1e1e 0%, #252525 100%);
    box-shadow: inset 0 0 0 1px rgba(245, 158, 11, 0.3), var(--shadow-lg), 0 0 16px rgba(245, 158, 11, 0.2);
  }

  .btn-card.multi-command.selected {
    border-color: var(--accent-primary);
    border-width: 3px;
    box-shadow: inset 0 0 0 1px rgba(0, 212, 170, 0.4), var(--shadow-lg), var(--glow-cyan);
  }

  .btn-card.empty {
    align-items: center;
    justify-content: center;
    background: #111111;
    border-style: dashed;
    border-color: var(--border-default);
    cursor: default;
    color: #333333;
  }

  .btn-led {
    width: 14px;
    height: 14px;
    border-radius: 50%;
    flex-shrink: 0;
    box-shadow: 0 0 10px currentColor, 0 0 20px currentColor;
    margin-bottom: 4px;
  }

  .btn-label {
    font-size: var(--text-lg);
    font-weight: 800;
    color: var(--text-primary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
  }

  .btn-type {
    font-size: var(--text-xs);
    color: var(--text-secondary);
    font-family: var(--font-family);
    font-weight: 500;
  }

  .btn-vals {
    display: flex;
    gap: 6px;
    font-size: 10px;
    margin-top: auto;
    margin-bottom: 32px;
    flex-wrap: wrap;
    width: 100%;
  }

  .val-pill {
    background: rgba(0, 0, 0, 0.35);
    color: #9ca3af;
    padding: 3px 7px;
    border-radius: 10px;
    font-family: monospace;
    font-weight: 500;
    border: 1px solid rgba(255, 255, 255, 0.05);
    white-space: nowrap;
  }

  .btn-num {
    position: absolute;
    bottom: 10px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 11px;
    color: var(--text-secondary);
    font-weight: 600;
    background: rgba(0, 0, 0, 0.5);
    padding: 3px 10px;
    border-radius: 12px;
    border: 1px solid rgba(255, 255, 255, 0.08);
  }

  .multi-badge {
    position: absolute;
    top: 12px;
    right: 12px;
    background: var(--accent-primary);
    color: var(--bg-dark);
    font-size: 11px;
    font-weight: 800;
    padding: 4px 8px;
    border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0, 212, 170, 0.4);
  }

  .mode-badge {
    position: absolute;
    bottom: 36px;
    left: 14px;
    font-size: 10px;
    font-weight: 700;
    padding: 4px 8px;
    border-radius: 6px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .mode-toggle {
    background: rgba(59, 130, 246, 0.2);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.4);
  }

  .mode-momentary {
    background: rgba(16, 185, 129, 0.2);
    color: #34d399;
    border: 1px solid rgba(16, 185, 129, 0.4);
  }

  .mode-select {
    background: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
    border: 1px solid rgba(245, 158, 11, 0.4);
  }

  .mode-tap {
    background: rgba(249, 115, 22, 0.2);
    color: #fb923c;
    border: 1px solid rgba(249, 115, 22, 0.4);
  }

  .empty-plus {
    font-size: 20px;
    color: #333333;
    margin-bottom: 12px;
  }
</style>
