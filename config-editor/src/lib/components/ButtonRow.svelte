<script lang="ts">
  import ColorSelect from './ColorSelect.svelte';
  import type { ButtonConfig, ButtonColor, ButtonMode, OffMode } from '$lib/types';
  import { validationErrors } from '$lib/formStore';
  
  interface Props {
    button: ButtonConfig;
    index: number;
    disabled?: boolean;
    onUpdate: (field: string, value: any) => void;
  }
  
  let { button, index, disabled = false, onUpdate }: Props = $props();
  
  const basePath = `buttons[${index}]`;
  
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
    onUpdate('mode', target.value as ButtonMode);
  }
  
  function handleOffModeChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    onUpdate('off_mode', target.value as OffMode);
  }
  
  let labelError = $derived($validationErrors.get(`${basePath}.label`));
  let ccError = $derived($validationErrors.get(`${basePath}.cc`));
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
    <label class="field-label">CC:</label>
    <input 
      type="number" 
      class="input-cc"
      class:error={!!ccError}
      value={button.cc}
      onblur={handleCCChange}
      disabled={disabled}
      min="0"
      max="127"
    />
    {#if ccError}
      <span class="error-text">{ccError}</span>
    {/if}
  </div>
  
  <div class="field">
    <label class="field-label">Color:</label>
    <ColorSelect 
      value={button.color} 
      onchange={handleColorChange}
    />
  </div>
  
  <div class="field">
    <label class="field-label">Mode:</label>
    <select 
      class="select"
      value={button.mode || 'toggle'}
      onchange={handleModeChange}
      disabled={disabled}
    >
      <option value="toggle">Toggle</option>
      <option value="momentary">Momentary</option>
    </select>
  </div>
  
  <div class="field">
    <label class="field-label">Off:</label>
    <select 
      class="select"
      value={button.off_mode || 'dim'}
      onchange={handleOffModeChange}
      disabled={disabled}
    >
      <option value="dim">Dim</option>
      <option value="off">Off</option>
    </select>
  </div>
  
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
    gap: 0.75rem;
    padding: 0.5rem;
    border: 1px solid #e5e5e5;
    border-radius: 4px;
    margin-bottom: 0.5rem;
    position: relative;
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
</style>
