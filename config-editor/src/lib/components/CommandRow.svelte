<script lang="ts">
  import type { CommandOrConditional, MidiCommand, MessageType } from '$lib/types';
  import ConditionalCommandBlock from './ConditionalCommandBlock.svelte';
  
  interface Props {
    command: CommandOrConditional;
    index: number;
    globalChannel: number;
    onUpdate: (cmd: CommandOrConditional) => void;
    onRemove: () => void;
    buttonIndex?: number;
  }
  
  let { command, index, globalChannel, onUpdate, onRemove, buttonIndex }: Props = $props();
  
  // Check if this is a conditional command
  let isConditional = $derived(
    typeof command === 'object' && 
    'type' in command && 
    command.type === 'conditional'
  );
  
  function updateMidiField(field: string, value: any) {
    if (!isConditional) {
      onUpdate({ ...command as MidiCommand, [field]: value });
    }
  }
  
  function numVal(e: Event): number | undefined {
    const v = (e.target as HTMLInputElement).value;
    return v === '' ? undefined : parseInt(v);
  }
</script>

{#if isConditional}
  <!-- Recursive: Conditional command -->
  <ConditionalCommandBlock
    conditional={command as any}
    globalChannel={globalChannel}
    onUpdate={onUpdate}
    onRemove={onRemove}
    buttonIndex={buttonIndex}
  />
{:else}
  <!-- Base case: Regular MIDI command -->
  <div class="command-row">
    <span class="command-number">{index + 1}</span>
    
    <div class="command-fields">
      <div class="field">
        <label>Type</label>
        <select value={(command as MidiCommand).type ?? 'cc'} onchange={(e) => updateMidiField('type', (e.target as HTMLSelectElement).value as MessageType)}>
          <option value="cc">CC</option>
          <option value="note">Note</option>
          <option value="pc">PC</option>
          <option value="pc_inc">PC+</option>
          <option value="pc_dec">PC-</option>
        </select>
      </div>
      
      {#if ((command as MidiCommand).type ?? 'cc') === 'cc'}
        <div class="field">
          <label>CC#</label>
          <input type="number" min="0" max="127"
            value={(command as MidiCommand).cc ?? ''} placeholder="20"
            onblur={(e) => updateMidiField('cc', numVal(e))} />
        </div>
        <div class="field">
          <label>Value</label>
          <input type="number" min="0" max="127"
            value={(command as MidiCommand).value ?? ''} placeholder="127"
            onblur={(e) => updateMidiField('value', numVal(e))} />
        </div>
      {:else if ((command as MidiCommand).type ?? 'cc') === 'note'}
        <div class="field">
          <label>Note</label>
          <input type="number" min="0" max="127"
            value={(command as MidiCommand).note ?? ''} placeholder="60"
            onblur={(e) => updateMidiField('note', numVal(e))} />
        </div>
        <div class="field">
          <label>Velocity</label>
          <input type="number" min="0" max="127"
            value={(command as MidiCommand).velocity ?? ''} placeholder="127"
            onblur={(e) => updateMidiField('velocity', numVal(e))} />
        </div>
      {:else if ((command as MidiCommand).type ?? 'cc') === 'pc'}
        <div class="field">
          <label>Program</label>
          <input type="number" min="0" max="127"
            value={(command as MidiCommand).program ?? ''} placeholder="0"
            onblur={(e) => updateMidiField('program', numVal(e))} />
        </div>
      {:else if ((command as MidiCommand).type ?? 'cc') === 'pc_inc' || ((command as MidiCommand).type ?? 'cc') === 'pc_dec'}
        <div class="field">
          <label>Step</label>
          <input type="number" min="1" max="127"
            value={(command as MidiCommand).pc_step ?? ''} placeholder="1"
            onblur={(e) => updateMidiField('pc_step', numVal(e))} />
        </div>
      {/if}
      
      <div class="field">
        <label>Channel</label>
        <input type="number" min="1" max="16"
          value={(command as MidiCommand).channel !== undefined ? (command as MidiCommand).channel! + 1 : ''}
          placeholder={`${globalChannel + 1}`}
          onblur={(e) => {
            const val = numVal(e);
            updateMidiField('channel', val !== undefined ? val - 1 : undefined);
          }} />
      </div>
    </div>
    
    <button class="remove-btn" type="button" onclick={onRemove} title="Remove command">×</button>
  </div>
{/if}

<style>
  .command-row {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    background: #2a2a3e;
    border: 1px solid #3a3a55;
    border-radius: 6px;
  }
  
  .command-number {
    font-weight: 600;
    color: #9ca3af;
    min-width: 20px;
    text-align: center;
  }
  
  .command-fields {
    flex: 1;
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
    gap: 8px;
  }
  
  .field {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  
  .field label {
    font-size: 11px;
    font-weight: 500;
    color: #9ca3af;
  }
  
  .field select,
  .field input {
    width: 100%;
    padding: 6px 8px;
    border: 1px solid #3a3a55;
    border-radius: 4px;
    font-size: 13px;
    background: #1f1f35;
    color: #e5e7eb;
  }
  
  .field select:focus,
  .field input:focus {
    outline: none;
    border-color: #6366f1;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
  }
  
  .remove-btn {
    background: #ef4444;
    color: white;
    border: none;
    border-radius: 4px;
    width: 28px;
    height: 28px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 20px;
    line-height: 1;
    flex-shrink: 0;
  }
  
  .remove-btn:hover {
    background: #dc2626;
  }
</style>
