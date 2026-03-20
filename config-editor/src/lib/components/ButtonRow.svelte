<script lang="ts">
  import ColorSelect from './ColorSelect.svelte';
  import ButtonCommandsEditor from './ButtonCommandsEditor.svelte';
  import type { ButtonConfig, ButtonColor, ButtonMode, OffMode, MessageType, MidiCommand, CommandOrConditional } from '$lib/types';
  import { validationErrors, syncButtonStates } from '$lib/formStore';

  interface Props {
    button: ButtonConfig;
    index: number;
    disabled?: boolean;
    globalChannel?: number;
    onUpdate: (field: string, value: any) => void;
  }

  let { button, index, disabled = false, globalChannel = 0, onUpdate }: Props = $props();

  // Type guard to check if a command is a MIDI command (not conditional)
  function isMidiCommand(cmd: CommandOrConditional | undefined): cmd is MidiCommand {
    return cmd !== undefined && cmd.type !== 'conditional';
  }

  // Get first MIDI command from long_press/long_release arrays (filter out conditionals)
  let longPressCmd = $derived.by(() => {
    const first = button.long_press?.[0];
    return isMidiCommand(first) ? first : undefined;
  });

  let longReleaseCmd = $derived.by(() => {
    const first = button.long_release?.[0];
    return isMidiCommand(first) ? first : undefined;
  });

  const basePath = `buttons[${index}]`;

  // Track which state details are open (persists across re-renders)
  // Using a reactive object for proper bind:open two-way binding
  let stateOpen: Record<number, boolean> = $state({ 0: true });

  // Update stateOpen when keytimes changes to ensure valid indices
  $effect(() => {
    const maxIndex = (button.keytimes ?? 1) - 1;
    const newStateOpen: Record<number, boolean> = {};
    // Keep open states that are still valid
    for (let i = 0; i <= maxIndex; i++) {
      newStateOpen[i] = stateOpen[i] ?? (i === 0);
    }
    stateOpen = newStateOpen;
  });

  let msgType = $derived((button.type ?? 'cc') as MessageType);
  let isCC = $derived(msgType === 'cc');
  let isNote = $derived(msgType === 'note');
  let isPC = $derived(msgType === 'pc');
  let isPCIncDec = $derived(msgType === 'pc_inc' || msgType === 'pc_dec');
  let showMode = $derived(isCC || isNote);

  function handleLabelChange(e: Event) {
    const target = e.target as HTMLInputElement;
    onUpdate('label', target.value);
  }

  function handleCCChange(e: Event) {
    const target = e.target as HTMLInputElement;
    onUpdate('cc', parseInt(target.value));
  }

  function handleColorChange(color: ButtonColor) {
    onUpdate('color', color);
  }

  function handleModeChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    const modeVal = target.value as ButtonMode;
    onUpdate('mode', modeVal);
    // If user selects tap mode, map to led_mode and clear select_group
    if (modeVal === 'tap') {
      onUpdate('led_mode', 'tap');
      onUpdate('select_group', undefined);
    } else {
      if (button.led_mode === 'tap') onUpdate('led_mode', undefined);
    }
  }

  function handleOffModeChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    onUpdate('off_mode', target.value as OffMode);
  }

  // LED tap mode handlers
  function handleLedModeChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    const v = target.value === '' ? undefined : target.value;
    onUpdate('led_mode', v);
  }

  // Long-press handlers
  function handleLongPressTypeChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    onUpdate('long_press[0].type', target.value);
  }

  function handleLongPressEnableChange(e: Event) {
    const target = e.target as HTMLInputElement;
    if (target.checked) {
      const firstCmd = button.long_press?.[0];
      const ch = (isMidiCommand(firstCmd) && firstCmd.channel !== undefined) 
        ? firstCmd.channel 
        : (button.channel !== undefined ? button.channel : globalChannel);
      const thresholdMs = (isMidiCommand(firstCmd) && firstCmd.threshold_ms !== undefined) 
        ? firstCmd.threshold_ms 
        : 600;
      onUpdate('long_press', [{ type: 'cc', cc: button.cc ?? 20 + index, value: 127, channel: ch, threshold_ms: thresholdMs }]);
    } else {
      onUpdate('long_press', undefined);
    }
  }

  function handleLongPressNumberField(field: string, e: Event) {
    const target = e.target as HTMLInputElement;
    let value: number | undefined = target.value === '' ? undefined : parseInt(target.value);
    // Adjust channel from 1-16 display to 0-15 storage
    if (field === 'channel' && value !== undefined) {
      value = value - 1;
    }
    onUpdate(`long_press[0].${field}`, value);
  }

  function handleLongReleaseTypeChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    onUpdate('long_release[0].type', target.value);
  }

  function handleLongReleaseEnableChange(e: Event) {
    const target = e.target as HTMLInputElement;
    if (target.checked) {
      const firstCmd = button.long_release?.[0];
      const ch = (isMidiCommand(firstCmd) && firstCmd.channel !== undefined) 
        ? firstCmd.channel 
        : (button.channel !== undefined ? button.channel : globalChannel);
      onUpdate('long_release', [{ type: 'cc', cc: button.cc ?? 20 + index, value: 0, channel: ch }]);
    } else {
      onUpdate('long_release', undefined);
    }
  }

  function handleLongReleaseNumberField(field: string, e: Event) {
    const target = e.target as HTMLInputElement;
    let value: number | undefined = target.value === '' ? undefined : parseInt(target.value);
    // Adjust channel from 1-16 display to 0-15 storage
    if (field === 'channel' && value !== undefined) {
      value = value - 1;
    }
    onUpdate(`long_release[0].${field}`, value);
  }

  function handleChannelChange(e: Event) {
    const target = e.target as HTMLInputElement;
    if (target.value === '') {
      onUpdate('channel', undefined);
    } else {
      const value = parseInt(target.value);
      // Convert from 1-16 display to 0-15 storage
      onUpdate('channel', value - 1);
    }
  }

  function handleCCOnChange(e: Event) {
    const target = e.target as HTMLInputElement;
    const value = target.value === '' ? undefined : parseInt(target.value);
    onUpdate('cc_on', value);
  }

  function handleCCOffChange(e: Event) {
    const target = e.target as HTMLInputElement;
    const value = target.value === '' ? undefined : parseInt(target.value);
    onUpdate('cc_off', value);
  }

  function handleTypeChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    onUpdate('type', target.value as MessageType);
  }

  function handleNoteChange(e: Event) {
    const target = e.target as HTMLInputElement;
    onUpdate('note', parseInt(target.value));
  }

  function handleVelocityOnChange(e: Event) {
    const target = e.target as HTMLInputElement;
    const value = target.value === '' ? undefined : parseInt(target.value);
    onUpdate('velocity_on', value);
  }

  function handleVelocityOffChange(e: Event) {
    const target = e.target as HTMLInputElement;
    const value = target.value === '' ? undefined : parseInt(target.value);
    onUpdate('velocity_off', value);
  }

  function handleProgramChange(e: Event) {
    const target = e.target as HTMLInputElement;
    onUpdate('program', parseInt(target.value));
  }

  function handlePCStepChange(e: Event) {
    const target = e.target as HTMLInputElement;
    onUpdate('pc_step', parseInt(target.value));
  }

  function handleFlashMsChange(e: Event) {
    const target = e.target as HTMLInputElement;
    const value = target.value === '' ? undefined : parseInt(target.value);
    onUpdate('flash_ms', value);
  }

  let flashMsError = $derived($validationErrors.get(`${basePath}.flash_ms`));

  let hasKeytimes = $derived((button.keytimes ?? 1) > 1);
  let keytimesError = $derived($validationErrors.get(`${basePath}.keytimes`));

  function handleKeytimesChange(e: Event) {
    const target = e.target as HTMLInputElement;
    const value = target.value === '' ? 1 : Math.min(99, Math.max(1, parseInt(target.value) || 1));
    syncButtonStates(index, value);
  }

  function handleSelectGroupChange(e: Event) {
    const target = e.target as HTMLInputElement;
    onUpdate('select_group', target.value === '' ? undefined : target.value);
  }

  function handleDefaultSelectedChange(e: Event) {
    const target = e.target as HTMLInputElement;
    onUpdate('default_selected', target.checked);
  }

  function handleStateFieldChange(si: number, field: string, e: Event) {
    const target = e.target as HTMLInputElement;
    const value = target.value === '' ? undefined : parseInt(target.value);
    onUpdate(`states[${si}].${field}`, value);
  }

  function handleStateColorChange(si: number, color: ButtonColor) {
    onUpdate(`states[${si}].color`, color);
  }

  function handleStateLabelChange(si: number, e: Event) {
    const target = e.target as HTMLInputElement;
    onUpdate(`states[${si}].label`, target.value === '' ? undefined : target.value);
  }

  function handleStateCommandsChange(si: number, eventName: 'press' | 'release' | 'long_press' | 'long_release', commands: CommandOrConditional[]) {
    onUpdate(`states[${si}].${eventName}`, commands.length > 0 ? commands : undefined);
  }

  function stateError(si: number, field: string): string | undefined {
    return $validationErrors.get(`${basePath}.states[${si}].${field}`);
  }

  let labelError = $derived($validationErrors.get(`${basePath}.label`));
  let ccError = $derived($validationErrors.get(`${basePath}.cc`));
  let channelError = $derived($validationErrors.get(`${basePath}.channel`));
  let ccOnError = $derived($validationErrors.get(`${basePath}.cc_on`));
  let ccOffError = $derived($validationErrors.get(`${basePath}.cc_off`));
  let noteError = $derived($validationErrors.get(`${basePath}.note`));
  let velocityOnError = $derived($validationErrors.get(`${basePath}.velocity_on`));
  let velocityOffError = $derived($validationErrors.get(`${basePath}.velocity_off`));
  let programError = $derived($validationErrors.get(`${basePath}.program`));
  let pcStepError = $derived($validationErrors.get(`${basePath}.pc_step`));

  // Display effective channel as 1-16 (stored internally as 0-15)
  let effectiveChannel = $derived(
    button.channel !== undefined ? button.channel + 1 : globalChannel + 1
  );

  // Display button channel as 1-16 if set (stored as 0-15)
  let displayChannel = $derived(
    button.channel !== undefined ? button.channel + 1 : undefined
  );

  // Show default checkbox only when select_group is set and allowed (non-momentary, not tap, keytimes==1)
  let showDefaultCheckbox = $derived(
    !!(button.select_group && (button.mode ?? 'toggle') !== 'momentary' && (button.mode ?? 'toggle') !== 'tap' && (button.keytimes ?? 1) <= 1)
  );

