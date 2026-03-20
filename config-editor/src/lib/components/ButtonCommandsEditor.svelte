<script lang="ts">
  import type { CommandOrConditional } from '$lib/types';
  import CommandRow from './CommandRow.svelte';
  
  interface Props {
    eventLabel: string;  // "Press", "Release", "Long Press", "Long Release"
    commands: CommandOrConditional[];
    globalChannel?: number;
    onUpdate: (commands: CommandOrConditional[]) => void;
    buttonIndex?: number; // For conditional validation (prevent self-reference)
  }
  
  let { eventLabel, commands = [], globalChannel = 0, onUpdate, buttonIndex }: Props = $props();
  
  function addCommand() {
    onUpdate([...commands, { type: 'cc', cc: 20, value: 127, channel: globalChannel }]);
  }
  
  function addConditional() {
    onUpdate([...commands, {
      type: 'conditional',
      command_type: 'conditional',
      if: { type: 'button_state', button: 0, state: 'on' },
      then: [{ type: 'cc', cc: 20, value: 127 }],
      else: [{ type: 'cc', cc: 20, value: 0 }]
    }]);
  }
  
  function removeCommand(index: number) {
    onUpdate(commands.filter((_, i) => i !== index));
  }
  
  function updateCommand(index: number, cmd: CommandOrConditional) {
    const updated = [...commands];
    updated[index] = cmd;
    onUpdate(updated);
  }
</script>

<div class="commands-editor">
  <div class="editor-header">
    <span class="event-label">{eventLabel}</span>
    <div class="header-buttons">
      <button class="add-btn" type="button" onclick={addCommand}>
        <span class="add-icon">+</span>
        Add Command
      </button>
      <button class="add-conditional-btn" type="button" onclick={addConditional} title="Add conditional logic (if/then/else)">
        <span class="if-icon">↯</span>
        Add If/Then
      </button>
    </div>
  </div>
  
  {#if commands.length === 0}
    <div class="empty-commands">
      No commands. Click "Add Command" for MIDI or "Add If/Then" for conditional logic.
    </div>
  {:else}
    <div class="commands-list">
      {#each commands as cmd, i}
        <CommandRow
          command={cmd}
          index={i}
          globalChannel={globalChannel}
          onUpdate={(updated) => updateCommand(i, updated)}
          onRemove={() => removeCommand(i)}
          buttonIndex={buttonIndex}
        />
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
  
  .header-buttons {
    display: flex;
    gap: 8px;
  }
  
  .add-btn,
  .add-conditional-btn {
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
  
  .add-btn:hover,
  .add-conditional-btn:hover {
    background: #2a2a3e;
    color: #e5e7eb;
    border-color: #4a4a5e;
  }
  
  .add-conditional-btn {
    background: #312e81;
    border-color: #4338ca;
  }
  
  .add-conditional-btn:hover {
    background: #3730a3;
    border-color: #4f46e5;
  }
  
  .add-icon,
  .if-icon {
    font-size: 14px;
    font-weight: 600;
  }
  
  .if-icon {
    font-size: 16px;
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
</style>
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
