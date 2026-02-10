<script lang="ts">
  import { onMount } from 'svelte';

  // Placeholder toolbar actions (will be connected to formStore later)
  let canUndo = false;
  let canRedo = false;
  let hasErrors = false;
  let isDirty = false;

  function handleUndo() {
    console.log('Undo clicked');
    // TODO: Connect to formStore.undo()
  }

  function handleRedo() {
    console.log('Redo clicked');
    // TODO: Connect to formStore.redo()
  }

  function handleViewJson() {
    console.log('View JSON clicked');
    // TODO: Export config as JSON
  }

  function handleSave() {
    console.log('Save clicked');
    // TODO: Validate and save to device
  }

  // Keyboard shortcuts
  function handleKeydown(event: KeyboardEvent) {
    const isCmd = event.metaKey || event.ctrlKey;
    
    if (isCmd && event.key === 'z') {
      event.preventDefault();
      if (event.shiftKey) {
        handleRedo();
      } else {
        handleUndo();
      }
    } else if (isCmd && event.key === 's') {
      event.preventDefault();
      handleSave();
    }
  }

  onMount(() => {
    window.addEventListener('keydown', handleKeydown);
    return () => {
      window.removeEventListener('keydown', handleKeydown);
    };
  });

  // Accordion state (all expanded by default)
  let expandedSections = {
    device: true,
    buttons: true,
    encoder: true,
    expression: true,
    display: true,
  };

  function toggleSection(section: keyof typeof expandedSections) {
    expandedSections[section] = !expandedSections[section];
  }
</script>

<svelte:head>
  <title>Config Form Editor - MIDI Captain</title>
</svelte:head>

