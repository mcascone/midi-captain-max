<script lang="ts">
  import { config, updateField, syncButtonStates } from '$lib/formStore';
  import { selectedButtonIndex } from '$lib/stores';
  import ColorSelect from './ColorSelect.svelte';
  import ButtonCommandsEditor from './ButtonCommandsEditor.svelte';
  import type { MidiCommand } from '$lib/types';
  import { BUTTON_COLORS } from '$lib/types';

  let btn    = $derived($config.buttons[$selectedButtonIndex] ?? null);
  let buttons = $derived($config.buttons);
  let globalCh = $derived($config.global_channel ?? 0);

  let effectiveChannel = $derived((btn?.channel !== undefined ? btn.channel : globalCh) + 1);
  let displayChannel   = $derived(btn?.channel !== undefined ? btn.channel + 1 : undefined);

  let keytimes = $derived(btn?.keytimes ?? 1);
  let hasMultipleStates = $derived(keytimes > 1);

  let activeStateTab = $state('state-0');

  // Dim brightness reactive value
  let dimBrightness = $state(30);

  // Update local state when button changes
  $effect(() => {
    if (btn) {
      // Clamp to 0-100 range to match firmware behavior and prevent invalid preview colors
      dimBrightness = Math.max(0, Math.min(100, btn.dim_brightness ?? 15));
    }
  });

  // Calculate dimmed color preview
  let dimmedColorPreview = $derived.by(() => {
    if (!btn) return '#000000';
    const colorName = btn.color;
    const rgb = BUTTON_COLORS[colorName] ?? '#ffffff';
    // Parse hex color to RGB
    const r = parseInt(rgb.slice(1, 3), 16);
    const g = parseInt(rgb.slice(3, 5), 16);
    const b = parseInt(rgb.slice(5, 7), 16);
    // Apply dim factor (using Math.floor to match firmware's int() truncation)
    const factor = dimBrightness / 100;
    const dimR = Math.floor(r * factor);
    const dimG = Math.floor(g * factor);
    const dimB = Math.floor(b * factor);
    return `rgb(${dimR}, ${dimG}, ${dimB})`;
  });

  function handleDimBrightnessChange(e: Event) {
    const value = parseInt((e.target as HTMLInputElement).value);
    dimBrightness = value;
    update('dim_brightness', value);
  }

  // Reset to first state tab if keytimes changes to a value that makes current tab invalid
  $effect(() => {
    if (btn) {
      const maxStateIndex = keytimes - 1;
      const currentStateMatch = activeStateTab.match(/^state-(\d+)$/);
      if (currentStateMatch) {
        const stateIndex = parseInt(currentStateMatch[1]);
        if (stateIndex > maxStateIndex) {
          activeStateTab = 'state-0';
        }
      }
    }
  });

  // Ensure states array is initialized when keytimes > 1
  $effect(() => {
    if (btn && keytimes > 1) {
      const currentStates = btn.states ?? [];
      if (currentStates.length !== keytimes) {
        syncButtonStates($selectedButtonIndex, keytimes);
      }
    }
  });

  function update(field: string, value: unknown) {
    updateField(`buttons[${$selectedButtonIndex}].${field}`, value);
  }

  function updateState(stateIndex: number, field: string, value: unknown) {
    // Ensure states array exists and is large enough before updating
    if (!btn || !btn.states || stateIndex < 0 || stateIndex >= btn.states.length) {
      console.warn(`updateState called with invalid state index ${stateIndex} (states length: ${btn?.states?.length ?? 0})`);
      return;
    }
    updateField(`buttons[${$selectedButtonIndex}].states[${stateIndex}].${field}`, value);
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

      <div class="field full">
        <label>Long Press Label <span class="field-hint">(optional)</span></label>
        <input
          type="text"
          value={btn.long_press_label ?? ''}
          maxlength="6"
          placeholder={btn.label}
          onblur={(e) => update('long_press_label', strVal(e) || undefined)}
        />
      </div>

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

      <div class="field-row">
        <div class="field">
          <label>Switch Mode:</label>
          <select value={btn.mode ?? 'toggle'} onchange={(e) => update('mode', strVal(e))}>
            <option value="toggle">Toggle</option>
            <option value="momentary">Momentary</option>
            <option value="select">Select</option>
            <option value="tap">Tap</option>
          </select>
        </div>
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
        {#if btn.mode !== 'momentary' && btn.mode !== 'tap' && (btn.keytimes ?? 1) === 1}
          <div class="field">
            <label>Select Group:</label>
            <input type="text" value={btn.select_group ?? ''} placeholder="group name"
              onblur={(e) => { const v = strVal(e); update('select_group', v === '' ? undefined : v); }} />
          </div>
        {/if}
      </div>

      {#if (btn.off_mode ?? 'dim') === 'dim'}
        <div class="dim-brightness-section">
          <label class="dim-label">Dim Brightness: {dimBrightness}%</label>
          <div class="dim-controls">
            <div class="color-preview">
              <div class="preview-box">
                <div class="preview-color full" style="background-color: {BUTTON_COLORS[btn.color]}"></div>
                <span class="preview-label">Full</span>
              </div>
              <div class="preview-box">
                <div class="preview-color dimmed" style="background-color: {dimmedColorPreview}"></div>
                <span class="preview-label">Dim</span>
              </div>
            </div>
            <input
              type="range"
              class="dim-slider"
              min="0"
              max="100"
              value={dimBrightness}
              oninput={handleDimBrightnessChange}
            />
          </div>
        </div>
      {/if}
    </div>

    <!-- ── Actions Section ───────────────────── -->
    <div class="section">
      <div class="section-header">
        <span class="section-icon">⚡</span>
        <span class="section-title">Actions</span>
      </div>

      {#if hasMultipleStates}
        <!-- State Tabs -->
        <div class="state-tabs">
          <div class="state-tab-buttons">
            {#each Array(keytimes) as _, i}
              <button
                class="state-tab-btn"
                class:active={activeStateTab === `state-${i}`}
                onclick={() => activeStateTab = `state-${i}`}
              >
                State {i + 1}
              </button>
            {/each}
          </div>

          <div class="state-tab-content">
            {#each Array(keytimes) as _, i}
              {#if activeStateTab === `state-${i}`}
                {@const state = btn.states?.[i] ?? {}}

                <div class="state-visual-config">
                  <div class="field-row">
                    <div class="field">
                      <label>Color:</label>
                      <ColorSelect
                        value={state.color ?? btn.color}
                        onchange={(c) => updateState(i, 'color', c)}
                      />
                    </div>
                    <div class="field">
                      <label>Label:</label>
                      <input
                        type="text"
                        value={state.label ?? ''}
                        maxlength="6"
                        placeholder={btn.label}
                        onblur={(e) => { const v = strVal(e); updateState(i, 'label', v === '' ? undefined : v); }}
                      />
                    </div>
                  </div>
                </div>

                <ButtonCommandsEditor
                  eventLabel="Press"
                  commands={state.press ?? []}
                  globalChannel={globalCh}
                  onUpdate={(cmds) => updateState(i, 'press', cmds.length > 0 ? cmds : undefined)}
                />

                <ButtonCommandsEditor
                  eventLabel="Release"
                  commands={state.release ?? []}
                  globalChannel={globalCh}
                  onUpdate={(cmds) => updateState(i, 'release', cmds.length > 0 ? cmds : undefined)}
                />

                <ButtonCommandsEditor
                  eventLabel="Long Press"
                  commands={state.long_press ?? []}
                  globalChannel={globalCh}
                  onUpdate={(cmds) => updateState(i, 'long_press', cmds.length > 0 ? cmds : undefined)}
                />

                <ButtonCommandsEditor
                  eventLabel="Long Release"
                  commands={state.long_release ?? []}
                  globalChannel={globalCh}
                  onUpdate={(cmds) => updateState(i, 'long_release', cmds.length > 0 ? cmds : undefined)}
                />
              {/if}
            {/each}
          </div>
        </div>
      {:else}
        <!-- Single keytime: show button-level commands only -->
        <ButtonCommandsEditor
          eventLabel="Press"
          commands={btn.press ?? []}
          globalChannel={globalCh}
          onUpdate={(cmds) => update('press', cmds.length > 0 ? cmds : undefined)}
        />

        {#if (btn.mode ?? 'toggle') === 'momentary'}
          <ButtonCommandsEditor
            eventLabel="Release"
            commands={btn.release ?? []}
            globalChannel={globalCh}
            onUpdate={(cmds) => update('release', cmds.length > 0 ? cmds : undefined)}
          />
        {/if}

        <ButtonCommandsEditor
          eventLabel="Long Press"
          commands={btn.long_press ?? []}
          globalChannel={globalCh}
          onUpdate={(cmds) => update('long_press', cmds.length > 0 ? cmds : undefined)}
        />

        <ButtonCommandsEditor
          eventLabel="Long Release"
          commands={btn.long_release ?? []}
          globalChannel={globalCh}
          onUpdate={(cmds) => update('long_release', cmds.length > 0 ? cmds : undefined)}
        />
      {/if}
    </div>

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

  .empty-state {
    display: flex;
    align-items: center;
    justify-content: center;
    flex: 1;
    color: #4b5563;
    font-size: 13px;
    padding: 40px;
  }

  /* State tabs */
  .state-tabs {
    margin-top: 8px;
  }

  .state-tab-buttons {
    display: flex;
    gap: 4px;
    margin-bottom: 12px;
    overflow-x: auto;
    padding-bottom: 4px;
  }

  .state-tab-btn {
    padding: 6px 12px;
    background: #1a1a2e;
    border: 1px solid #2a2a3e;
    border-radius: 6px;
    color: #9ca3af;
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
    white-space: nowrap;
    transition: all 0.15s;
  }

  .state-tab-btn:hover {
    border-color: #3a3a55;
    color: #d1d5db;
  }

  .state-tab-btn.active {
    background: #6366f1;
    border-color: #6366f1;
    color: #ffffff;
  }

  .state-tab-content {
    margin-top: 12px;
  }

  .state-visual-config {
    margin-bottom: 16px;
    padding: 12px;
    background: #1a1a2e;
    border: 1px solid #2a2a3e;
    border-radius: 8px;
  }

  .state-info {
    font-size: 11px;
    color: #6b7280;
    margin-bottom: 12px;
    padding: 8px 12px;
    background: #16162a;
    border-left: 2px solid #4b5563;
    border-radius: 4px;
  }

  /* Dim brightness section */
  .dim-brightness-section {
    margin-top: 12px;
    padding: 12px;
    background: #1a1a2e;
    border: 1px solid #2a2a3e;
    border-radius: 8px;
  }

  .dim-label {
    display: block;
    font-size: 11px;
    font-weight: 600;
    color: #9ca3af;
    margin-bottom: 10px;
  }

  .dim-controls {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .color-preview {
    display: flex;
    gap: 12px;
    justify-content: center;
  }

  .preview-box {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
  }

  .preview-color {
    width: 48px;
    height: 48px;
    border-radius: 8px;
    border: 1px solid #3a3a55;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  }

  .preview-label {
    font-size: 10px;
    color: #6b7280;
    font-weight: 500;
  }

  .dim-slider {
    width: 100%;
    height: 6px;
    border-radius: 3px;
    background: linear-gradient(to right, #1a1a2e 0%, #6366f1 100%);
    outline: none;
    -webkit-appearance: none;
    appearance: none;
  }

  .dim-slider::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #6366f1;
    cursor: pointer;
    border: 2px solid #1a1a2e;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    transition: all 0.15s;
  }

  .dim-slider::-webkit-slider-thumb:hover {
    background: #818cf8;
    transform: scale(1.1);
  }

  .dim-slider::-moz-range-thumb {
    width: 18px;
    height: 18px;
    border-radius: 50%;
    background: #6366f1;
    cursor: pointer;
    border: 2px solid #1a1a2e;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    transition: all 0.15s;
  }

  .dim-slider::-moz-range-thumb:hover {
    background: #818cf8;
    transform: scale(1.1);
  }
</style>
