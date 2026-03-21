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
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }
  
  .header-buttons {
    display: flex;
    gap: 8px;
  }
  
  .add-btn,
  .add-conditional-btn {
    background: var(--bg-input);
    border: 1px solid var(--border-default);
    border-radius: 6px;
    color: var(--text-secondary);
    font-size: 12px;
    font-weight: 500;
    padding: 6px 12px;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 4px;
    transition: all 0.15s;
  }
  
  .add-btn:hover,
  .add-conditional-btn:hover {
    background: var(--bg-card);
    color: var(--text-primary);
    border-color: var(--border-accent);
  }
  
  .add-conditional-btn {
    background: var(--accent-primary-dim);
    border-color: var(--accent-primary);
    color: var(--accent-primary);
  }
  
  .add-conditional-btn:hover {
    background: var(--accent-primary);
    color: var(--bg-dark);
    border-color: var(--accent-primary-hover);
  }
  
  .add-icon {
    font-size: 14px;
    font-weight: 600;
  }
  
  .empty-commands {
    padding: 20px;
    text-align: center;
    color: var(--text-tertiary);
    font-size: 12px;
    background: var(--bg-input);
    border: 1px dashed var(--border-default);
    border-radius: 6px;
  }
  
  .commands-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
</style>