</script>

<div class="button-row" class:disabled>
  <span class="button-num">Button {index + 1}:</span>

  <div class="field">
    <input
      type="text"
      class="input-label"
      class:error={!!labelError}
      value={button.label}
      onblur={handleLabelChange}
      disabled={disabled}
      maxlength="6"
      placeholder="Label"
    />
    {#if labelError}
      <span class="error-text">{labelError}</span>
    {/if}
  </div>

  <div class="field">
    <label class="field-label">Type:</label>
    <select
      class="select"
      value={button.type ?? 'cc'}
      onchange={handleTypeChange}
      disabled={disabled}
    >
      <option value="cc">CC</option>
      <option value="note">Note</option>
      <option value="pc">PC Fixed</option>
      <option value="pc_inc">PC+</option>
      <option value="pc_dec">PC-</option>
    </select>
  </div>

  <div class="field">
    <label class="field-label">Channel:</label>
    <input
      type="number"
      class="input-channel"
      class:error={!!channelError}
      value={displayChannel !== undefined ? displayChannel : ''}
      onblur={handleChannelChange}
      disabled={disabled}
      min="1"
      max="16"
      placeholder={effectiveChannel.toString()}
      title={button.channel !== undefined ? `MIDI Ch ${effectiveChannel}` : `Using global: ${effectiveChannel}`}
    />
    {#if channelError}
      <span class="error-text">{channelError}</span>
    {/if}
  </div>

  {#if isCC}
    <div class="field">
      <label class="field-label">CC:</label>
      <input type="number" class="input-cc" class:error={!!ccError}
        value={button.cc ?? ''} onblur={handleCCChange} disabled={disabled}
        min="0" max="127" />
      {#if ccError}<span class="error-text">{ccError}</span>{/if}
    </div>
    <div class="field">
      <label class="field-label">ON Value:</label>
      <input type="number" class="input-cc-value" class:error={!!ccOnError}
        value={button.cc_on !== undefined ? button.cc_on : ''} onblur={handleCCOnChange}
        disabled={disabled} min="0" max="127" placeholder="127" />
      {#if ccOnError}<span class="error-text">{ccOnError}</span>{/if}
    </div>
    <div class="field">
      <label class="field-label">OFF Value:</label>
      <input type="number" class="input-cc-value" class:error={!!ccOffError}
        value={button.cc_off !== undefined ? button.cc_off : ''} onblur={handleCCOffChange}
        disabled={disabled} min="0" max="127" placeholder="0" />
      {#if ccOffError}<span class="error-text">{ccOffError}</span>{/if}
    </div>
  {:else if isNote}
    <div class="field">
      <label class="field-label">Note:</label>
      <input type="number" class="input-cc" class:error={!!noteError}
        value={button.note ?? 60} onblur={handleNoteChange} disabled={disabled}
        min="0" max="127" />
      {#if noteError}<span class="error-text">{noteError}</span>{/if}
    </div>
    <div class="field">
      <label class="field-label">Vel ON:</label>
      <input type="number" class="input-cc-value" class:error={!!velocityOnError}
        value={button.velocity_on !== undefined ? button.velocity_on : ''} onblur={handleVelocityOnChange}
        disabled={disabled} min="0" max="127" placeholder="127" />
      {#if velocityOnError}<span class="error-text">{velocityOnError}</span>{/if}
    </div>
    <div class="field">
      <label class="field-label">Vel OFF:</label>
      <input type="number" class="input-cc-value" class:error={!!velocityOffError}
        value={button.velocity_off !== undefined ? button.velocity_off : ''} onblur={handleVelocityOffChange}
        disabled={disabled} min="0" max="127" placeholder="0" />
      {#if velocityOffError}<span class="error-text">{velocityOffError}</span>{/if}
    </div>
  {:else if isPC}
    <div class="field">
      <label class="field-label">Program:</label>
      <input type="number" class="input-cc" class:error={!!programError}
        value={button.program ?? 0} onblur={handleProgramChange} disabled={disabled}
        min="0" max="127" />
      {#if programError}<span class="error-text">{programError}</span>{/if}
    </div>
  {:else if isPCIncDec}
    <div class="field">
      <label class="field-label">Step:</label>
      <input type="number" class="input-cc" class:error={!!pcStepError}
        value={button.pc_step ?? 1} onblur={handlePCStepChange} disabled={disabled}
        min="1" max="127" />
      {#if pcStepError}<span class="error-text">{pcStepError}</span>{/if}
    </div>
  {/if}

  {#if isPC || isPCIncDec}
    <div class="field">
      <label class="field-label">Flash (ms):</label>
      <input type="number" class="input-cc" class:error={!!flashMsError}
        value={button.flash_ms ?? ''} onblur={handleFlashMsChange} disabled={disabled}
        min="50" max="5000" step="50" placeholder="200" />
      {#if flashMsError}<span class="error-text">{flashMsError}</span>{/if}
    </div>
  {/if}

  <div class="field">
    <label class="field-label">Keytimes:</label>
    <input
      type="number"
      class="input-cc"
      class:error={!!keytimesError}
      value={button.keytimes ?? 1}
      onblur={handleKeytimesChange}
      disabled={disabled}
      min="1"
      max="99"
    />
    {#if keytimesError}<span class="error-text">{keytimesError}</span>{/if}
  </div>

  <div class="field">
    <label class="field-label">LED Color:</label>
    <ColorSelect
      value={button.color}
      onchange={handleColorChange}
    />
  </div>

  <div class="field">
    <label class="field-label">Select Group:</label>
    <input type="text" class="input-cc" value={button.select_group ?? ''} onblur={handleSelectGroupChange} disabled={disabled || button.mode === 'tap'} placeholder="group name" />
    {#if showDefaultCheckbox}
      <label style="font-size:0.8rem;margin-left:0.5rem;"><input type="checkbox" checked={button.default_selected ?? false} onchange={handleDefaultSelectedChange} disabled={disabled}/> Default</label>
    {:else}
      <label style="font-size:0.8rem;margin-left:0.5rem;color:#888">Default</label>
    {/if}
  </div>

  {#if showMode}
    <div class="field">
      <label class="field-label">Switch Mode:</label>
      <select class="select" value={button.mode || 'toggle'} onchange={handleModeChange} disabled={disabled}>
        <option value="toggle">Toggle</option>
        <option value="momentary">Momentary</option>
        <option value="select">Select</option>
        <option value="tap">Tap (always active — blinks when tapped)</option>
      </select>
    </div>
  {/if}

  <div class="field">
    <label class="field-label">LED Off Mode:</label>
    <select class="select" value={button.off_mode || 'dim'} onchange={handleOffModeChange} disabled={disabled}>
      <option value="dim">Dim</option>
      <option value="off">Off</option>
    </select>
  </div>

  <!-- Tap tempo is derived at runtime from user taps; no manual tap-rate input -->

  <div class="field">
    <label class="field-label">LED Mode:</label>
    <select class="select" value={button.led_mode ?? ''} onchange={handleLedModeChange} disabled={disabled || button.mode === 'tap'}>
      <option value="">Normal</option>
      <option value="tap">Tap (always active)</option>
    </select>
  </div>

  <!-- No manual tap-rate control shown; tempo is set by tapping the switch -->

  <details class="long-section" open>
    <summary>Long Press ▸</summary>
    <small class="hint">Optional action fired when the switch is held beyond the threshold.</small>
    <div style="margin-bottom:0.5rem;">
      <label style="font-size:0.9rem;"><input type="checkbox" checked={!!button.long_press} onchange={handleLongPressEnableChange} disabled={disabled}/> Enable long press</label>
    </div>
    {#if button.long_press}
    <div class="field long-fields">
      <label class="field-label">Type:</label>
      <select class="select" value={longPressCmd?.type ?? 'cc'} onchange={handleLongPressTypeChange} disabled={disabled} title="Message type for long press">
        <option value="cc">CC</option>
        <option value="note">Note</option>
        <option value="pc">PC</option>
      </select>
      {#if (longPressCmd?.type ?? 'cc') === 'cc'}
        <input type="number" class="input-cc" value={longPressCmd?.cc ?? ''} onblur={(e)=>handleLongPressNumberField('cc', e)} disabled={disabled} min="0" max="127" placeholder="CC" title="CC number (0-127)" />
        <input type="number" class="input-cc-value" value={longPressCmd?.value ?? ''} onblur={(e)=>handleLongPressNumberField('value', e)} disabled={disabled} min="0" max="127" placeholder="Value" title="Value (0-127)" />
        <input type="number" class="input-cc" value={longPressCmd?.threshold_ms ?? ''} onblur={(e)=>handleLongPressNumberField('threshold_ms', e)} disabled={disabled} min="50" max="10000" placeholder="Thr ms" title="Threshold in ms (hold duration)" />
      {:else if (longPressCmd?.type ?? '') === 'note'}
        <input type="number" class="input-cc" value={longPressCmd?.note ?? ''} onblur={(e)=>handleLongPressNumberField('note', e)} disabled={disabled} min="0" max="127" placeholder="Note" title="Note number (0-127)" />
        <input type="number" class="input-cc-value" value={longPressCmd?.value ?? ''} onblur={(e)=>handleLongPressNumberField('value', e)} disabled={disabled} min="0" max="127" placeholder="Vel" title="Velocity (0-127)" />
      {:else}
        <input type="number" class="input-cc" value={longPressCmd?.program ?? ''} onblur={(e)=>handleLongPressNumberField('program', e)} disabled={disabled} min="0" max="127" placeholder="Program" title="Program number (0-127)" />
      {/if}
      <input type="number" class="input-channel" value={longPressCmd?.channel !== undefined ? longPressCmd.channel + 1 : ''} onblur={(e)=>handleLongPressNumberField('channel', e)} disabled={disabled} min="1" max="16" placeholder="Ch" title="MIDI channel (1-16)" />
    </div>
    {/if}
  </details>

  <details class="long-section">
    <summary>Long Release ▸</summary>
    <small class="hint">Optional action fired when the long-press is released.</small>
    <div style="margin-bottom:0.5rem;">
      <label style="font-size:0.9rem;"><input type="checkbox" checked={!!button.long_release} onchange={handleLongReleaseEnableChange} disabled={disabled}/> Enable long release</label>
    </div>
    {#if button.long_release}
    <div class="field long-fields">
      <label class="field-label">Type:</label>
      <select class="select" value={longReleaseCmd?.type ?? 'cc'} onchange={handleLongReleaseTypeChange} disabled={disabled} title="Message type for long-release">
        <option value="cc">CC</option>
        <option value="note">Note</option>
        <option value="pc">PC</option>
      </select>
      {#if (longReleaseCmd?.type ?? 'cc') === 'cc'}
        <input type="number" class="input-cc" value={longReleaseCmd?.cc ?? ''} onblur={(e)=>handleLongReleaseNumberField('cc', e)} disabled={disabled} min="0" max="127" placeholder="CC" title="CC number (0-127)" />
        <input type="number" class="input-cc-value" value={longReleaseCmd?.value ?? ''} onblur={(e)=>handleLongReleaseNumberField('value', e)} disabled={disabled} min="0" max="127" placeholder="Value" title="Value (0-127)" />
      {:else if (longReleaseCmd?.type ?? '') === 'note'}
        <input type="number" class="input-cc" value={longReleaseCmd?.note ?? ''} onblur={(e)=>handleLongReleaseNumberField('note', e)} disabled={disabled} min="0" max="127" placeholder="Note" title="Note number (0-127)" />
        <input type="number" class="input-cc-value" value={longReleaseCmd?.value ?? ''} onblur={(e)=>handleLongReleaseNumberField('value', e)} disabled={disabled} min="0" max="127" placeholder="Vel" title="Velocity (0-127)" />
      {:else}
        <input type="number" class="input-cc" value={longReleaseCmd?.program ?? ''} onblur={(e)=>handleLongReleaseNumberField('program', e)} disabled={disabled} min="0" max="127" placeholder="Program" title="Program number (0-127)" />
      {/if}
      <input type="number" class="input-channel" value={longReleaseCmd?.channel !== undefined ? longReleaseCmd.channel + 1 : ''} onblur={(e)=>handleLongReleaseNumberField('channel', e)} disabled={disabled} min="1" max="16" placeholder="Ch" title="MIDI channel (1-16)" />
    </div>
    {/if}
  </details>

  {#if hasKeytimes && !disabled}
    <div class="states-section">
      <span class="states-label">States ({button.states?.length ?? 0}):</span>
      {#each (button.states ?? []) as state, si}
        <details class="state-details" bind:open={stateOpen[si]}>
          <summary class="state-summary">
            <span class="state-num">State {si + 1}</span>
            <span class="state-label-preview">{state.label || button.label || `S${si + 1}`}</span>
            <span class="state-color-dot" style="background-color: {state.color || button.color || 'white'};"></span>
          </summary>
          
          <div class="state-content">
            <!-- Visual overrides -->
            <div class="state-visual-fields">
              <div class="field">
                <label class="field-label">Color:</label>
                <ColorSelect
                  value={state.color ?? button.color}
                  onchange={(color) => handleStateColorChange(si, color)}
                />
              </div>
              <div class="field">
                <label class="field-label">Label:</label>
                <input type="text" class="input-label" class:error={!!stateError(si, 'label')}
                  value={state.label ?? ''}
                  onblur={(e) => handleStateLabelChange(si, e)}
                  maxlength="6"
                  placeholder={button.label} />
                {#if stateError(si, 'label')}<span class="error-text">{stateError(si, 'label')}</span>{/if}
              </div>
            </div>
            
            <!-- Multi-command event editors -->
            <div class="state-commands">
              <ButtonCommandsEditor
                eventLabel="Press"
                commands={state.press ?? []}
                globalChannel={globalChannel}
                onUpdate={(cmds) => handleStateCommandsChange(si, 'press', cmds)}
              />
              
              <ButtonCommandsEditor
                eventLabel="Release"
                commands={state.release ?? []}
                globalChannel={globalChannel}
                onUpdate={(cmds) => handleStateCommandsChange(si, 'release', cmds)}
              />
              
              <ButtonCommandsEditor
                eventLabel="Long Press"
                commands={state.long_press ?? []}
                globalChannel={globalChannel}
                onUpdate={(cmds) => handleStateCommandsChange(si, 'long_press', cmds)}
              />
              
              <ButtonCommandsEditor
                eventLabel="Long Release"
                commands={state.long_release ?? []}
                globalChannel={globalChannel}
                onUpdate={(cmds) => handleStateCommandsChange(si, 'long_release', cmds)}
              />
            </div>
          </div>
        </details>
      {/each}
    </div>
  {/if}

  {#if disabled}
    <div class="disabled-overlay">
      Not available on Mini6
    </div>
  {/if}
</div>

<style>
  .button-row {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    padding: 0.5rem;
    border: 1px solid #e5e5e5;
    border-radius: 4px;
    margin-bottom: 0.5rem;
    position: relative;
    flex-wrap: wrap;
  }

  .button-row.disabled {
    opacity: 0.6;
    background: #f9f9f9;
  }

  .button-num {
    font-weight: 500;
    color: #666;
    min-width: 80px;
    padding-top: 0.4rem;
  }

  .field {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    flex-direction: column;
    position: relative;
  }

  .field-label {
    font-size: 0.75rem;
    color: #666;
    align-self: flex-start;
  }

  .input-label {
    width: 80px;
    padding: 0.375rem 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.875rem;
  }

  .input-cc {
    width: 60px;
    padding: 0.375rem 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.875rem;
  }

  .input-channel {
    width: 60px;
    padding: 0.375rem 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.875rem;
  }

  .input-cc-value {
    width: 60px;
    padding: 0.375rem 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.875rem;
  }

  .select {
    padding: 0.375rem 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.875rem;
    background: white;
  }

  input.error {
    border-color: #dc3545;
  }

  .error-text {
    position: absolute;
    top: 100%;
    left: 0;
    font-size: 0.75rem;
    color: #dc3545;
    white-space: nowrap;
    margin-top: 2px;
  }

  .states-section {
    width: 100%;
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px dashed #e0e0e0;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .states-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #555;
    margin-bottom: 0.25rem;
  }

  .state-row {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    flex-wrap: wrap;
    padding: 0.25rem 0.5rem;
    background: #fafafa;
    border: 1px solid #eee;
    border-radius: 4px;
  }

  .state-num {
    font-size: 0.75rem;
    color: #888;
    min-width: 28px;
    padding-top: 1.5rem;
  }

  /* Long-press UI tweaks */
  .long-section {
    width: 100%;
    margin-top: 0.25rem;
    padding: 0.35rem 0.5rem;
    border-radius: 4px;
    background: #ffffff;
    border: 1px solid #f0f0f0;
  }

  .long-section summary {
    font-size: 0.8rem;
    font-weight: 600;
    color: #333;
    list-style: none;
    cursor: pointer;
    outline: none;
    margin-bottom: 0.25rem;
  }

  .long-section .hint {
    font-size: 0.75rem;
    color: #666;
    margin-bottom: 0.35rem;
    display: block;
  }

  .long-fields {
    display: flex;
    gap: 0.5rem;
    align-items: center;
    flex-wrap: wrap;
  }

  .disabled-overlay {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.8);
    color: #666;
    font-size: 0.875rem;
    font-weight: 500;
    pointer-events: none;
  }

  /* State details sections */
  .state-details {
    margin-bottom: 0.75rem;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 0.5rem;
    background: #f8f8f8;
  }

  .state-summary {
    font-size: 0.85rem;
    font-weight: 600;
    color: #333;
    list-style: none;
    cursor: pointer;
    outline: none;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  .state-summary::-webkit-details-marker {
    display: none;
  }

  .state-num {
    color: #555;
  }

  .state-label-preview {
    flex: 1;
    font-weight: 400;
    color: #666;
  }

  .state-color-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 1px solid #999;
  }

  .state-content {
    margin-top: 0.75rem;
  }

  .state-visual-fields {
    display: flex;
    gap: 1rem;
    margin-bottom: 0.75rem;
    align-items: flex-end;
  }

  .state-commands {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
</style>
