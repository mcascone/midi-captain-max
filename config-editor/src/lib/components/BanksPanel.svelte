<script lang="ts">
  import { Carousel, Dialog, Portal } from '@skeletonlabs/skeleton-svelte';
  import { activeBankIndex, activeBank, bankCount, config, switchBank, addBank, duplicateBank, deleteBank, renameBank } from '$lib/formStore';

  let isEditing = false;
  let editingValue = '';
  let showDeleteConfirm = false;

  // Get banks array for iteration
  $: banks = $config.banks ?? [];
  $: currentBank = banks[$activeBankIndex];

  // Declare and update carousel page when active bank changes
  let carouselPage = 0;
  $: carouselPage = $activeBankIndex;

  function handlePageChange(details: { page: number }) {
    switchBank(details.page);
  }

  function handleAddBank() {
    addBank();
  }

  function handleDuplicateBank() {
    duplicateBank($activeBankIndex);
  }

  function startRename() {
    isEditing = true;
    editingValue = currentBank.name;
  }

  function finishRename() {
    if (isEditing && editingValue.trim()) {
      renameBank($activeBankIndex, editingValue.trim());
    }
    isEditing = false;
  }

  function cancelRename() {
    isEditing = false;
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') {
      finishRename();
    } else if (e.key === 'Escape') {
      cancelRename();
    }
  }

  function confirmDelete() {
    showDeleteConfirm = true;
  }

  function handleDeleteBank() {
    deleteBank($activeBankIndex);
    showDeleteConfirm = false;
  }

  function cancelDelete() {
    showDeleteConfirm = false;
  }
</script>

