<script lang="ts">
  import type { ExpressionConfig } from '$lib/types';
  import { config } from '$lib/formStore';
  import Knob from './Knob.svelte';
  import Toggle from './Toggle.svelte';

  interface Props {
    pedal: ExpressionConfig;
    name: string;
    onUpdate: (field: string, value: any) => void;
  }

  let { pedal, name, onUpdate }: Props = $props();

  let globalChannel = $derived($config.global_channel ?? 0);

  function handleCheckbox(e: Event) {
    const target = e.target as HTMLInputElement;
    onUpdate('enabled', target.checked);
  }

  function handleNumberInput(field: string, e: Event) {
    const target = e.target as HTMLInputElement;
    const value = target.value === '' ? undefined : parseInt(target.value, 10);
    onUpdate(field, value);
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

  function handleSelect(field: string, e: Event) {
    const target = e.target as HTMLSelectElement;
    onUpdate(field, target.value);
  }

  // Display channel as 1-16 (stored as 0-15)
  let displayChannel = $derived(
    pedal.channel !== undefined ? pedal.channel + 1 : undefined
  );
  let effectiveChannel = $derived(
    pedal.channel !== undefined ? pedal.channel + 1 : globalChannel + 1
  );
</script>

<div class="pedal-config">
  <div class="pedal-header">
    <Toggle
      checked={pedal.enabled}
      label={name}
      onchange={(checked) => onUpdate('enabled', checked)}
    />
  </div>

  {#if pedal.enabled}
    <div class="pedal-fields">
      <label>
        <span class="field-label">Label:</span>
        <input
          type="text"
          value={pedal.label}
          maxlength="6"
          on:blur={(e) => onUpdate('label', (e.target as HTMLInputElement).value)}
        />
      </label>

      <label>
        <span class="field-label">Channel:</span>
        <input
          type="number"
          value={displayChannel !== undefined ? displayChannel : ''}
          min="1"
          max="16"
          placeholder={effectiveChannel.toString()}
          title={pedal.channel !== undefined ? `MIDI Ch ${effectiveChannel}` : `Using global: ${effectiveChannel}`}
          on:blur={handleChannelChange}
        />
      </label>

      <label>
        <span class="field-label">CC:</span>
        <input
          type="number"
          value={pedal.cc}
          min="0"
          max="127"
          on:blur={(e) => handleNumberInput('cc', e)}
        />
      </label>

      <label>
        <span class="field-label">Polarity:</span>
        <select
          value={pedal.polarity || 'normal'}
          on:change={(e) => handleSelect('polarity', e)}
        >
          <option value="normal">Normal</option>
          <option value="inverted">Inverted</option>
        </select>
      </label>

      <div class="knobs-row">
        <Knob
          bind:value={pedal.min}
          min={0}
          max={127}
          label="MIN"
          onchange={(val) => onUpdate('min', val)}
        />

        <Knob
          bind:value={pedal.max}
          min={0}
          max={127}
          label="MAX"
          onchange={(val) => onUpdate('max', val)}
        />
      </div>

      <label>
        <span class="field-label">Threshold:</span>
        <input
          type="number"
          value={pedal.threshold ?? 5}
          min="0"
          max="127"
          placeholder="5"
          on:blur={(e) => handleNumberInput('threshold', e)}
        />
      </label>
    </div>
  {/if}
</div>

<style>
  .pedal-config {
    border: 1px solid #333333;
    border-radius: 4px;
    padding: 1rem;
    background: #121212;
  }

  .pedal-header {
    margin-bottom: 0.75rem;
  }

  .pedal-name {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    font-size: 0.95rem;
    cursor: pointer;
    color: #e5e7eb;
  }

  .pedal-name input[type="checkbox"] {
    cursor: pointer;
  }

  .pedal-fields {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    margin-top: 0.75rem;
    padding: 1rem;
    background: var(--bg-input);
    border-radius: 4px;
  }

  .pedal-fields label {
    display: grid;
    grid-template-columns: 80px 1fr;
    align-items: center;
    gap: 0.75rem;
    color: #e5e7eb;
  }

  .field-label {
    font-size: 0.875rem;
    color: #9ca3af;
    text-align: right;
    font-weight: 500;
  }

  input[type="text"],
  input[type="number"],
  select {
    padding: 0.5rem 0.75rem;
    border: 1px solid #444444;
    border-radius: 4px;
    font-size: 0.875rem;
    font-family: inherit;
    background: #333333;
    color: #e5e7eb;
    width: 100%;
  }

  input[type="text"]:hover,
  input[type="number"]:hover,
  select:hover {
    background: #444444;
  }

  select {
    cursor: pointer;
  }

  input:focus,
  select:focus {
    outline: 2px solid var(--accent-primary);
    outline-offset: 1px;
  }

  input:disabled,
  select:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .knobs-row {
    grid-column: 1 / -1;
    display: flex;
    gap: 2rem;
    align-items: center;
    justify-content: center;
    padding: 1.5rem;
    background: var(--bg-dark);
    border-radius: 8px;
    border: 1px solid var(--border-default);
  }
</style>
