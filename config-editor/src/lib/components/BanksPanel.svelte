<script lang="ts">
  import { activeBankIndex, activeBank, bankCount, config, switchBank, addBank, duplicateBank, deleteBank, renameBank } from '$lib/formStore';
  
  let editingBankIndex: number | null = null;
  let editingValue = '';
  let showDeleteConfirm: number | null = null;
  
  // Get banks array for iteration
  $: banks = $config.banks ?? [];
  
  function handleTabClick(index: number) {
    switchBank(index);
  }
  
  function handleAddBank() {
    addBank();
  }
  
  function handleDuplicateBank(index: number) {
    duplicateBank(index);
  }
  
  function startRename(index: number, currentName: string) {
    editingBankIndex = index;
    editingValue = currentName;
  }
  
  function finishRename() {
    if (editingBankIndex !== null && editingValue.trim()) {
      renameBank(editingBankIndex, editingValue.trim());
    }
    editingBankIndex = null;
  }
  
  function cancelRename() {
    editingBankIndex = null;
  }
  
  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      finishRename();
    } else if (e.key === 'Escape') {
      cancelRename();
    }
  }
  
  function confirmDelete(index: number) {
    showDeleteConfirm = index;
  }
  
  function handleDeleteBank(index: number) {
    deleteBank(index);
    showDeleteConfirm = null;
  }
  
  function cancelDelete() {
    showDeleteConfirm = null;
  }
</script>