<div class="banks-panel">
  <Carousel
    slideCount={banks.length}
    page={carouselPage}
    onPageChange={handlePageChange}
    loop={false}
  >
    <div class="carousel-layout">
      <Carousel.Control>
        <Carousel.PrevTrigger class="carousel-nav-btn">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M10 3L5 8L10 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </Carousel.PrevTrigger>
      </Carousel.Control>

      <Carousel.ItemGroup class="carousel-items">
        {#each banks as bank, i}
          <Carousel.Item index={i} class="carousel-item">
            {#if isEditing && i === $activeBankIndex}
              <input
                type="text"
                class="bank-rename-input"
                bind:value={editingValue}
                onblur={finishRename}
                onkeydown={handleKeydown}
                autofocus
                maxlength="20"
              />
            {:else}
              <div
                class="bank-display"
                ondblclick={() => i === $activeBankIndex && startRename()}
                role="button"
                tabindex="0"
              >
                <span class="bank-name">{bank.name}</span>
                <span class="bank-counter">{i + 1} / {banks.length}</span>
              </div>
            {/if}
          </Carousel.Item>
        {/each}
      </Carousel.ItemGroup>

      <Carousel.Control>
        <Carousel.NextTrigger class="carousel-nav-btn">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 3L11 8L6 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </Carousel.NextTrigger>
      </Carousel.Control>

      <div class="action-buttons">
        <button
          type="button"
          class="action-btn"
          onclick={handleAddBank}
          disabled={banks.length >= 8}
          title="Add new bank"
          aria-label="Add new bank"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M8 2v12M2 8h12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
          </svg>
        </button>

        <button
          type="button"
          class="action-btn"
          onclick={handleDuplicateBank}
          disabled={banks.length >= 8}
          title="Duplicate bank"
          aria-label="Duplicate bank"
        >
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="4" y="4" width="8" height="8" rx="1" stroke="currentColor" stroke-width="1.5"/>
            <path d="M6 12H12V6" stroke="currentColor" stroke-width="1.5"/>
          </svg>
        </button>

        {#if banks.length > 1}
          <button
            type="button"
            class="action-btn delete"
            onclick={confirmDelete}
            title="Delete bank"
            aria-label="Delete bank"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M3 5L13 5M6 5V4a1 1 0 011-1h2a1 1 0 011 1v1M7 7v5M9 7v5M5 5v8a1 1 0 001 1h4a1 1 0 001-1V5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
            </svg>
          </button>
        {/if}
      </div>
    </div>
  </Carousel>
</div>

<!-- Delete Confirmation Dialog -->
<Dialog open={showDeleteConfirm} onOpenChange={(details) => showDeleteConfirm = details.open} role="alertdialog">
  <Portal>
    <Dialog.Backdrop class="delete-modal-backdrop" />
    <Dialog.Positioner class="delete-modal-positioner">
      <Dialog.Content class="delete-modal-content">
        <Dialog.Title class="delete-modal-title">Delete Bank?</Dialog.Title>
        <Dialog.Description class="delete-modal-description">
          Are you sure you want to delete "{currentBank?.name ?? `Bank ${$activeBankIndex + 1}`}"?
          <br />
          <strong class="warning-text">This action cannot be undone.</strong>
        </Dialog.Description>
        <div class="delete-modal-actions">
          <Dialog.CloseTrigger class="btn btn-secondary">Cancel</Dialog.CloseTrigger>
          <button type="button" class="btn btn-danger" onclick={handleDeleteBank}>Delete</button>
        </div>
      </Dialog.Content>
    </Dialog.Positioner>
  </Portal>
</Dialog>

<style>
  .banks-panel {
    padding: 1rem;
    background: var(--bg-input);
    border-bottom: 1px solid var(--border-default);
  }

  .carousel-layout {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  /* Carousel navigation buttons - uses Skeleton's Control wrapper */
  .banks-panel :global(.carousel-nav-btn) {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    padding: 0;
    background: var(--bg-input);
    border: 1px solid var(--border-default);
    border-radius: 0.375rem;
    cursor: pointer;
    color: #e2e8f0;
    transition: all 0.15s ease;
    flex-shrink: 0;
  }

  .banks-panel :global(.carousel-nav-btn:hover:not(:disabled)) {
    border-color: var(--accent-primary);
    background: var(--bg-input);
    color: var(--accent-primary);
  }

  .banks-panel :global(.carousel-nav-btn:disabled) {
    cursor: not-allowed;
    opacity: 0.3;
  }

  /* Carousel items container */
  .banks-panel :global(.carousel-items) {
    flex: 1;
    display: flex;
    overflow: hidden;
    min-width: 0;
  }

  .banks-panel :global(.carousel-item) {
    flex: 0 0 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  /* Bank display */
  .bank-display {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    padding: 0.5rem 1rem;
    cursor: pointer;
    border-radius: 0.375rem;
    transition: background 0.15s ease;
    width: 100%;
    max-width: 280px;
  }

  .bank-display:hover {
    background: var(--accent-primary-dim);
  }

  .bank-name {
    font-size: 1rem;
    font-weight: 600;
    color: #e2e8f0;
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
  }

  .bank-counter {
    font-size: 0.75rem;
    color: #9ca3af;
    font-weight: 500;
  }

  .bank-rename-input {
    width: 100%;
    max-width: 280px;
    padding: 0.5rem 1rem;
    border: 2px solid var(--accent-primary);
    border-radius: 0.375rem;
    font-size: 1rem;
    font-weight: 600;
    background: var(--bg-input);
    color: #e2e8f0;
    text-align: center;
  }

  .bank-rename-input:focus {
    outline: none;
    box-shadow: 0 0 0 3px var(--accent-primary-dim);
  }

  /* Action buttons */
  .action-buttons {
    display: flex;
    gap: 0.5rem;
    flex-shrink: 0;
  }

  .action-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 36px;
    height: 36px;
    padding: 0;
    background: var(--bg-input);
    border: 1px solid var(--border-default);
    border-radius: 0.375rem;
    cursor: pointer;
    color: #9ca3af;
    transition: all 0.15s ease;
  }

  .action-btn:hover:not(:disabled) {
    border-color: var(--accent-primary);
    color: var(--accent-primary);
    background: var(--bg-input);
  }

  .action-btn.delete:hover:not(:disabled) {
    border-color: #ef4444;
    color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
  }

  .action-btn:disabled {
    cursor: not-allowed;
    opacity: 0.3;
  }

  /* Delete Dialog styles */
  :global(.delete-modal-backdrop) {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.7) !important;
    z-index: 1000;
  }

  :global(.delete-modal-positioner) {
    position: fixed;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1001;
  }

  :global(.delete-modal-content) {
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 0.5rem;
    padding: 1.5rem;
    max-width: 400px;
    width: 90%;
    box-shadow: 0 10px 25px rgba(0, 0, 0, 0.5);
  }

  :global(.delete-modal-title) {
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
    font-weight: 600;
    color: #f3f4f6;
  }

  :global(.delete-modal-description) {
    margin: 0.5rem 0;
    color: #d1d5db;
  }

  .warning-text {
    color: #ef4444;
    font-weight: 500;
    font-size: 0.875rem;
  }

  .delete-modal-actions {
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
