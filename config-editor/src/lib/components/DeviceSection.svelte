<script lang="ts">
  import Accordion from './Accordion.svelte';
  import { config, setDevice, updateField } from '$lib/formStore';
  import type { DeviceType } from '$lib/types';
  
  function handleDeviceChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    setDevice(target.value as DeviceType);
  }
  
  function handleGlobalChannelChange(e: Event) {
    const target = e.target as HTMLInputElement;
    const value = parseInt(target.value);
    // Clamp to valid MIDI channel range (0-15)
    const clamped = Math.max(0, Math.min(15, value));
    updateField('global_channel', clamped);
  }
  
  let globalChannel = $derived($config.global_channel ?? 0);

</script>

<Accordion title="Device Settings">
  <div class="device-section">
    <div class="field-group">
      <label for="device-type">Device Type:</label>
      <select 
        id="device-type"
        class="select"
        value={$config.device}
        onchange={handleDeviceChange}
      >
        <option value="std10">STD10 (10 buttons)</option>
        <option value="mini6">Mini6 (6 buttons)</option>
      </select>
      
      <p class="help-text">
        {#if $config.device === 'mini6'}
          Mini6 supports 6 buttons only. Encoder and expression pedals are not available.
        {:else}
          STD10 supports 10 buttons, encoder, and expression pedals.
        {/if}
      </p>
    </div>
    
    <div class="field-group">
      <label for="global-channel">Global MIDI Channel:</label>
      <div class="channel-input-group">
        <input 
          id="global-channel"
          type="number"
          class="input-number"
          value={globalChannel}
          onblur={handleGlobalChannelChange}
          min="0"
          max="15"
        />
        <span class="channel-display">= MIDI Ch {globalChannel + 1}</span>
      </div>
      <p class="help-text">
        Default MIDI channel for all buttons (0-15 = MIDI Ch 1-16).
        Individual buttons can override this setting.
      </p>
    </div>
  </div>
</Accordion>

<style>
  .device-section {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .field-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  label {
    font-weight: 500;
  }
  
  .select {
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.875rem;
    background: white;
    max-width: 250px;
  }
  
  .input-number {
    width: 80px;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.875rem;
  }
  
  .channel-input-group {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  
  .channel-display {
    font-size: 0.875rem;
    color: #666;
  }
  
  .help-text {
    font-size: 0.875rem;
    color: #666;
    margin: 0;
  }
</style>
