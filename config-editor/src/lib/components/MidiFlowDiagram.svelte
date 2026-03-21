<script lang="ts">
  import type { ButtonConfig } from '$lib/types';

  interface Props {
    button: ButtonConfig | null;
    buttonIndex: number;
  }

  let { button, buttonIndex }: Props = $props();

  // Helper to get command count for each event type
  function getCommandCount(commands: any): number {
    if (!commands) return 0;
    return Array.isArray(commands) ? commands.length : 1;
  }

  let hasPress = $derived(button && getCommandCount(button.press) > 0);
  let hasRelease = $derived(button && getCommandCount(button.release) > 0);
  let hasLongPress = $derived(button && getCommandCount(button.long_press) > 0);
  let hasLongRelease = $derived(button && getCommandCount(button.long_release) > 0);

  let pressCount = $derived(button ? getCommandCount(button.press) : 0);
  let releaseCount = $derived(button ? getCommandCount(button.release) : 0);
  let longPressCount = $derived(button ? getCommandCount(button.long_press) : 0);
  let longReleaseCount  = $derived(button ? getCommandCount(button.long_release) : 0);
</script>

{#if button}
  <div class="flow-diagram">
    <div class="flow-header">
      <h4>MIDI Flow</h4>
      <span class="flow-subtitle">Button {buttonIndex + 1}</span>
    </div>

    <svg viewBox="0 0 800 400" class="flow-svg">
      <!-- Input node -->
      <g class="node input-node">
        <rect x="20" y="180" width="120" height="60" rx="8" />
        <text x="80" y="215" text-anchor="middle">Button {buttonIndex + 1}</text>
      </g>

      <!-- Event nodes -->
      {#if hasPress}
        <g class="node event-node">
          <rect x="200" y="50" width="140" height="60" rx="8" />
          <text x="270" y="75" text-anchor="middle" class="event-label">PRESS</text>
          <text x="270" y="95" text-anchor="middle" class="command-count">×{pressCount}</text>
          <line x1="140" y1="200" x2="200" y2="80" stroke="var(--accent-primary)" stroke-width="2" />
        </g>

        <!-- Output node for press -->
        <g class="node output-node">
          <rect x="420" y="50" width="120" height="60" rx="8" />
          <text x="480" y="85" text-anchor="middle">Host</text>
          <line x1="340" y1="80" x2="420" y2="80" stroke="var(--accent-primary)" stroke-width="2" marker-end="url(#arrowhead)" />
        </g>
      {/if}

      {#if hasRelease}
        <g class="node event-node">
          <rect x="200" y="130" width="140" height="60" rx="8" />
          <text x="270" y="155" text-anchor="middle" class="event-label">RELEASE</text>
          <text x="270" y="175" text-anchor="middle" class="command-count">×{releaseCount}</text>
          <line x1="140" y1="205" x2="200" y2="160" stroke="#10b981" stroke-width="2" />
        </g>

        <g class="node output-node">
          <rect x="420" y="130" width="120" height="60" rx="8" />
          <text x="480" y="165" text-anchor="middle">Host</text>
          <line x1="340" y1="160" x2="420" y2="160" stroke="#10b981" stroke-width="2" marker-end="url(#arrowhead-green)" />
        </g>
      {/if}

      {#if hasLongPress}
        <g class="node event-node">
          <rect x="200" y="210" width="140" height="60" rx="8" />
          <text x="270" y="235" text-anchor="middle" class="event-label">LONG PRESS</text>
          <text x="270" y="255" text-anchor="middle" class="command-count">×{longPressCount}</text>
          <line x1="140" y1="210" x2="200" y2="240" stroke="#3b82f6" stroke-width="2" />
        </g>

        <g class="node output-node">
          <rect x="420" y="210" width="120" height="60" rx="8" />
          <text x="480" y="245" text-anchor="middle">Host</text>
          <line x1="340" y1="240" x2="420" y2="240" stroke="#3b82f6" stroke-width="2" marker-end="url(#arrowhead-blue)" />
        </g>
      {/if}

      {#if hasLongRelease}
        <g class="node event-node">
          <rect x="200" y="290" width="140" height="60" rx="8" />
          <text x="270" y="315" text-anchor="middle" class="event-label">LONG RELEASE</text>
          <text x="270" y="335" text-anchor="middle" class="command-count">×{longReleaseCount}</text>
          <line x1="140" y1="215" x2="200" y2="320" stroke="#f59e0b" stroke-width="2" />
        </g>

        <g class="node output-node">
          <rect x="420" y="290" width="120" height="60" rx="8" />
          <text x="480" y="325" text-anchor="middle">Host</text>
          <line x1="340" y1="320" x2="420" y2="320" stroke="#f59e0b" stroke-width="2" marker-end="url(#arrowhead-amber)" />
        </g>
      {/if}

      <!-- Arrow definitions -->
      <defs>
        <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
          <polygon points="0 0, 10 3, 0 6" fill="var(--accent-primary)" />
        </marker>
        <marker id="arrowhead-green" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
          <polygon points="0 0, 10 3, 0 6" fill="#10b981" />
        </marker>
        <marker id="arrowhead-blue" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
          <polygon points="0 0, 10 3, 0 6" fill="#3b82f6" />
        </marker>
        <marker id="arrowhead-amber" markerWidth="10" markerHeight="10" refX="9" refY="3" orient="auto">
          <polygon points="0 0, 10 3, 0 6" fill="#f59e0b" />
        </marker>
      </defs>
    </svg>

    {#if !hasPress && !hasRelease && !hasLongPress && !hasLongRelease}
      <div class="empty-flow">
        <p>No MIDI commands configured</p>
      </div>
    {/if}
  </div>
{:else}
  <div class="flow-diagram empty">
    <p class="empty-message">Select a button to view MIDI flow</p>
  </div>
{/if}

<style>
  .flow-diagram {
    padding: 20px 24px;
    margin: 12px 16px;
    background: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: 10px;
    box-shadow: var(--shadow-sm);
  }

  .flow-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 1rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid #2a2a2a;
  }

  .flow-header h4 {
    margin: 0;
    font-size: var(--text-lg);
    font-weight: 700;
    color: var(--text-primary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .flow-subtitle {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    font-weight: 600;
  }

  .flow-svg {
    width: 100%;
    height: auto;
    max-height: 400px;
  }

  .node rect {
    fill: var(--bg-input);
    stroke: var(--border-default);
    stroke-width: 2;
  }

  .node text {
    fill: var(--text-primary);
    font-size: 14px;
    font-weight: 600;
  }

  .input-node rect {
    fill: var(--bg-dark);
    stroke: var(--accent-primary);
  }

  .event-node rect {
    stroke: var(--accent-primary);
  }

  .event-label {
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .command-count {
    font-size: 16px;
    fill: var(--accent-primary);
    font-weight: 700;
  }

  .output-node rect {
    fill: var(--bg-dark);
    stroke: #10b981;
  }

  .empty-flow {
    text-align: center;
    padding: 2rem;
    color: var(--text-secondary);
  }

  .flow-diagram.empty {
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 200px;
  }

  .empty-message {
    color: var(--text-secondary);
    font-style: italic;
  }
</style>
