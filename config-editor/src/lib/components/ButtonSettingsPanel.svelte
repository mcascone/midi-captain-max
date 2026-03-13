<script lang="ts">
  import { config, updateField, syncButtonStates } from '$lib/formStore';
  import { selectedButtonIndex } from '$lib/stores';
  import ColorSelect from './ColorSelect.svelte';
  import ButtonCommandsEditor from './ButtonCommandsEditor.svelte';
  import type { MessageType, MidiCommand } from '$lib/types';

  let btn    = $derived($config.buttons[$selectedButtonIndex] ?? null);
  let buttons = $derived($config.buttons);
  let globalCh = $derived($config.global_channel ?? 0);

  let msgType     = $derived((btn?.type ?? 'cc') as MessageType);
  let isCC        = $derived(msgType === 'cc');
  let isNote      = $derived(msgType === 'note');
  let isPC        = $derived(msgType === 'pc');
  let isPCIncDec  = $derived(msgType === 'pc_inc' || msgType === 'pc_dec');
  let showMode    = $derived(isCC || isNote);

  let effectiveChannel = $derived((btn?.channel !== undefined ? btn.channel : globalCh) + 1);
  let displayChannel   = $derived(btn?.channel !== undefined ? btn.channel + 1 : undefined);

  // Multi-command mode state
  let advancedMode = $state(false);
  
  // Detect if button uses new multi-command format
  let hasMultiCommands = $derived(
    btn && (
      (Array.isArray(btn.press) && btn.press.length > 1) ||
      (Array.isArray(btn.release) && btn.release.length > 0) ||
      (Array.isArray(btn.long_press) && btn.long_press.length > 0) ||
      (Array.isArray(btn.long_release) && btn.long_release.length > 0)
    )
  );
  
  // Auto-enable advanced mode if button has multi-commands
  $effect(() => {
    if (hasMultiCommands) {
      advancedMode = true;
    }
  });

  function update(field: string, value: unknown) {
    updateField(`buttons[${$selectedButtonIndex}].${field}`, value);
  }

  function numVal(e: Event): number | undefined {
    const v = (e.target as HTMLInputElement).value;
    return v === '' ? undefined : parseInt(v);
  }

  function strVal(e: Event): string {
    return (e.target as HTMLInputElement | HTMLSelectElement).value;
  }

  function prevButton() {
    if ($selectedButtonIndex > 0) selectedButtonIndex.update(n => n - 1);
  }
  function nextButton() {
    if ($selectedButtonIndex < $config.buttons.length - 1) selectedButtonIndex.update(n => n + 1);
  }
</script>

