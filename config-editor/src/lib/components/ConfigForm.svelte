<script lang="ts">
  import { onMount, type Snippet } from 'svelte';
  import { Dialog, Portal } from '@skeletonlabs/skeleton-svelte';
  import { isDirty, canUndo, canRedo, undo, redo, validationErrors, config } from '$lib/formStore';
  
  interface Props {
    onSave: () => void;
    children: Snippet;
  }
  
  let { onSave, children }: Props = $props();
  
  let hasErrors = $derived($validationErrors.size > 0);
  let showJsonModal = $state(false);
  let jsonText = $state('');
  let showErrorPanel = $state(true);

  // Get array of error entries for display
  let errorList = $derived(Array.from($validationErrors.entries()));

  // Show error panel when errors appear
  $effect(() => {
    if (hasErrors) {
      showErrorPanel = true;
    }
  });

  function handleUndo() {
    undo();
  }

  function handleRedo() {
    redo();
  }

  function handleViewJson() {
    jsonText = JSON.stringify($config, null, 2);
    showJsonModal = true;
  }
  
  function closeJsonModal() {
    showJsonModal = false;
  }
  
  function copyJsonToClipboard() {
    navigator.clipboard.writeText(jsonText);
  }

  function handleSave() {
    onSave();
  }

  // Keyboard shortcuts
  function handleKeydown(event: KeyboardEvent) {
    const isCmd = event.metaKey || event.ctrlKey;
    
    if (isCmd && event.key === 'z') {
      event.preventDefault();
      if (event.shiftKey && $canRedo) {
        handleRedo();
      } else if ($canUndo) {
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
        disabled={!$canUndo}
        onclick={handleUndo}
        title="Undo (⌘Z)"
      >
        Undo
      </button>
      <button
        class="toolbar-btn"
        disabled={!$canRedo}
        onclick={handleRedo}
        title="Redo (⌘⇧Z)"
      >
        Redo
      </button>
    </div>

    <div class="toolbar-group">
      <button class="toolbar-btn secondary" onclick={handleViewJson}>
        View JSON
      </button>
      <button
        class="toolbar-btn primary"
        disabled={hasErrors}
        onclick={handleSave}
        title="Save (⌘S)"
      >
        {hasErrors ? 'Fix errors to save' : $isDirty ? 'Save to Device *' : 'Save to Device'}
      </button>
    </div>
  </div>

  <!-- Validation Errors Panel -->
  {#if hasErrors && showErrorPanel}
    <div class="error-panel">
      <div class="error-header">
        <div class="error-title">
          <span class="error-icon">⚠️</span>
          <strong>{$validationErrors.size} validation {$validationErrors.size === 1 ? 'error' : 'errors'}</strong>
        </div>
        <button class="error-close" onclick={() => showErrorPanel = false} title="Dismiss">✕</button>
      </div>
      <div class="error-list">
        {#each errorList.slice(0, 10) as [field, message]}
          <div class="error-item">
            <code class="error-field">{field}</code>
            <span class="error-message">{message}</span>
          </div>
        {/each}
        {#if errorList.length > 10}
          <div class="error-item error-more">
            ... and {errorList.length - 10} more {errorList.length - 10 === 1 ? 'error' : 'errors'}
          </div>
        {/if}
      </div>
    </div>
  {/if}

  <!-- Form sections -->
  <div class="form-sections">
    {@render children()}
  </div>
</div>

<!-- JSON Modal -->
<Dialog open={showJsonModal} onOpenChange={(details) => showJsonModal = details.open}>
  <Portal>
    <Dialog.Backdrop class="modal-backdrop" />
    <Dialog.Positioner class="modal-positioner">
      <Dialog.Content class="modal-content">
        <Dialog.Title class="modal-title">Current Configuration (JSON)</Dialog.Title>
        
        <div class="modal-body">
          <pre class="json-display">{jsonText}</pre>
        </div>
        
        <div class="modal-footer">
          <button class="toolbar-btn secondary" onclick={copyJsonToClipboard}>Copy to Clipboard</button>
          <Dialog.CloseTrigger class="toolbar-btn">Close</Dialog.CloseTrigger>
        </div>
      </Dialog.Content>
    </Dialog.Positioner>
  </Portal>
</Dialog>

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

  /* JSON Modal */
  :global(.modal-backdrop) {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.6) !important;
    z-index: 1000;
  }

  :global(.modal-positioner) {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1001;
  }

  :global(.modal-content) {
    background-color: var(--color-bg);
    border-radius: 8px;
    width: 90%;
    max-width: 800px;
    max-height: 80vh;
    display: flex;
    flex-direction: column;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
    border: 1px solid var(--color-border);
  }

  :global(.modal-title) {
    padding: 16px 20px;
    border-bottom: 1px solid var(--color-border);
    margin: 0;
    font-size: 18px;
    font-weight: 600;
  }

  .modal-body {
    flex: 1;
    overflow: auto;
    padding: 20px;
  }

  .json-display {
    background-color: var(--color-bg-secondary);
    border: 1px solid var(--color-border);
    border-radius: 4px;
    padding: 16px;
    font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
    font-size: 13px;
    line-height: 1.5;
    overflow-x: auto;
    margin: 0;
    white-space: pre;
    color: var(--color-text);
  }

  .modal-footer {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    padding: 16px 20px;
    border-top: 1px solid var(--color-border);
  }

  /* Error Panel */
  .error-panel {
    background-color: #3a1f1f;
    border: 1px solid #8b3a3a;
    border-left: 4px solid #d32f2f;
    border-radius: 4px;
    margin: 12px 16px;
    overflow: hidden;
  }

  .error-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 10px 12px;
    background-color: rgba(211, 47, 47, 0.1);
    border-bottom: 1px solid #8b3a3a;
  }

  .error-title {
    display: flex;
    align-items: center;
    gap: 8px;
    color: #ff6b6b;
    font-size: 14px;
  }

  .error-icon {
    font-size: 16px;
  }

  .error-close {
    background: none;
    border: none;
    color: #999;
    cursor: pointer;
    padding: 4px 8px;
    font-size: 18px;
    line-height: 1;
    opacity: 0.7;
    transition: opacity 0.2s;
  }

  .error-close:hover {
    opacity: 1;
    color: #ccc;
  }

  .error-list {
    max-height: 200px;
    overflow-y: auto;
    padding: 8px 12px;
  }

  .error-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 8px;
    margin-bottom: 6px;
    background-color: rgba(0, 0, 0, 0.2);
    border-radius: 3px;
    font-size: 13px;
  }

  .error-item:last-child {
    margin-bottom: 0;
  }

  .error-field {
    font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
    font-size: 12px;
    color: #ff9999;
    background-color: rgba(0, 0, 0, 0.3);
    padding: 2px 6px;
    border-radius: 3px;
    align-self: flex-start;
  }

  .error-message {
    color: #ffcccc;
    padding-left: 2px;
  }

  .error-more {
    text-align: center;
    color: #999;
    font-style: italic;
    background-color: transparent;
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
