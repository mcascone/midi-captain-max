<script lang="ts">
  import type { Condition, ConditionOperator } from '$lib/types';
  import { config, activeBank, isMultiBankMode } from '$lib/formStore';
  
  interface Props {
    condition: Condition;
    onUpdate: (condition: Condition) => void;
    buttonIndex?: number; // Current button index (to prevent self-reference)
  }
  
  let { condition, onUpdate, buttonIndex }: Props = $props();
  
  // Get button labels for dropdown (exclude current button if provided)
  // Use activeBank buttons if multi-bank mode, otherwise use top-level buttons
  let buttonLabels = $derived(
    ($isMultiBankMode && $activeBank 
      ? $activeBank.buttons 
      : $config.buttons ?? [])
      .map((btn, i) => ({ 
        index: i, 
        label: btn.label || `Button ${i + 1}` 
      }))
      .filter((btn) => buttonIndex === undefined || btn.index !== buttonIndex)
  );
  
  // Current condition type
  let conditionType = $state(condition.type);
  
  // Update parent when condition type changes
  function handleTypeChange(newType: string) {
    conditionType = newType as any;
    
    // Reset to default condition of selected type
    if (newType === 'button_state') {
      onUpdate({ type: 'button_state', button: 0, state: 'on' });
    } else if (newType === 'button_keytime') {
      onUpdate({ type: 'button_keytime', button: 0, keytime: 0 });
    } else if (newType === 'received_midi') {
      onUpdate({ type: 'received_midi', cc: 20, channel: 0, operator: '==', value: 127 });
    } else if (newType === 'expression') {
      onUpdate({ type: 'expression', pedal: 'exp1', operator: '>', value: 64 });
    } else if (newType === 'encoder') {
      onUpdate({ type: 'encoder', operator: '>', value: 64 });
    }
  }
  
  function updateField(field: string, value: any) {
    onUpdate({ ...condition, [field]: value });
  }
</script>

<div class="condition-builder">
  <div class="field">
    <label>Condition Type</label>
    <select value={conditionType} onchange={(e) => handleTypeChange((e.target as HTMLSelectElement).value)}>
      <option value="button_state">Button State</option>
      <option value="button_keytime">Button Keytime</option>
      <option value="received_midi">Received MIDI Value</option>
      <option value="expression">Expression Pedal</option>
      <option value="encoder">Encoder Value</option>
    </select>
  </div>
  
  {#if condition.type === 'button_state'}
    <div class="field">
      <label>Button</label>
      <select value={condition.button} onchange={(e) => updateField('button', parseInt((e.target as HTMLSelectElement).value))}>
        {#each buttonLabels as btn}
          <option value={btn.index}>{btn.label}</option>
        {/each}
      </select>
    </div>
    <div class="field">
      <label>State</label>
      <select value={condition.state} onchange={(e) => updateField('state', (e.target as HTMLSelectElement).value)}>
        <option value="on">ON</option>
        <option value="off">OFF</option>
      </select>
    </div>
  {:else if condition.type === 'button_keytime'}
    <div class="field">
      <label>Button</label>
      <select value={condition.button} onchange={(e) => updateField('button', parseInt((e.target as HTMLSelectElement).value))}>
        {#each buttonLabels as btn}
          <option value={btn.index}>{btn.label}</option>
        {/each}
      </select>
    </div>
    <div class="field">
      <label>Keytime</label>
      <input type="number" min="0" max="98" value={condition.keytime}
        onchange={(e) => updateField('keytime', parseInt((e.target as HTMLInputElement).value))} />
    </div>
  {:else if condition.type === 'received_midi'}
    <div class="field">
      <label>CC Number</label>
      <input type="number" min="0" max="127" value={condition.cc}
        onchange={(e) => updateField('cc', parseInt((e.target as HTMLInputElement).value))} />
    </div>
    <div class="field">
      <label>Channel</label>
      <input type="number" min="1" max="16" value={condition.channel + 1}
        onchange={(e) => updateField('channel', parseInt((e.target as HTMLInputElement).value) - 1)} />
    </div>
    <div class="field">
      <label>Operator</label>
      <select value={condition.operator} onchange={(e) => updateField('operator', (e.target as HTMLSelectElement).value as ConditionOperator)}>
        <option value="==">= (equals)</option>
        <option value="!=">≠ (not equal)</option>
        <option value=">">{'>'} (greater than)</option>
        <option value="<">{'<'} (less than)</option>
        <option value=">=">&ge; (greater or equal)</option>
        <option value="<=">&le; (less or equal)</option>
      </select>
    </div>
    <div class="field">
      <label>Value</label>
      <input type="number" min="0" max="127" value={condition.value}
        onchange={(e) => updateField('value', parseInt((e.target as HTMLInputElement).value))} />
    </div>
  {:else if condition.type === 'expression'}
    <div class="field">
      <label>Pedal</label>
      <select value={condition.pedal} onchange={(e) => updateField('pedal', (e.target as HTMLSelectElement).value)}>
        <option value="exp1">Expression 1</option>
        <option value="exp2">Expression 2</option>
      </select>
    </div>
    <div class="field">
      <label>Operator</label>
      <select value={condition.operator} onchange={(e) => updateField('operator', (e.target as HTMLSelectElement).value as ConditionOperator)}>
        <option value="==">= (equals)</option>
        <option value="!=">≠ (not equal)</option>
        <option value=">">{'>'} (greater than)</option>
        <option value="<">{'<'} (less than)</option>
        <option value=">=">&ge; (greater or equal)</option>
        <option value="<=">&le; (less or equal)</option>
      </select>
    </div>
    <div class="field">
      <label>Value</label>
      <input type="number" min="0" max="127" value={condition.value}
        onchange={(e) => updateField('value', parseInt((e.target as HTMLInputElement).value))} />
    </div>
  {:else if condition.type === 'encoder'}
    <div class="field">
      <label>Operator</label>
      <select value={condition.operator} onchange={(e) => updateField('operator', (e.target as HTMLSelectElement).value as ConditionOperator)}>
        <option value="==">= (equals)</option>
        <option value="!=">≠ (not equal)</option>
        <option value=">">{'>'} (greater than)</option>
        <option value="<">{'<'} (less than)</option>
        <option value=">=">&ge; (greater or equal)</option>
        <option value="<=">&le; (less or equal)</option>
      </select>
    </div>
    <div class="field">
      <label>Value</label>
      <input type="number" min="0" max="127" value={condition.value}
        onchange={(e) => updateField('value', parseInt((e.target as HTMLInputElement).value))} />
    </div>
  {/if}
</div>

<style>
  .condition-builder {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 12px;
    padding: 12px;
    background: #2a2745;
    border-radius: 6px;
    border: 1px solid #3a3a55;
  }
  
  .field {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  .field label {
    font-size: 12px;
    font-weight: 500;
    color: #9ca3af;
  }
  
  .field select,
  .field input {
    width: 100%;
    padding: 6px 8px;
    border: 1px solid #3a3a55;
    border-radius: 4px;
    font-size: 14px;
    background: #1f1f35;
    color: #e5e7eb;
  }
  
  .field select:focus,
  .field input:focus {
    outline: none;
    border-color: #6366f1;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
  }
</style>
