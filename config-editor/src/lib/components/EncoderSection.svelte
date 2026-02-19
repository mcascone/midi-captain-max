<script lang="ts">
  import Accordion from './Accordion.svelte';
  import { config, updateField } from '$lib/formStore';
  import { validationErrors } from '$lib/formStore';
  
  let deviceType = $derived($config.device);
  let encoder = $derived($config.encoder);
  let isDisabled = $derived(deviceType === 'mini6');
  let message = $derived(isDisabled ? 'Disabled on Mini6' : undefined);
  let globalChannel = $derived($config.global_channel ?? 0);
  
  function handleField(path: string, e: Event) {
    const target = e.target as HTMLInputElement | HTMLSelectElement;
    const value = target.type === 'checkbox' 
      ? (target as HTMLInputElement).checked
      : target.type === 'number'
      ? parseInt(target.value)
      : target.value;
    
    updateField(`encoder.${path}`, value);
  }
  
  function handleChannelChange(path: string, e: Event) {
    const target = e.target as HTMLInputElement;
    if (target.value === '') {
      updateField(`encoder.${path}`, undefined);
    } else {
      const value = parseInt(target.value);
      // Convert from 1-16 display to 0-15 storage
      updateField(`encoder.${path}`, value - 1);
    }
  }
  
  // Display channel as 1-16 (stored as 0-15)
  let displayChannel = $derived(
    encoder?.channel !== undefined ? encoder.channel + 1 : undefined
  );
  let effectiveChannel = $derived(
    encoder?.channel !== undefined ? encoder.channel + 1 : globalChannel + 1
  );
  
  let displayPushChannel = $derived(
    encoder?.push?.channel !== undefined ? encoder.push.channel + 1 : undefined
  );
  let effectivePushChannel = $derived(
    encoder?.push?.channel !== undefined ? encoder.push.channel + 1 : globalChannel + 1
  );
  
  let ccError = $derived($validationErrors.get('encoder.cc'));
  let pushCCError = $derived($validationErrors.get('encoder.push.cc'));
</script>

<Accordion 
  title="Encoder" 
  defaultOpen={!isDisabled}
  disabled={isDisabled}
  {message}
>
  {#if encoder}
    <div class="encoder-section">
      <div class="field-row">
        <label>
          <input 
            type="checkbox" 
            checked={encoder.enabled || false}
            onchange={(e) => handleField('enabled', e)}
            disabled={isDisabled}
          />
          Enabled
        </label>
      </div>
      
      {#if encoder.enabled}
        <div class="field-row">
          <label>CC:</label>
          <input 
            type="number" 
            class:error={!!ccError}
            value={encoder.cc}
            onblur={(e) => handleField('cc', e)}
            min="0"
            max="127"
            disabled={isDisabled}
          />
          {#if ccError}
            <span class="error-text">{ccError}</span>
          {/if}
        </div>
        
        <div class="field-row">
          <label>Label:</label>
          <input 
            type="text" 
            value={encoder.label}
            onblur={(e) => handleField('label', e)}
            maxlength="6"
            disabled={isDisabled}
          />
        </div>
        
        <div class="field-row">
          <label>Channel:</label>
          <input 
            type="number" 
            value={displayChannel !== undefined ? displayChannel : ''}
            onblur={(e) => handleChannelChange('channel', e)}
            min="1"
            max="16"
            placeholder={effectiveChannel.toString()}
            title={encoder.channel !== undefined ? `MIDI Ch ${effectiveChannel}` : `Using global: ${effectiveChannel}`}
            disabled={isDisabled}
          />
        </div>
        
        <div class="field-row">
          <label>Min:</label>
          <input 
            type="number" 
            value={encoder.min ?? 0}
            onblur={(e) => handleField('min', e)}
            min="0"
            max="127"
            disabled={isDisabled}
          />
        </div>
        
        <div class="field-row">
          <label>Max:</label>
          <input 
            type="number" 
            value={encoder.max ?? 127}
            onblur={(e) => handleField('max', e)}
            min="0"
            max="127"
            disabled={isDisabled}
          />
        </div>
        
        <div class="field-row">
          <label>Initial:</label>
          <input 
            type="number" 
            value={encoder.initial ?? 64}
            onblur={(e) => handleField('initial', e)}
            min="0"
            max="127"
            disabled={isDisabled}
          />
        </div>
        
        <h4>Encoder Push Button</h4>
        
        <div class="field-row">
          <label>
            <input 
              type="checkbox" 
              checked={encoder.push?.enabled || false}
              onchange={(e) => handleField('push.enabled', e)}
              disabled={isDisabled}
            />
            Enabled
          </label>
        </div>
        
        {#if encoder.push?.enabled}
          <div class="field-row">
            <label>CC:</label>
            <input 
              type="number" 
              class:error={!!pushCCError}
              value={encoder.push.cc}
              onblur={(e) => handleField('push.cc', e)}
              min="0"
              max="127"
              disabled={isDisabled}
            />
            {#if pushCCError}
              <span class="error-text">{pushCCError}</span>
            {/if}
          </div>
          
          <div class="field-row">
            <label>Label:</label>
            <input 
              type="text" 
              value={encoder.push.label}
              onblur={(e) => handleField('push.label', e)}
              maxlength="6"
              disabled={isDisabled}
            />
          </div>
          
          <div class="field-row">
            <label>Mode:</label>
            <select 
              value={encoder.push.mode || 'momentary'}
              onchange={(e) => handleField('push.mode', e)}
              disabled={isDisabled}
            >
              <option value="toggle">Toggle</option>
              <option value="momentary">Momentary</option>
            </select>
          </div>
          
          <div class="field-row">
            <label>Channel:</label>
            <input 
              type="number" 
              value={displayPushChannel !== undefined ? displayPushChannel : ''}
              onblur={(e) => handleChannelChange('push.channel', e)}
              min="1"
              max="16"
              placeholder={effectivePushChannel.toString()}
              title={encoder.push.channel !== undefined ? `MIDI Ch ${effectivePushChannel}` : `Using global: ${effectivePushChannel}`}
              disabled={isDisabled}
            />
          </div>
        {/if}
      {/if}
    </div>
  {/if}
</Accordion>

<style>
  .encoder-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .field-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    position: relative;
  }
  
  .field-row label {
    min-width: 80px;
    font-size: 0.875rem;
  }
  
  .field-row input[type="text"],
  .field-row input[type="number"],
  .field-row select {
    padding: 0.375rem 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.875rem;
  }
  
  .field-row input[type="checkbox"] {
    margin-right: 0.25rem;
  }
  
  input.error {
    border-color: #dc3545;
  }
  
  .error-text {
    position: absolute;
    left: 100px;
    top: 100%;
    font-size: 0.75rem;
    color: #dc3545;
    white-space: nowrap;
  }
  
  h4 {
    margin: 0.5rem 0 0 0;
    font-size: 0.875rem;
    color: #666;
  }
</style>
