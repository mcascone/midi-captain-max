<script lang="ts">
  import type { MidiCommand, MessageType } from '$lib/types';
  
  interface Props {
    eventLabel: string;  // "Press", "Release", "Long Press", "Long Release"
    commands: MidiCommand[];
    globalChannel?: number;
    onUpdate: (commands: MidiCommand[]) => void;
  }
  
  let { eventLabel, commands = [], globalChannel = 0, onUpdate }: Props = $props();
  
  function addCommand() {
    onUpdate([...commands, { type: 'cc', cc: 20, value: 127, channel: globalChannel }]);
  }
  
  function removeCommand(index: number) {
    onUpdate(commands.filter((_, i) => i !== index));
  }
  
  function updateCommand(index: number, field: string, value: any) {
    const updated = [...commands];
    updated[index] = { ...updated[index], [field]: value };
    onUpdate(updated);
  }
  
  function numVal(e: Event): number | undefined {
    const v = (e.target as HTMLInputElement).value;
    return v === '' ? undefined : parseInt(v);
  }
</script>

<div class="commands-editor">
  <div class="editor-header">
    <span class="event-label">{eventLabel}</span>
    <button class="add-btn" type="button" onclick={addCommand}>
      <span class="add-icon">+</span>
      Add Command
    </button>
  </div>
  
  {#if commands.length === 0}
    <div class="empty-commands">
      No commands. Click "Add Command" to create one.
    </div>
  {:else}
    <div class="commands-list">
      {#each commands as cmd, i}
        <div class="command-row">
          <span class="command-number">{i + 1}</span>
          
          <div class="command-fields">
            <div class="field">
              <label>Type</label>
              <select value={cmd.type ?? 'cc'} onchange={(e) => updateCommand(i, 'type', (e.target as HTMLSelectElement).value as MessageType)}>
                <option value="cc">CC</option>
                <option value="note">Note</option>
                <option value="pc">PC</option>
                <option value="pc_inc">PC+</option>
                <option value="pc_dec">PC-</option>
              </select>
            </div>
            
            {#if (cmd.type ?? 'cc') === 'cc'}
              <div class="field">
                <label>CC#</label>
                <input type="number" min="0" max="127"
                  value={cmd.cc ?? ''} placeholder="20"
                  onblur={(e) => updateCommand(i, 'cc', numVal(e))} />
              </div>
              <div class="field">
                <label>Value</label>
                <input type="number" min="0" max="127"
                  value={cmd.value ?? ''} placeholder="127"
                  onblur={(e) => updateCommand(i, 'value', numVal(e))} />
              </div>
            {:else if (cmd.type ?? 'cc') === 'note'}
              <div class="field">
                <label>Note</label>
                <input type="number" min="0" max="127"
                  value={cmd.note ?? ''} placeholder="60"
                  onblur={(e) => updateCommand(i, 'note', numVal(e))} />
              </div>
              <div class="field">
                <label>Velocity</label>
                <input type="number" min="0" max="127"
                  value={cmd.velocity ?? ''} placeholder="127"
                  onblur={(e) => updateCommand(i, 'velocity', numVal(e))} />
              </div>
            {:else if (cmd.type ?? 'cc') === 'pc'}
              <div class="field">
                <label>Program</label>
                <input type="number" min="0" max="127"
                  value={cmd.program ?? ''} placeholder="0"
                  onblur={(e) => updateCommand(i, 'program', numVal(e))} />
              </div>
            {:else if (cmd.type ?? 'cc') === 'pc_inc' || (cmd.type ?? 'cc') === 'pc_dec'}
              <div class="field">
                <label>Step</label>
                <input type="number" min="1" max="127"
                  value={cmd.pc_step ?? ''} placeholder="1"
                  onblur={(e) => updateCommand(i, 'pc_step', numVal(e))} />
              </div>
            {/if}
            
            <div class="field narrow">
              <label>Ch</label>
              <input type="number" min="1" max="16"
                value={(cmd.channel ?? globalChannel) + 1}
                onblur={(e) => {
                  const v = numVal(e);
                  updateCommand(i, 'channel', v !== undefined ? v - 1 : globalChannel);
                }} />
            </div>
            
            {#if eventLabel === 'Long Press'}
              <div class="field">
                <label>Threshold (ms)</label>
                <input type="number" min="50" max="10000"
                  value={cmd.threshold_ms ?? ''} placeholder="600"
                  onblur={(e) => updateCommand(i, 'threshold_ms', numVal(e))} />
              </div>
            {/if}
          </div>
          
          <button class="remove-btn" type="button" onclick={() => removeCommand(i)} title="Remove command">
            ✕
          </button>
        </div>
      {/each}
    </div>
  {/if}
</div>

<style>
  .commands-editor {
    margin-top: 12px;
  }
  
  .editor-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 10px;
  }
  
  .event-label {
    font-size: 12px;
    font-weight: 600;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  
  .add-btn {
    background: #1f1f35;
    border: 1px solid #3a3a55;
    border-radius: 6px;
    color: #9ca3af;
    font-size: 12px;
    font-weight: 500;
    padding: 5px 10px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 4px;
    transition: all 0.15s;
  }
  
  .add-btn:hover {
    background: #2a2a3e;
    color: #e5e7eb;
    border-color: #4a4a5e;
  }
  
  .add-icon {
    font-size: 14px;
    font-weight: 600;
  }
  
  .empty-commands {
    padding: 20px;
    text-align: center;
    color: #6b7280;
    font-size: 12px;
    background: #1a1a2e;
    border: 1px dashed #2a2a3e;
    border-radius: 6px;
  }
  
  .commands-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .command-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px;
    background: #1a1a2e;
    border: 1px solid #2a2a3e;
    border-radius: 6px;
    transition: border-color 0.15s;
  }
  
  .command-row:hover {
    border-color: #3a3a4e;
  }
  
  .command-number {
    font-size: 11px;
    font-weight: 700;
    color: #6b7280;
    min-width: 18px;
  }
  
  .command-fields {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    flex: 1;
  }
  
  .field {
    display: flex;
    flex-direction: column;
    gap: 4px;
    flex: 1;
    min-width: 90px;
  }
  
  .field.narrow {
    flex: 0 0 auto;
    min-width: 60px;
  }
  
  label {
    font-size: 10px;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    white-space: nowrap;
  }
  
  input[type="number"],
  select {
    padding: 7px 10px;
    background: #13131f;
    border: 1px solid #2a2a3e;
    border-radius: 4px;
    color: #e5e7eb;
    font-size: 13px;
    width: 100%;
    min-width: 0;
    height: 36px;
    line-height: 1.4;
    transition: border-color 0.15s;
  }
  
  input:focus, select:focus {
    outline: none;
    border-color: #6366f1;
  }
  
  .remove-btn {
    background: transparent;
    border: none;
    color: #6b7280;
    font-size: 16px;
    cursor: pointer;
    padding: 4px 8px;
    line-height: 1;
    border-radius: 4px;
    transition: all 0.15s;
    flex-shrink: 0;
  }
  
  .remove-btn:hover {
    background: #ef4444;
    color: #fff;
  }
</style>
