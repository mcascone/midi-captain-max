<script lang="ts">
  import { config, activeBank, isMultiBankMode } from '$lib/formStore';
  import { selectedButtonIndex, buttonStates, selectedMidiPort, midiPorts, showToast } from '$lib/stores';
  import { onMount, onDestroy } from 'svelte';
  import { onMidiEvent, sendMidiMessage, listMidiPorts, startMidiInputListener, stopMidiInputListener } from '$lib/api';
  import { get } from 'svelte/store';
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

  // LED highlight state for incoming MIDI events (use $state for reactivity)
  let lit = $state<boolean[]>([]);
  let states = $state<boolean[]>([]);
  $effect(() => {
    const n = (deviceType === 'mini6' ? 6 : 10);
    if (!lit || lit.length !== n) lit = Array(n).fill(false);
    if (!states || states.length !== n) {
      states = Array(n).fill(false);
      // Initialize the global store as well
      buttonStates.set(states);
    }
  });

  // Subscribe to global button states
  $effect(() => {
    states = $buttonStates;
  });

  // Watch for MIDI port changes and manage listener
  $effect(() => {
    const port = $selectedMidiPort;
    if (port) {
      console.log(`[MIDI] Port selected: ${port}, starting listener...`);
      // Stop any existing listener first
      stopMidiInputListener();
      // Start new listener
      startMidiInputListener(port)
        .then(() => console.log(`[MIDI] ✓ Input listener started on port: ${port}`))
        .catch(e => console.error('[MIDI] ✗ Failed to start input listener:', e));
    } else {
      console.log('[MIDI] No port selected, stopping listener');
      stopMidiInputListener();
    }
  });

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

  let unlistenMidi: (() => void) | null = null;
  onMount(async () => {
    console.log('[MIDI] Subscribing to MIDI events...');
    unlistenMidi = await onMidiEvent((evt) => {
      const data = evt.data;
      if (!data || data.length === 0) return;
      const status = data[0] & 0xf0;
      const channel = data[0] & 0x0f;
      const d1 = data[1];
      const d2 = data[2] ?? 0;

      console.log('[MIDI IN]', `Status: 0x${status.toString(16)}, Ch: ${channel}, D1: ${d1}, D2: ${d2}, Port: ${evt.port}`);

      let matchFound = false;
      buttons.forEach((btn: ButtonConfig, idx: number) => {
        const cmd: any = getPrimaryPressCommand(btn);
        if (!cmd) return;

        const cmdType = cmd.type ?? 'cc';
        const cmdChannel = (cmd.channel ?? btn.channel ?? $config.global_channel ?? 0) & 0x0f;

        let match = false;
        if (cmdType === 'cc' && status === 0xB0 && cmdChannel === channel) {
          // For CC: match on CC number
          const ccMatches = (cmd.cc === d1);

          if (ccMatches) {
            // Check if this button has a specific value configured (for select groups)
            const btnValue = cmd.value ?? cmd.value_on;
            const hasSpecificValue = btnValue !== undefined;

            if (hasSpecificValue) {
              // For select_group buttons: match BOTH CC and value
              match = (btnValue === d2);
              if (match) {
                console.log(`[MIDI MATCH] Button ${idx} (${btn.label}) matched CC${d1}=${d2} (exact value match) on ch${channel}`);
              }
            } else {
              // No specific value configured: match any value on this CC
              match = true;
              console.log(`[MIDI MATCH] Button ${idx} (${btn.label}) matched CC${d1}=${d2} (any value) on ch${channel}`);
            }
          }

          if (match) {
            // Update persistent state based on CC value
            const mode = btn.mode ?? 'toggle';
            const btnValue = cmd.value ?? cmd.value_on;
            const hasSpecificValue = btnValue !== undefined;

            if (mode === 'toggle' || mode === 'select') {
              // For select_group buttons with specific values: matching CC+value means this button is ON
              // For regular toggle buttons: value > 0 = on, value = 0 = off
              const newState = hasSpecificValue ? true : (d2 > 0);
              states[idx] = newState;
              buttonStates.set([...states]);
              console.log(`[DeviceGrid] Updated button ${idx} state to ${newState}, store:`, get(buttonStates));

              // If turning ON, also select this button in the UI
              if (newState) {
                selectedButtonIndex.set(idx);
                console.log(`[DeviceGrid] Selected button ${idx} in UI`);
              }
            } else if (mode === 'momentary') {
              // Momentary: on during press, off on release
              const newState = d2 > 0;
              states[idx] = newState;
              buttonStates.set([...states]);
              console.log(`[DeviceGrid] Updated button ${idx} state to ${newState}, store:`, get(buttonStates));

              // On press, select this button
              if (newState) {
                selectedButtonIndex.set(idx);
                console.log(`[DeviceGrid] Selected button ${idx} in UI`);
              }
            }
          }
        } else if (cmdType === 'note' && (status === 0x90 || status === 0x80) && cmdChannel === channel) {
          match = (cmd.note === d1);
          if (match) {
            // Note on/off tracking
            const noteOn = (status === 0x90 && d2 > 0);
            states[idx] = noteOn;
            buttonStates.set([...states]);

            // Select button when note turns on
            if (noteOn) {
              selectedButtonIndex.set(idx);
              console.log(`[DeviceGrid] Selected button ${idx} in UI (note on)`);
            }
          }
        } else if (cmdType === 'pc' && status === 0xC0 && cmdChannel === channel) {
          match = (cmd.program === d1);
          if (match) {
            // PC buttons don't have persistent state (just flash), but select in UI
            selectedButtonIndex.set(idx);
            console.log(`[DeviceGrid] Selected button ${idx} in UI (PC)`);
          }
        }

        if (match) {
          matchFound = true;
          lit[idx] = true;
          setTimeout(() => { lit[idx] = false; }, 300);
        }
      });

      if (!matchFound) {
        console.log('[MIDI] No button matched this MIDI message');
      }
    });
    console.log('[MIDI] Event subscription active');
  });

  onDestroy(() => {
    if (unlistenMidi) unlistenMidi();
    stopMidiInputListener();
  });

  async function ensureMidiPortList() {
    try {
      const ports = await listMidiPorts();
      console.log(`[MIDI] Found ${ports.length} MIDI ports:`, ports);
      midiPorts.set(ports);
      if (!get(selectedMidiPort) && ports.length > 0) {
        console.log(`[MIDI] Auto-selecting first port: ${ports[0]}`);
        selectedMidiPort.set(ports[0]);
        // Note: The reactive effect will start the listener
      }
    } catch (e) {
      console.error('[MIDI] Failed to list MIDI ports:', e);
    }
  }

  // Call once on mount to populate ports
  onMount(() => { ensureMidiPortList(); });

  async function handleButtonClick(btn: ButtonConfig, idx: number) {
    selectedButtonIndex.set(idx);

    // Determine primary press MIDI command
    const cmd: any = getPrimaryPressCommand(btn);
    if (!cmd) return;

    // Optimistic state update for toggle/select buttons
    const mode = btn.mode ?? 'toggle';
    if (mode === 'toggle' || mode === 'select') {
      // Toggle the state optimistically
      states[idx] = !states[idx];
      buttonStates.set([...states]);
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
      showToast('Unsupported click MIDI command', 'info');
      return;
    }

    try {
      await sendMidiMessage(port, bytes);
      showToast('MIDI sent', 'success', 800);
    } catch (e) {
      console.error('MIDI send failed', e);
      showToast('MIDI send failed', 'error');
    }
  }

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
        class:lit={lit[i]}        class:active={states[i]}        class:multi-command={isMultiCommand(btn)}
        title={isMultiCommand(btn) ? commandTooltip(btn) : ''}
        onclick={() => handleButtonClick(btn, i)}
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

  .btn-led.lit {
    box-shadow: 0 0 22px currentColor, 0 0 40px currentColor, 0 0 60px rgba(255,255,255,0.08);
  }

  .btn-card.lit {
    box-shadow: 0 6px 30px rgba(0, 220, 180, 0.12), inset 0 0 40px rgba(0, 220, 180, 0.03);
    transform: translateY(-2px);
  }

  .btn-card.active {
    background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%);
    border-color: var(--accent-primary);
  }

  .btn-card.active .btn-led {
    box-shadow: 0 0 16px currentColor, 0 0 32px currentColor, 0 0 48px rgba(255,255,255,0.1);
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