<div class="banks-panel">
  <div class="bank-tabs">
    {#each banks as bank, i}
      {@const isActive = i === $activeBankIndex}
      {@const isEditing = editingBankIndex === i}
      
      <div
        class="bank-tab"
        class:active={isActive}
        on:click={() => !isEditing && handleTabClick(i)}
        on:keydown={(e) => e.key === 'Enter' && !isEditing && handleTabClick(i)}
        role="tab"
        tabindex={isEditing ? -1 : 0}
        aria-selected={isActive}
      >
        {#if isEditing}
          <input
            type="text"
            class="bank-rename-input"
            bind:value={editingValue}
            on:blur={finishRename}
            on:keydown={handleKeydown}
            autofocus
            maxlength="20"
          />
        {:else}
          <span class="bank-name" on:dblclick={() => startRename(i, bank.name)}>
            {bank.name}
          </span>
          
          {#if isActive && banks.length > 1}
            <div class="bank-actions">
              <button
                type="button"
                class="bank-action-btn duplicate"
                on:click|stopPropagation={() => handleDuplicateBank(i)}
                title="Duplicate bank"
                aria-label="Duplicate bank"
              >
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <rect x="2" y="2" width="6" height="6" rx="0.5" stroke="currentColor" stroke-width="1.5"/>
                  <path d="M4 10H10V4" stroke="currentColor" stroke-width="1.5"/>
                </svg>
              </button>
              
              {#if banks.length > 1}
                <button
                  type="button"
                  class="bank-action-btn delete"
                  on:click|stopPropagation={() => confirmDelete(i)}
                  title="Delete bank"
                  aria-label="Delete bank"
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M2 3L10 3M4 3V2a1 1 0 011-1h2a1 1 0 011 1v1M5 5.5v3M7 5.5v3M3.5 3v6.5a1 1 0 001 1h3a1 1 0 001-1V3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                  </svg>
                </button>
              {/if}
            </div>
          {/if}
        {/if}
      </div>
    {/each}
    
    <button
      type="button"
      class="add-bank-btn"
      on:click={handleAddBank}
      title="Add new bank"
      aria-label="Add new bank"
    >
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
        <path d="M7 1v12M1 7h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
      </svg>
    </button>
  </div>
  
  <div class="bank-info">
    <span class="bank-counter">
      Bank {$activeBankIndex + 1} / {banks.length}
    </span>
  </div>
</div>

{#if showDeleteConfirm !== null}
  <div class="modal-overlay" on:click={cancelDelete} role="presentation">
    <div class="modal-dialog" on:click|stopPropagation role="dialog" aria-modal="true">
      <h3>Delete Bank?</h3>
      <p>Are you sure you want to delete "{banks[showDeleteConfirm]?.name ?? `Bank ${showDeleteConfirm + 1}`}"?</p>
      <p class="warning">This action cannot be undone.</p>
      <div class="modal-actions">
        <button type="button" class="btn btn-secondary" on:click={cancelDelete}>Cancel</button>
        <button type="button" class="btn btn-danger" on:click={() => handleDeleteBank(showDeleteConfirm!)}>Delete</button>
      </div>
    </div>
  </div>
{/if}

<style>
  .banks-panel {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 1rem;
    background: #1a1f2e;
    border-bottom: 1px solid #374151;
  }
  
  .bank-tabs {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
  }
  
  .bank-tab {
    position: relative;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    background: #2d3748;
    border: 1px solid #4a5568;
    border-radius: 0.375rem;
    cursor: pointer;
    transition: all 0.15s ease;
    min-width: 120px;
    color: #e2e8f0;
  }
  
  .bank-tab:hover {
    border-color: #3b82f6;
    box-shadow: 0 1px 3px rgba(59, 130, 246, 0.3);
    background: #374151;
  }
  
  .bank-tab.active {
    background: #3b82f6;
    color: white;
    border-color: #3b82f6;
    box-shadow: 0 1px 3px rgba(59, 130, 246, 0.5);
  }
  
  .bank-tab:focus-visible {
    outline: 2px solid #3b82f6;
    outline-offset: 2px;
  }
  
  .bank-name {
    flex: 1;
    font-weight: 500;
    font-size: 0.875rem;
  }
  
  .bank-rename-input {
    flex: 1;
    padding: 0.25rem 0.5rem;
    border: 1px solid #4a5568;
    border-radius: 0.25rem;
    font-size: 0.875rem;
    font-weight: 500;
    background: #1a1f2e;
    color: #e2e8f0;
  }
  
  .bank-rename-input:focus {
    outline: 2px solid #3b82f6;
    border-color: #3b82f6;
  }
  
  .bank-actions {
    display: flex;
    gap: 0.25rem;
    margin-left: 0.5rem;
  }
  
  .bank-action-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 24px;
    height: 24px;
    padding: 0;
    background: transparent;
    border: none;
    border-radius: 0.25rem;
    cursor: pointer;
    color: white;
    opacity: 0.8;
    transition: all 0.15s ease;
  }
  
  .bank-action-btn:hover {
    opacity: 1;
    background: rgba(255, 255, 255, 0.1);
  }
  
  .bank-action-btn.delete:hover {
    background: rgba(239, 68, 68, 0.9);
  }
  
  .add-bank-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 40px;
    height: 40px;
    padding: 0;
    background: #2d3748;
    border: 2px dashed #4a5568;
    border-radius: 0.375rem;
    cursor: pointer;
    color: #9ca3af;
    transition: all 0.15s ease;
  }
  
  .add-bank-btn:hover {
    border-color: #3b82f6;
    color: #3b82f6;
    background: #374151;
  }
  
  .bank-info {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  
  .bank-counter {
    font-size: 0.75rem;
    color: #9ca3af;
    font-weight: 500;
  }
  
  /* Modal styles */
  .modal-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.7);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
  }
  
  .modal-dialog {
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 0.5rem;
    padding: 1.5rem;
    max-width: 400px;
    width: 90%;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  }
  
  .modal-dialog h3 {
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: #f3f4f6;
  }
  
  .modal-dialog p {
    margin: 0.5rem 0;
    color: #d1d5db;
  }
  
  .modal-dialog p.warning {
    color: #ef4444;
    font-weight: 500;
    font-size: 0.875rem;
  }
  
  .modal-actions {
    display: flex;
    gap: 0.75rem;
    margin-top: 1.5rem;
    justify-content: flex-end;
  }
  
  .btn {
    padding: 0.5rem 1rem;
    border-radius: 0.375rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
    border: none;
    font-size: 0.875rem;
  }
  
  .btn-secondary {
    background: #374151;
    color: #f3f4f6;
    border: 1px solid #4b5563;
  }
  
  .btn-secondary:hover {
    background: #4b5563;
  }
  
  .btn-danger {
    background: #ef4444;
    color: white;
  }
  
  .btn-danger:hover {
    background: #dc2626;
  }
</style>
