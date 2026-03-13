<script lang="ts">
  import { config } from '$lib/formStore';
  import { selectedButtonIndex } from '$lib/stores';
  import { BUTTON_COLORS } from '$lib/types';
  import type { ButtonConfig } from '$lib/types';

  let buttons = $derived($config.buttons);
  let deviceType = $derived($config.device ?? 'std10');
  let totalSlots = $derived(deviceType === 'mini6' ? 6 : 10);
  let cols = $derived(deviceType === 'mini6' ? 3 : 5);

  function typeLabel(btn: ButtonConfig): string {
    const type = btn.type ?? 'cc';
    if (type === 'cc')     return `CC${btn.cc ?? '?'}`;
    if (type === 'note')   return `Note${btn.note ?? '?'}`;
    if (type === 'pc')     return `PC${btn.program ?? '?'}`;
    if (type === 'pc_inc') return 'PC+';
    if (type === 'pc_dec') return 'PC-';
    return type.toUpperCase();
  }

  function colorHex(btn: ButtonConfig): string {
    return BUTTON_COLORS[btn.color] ?? '#ffffff';
  }

  function onValues(btn: ButtonConfig): string {
    const type = btn.type ?? 'cc';
    const ch = (btn.channel ?? $config.global_channel ?? 0) + 1;
    if (type === 'cc')   return `${ch}   ${btn.cc_on ?? 127}`;
    if (type === 'note') return `${ch}   ${btn.velocity_on ?? 127}`;
    return String(ch);
  }

  function offValues(btn: ButtonConfig): string {
    const type = btn.type ?? 'cc';
    if (type === 'cc')   return String(btn.cc_off ?? 0);
    if (type === 'note') return String(btn.velocity_off ?? 0);
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
        onclick={() => selectedButtonIndex.set(i)}
      >
        <div class="btn-led" style="background: {colorHex(btn)}"></div>

        <div class="btn-label">{btn.label}</div>
        <div class="btn-type">{typeLabel(btn)}</div>

        <div class="btn-vals">
          <span>{(btn.channel ?? $config.global_channel ?? 0) + 1}</span>
          <span>{(btn.channel ?? $config.global_channel ?? 0) + 1}</span>
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
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    color: #9ca3af; /* zinc-400 */
    letter-spacing: 0.15em;
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
    gap: 10px;
    padding: 8px 16px 20px;
  }

  .btn-card {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    padding: 12px 10px 8px;
    background: #18182a;
    border: 1px solid #2a2a3e;
    border-radius: 10px;
    cursor: pointer;
    text-align: left;
    min-height: 110px;
    transition: border-color 0.15s, background 0.15s;
    color: #e5e7eb;
    gap: 2px;
  }

  .btn-card:hover {
    border-color: #4b5563;
    background: #1f1f35;
  }

  .btn-card.selected {
    border-color: #6366f1;
    background: #1e1e38;
  }

  .btn-card.empty {
    align-items: center;
    justify-content: center;
    background: #111120;
    border-style: dashed;
    border-color: #2a2a3e;
    cursor: default;
    color: #374151;
  }

  .btn-led {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    flex-shrink: 0;
    box-shadow: 0 0 6px currentColor;
    margin-bottom: 6px;
  }

  .btn-label {
    font-size: 13px;
    font-weight: 700;
    color: #f3f4f6;
    text-transform: uppercase;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
  }

  .btn-type {
    font-size: 11px;
    color: #9ca3af;
    font-family: monospace;
  }

  .btn-vals {
    display: flex;
    gap: 12px;
    font-size: 11px;
    color: #6b7280;
    margin-top: 4px;
  }

  .btn-num {
    position: absolute;
    bottom: 8px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 11px;
    color: #4b5563;
    font-weight: 500;
  }

  .empty-plus {
    font-size: 20px;
    color: #374151;
    margin-bottom: 12px;
  }
</style>
