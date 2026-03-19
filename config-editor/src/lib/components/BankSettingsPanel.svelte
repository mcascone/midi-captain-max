<script lang="ts">
  import { config, updateField } from '$lib/formStore';
  import type { BankSwitchMethod } from '$lib/types';
  
  $: bankSwitch = $config.bank_switch ?? {
    method: 'button' as BankSwitchMethod,
    button: 10,
    channel: 0,
  };
  
  $: method = bankSwitch.method ?? 'button';
  $: button = bankSwitch.button ?? 10;
  $: buttonNext = bankSwitch.button_next;
  $: buttonPrev = bankSwitch.button_prev;
  $: cc = bankSwitch.cc ?? 64;
  $: pcBase = bankSwitch.pc_base ?? 0;
  $: channel = bankSwitch.channel ?? 0;
  
  // Determine mode: dual-button if both next/prev are set, otherwise single-button
  $: useDualButton = buttonNext !== undefined || buttonPrev !== undefined;
  
  // STD10 has 10 footswitches (buttons 1-10)
  // Mini6 has 6 switches
  $: deviceType = $config.device ?? 'std10';
  $: maxButton = deviceType === 'mini6' ? 6 : 10;
  
  function handleMethodChange(newMethod: BankSwitchMethod) {
    updateField('bank_switch.method', newMethod);
  }
  
  function handleButtonChange(value: string) {
    const num = parseInt(value, 10);
    if (!isNaN(num) && num >= 1 && num <= maxButton) {
      updateField('bank_switch.button', num);
    }
  }
  
  function handleButtonNextChange(value: string) {
    const num = parseInt(value, 10);
    if (!isNaN(num) && num >= 1 && num <= maxButton) {
      updateField('bank_switch.button_next', num);
    }
  }
  
  function handleButtonPrevChange(value: string) {
    const num = parseInt(value, 10);
    if (!isNaN(num) && num >= 1 && num <= maxButton) {
      updateField('bank_switch.button_prev', num);
    }
  }
  
  function toggleButtonMode() {
    const maxButton = $config.device === 'mini6' ? 6 : 10;
    if (useDualButton) {
      // Switch to single-button: clear next/prev, set button
      updateField('bank_switch.button_next', undefined);
      updateField('bank_switch.button_prev', undefined);
      updateField('bank_switch.button', maxButton);
    } else {
      // Switch to dual-button: set next/prev, clear button
      updateField('bank_switch.button_next', maxButton);
      updateField('bank_switch.button_prev', Math.max(1, maxButton - 1));
      updateField('bank_switch.button', undefined);
    }
  }
  
  function handleCCChange(value: string) {
    const num = parseInt(value, 10);
    if (!isNaN(num) && num >= 0 && num <= 127) {
      updateField('bank_switch.cc', num);
    }
  }
  
  function handlePCBaseChange(value: string) {
    const num = parseInt(value, 10);
    if (!isNaN(num) && num >= 0 && num <= 127) {
      updateField('bank_switch.pc_base', num);
    }
  }
  
  function handleChannelChange(value: string) {
    const num = parseInt(value, 10);
    if (!isNaN(num) && num >= 0 && num <= 15) {
      updateField('bank_switch.channel', num);
    }
  }
</script>

