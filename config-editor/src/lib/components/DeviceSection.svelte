<script lang="ts">
  import Accordion from './Accordion.svelte';
  import { config, setDevice } from '$lib/formStore';
  import type { DeviceType } from '$lib/types';
  
  function handleDeviceChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    setDevice(target.value as DeviceType);
  }
</script>

<Accordion title="Device Settings">
  <div class="device-section">
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
</Accordion>

<style>
  .device-section {
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
  
  .help-text {
    font-size: 0.875rem;
    color: #666;
    margin: 0;
  }
</style>