<div class="config-form">
  <!-- Toolbar -->
  <div class="toolbar">
    <div class="toolbar-group">
      <button
        class="toolbar-btn"
        disabled={!canUndo}
        on:click={handleUndo}
        title="Undo (⌘Z)"
      >
        Undo
      </button>
      <button
        class="toolbar-btn"
        disabled={!canRedo}
        on:click={handleRedo}
        title="Redo (⌘⇧Z)"
      >
        Redo
      </button>
    </div>

    <div class="toolbar-group">
      <button class="toolbar-btn secondary" on:click={handleViewJson}>
        View JSON
      </button>
      <button
        class="toolbar-btn primary"
        disabled={hasErrors}
        on:click={handleSave}
        title="Save (⌘S)"
      >
        {hasErrors ? 'Fix errors to save' : isDirty ? 'Save to Device *' : 'Save to Device'}
      </button>
    </div>
  </div>

  <!-- Form sections (accordion) -->
  <div class="form-sections">
    <!-- Device Settings -->
    <section class="form-section">
      <button
        class="section-header"
        class:expanded={expandedSections.device}
        on:click={() => toggleSection('device')}
      >
        <span class="expand-icon">{expandedSections.device ? '▼' : '▶'}</span>
        <span class="section-title">Device Settings</span>
      </button>
      {#if expandedSections.device}
        <div class="section-content">
          <p class="placeholder">Device section coming soon...</p>
        </div>
      {/if}
    </section>

    <!-- Buttons -->
    <section class="form-section">
      <button
        class="section-header"
        class:expanded={expandedSections.buttons}
        on:click={() => toggleSection('buttons')}
      >
        <span class="expand-icon">{expandedSections.buttons ? '▼' : '▶'}</span>
        <span class="section-title">Buttons</span>
      </button>
      {#if expandedSections.buttons}
        <div class="section-content">
          <p class="placeholder">Buttons section coming soon...</p>
        </div>
      {/if}
    </section>

    <!-- Encoder -->
    <section class="form-section">
      <button
        class="section-header"
        class:expanded={expandedSections.encoder}
        on:click={() => toggleSection('encoder')}
      >
        <span class="expand-icon">{expandedSections.encoder ? '▼' : '▶'}</span>
        <span class="section-title">Encoder</span>
      </button>
      {#if expandedSections.encoder}
        <div class="section-content">
          <p class="placeholder">Encoder section coming soon...</p>
        </div>
      {/if}
    </section>

    <!-- Expression Pedals -->
    <section class="form-section">
      <button
        class="section-header"
        class:expanded={expandedSections.expression}
        on:click={() => toggleSection('expression')}
      >
        <span class="expand-icon">{expandedSections.expression ? '▼' : '▶'}</span>
        <span class="section-title">Expression Pedals</span>
      </button>
      {#if expandedSections.expression}
        <div class="section-content">
          <p class="placeholder">Expression section coming soon...</p>
        </div>
      {/if}
    </section>

    <!-- Display -->
    <section class="form-section">
      <button
        class="section-header"
        class:expanded={expandedSections.display}
        on:click={() => toggleSection('display')}
      >
        <span class="expand-icon">{expandedSections.display ? '▼' : '▶'}</span>
        <span class="section-title">Display</span>
      </button>
      {#if expandedSections.display}
        <div class="section-content">
          <p class="placeholder">Display section coming soon...</p>
        </div>
      {/if}
    </section>
  </div>
</div>

<style>
  .config-form {
    display: flex;
    flex-direction: column;
    height: 100%;
    background-color: var(--color-bg);
  }

  /* Toolbar */
  .toolbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 16px;
    background-color: var(--color-bg-secondary);
    border-bottom: 1px solid var(--color-border);
    gap: 12px;
  }

  .toolbar-group {
    display: flex;
    gap: 8px;
  }

  .toolbar-btn {
    padding: 6px 12px;
    border-radius: 4px;
    border: 1px solid var(--color-border);
    background-color: var(--color-bg);
    color: var(--color-text);
    font-size: 14px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .toolbar-btn:hover:not(:disabled) {
    background-color: var(--color-bg-hover);
    border-color: var(--color-border-hover);
  }

  .toolbar-btn:active:not(:disabled) {
    transform: translateY(1px);
  }

  .toolbar-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .toolbar-btn.primary {
    background-color: var(--color-primary);
    color: white;
    border-color: var(--color-primary);
  }

  .toolbar-btn.primary:hover:not(:disabled) {
    background-color: var(--color-primary-hover);
    border-color: var(--color-primary-hover);
  }

  .toolbar-btn.secondary {
    background-color: transparent;
  }

  /* Form sections */
  .form-sections {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
  }

  .form-section {
    margin-bottom: 12px;
    border: 1px solid var(--color-border);
    border-radius: 6px;
    background-color: var(--color-bg-secondary);
    overflow: hidden;
  }

  .section-header {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px 16px;
    background-color: var(--color-bg-secondary);
    border: none;
    color: var(--color-text);
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background-color 0.15s ease;
  }

  .section-header:hover {
    background-color: var(--color-bg-hover);
  }

  .section-header.expanded {
    border-bottom: 1px solid var(--color-border);
  }

  .expand-icon {
    width: 16px;
    text-align: center;
    font-size: 12px;
    transition: transform 0.2s ease;
  }

  .section-title {
    flex: 1;
    text-align: left;
  }

  .section-content {
    padding: 16px;
    animation: slideDown 0.2s ease;
  }

  @keyframes slideDown {
    from {
      opacity: 0;
      transform: translateY(-8px);
    }
    to {
      opacity: 1;
      transform: translateY(0);
    }
  }

  .placeholder {
    color: var(--color-text-secondary);
    font-style: italic;
    margin: 0;
  }

  /* CSS Variables (will inherit from app theme) */
  :root {
    --color-bg: #1e1e1e;
    --color-bg-secondary: #252526;
    --color-bg-hover: #2a2d2e;
    --color-text: #cccccc;
    --color-text-secondary: #808080;
    --color-border: #3e3e42;
    --color-border-hover: #555555;
    --color-primary: #0e639c;
    --color-primary-hover: #1177bb;
  }
</style>