<div class="bank-settings-panel">
  <h3>Bank Switching</h3>
  
  <div class="form-group">
    <label for="bank-switch-method">Switch Method</label>
    <select
      id="bank-switch-method"
      value={method}
      on:change={(e) => handleMethodChange(e.currentTarget.value as BankSwitchMethod)}
    >
      <option value="button">Button Press</option>
      <option value="cc">MIDI CC</option>
      <option value="pc">MIDI PC</option>
    </select>
    <p class="help-text">
      {#if method === 'button'}
        Press one or two buttons to navigate banks
      {:else if method === 'cc'}
        CC value maps directly to bank index (0 → Bank 1, 1 → Bank 2, etc.)
      {:else if method === 'pc'}
        PC number maps to bank (PC {pcBase} → Bank 1, PC {pcBase + 1} → Bank 2, etc.)
      {/if}
    </p>
  </div>
  
  {#if method === 'button'}
    <div class="form-group">
      <label>Button Mode</label>
      <button type="button" class="mode-toggle-btn" on:click={toggleButtonMode}>
        {useDualButton ? 'Switch to Single Button (Cycle)' : 'Switch to Two Buttons (Up/Down)'}
      </button>
      <p class="help-text">
        {#if useDualButton}
          Use two buttons: one for next bank, one for previous bank
        {:else}
          Use one button to cycle through banks (wraps around)
        {/if}
      </p>
    </div>
    
    {#if useDualButton}
      <div class="button-group">
        <div class="form-group">
          <label for="bank-switch-next">Bank Up Button</label>
          <input
            type="number"
            id="bank-switch-next"
            min="1"
            max={maxButton}
            value={buttonNext ?? 10}
            on:input={(e) => handleButtonNextChange(e.currentTarget.value)}
          />
          <p class="help-text">Button for next bank (1-{maxButton})</p>
        </div>
        
        <div class="form-group">
          <label for="bank-switch-prev">Bank Down Button</label>
          <input
            type="number"
            id="bank-switch-prev"
            min="1"
            max={maxButton}
            value={buttonPrev ?? 11}
            on:input={(e) => handleButtonPrevChange(e.currentTarget.value)}
          />
          <p class="help-text">Button for previous bank (1-{maxButton})</p>
        </div>
      </div>
      
    {:else}
      <div class="form-group">
        <label for="bank-switch-button">Button Number</label>
        <input
          type="number"
          id="bank-switch-button"
          min="1"
          max={maxButton}
          value={button}
          on:input={(e) => handleButtonChange(e.currentTarget.value)}
        />
        <p class="help-text">
          Button to press for cycling through banks (1-{maxButton})
        </p>
      </div>
    {/if}
  {/if}
  
  {#if method === 'cc'}
    <div class="form-group">
      <label for="bank-switch-cc">CC Number</label>
      <input
        type="number"
        id="bank-switch-cc"
        min="0"
        max="127"
        value={cc}
        on:input={(e) => handleCCChange(e.currentTarget.value)}
      />
      <p class="help-text">MIDI CC number for bank switching (0-127)</p>
    </div>
  {/if}
  
  {#if method === 'pc'}
    <div class="form-group">
      <label for="bank-switch-pc-base">Base PC Number</label>
      <input
        type="number"
        id="bank-switch-pc-base"
        min="0"
        max="127"
        value={pcBase}
        on:input={(e) => handlePCBaseChange(e.currentTarget.value)}
      />
      <p class="help-text">
        Starting PC number (0-127)<br>
        Bank 1 = PC {pcBase}, Bank 2 = PC {pcBase + 1}, etc.
      </p>
    </div>
  {/if}
  
  {#if method === 'cc' || method === 'pc'}
    <div class="form-group">
      <label for="bank-switch-channel">MIDI Channel</label>
      <input
        type="number"
        id="bank-switch-channel"
        min="0"
        max="15"
        value={channel}
        on:input={(e) => handleChannelChange(e.currentTarget.value)}
      />
      <p class="help-text">MIDI channel for bank switching (0-15, display as 1-16)</p>
    </div>
  {/if}
  
  <div class="info-box">
    <svg class="info-icon" width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="8" cy="8" r="7" stroke="currentColor" stroke-width="1.5"/>
      <path d="M8 7v4M8 5h.01" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    </svg>
    <div>
      <strong>How Bank Switching Works:</strong>
      <ul>
        <li><strong>Single Button:</strong> Press to cycle forward through banks (wraps around)</li>
        <li><strong>Two Buttons:</strong> One for next bank, one for previous bank</li>
        <li><strong>CC:</strong> Send CC with value = target bank index (0-based)</li>
        <li><strong>PC:</strong> Send PC = (base + bank index) to switch</li>
      </ul>
    </div>
  </div>
</div>

<style>
  .bank-settings-panel {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  h3 {
    margin: 0;
    font-size: 1.125rem;
    font-weight: 600;
    color: var(--color-text, #1f2937);
  }
  
  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .button-group {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
  
  label {
    font-size: 0.875rem;
    font-weight: 500;
    color: var(--color-text, #1f2937);
  }
  
  select,
  input[type="number"] {
    padding: 0.5rem 0.75rem;
    border: 1px solid var(--color-border, #e5e7eb);
    border-radius: 0.375rem;
    font-size: 0.875rem;
    background: white;
    transition: border-color 0.15s ease;
  }
  
  select:focus,
  input[type="number"]:focus {
    outline: none;
    border-color: var(--color-primary, #3b82f6);
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
  }
  
  .mode-toggle-btn {
    padding: 0.5rem 1rem;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    font-weight: 500;
    cursor: pointer;
    transition: background 0.15s ease;
  }
  
  .mode-toggle-btn:hover {
    background: #2563eb;
  }
  
  .mode-toggle-btn:active {
    background: #1d4ed8;
  }
  
  .help-text {
    margin: 0;
    font-size: 0.75rem;
    color: var(--color-text-secondary, #6b7280);
    line-height: 1.5;
  }
  
  .help-text strong {
    color: var(--color-text, #1f2937);
  }
  
  .help-text.note {
    padding: 0.5rem;
    background: #fef3c7;
    border: 1px solid #fcd34d;
    border-radius: 0.25rem;
    color: #92400e;
  }
  
  .info-box {
    display: flex;
    gap: 0.75rem;
    padding: 1rem;
    background: #eff6ff;
    border: 1px solid #bfdbfe;
    border-radius: 0.375rem;
    font-size: 0.875rem;
    line-height: 1.5;
  }
  
  .info-icon {
    flex-shrink: 0;
    color: #3b82f6;
    margin-top: 0.125rem;
  }
  
  .info-box strong {
    display: block;
    margin-bottom: 0.5rem;
    color: var(--color-text, #1f2937);
  }
  
  .info-box ul {
    margin: 0;
    padding-left: 1.25rem;
    color: var(--color-text-secondary, #6b7280);
  }
  
  .info-box li {
    margin-bottom: 0.25rem;
  }
</style>
