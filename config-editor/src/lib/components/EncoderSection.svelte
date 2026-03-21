<script lang="ts">
  import { config, updateField } from '$lib/formStore';
  import { validationErrors } from '$lib/formStore';
  
  let deviceType = $derived($config.device);
  let encoder = $derived($config.encoder);
  let isDisabled = $derived(deviceType === 'mini6');
  let message = $derived(isDisabled ? 'Disabled on Mini6' : undefined);
  let globalChannel = $derived($config.global_channel ?? 0);
  
  function handleField(path: string, e: Event) {
    const target = e.target as HTMLInputElement | HTMLSelectElement;
    let value: any;
    
    if (target.type === 'checkbox') {
      value = (target as HTMLInputElement).checked;
    } else if (target.type === 'number') {
      // For number inputs, handle empty string as undefined
      const numValue = parseInt(target.value);
      value = target.value === '' ? undefined : numValue;
    } else {
      value = target.value;
    }
    
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

{#if encoder}
  <div class="encoder-section">
    <label class="checkbox-label">
      <input 
        type="checkbox" 
        checked={encoder.enabled || false}
        onchange={(e) => handleField('enabled', e)}
        disabled={isDisabled}
      />
      <span>Enabled</span>
    </label>
    
    {#if encoder.enabled}
      <div class="encoder-fields">
        <label>
          <span class="field-label">Label:</span>
          <input 
            type="text" 
            value={encoder.label}
            onblur={(e) => handleField('label', e)}
            maxlength="6"
            disabled={isDisabled}
          />
        </label>

        <label>
          <span class="field-label">Channel:</span>
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
        </label>

        <label>
          <span class="field-label">CC:</span>
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
            <span class="error-inline">{ccError}</span>
          {/if}
        </label>

        <label>
          <span class="field-label">Min:</span>
          <input 
            type="number" 
            value={encoder.min ?? 0}
            onblur={(e) => handleField('min', e)}
            min="0"
            max="127"
            disabled={isDisabled}
          />
        </label>
        
        <label>
          <span class="field-label">Max:</span>
          <input 
            type="number" 
            value={encoder.max ?? 127}
            onblur={(e) => handleField('max', e)}
            min="0"
            max="127"
            disabled={isDisabled}
          />
        </label>
        
        <label>
          <span class="field-label">Initial:</span>
          <input 
            type="number" 
            value={encoder.initial ?? 64}
            onblur={(e) => handleField('initial', e)}
            min="0"
            max="127"
            disabled={isDisabled}
          />
        </label>
      </div>
      
      <h4 class="section-heading">Encoder Push Button</h4>
      
      <label class="checkbox-label">
        <input 
          type="checkbox" 
          checked={encoder.push?.enabled || false}
          onchange={(e) => handleField('push.enabled', e)}
          disabled={isDisabled}
        />
        <span>Enabled</span>
      </label>
      
      {#if encoder.push?.enabled}
        <div class="encoder-fields">
          <label>
            <span class="field-label">Label:</span>
            <input 
              type="text" 
              value={encoder.push.label}
              onblur={(e) => handleField('push.label', e)}
              maxlength="6"
              disabled={isDisabled}
            />
          </label>
          
          <label>
            <span class="field-label">Channel:</span>
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
          </label>

          <label>
            <span class="field-label">CC:</span>
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
              <span class="error-inline">{pushCCError}</span>
            {/if}
          </label>
          
          <label>
            <span class="field-label">Mode:</span>
            <select 
              value={encoder.push.mode || 'momentary'}
              onchange={(e) => handleField('push.mode', e)}
              disabled={isDisabled}
            >
              <option value="toggle">Toggle</option>
              <option value="momentary">Momentary</option>
            </select>
          </label>
          
          <label>
            <span class="field-label">ON Value:</span>
            <input 
              type="number" 
              value={encoder.push.cc_on !== undefined ? encoder.push.cc_on : ''}
              onblur={(e) => handleField('push.cc_on', e)}
              min="0"
              max="127"
              placeholder="127"
              disabled={isDisabled}
            />
          </label>
          
          <label>
            <span class="field-label">OFF Value:</span>
            <input 
              type="number" 
              value={encoder.push.cc_off !== undefined ? encoder.push.cc_off : ''}
              onblur={(e) => handleField('push.cc_off', e)}
              min="0"
              max="127"
              placeholder="0"
              disabled={isDisabled}
            />
          </label>
        </div>
      {/if}
    {/if}
  </div>
{:else}
  <div class="encoder-section">
    <div class="empty-state">
      {#if isDisabled}
        <p class="empty-message">
          <strong>Encoder not available</strong><br/>
          The encoder is not supported on Mini6 devices. Only STD10 devices have an encoder and expression pedal support.
        </p>
      {:else}
        <p class="empty-message">
          <strong>Encoder not configured</strong><br/>
          The encoder configuration is missing from your config file. This typically happens when relying on firmware defaults.
        </p>
        <p class="empty-help">
          To configure the encoder, add an "encoder" section to your config.json file or reload the config to initialize default settings.
        </p>
      {/if}
    </div>
  </div>
{/if}

<style>
  .encoder-section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 500;
    color: #e5e7eb;
    font-size: 0.95rem;
  }

  .checkbox-label input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
  }

  .encoder-fields {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    padding: 1rem;
    background: #0f172a;
    border-radius: 4px;
    margin-top: 0.5rem;
  }
  
  .encoder-fields label {
    display: grid;
    grid-template-columns: 80px 1fr;
    align-items: center;
    gap: 0.75rem;
    color: #e5e7eb;
    position: relative;
  }
  
  .field-label {
    font-size: 0.875rem;
    color: #9ca3af;
    text-align: right;
    font-weight: 500;
  }
  
  .encoder-fields input[type="text"],
  .encoder-fields input[type="number"],
  .encoder-fields select {
    padding: 0.5rem 0.75rem;
    border: 1px solid #4b5563;
    border-radius: 4px;
    font-size: 0.875rem;
    background: #374151;
    color: #e5e7eb;
    width: 100%;
  }

  .encoder-fields input[type="text"]:hover,
  .encoder-fields input[type="number"]:hover,
  .encoder-fields select:hover {
    background: #4b5563;
  }

  .encoder-fields select {
    cursor: pointer;
  }
  
  .encoder-fields input:focus,
  .encoder-fields select:focus {
    outline: 2px solid var(--accent-primary);
    outline-offset: 1px;
  }
  
  input.error {
    border-color: #ef4444;
  }
  
  .error-inline {
    grid-column: 2;
    font-size: 0.75rem;
    color: #ef4444;
    margin-top: -0.5rem;
  }
  
  .section-heading {
    margin: 1rem 0 0.5rem 0;
    font-size: 0.95rem;
    color: #e5e7eb;
    font-weight: 600;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #374151;
  }

  input:disabled,
  select:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .empty-state {
    padding: 2rem;
    background: #0f172a;
    border-radius: 4px;
    text-align: center;
  }

  .empty-message {
    color: #e5e7eb;
    font-size: 0.95rem;
    line-height: 1.6;
    margin: 0 0 1rem 0;
  }

  .empty-message strong {
    display: block;
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    color: #f9fafb;
  }

  .empty-help {
    color: #9ca3af;
    font-size: 0.875rem;
    line-height: 1.5;
    margin: 0;
  }
</style>
