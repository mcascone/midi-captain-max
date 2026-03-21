<script lang="ts">
  import type { ConditionalCommand, CommandOrConditional, MidiCommand } from '$lib/types';
  import ConditionBuilder from './ConditionBuilder.svelte';
  import CommandRow from './CommandRow.svelte';
  
  interface Props {
    conditional: ConditionalCommand;
    globalChannel: number;
    onUpdate: (cmd: ConditionalCommand) => void;
    onRemove: () => void;
    buttonIndex?: number;
  }
  
  let { conditional, globalChannel, onUpdate, onRemove, buttonIndex }: Props = $props();
  
  function updateCondition(newCondition: any) {
    onUpdate({ ...conditional, if: newCondition });
  }
  
  function updateThen(commands: CommandOrConditional[]) {
    onUpdate({ ...conditional, then: commands });
  }
  
  function updateElse(commands: CommandOrConditional[]) {
    onUpdate({ ...conditional, else: commands.length > 0 ? commands : undefined });
  }
  
  function addThenCommand() {
    onUpdate({
      ...conditional,
      then: [...conditional.then, { type: 'cc', cc: 20, value: 127 }]
    });
  }
  
  function addElseCommand() {
    onUpdate({
      ...conditional,
      else: [...(conditional.else ?? []), { type: 'cc', cc: 20, value: 0 }]
    });
  }
  
  function removeThenCommand(idx: number) {
    updateThen(conditional.then.filter((_, i) => i !== idx));
  }
  
  function removeElseCommand(idx: number) {
    const filtered = (conditional.else ?? []).filter((_, i) => i !== idx);
    updateElse(filtered);
  }
  
  function updateThenCommand(idx: number, cmd: CommandOrConditional) {
    const newThen = [...conditional.then];
    newThen[idx] = cmd;
    updateThen(newThen);
  }
  
  function updateElseCommand(idx: number, cmd: CommandOrConditional) {
    const newElse = [...(conditional.else ?? [])];
    newElse[idx] = cmd;
    updateElse(newElse);
  }
</script>

<div class="conditional-block">
  <div class="condition-header">
    <span class="if-label">IF</span>
    <button class="remove-conditional" type="button" onclick={onRemove} title="Remove condition">
      ✕
    </button>
  </div>
  
  <ConditionBuilder 
    condition={conditional.if} 
    onUpdate={updateCondition}
    buttonIndex={buttonIndex}
  />
  
  <div class="branch-container then-branch">
    <div class="branch-header">
      <span class="branch-label">THEN</span>
      <button class="add-command-btn" type="button" onclick={addThenCommand}>+ Add</button>
    </div>
    <div class="branch-commands">
      {#if conditional.then.length === 0}
        <div class="empty-branch">No commands. Click "+ Add" to create one.</div>
      {:else}
        {#each conditional.then as cmd, i}
          <CommandRow 
            command={cmd} 
            index={i}
            globalChannel={globalChannel}
            onUpdate={(updated) => updateThenCommand(i, updated)}
            onRemove={() => removeThenCommand(i)}
          />
        {/each}
      {/if}
    </div>
  </div>
  
  <div class="branch-container else-branch">
    <div class="branch-header">
      <span class="branch-label">ELSE</span>
      <button class="add-command-btn" type="button" onclick={addElseCommand}>+ Add</button>
    </div>
    <div class="branch-commands">
      {#if !conditional.else || conditional.else.length === 0}
        <div class="empty-branch">No commands. Click "+ Add" to create one.</div>
      {:else}
        {#each conditional.else as cmd, i}
          <CommandRow 
            command={cmd} 
            index={i}
            globalChannel={globalChannel}
            onUpdate={(updated) => updateElseCommand(i, updated)}
            onRemove={() => removeElseCommand(i)}
          />
        {/each}
      {/if}
    </div>
  </div>
</div>

<style>
  .conditional-block {
    border: 2px solid #4f46e5;
    border-radius: 8px;
    padding: 16px;
    margin: 12px 0;
    background: #1e1b3a;
  }
  
  .condition-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  
  .if-label {
    font-weight: 700;
    color: #818cf8;
    font-size: 14px;
    letter-spacing: 0.5px;
  }
  
  .remove-conditional {
    background: #ef4444;
    color: white;
    border: none;
    border-radius: 4px;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    font-size: 16px;
    line-height: 1;
  }
  
  .remove-conditional:hover {
    background: #dc2626;
  }
  
  .branch-container {
    margin-top: 12px;
    padding: 12px;
    border-radius: 6px;
    border-left: 3px solid;
  }
  
  .then-branch {
    background: rgba(16, 185, 129, 0.08);
    border-left-color: #10b981;
  }
  
  .else-branch {
    background: rgba(239, 68, 68, 0.08);
    border-left-color: #ef4444;
  }
  
  .branch-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }
  
  .branch-label {
    font-weight: 600;
    font-size: 12px;
    letter-spacing: 0.5px;
  }
  
  .then-branch .branch-label {
    color: #34d399;
  }
  
  .else-branch .branch-label {
    color: #f87171;
  }
  
  .add-command-btn {
    background: #2a2a3e;
    border: 1px solid #3a3a55;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 12px;
    color: #9ca3af;
    cursor: pointer;
    transition: all 0.2s;
  }
  
  .add-command-btn:hover {
    background: #35354e;
    border-color: #4f46e5;
    color: #e5e7eb;
  }
  
  .branch-commands {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  
  .empty-branch {
    padding: 12px;
    text-align: center;
    color: #9ca3af;
    font-size: 13px;
    font-style: italic;
  }
</style>