<div class="settings-panel">
  <!-- Panel header -->
  <div class="panel-header">
    <span class="panel-title">Button Settings</span>
    <button class="dots-btn">•••</button>
  </div>

  {#if btn}
    <!-- Button selector row -->
    <div class="selector-row">
      <select
        class="btn-selector"
        value={$selectedButtonIndex}
        onchange={(e) => selectedButtonIndex.set(parseInt((e.target as HTMLSelectElement).value))}
      >
        {#each buttons as b, i}
          <option value={i}>{b.label}</option>
        {/each}
      </select>
    </div>

    <!-- ── ID Section ─────────────────────────── -->
    <div class="section">
      <div class="section-header">
        <div class="nav-arrows">
          <button class="nav-btn" onclick={prevButton} disabled={$selectedButtonIndex === 0}>‹</button>
          <button class="nav-btn" onclick={nextButton} disabled={$selectedButtonIndex >= buttons.length - 1}>›</button>
        </div>
        <span class="section-icon">↔</span>
        <span class="section-title">ID</span>
      </div>
      <div class="section-sublabel">Label. <em>{btn.label}</em></div>

      <div class="field full">
        <label>Label</label>
        <input
          type="text"
          value={btn.label}
          maxlength="6"
          onblur={(e) => update('label', strVal(e))}
        />
      </div>

      {#if !advancedMode}
        <div class="field-row">
          <div class="field">
            <label>Type:</label>
            <select value={btn.type ?? 'cc'} onchange={(e) => update('type', strVal(e))}>
              <option value="cc">CC</option>
              <option value="note">Note</option>
              <option value="pc">PC Fixed</option>
              <option value="pc_inc">PC+</option>
              <option value="pc_dec">PC-</option>
            </select>
          </div>

          <div class="field narrow">
            <label>Channel:</label>
            <input
              type="number" min="1" max="16"
              value={displayChannel ?? ''}
              placeholder={String(effectiveChannel)}
              onblur={(e) => { const v = numVal(e); update('channel', v !== undefined ? v - 1 : undefined); }}
            />
          </div>

          {#if isCC}
            <div class="field narrow">
              <label>CC:</label>
              <input type="number" min="0" max="127"
                value={btn.cc ?? ''}
                onblur={(e) => update('cc', numVal(e))} />
            </div>
          {:else if isNote}
            <div class="field narrow">
              <label>Note:</label>
              <input type="number" min="0" max="127"
                value={btn.note ?? ''}
                onblur={(e) => update('note', numVal(e))} />
            </div>
          {:else if isPC}
            <div class="field narrow">
              <label>Program:</label>
              <input type="number" min="0" max="127"
                value={btn.program ?? ''}
                onblur={(e) => update('program', numVal(e))} />
            </div>
          {:else if isPCIncDec}
            <div class="field narrow">
              <label>Step:</label>
              <input type="number" min="1" max="127"
                value={btn.pc_step ?? 1}
                onblur={(e) => update('pc_step', numVal(e))} />
            </div>
          {/if}
        </div>

        {#if isCC}
          <div class="field-row">
            <div class="field narrow">
              <label>ON:</label>
              <input type="number" min="0" max="127"
                value={btn.cc_on ?? ''} placeholder="127"
                onblur={(e) => update('cc_on', numVal(e))} />
            </div>
            <div class="field narrow">
              <label>OFF:</label>
              <input type="number" min="0" max="127"
                value={btn.cc_off ?? ''} placeholder="0"
                onblur={(e) => update('cc_off', numVal(e))} />
            </div>
          </div>
        {:else if isNote}
          <div class="field-row">
            <div class="field narrow">
              <label>Vel ON:</label>
              <input type="number" min="0" max="127"
                value={btn.velocity_on ?? ''} placeholder="127"
                onblur={(e) => update('velocity_on', numVal(e))} />
            </div>
            <div class="field narrow">
              <label>Vel OFF:</label>
              <input type="number" min="0" max="127"
                value={btn.velocity_off ?? ''} placeholder="0"
                onblur={(e) => update('velocity_off', numVal(e))} />
            </div>
          </div>
        {/if}
      {/if}

      <div class="field-row">
        <div class="field">
          <label>Color:</label>
          <ColorSelect value={btn.color} onchange={(c) => update('color', c)} />
        </div>
      </div>
    </div>

    <!-- ── Behavior Section ──────────────────── -->
    <div class="section">
      <div class="section-header">
        <span class="section-icon">⚖</span>
        <span class="section-title">Behavior</span>
      </div>

      <!-- Multi-Command Mode Toggle -->
      <div class="mode-toggle-container">
        <label class="mode-toggle-label">
          <input type="checkbox" bind:checked={advancedMode} />
          <div class="toggle-content">
            <span class="toggle-title">Multi-Command Mode</span>
            <span class="toggle-description">
              {#if advancedMode}
                Click "+ Add Command" to send multiple MIDI messages per action
              {:else}
                Enable to send multiple MIDI messages from one button press
              {/if}
            </span>
          </div>
        </label>
        {#if hasMultiCommands}
          <span class="mode-badge">ACTIVE</span>
        {/if}
      </div>

      <div class="field-row">{#if showMode}
          <div class="field">
            <label>Switch Mode:</label>
            <select value={btn.mode ?? 'toggle'} onchange={(e) => update('mode', strVal(e))}>
              <option value="toggle">Toggle</option>
              <option value="momentary">Momentary</option>
              <option value="select">Select</option>
              <option value="tap">Tap</option>
            </select>
          </div>
        {/if}
        <div class="field narrow">
          <label>Keytimes:</label>
          <input type="number" min="1" max="99"
            value={btn.keytimes ?? 1}
            onblur={(e) => { const v = numVal(e); if (v) syncButtonStates($selectedButtonIndex, v); }} />
        </div>
      </div>

      <div class="field-row">
        <div class="field">
          <label>LED Off:</label>
          <select value={btn.off_mode ?? 'dim'} onchange={(e) => update('off_mode', strVal(e))}>
            <option value="dim">Dim</option>
            <option value="off">Off</option>
          </select>
        </div>
        {#if (btn.mode ?? 'toggle') !== 'tap'}
          <div class="field">
            <label>Select Group:</label>
            <input type="text" value={btn.select_group ?? ''} placeholder="group name"
              onblur={(e) => { const v = strVal(e); update('select_group', v === '' ? undefined : v); }} />
          </div>
        {/if}
      </div>
    </div>

    <!-- ── Actions Section ───────────────────── -->
    {#if advancedMode}
      <div class="section">
        <div class="section-header">
          <span class="section-icon">⚡</span>
          <span class="section-title">Actions</span>
        </div>

        <!-- Press Event -->
        <ButtonCommandsEditor
          eventLabel="Press"
          commands={btn.press ?? []}
          globalChannel={globalCh}
          onUpdate={(cmds) => update('press', cmds.length > 0 ? cmds : undefined)}
        />

        <!-- Release Event (only for momentary) -->
        {#if (btn.mode ?? 'toggle') === 'momentary'}
          <ButtonCommandsEditor
            eventLabel="Release"
            commands={btn.release ?? []}
            globalChannel={globalCh}
            onUpdate={(cmds) => update('release', cmds.length > 0 ? cmds : undefined)}
          />
        {/if}

        <!-- Long Press Event -->
        <ButtonCommandsEditor
          eventLabel="Long Press"
          commands={btn.long_press ?? []}
          globalChannel={globalCh}
          onUpdate={(cmds) => update('long_press', cmds.length > 0 ? cmds : undefined)}
        />

        <!-- Long Release Event -->
        <ButtonCommandsEditor
          eventLabel="Long Release"
          commands={btn.long_release ?? []}
          globalChannel={globalCh}
          onUpdate={(cmds) => update('long_release', cmds.length > 0 ? cmds : undefined)}
        />
      </div>
    {:else}
      <!-- ── LED Section (Simple Mode) ─────────── -->
      <div class="section">
        <div class="section-header">
          <span class="section-icon">⟳</span>
          <span class="section-title">LED</span>
        </div>

        <label class="checkbox-label">
          <input type="checkbox" checked={!!btn.long_press}
            onchange={(e) => {
              if ((e.target as HTMLInputElement).checked) {
                update('long_press', { type: 'cc', cc: btn.cc ?? 20, value: 127, channel: btn.channel ?? globalCh, threshold_ms: 600 });
              } else {
                update('long_press', undefined);
              }
            }}
          />
          Enable long press
        </label>

        {#if btn.long_press}
          <div class="field-row">
            <div class="field">
              <label>Type:</label>
              <select value={btn.long_press.type ?? 'cc'}
                onchange={(e) => update('long_press.type', strVal(e))}>
                <option value="cc">CC</option>
                <option value="note">Note</option>
                <option value="pc">PC</option>
              </select>
            </div>

            {#if btn.long_press.type === 'cc' || !btn.long_press.type}
              <div class="field narrow">
                <label>CC:</label>
                <input type="number" min="0" max="127"
                  value={btn.long_press.cc ?? ''}
                  onblur={(e) => update('long_press.cc', numVal(e))} />
              </div>
              <div class="field narrow">
                <label>Value:</label>
                <input type="number" min="0" max="127"
                  value={btn.long_press.value ?? ''}
                  onblur={(e) => update('long_press.value', numVal(e))} />
              </div>
            {:else if btn.long_press.type === 'note'}
              <div class="field narrow">
                <label>Note:</label>
                <input type="number" min="0" max="127"
                  value={btn.long_press.note ?? ''}
                  onblur={(e) => update('long_press.note', numVal(e))} />
              </div>
              <div class="field narrow">
                <label>Vel:</label>
                <input type="number" min="0" max="127"
                  value={btn.long_press.value ?? ''}
                  onblur={(e) => update('long_press.value', numVal(e))} />
              </div>
            {:else}
              <div class="field narrow">
                <label>Program:</label>
                <input type="number" min="0" max="127"
                  value={btn.long_press.program ?? ''}
                  onblur={(e) => update('long_press.program', numVal(e))} />
              </div>
            {/if}
          </div>
        {/if}
      </div>
    {/if}

  {:else}
    <div class="empty-state">Select a button to edit settings</div>
  {/if}
</div>

<style>
  .settings-panel {
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
  }

  .panel-title {
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    color: #9ca3af;
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

  /* Button selector */
  .selector-row {
    padding: 4px 16px 12px;
  }

  .btn-selector {
    width: 100%;
    padding: 8px 12px;
    background: #1f1f35;
    border: 1px solid #3a3a55;
    border-radius: 8px;
    color: #f3f4f6;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    appearance: auto;
  }

  /* Sections */
  .section {
    padding: 14px 16px;
    border-top: 1px solid #1e1e2e;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }

  .nav-arrows {
    display: flex;
    gap: 2px;
    margin-right: 4px;
  }

  .nav-btn {
    background: #1f1f35;
    border: 1px solid #3a3a55;
    border-radius: 4px;
    color: #9ca3af;
    font-size: 16px;
    width: 26px;
    height: 26px;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    line-height: 1;
  }
  .nav-btn:hover:not(:disabled) { color: #f3f4f6; }
  .nav-btn:disabled { opacity: 0.3; cursor: not-allowed; }

  .section-icon {
    font-size: 14px;
    color: #9ca3af;
  }

  .section-title {
    font-size: 12px;
    font-weight: 700;
    color: #e5e7eb;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    flex: 1;
  }

  .section-sublabel {
    font-size: 11px;
    color: #6b7280;
    margin-bottom: 14px;
    margin-top: -6px;
  }
  .section-sublabel em { color: #9ca3af; font-style: normal; }

  /* Form fields */
  .field {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .field.full { margin-bottom: 10px; }
  .field.narrow { flex: 0 0 auto; min-width: 64px; }

  .field-row {
    display: flex;
    gap: 10px;
    align-items: flex-end;
    margin-bottom: 10px;
    flex-wrap: wrap;
  }

  label {
    font-size: 11px;
    color: #9ca3af;
    white-space: nowrap;
  }

  input[type="text"],
  input[type="number"],
  select {
    padding: 7px 10px;
    background: #1a1a2e;
    border: 1px solid #2a2a3e;
    border-radius: 6px;
    color: #e5e7eb;
    font-size: 13px;
    width: 100%;
    min-width: 0;
    height: 36px;
    line-height: 1.4;
    transition: border-color 0.15s;
  }

  input:focus, select:focus {
    outline: none;
    border-color: #6366f1;
  }

  input[type="number"] { width: 72px; }

  .field.narrow input[type="number"],
  .field.narrow select { width: 72px; }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #d1d5db;
    cursor: pointer;
    margin-bottom: 10px;
  }

  input[type="checkbox"] {
    width: 15px;
    height: 15px;
    margin: 0;
    accent-color: #6366f1;
    cursor: pointer;
  }

  .mode-toggle-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px;
    background: #1f1f35;
    border: 1px solid #3a3a55;
    border-radius: 8px;
    margin-bottom: 14px;
    transition: all 0.2s;
  }

  .mode-toggle-container:hover {
    border-color: #4a4a65;
    background: #252540;
  }

  .mode-toggle-label {
    display: flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    flex: 1;
    margin: 0;
    min-width: 0; /* Allow shrinking */
  }

  .toggle-content {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
    min-width: 0; /* Allow shrinking */
  }

  .toggle-title {
    font-size: 13px;
    font-weight: 600;
    color: #e5e7eb;
  }

  .toggle-description {
    font-size: 11px;
    color: #9ca3af;
    line-height: 1.4;
    word-wrap: break-word;
    overflow-wrap: break-word;
    white-space: normal;
    max-width: 100%;
  }

  .mode-badge {
    font-size: 10px;
    font-weight: 700;
    color: #6366f1;
    background: rgba(99, 102, 241, 0.1);
    border: 1px solid #6366f1;
    padding: 3px 8px;
    border-radius: 4px;
    letter-spacing: 0.05em;
  }

  .mode-hint {
    font-size: 11px;
    color: #6b7280;
    font-style: italic;
    margin-left: auto;
  }

  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    color: #4b5563;
    font-size: 13px;
    padding: 40px;
  }
</style>
