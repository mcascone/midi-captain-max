<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { onMidiEvent, listMidiPorts, startMidiInputListener, stopMidiInputListener } from '$lib/api';
  import { midiPorts, selectedMidiPort } from '$lib/stores';
  import type { UnlistenFn } from '@tauri-apps/api/event';

  // MIDI message type
  interface MidiMessage {
    id: number;
    timestamp: Date;
    direction: 'in' | 'out';
    type: 'CC' | 'Note On' | 'Note Off' | 'PC' | 'SysEx' | 'Other';
    channel?: number;
    data1?: number;
    data2?: number;
    raw: number[];
    port: string;
  }

  // Component state
  let messages: MidiMessage[] = $state([]);
  let messageId = 0;
  let isPaused = $state(false);
  let maxMessages = 1000;
  
  // Filters
  let filterType = $state<string>('all');
  let filterChannel = $state<number | 'all'>('all');
  let filterDirection = $state<string>('all');

  // Auto-scroll
  let autoScroll = $state(true);
  let logContainer: HTMLDivElement;

  // Event listener cleanup
  let unlistenMidi: UnlistenFn | null = null;

  // Parse MIDI message type
  function parseMidiMessage(data: number[]): Omit<MidiMessage, 'id' | 'timestamp' | 'direction' | 'port' | 'raw'> {
    if (data.length === 0) return { type: 'Other' };

    const status = data[0];
    const statusType = status & 0xf0;
    const channel = (status & 0x0f) + 1; // 1-indexed for display

    switch (statusType) {
      case 0xb0: // Control Change
        return {
          type: 'CC',
          channel,
          data1: data[1], // CC number
          data2: data[2]  // Value
        };
      case 0x90: // Note On
        return {
          type: data[2] > 0 ? 'Note On' : 'Note Off',
          channel,
          data1: data[1], // Note number
          data2: data[2]  // Velocity
        };
      case 0x80: // Note Off
        return {
          type: 'Note Off',
          channel,
          data1: data[1], // Note number
          data2: data[2]  // Velocity
        };
      case 0xc0: // Program Change
        return {
          type: 'PC',
          channel,
          data1: data[1]  // Program number
        };
      case 0xf0: // SysEx or system message
        if (status === 0xf0) {
          return { type: 'SysEx' };
        }
        return { type: 'Other' };
      default:
        return { type: 'Other' };
    }
  }

  // Add message to log
  function addMessage(direction: 'in' | 'out', data: number[], port: string) {
    if (isPaused) return;

    const parsed = parseMidiMessage(data);
    const message: MidiMessage = {
      id: messageId++,
      timestamp: new Date(),
      direction,
      raw: data,
      port,
      ...parsed
    };

    messages = [message, ...messages].slice(0, maxMessages);

    // Auto-scroll to top (newest messages)
    if (autoScroll && logContainer) {
      setTimeout(() => {
        logContainer.scrollTop = 0;
      }, 10);
    }
  }

  // Format message for display
  function formatMessage(msg: MidiMessage): string {
    const time = msg.timestamp.toLocaleTimeString('en-US', { 
      hour12: false, 
      hour: '2-digit', 
      minute: '2-digit', 
      second: '2-digit',
      fractionalSecondDigits: 3
    });

    const dir = msg.direction === 'in' ? '←' : '→';
    const ch = msg.channel ? `Ch${msg.channel}` : '';

    switch (msg.type) {
      case 'CC':
        return `${time} ${dir} ${ch} CC${msg.data1} = ${msg.data2}`;
      case 'Note On':
        return `${time} ${dir} ${ch} Note ${msg.data1} ON (vel ${msg.data2})`;
      case 'Note Off':
        return `${time} ${dir} ${ch} Note ${msg.data1} OFF`;
      case 'PC':
        return `${time} ${dir} ${ch} PC ${msg.data1}`;
      case 'SysEx':
        return `${time} ${dir} SysEx [${msg.raw.length} bytes]`;
      default:
        return `${time} ${dir} ${msg.raw.map(b => b.toString(16).padStart(2, '0')).join(' ')}`;
    }
  }

  // Get row CSS class
  function getRowClass(msg: MidiMessage): string {
    const base = 'midi-row';
    const typeClass = `type-${msg.type.toLowerCase().replace(' ', '-')}`;
    const dirClass = `dir-${msg.direction}`;
    return `${base} ${typeClass} ${dirClass}`;
  }

  // Filter messages
  let filteredMessages = $derived(
    messages.filter(msg => {
      if (filterType !== 'all' && msg.type !== filterType) return false;
      if (filterChannel !== 'all' && msg.channel !== filterChannel) return false;
      if (filterDirection !== 'all' && msg.direction !== filterDirection) return false;
      return true;
    })
  );

  // Actions
  function clearLog() {
    messages = [];
    messageId = 0;
  }

  function togglePause() {
    isPaused = !isPaused;
  }

  function exportLog() {
    const text = messages
      .map(msg => formatMessage(msg))
      .reverse()
      .join('\n');
    
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `midi-log-${Date.now()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  }

  // Initialize MIDI monitoring
  onMount(async () => {
    // Load MIDI ports
    try {
      const ports = await listMidiPorts();
      midiPorts.set(ports);
    } catch (e) {
      console.error('[MIDI Monitor] Failed to list ports:', e);
    }

    // Subscribe to MIDI events
    unlistenMidi = await onMidiEvent((evt) => {
      addMessage('in', evt.data, evt.port);
    });

    // Start listening on selected port if available
    const port = $selectedMidiPort;
    if (port) {
      try {
        await startMidiInputListener(port);
      } catch (e) {
        console.error('[MIDI Monitor] Failed to start listener:', e);
      }
    }
  });

  onDestroy(async () => {
    if (unlistenMidi) {
      unlistenMidi();
    }
    try {
      await stopMidiInputListener();
    } catch (e) {
      // Ignore errors on cleanup
    }
  });

  // Handle port change
  async function handlePortChange(e: Event) {
    const select = e.target as HTMLSelectElement;
    const port = select.value;
    
    if (port) {
      selectedMidiPort.set(port);
      try {
        await stopMidiInputListener();
        await startMidiInputListener(port);
      } catch (e) {
        console.error('[MIDI Monitor] Failed to switch port:', e);
      }
    }
  }
</script>

<div class="midi-monitor">
  <!-- Header -->
  <div class="monitor-header">
    <div class="monitor-title">
      <h3>MIDI Monitor</h3>
      <span class="badge">{filteredMessages.length} / {messages.length}</span>
    </div>
    
    <div class="monitor-controls">
      <!-- Port selector -->
      <select class="port-select" onchange={handlePortChange} value={$selectedMidiPort ?? ''}>
        <option value="">Select MIDI Port...</option>
        {#each $midiPorts as port}
          <option value={port}>{port}</option>
        {/each}
      </select>

      <!-- Pause/Resume -->
      <button
        class="control-btn"
        class:active={isPaused}
        onclick={togglePause}
        title={isPaused ? 'Resume' : 'Pause'}
      >
        {isPaused ? 'Resume' : 'Pause'}
      </button>

      <!-- Clear -->
      <button
        class="control-btn"
        onclick={clearLog}
        title="Clear log"
      >
        Clear
      </button>

      <!-- Export -->
      <button
        class="control-btn"
        onclick={exportLog}
        title="Export to file"
        disabled={messages.length === 0}
      >
        Export
      </button>

      <!-- Auto-scroll -->
      <label class="toggle-label">
        <input type="checkbox" bind:checked={autoScroll} />
        Auto-scroll
      </label>
    </div>
  </div>

  <!-- Filters -->
  <div class="monitor-filters">
    <div class="filter-group">
      <label>Type:</label>
      <select bind:value={filterType}>
        <option value="all">All</option>
        <option value="CC">CC</option>
        <option value="Note On">Note On</option>
        <option value="Note Off">Note Off</option>
        <option value="PC">PC</option>
        <option value="SysEx">SysEx</option>
      </select>
    </div>

    <div class="filter-group">
      <label>Channel:</label>
      <select bind:value={filterChannel}>
        <option value="all">All</option>
        {#each Array.from({ length: 16 }, (_, i) => i + 1) as ch}
          <option value={ch}>{ch}</option>
        {/each}
      </select>
    </div>

    <div class="filter-group">
      <label>Direction:</label>
      <select bind:value={filterDirection}>
        <option value="all">All</option>
        <option value="in">IN ←</option>
        <option value="out">OUT →</option>
      </select>
    </div>
  </div>

  <!-- Message log -->
  <div class="monitor-log" bind:this={logContainer}>
    {#if filteredMessages.length === 0}
      <div class="empty-state">
        {#if messages.length === 0}
          <p>No MIDI messages yet.</p>
          <p class="hint">Select a MIDI port above to start monitoring.</p>
        {:else}
          <p>No messages match current filters.</p>
        {/if}
      </div>
    {:else}
      {#each filteredMessages as msg (msg.id)}
        <div class={getRowClass(msg)}>
          {formatMessage(msg)}
        </div>
      {/each}
    {/if}
  </div>
</div>

<style>
  .midi-monitor {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: 8px;
    overflow: hidden;
  }

  .monitor-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: var(--spacing-md);
    border-bottom: 1px solid var(--border-default);
    background: var(--bg-dark);
  }

  .monitor-title {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .monitor-title h3 {
    margin: 0;
    font-size: var(--text-lg);
    font-weight: 600;
    color: var(--text-primary);
  }

  .badge {
    background: var(--accent-primary-dim);
    color: var(--accent-primary);
    padding: 2px 8px;
    border-radius: 12px;
    font-size: var(--text-xs);
    font-weight: 600;
  }

  .monitor-controls {
    display: flex;
    align-items: center;
    gap: var(--spacing-sm);
  }

  .port-select {
    background: var(--bg-input);
    border: 1px solid var(--border-default);
    color: var(--text-primary);
    padding: 6px 12px;
    border-radius: 6px;
    font-size: var(--text-sm);
    min-width: 200px;
  }

  .port-select:focus {
    outline: none;
    border-color: var(--accent-primary);
    box-shadow: var(--glow-cyan-sm);
  }

  .control-btn {
    background: var(--bg-input);
    border: 1px solid var(--border-default);
    color: var(--text-secondary);
    padding: 6px 12px;
    border-radius: 6px;
    font-size: var(--text-base);
    cursor: pointer;
    transition: all 150ms;
  }

  .control-btn:hover:not(:disabled) {
    border-color: var(--accent-primary);
    color: var(--text-primary);
  }

  .control-btn:disabled {
    opacity: 0.4;
    cursor: not-allowed;
  }

  .control-btn.active {
    background: var(--accent-primary-dim);
    border-color: var(--accent-primary);
    color: var(--accent-primary);
  }

  .toggle-label {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: var(--text-sm);
    color: var(--text-secondary);
    cursor: pointer;
  }

  .toggle-label input[type="checkbox"] {
    cursor: pointer;
  }

  .monitor-filters {
    display: flex;
    gap: var(--spacing-md);
    padding: var(--spacing-sm) var(--spacing-md);
    background: var(--bg-dark);
    border-bottom: 1px solid var(--border-default);
  }

  .filter-group {
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .filter-group label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    white-space: nowrap;
  }

  .filter-group select {
    background: var(--bg-input);
    border: 1px solid var(--border-default);
    color: var(--text-primary);
    padding: 4px 8px;
    border-radius: 4px;
    font-size: var(--text-sm);
    min-width: 100px;
  }

  .filter-group select:focus {
    outline: none;
    border-color: var(--accent-primary);
  }

  .monitor-log {
    flex: 1;
    overflow-y: auto;
    padding: var(--spacing-sm);
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 12px;
    line-height: 1.6;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-tertiary);
    text-align: center;
  }

  .empty-state p {
    margin: 4px 0;
  }

  .hint {
    font-size: var(--text-sm);
    color: var(--text-tertiary);
  }

  .midi-row {
    padding: 4px 8px;
    margin-bottom: 2px;
    border-radius: 4px;
    white-space: pre;
    transition: background 150ms;
  }

  .midi-row:hover {
    background: rgba(255, 255, 255, 0.03);
  }

  /* Direction colors */
  .dir-in {
    color: #00d4aa; /* Incoming: cyan */
  }

  .dir-out {
    color: #ff9500; /* Outgoing: orange */
  }

  /* Type-specific styling */
  .type-cc {
    opacity: 1;
  }

  .type-note-on {
    font-weight: 600;
  }

  .type-note-off {
    opacity: 0.7;
  }

  .type-pc {
    color: #a78bfa; /* Purple for PC */
  }

  .type-sysex {
    color: #ef4444; /* Red for SysEx */
    font-style: italic;
  }

  /* Scrollbar styling */
  .monitor-log::-webkit-scrollbar {
    width: 8px;
  }

  .monitor-log::-webkit-scrollbar-track {
    background: var(--bg-dark);
  }

  .monitor-log::-webkit-scrollbar-thumb {
    background: var(--border-default);
    border-radius: 4px;
  }

  .monitor-log::-webkit-scrollbar-thumb:hover {
    background: var(--text-tertiary);
  }
</style>
