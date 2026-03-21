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
          <svg width="20" height="20" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
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
          <svg width="20" height="20" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
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
          <svg width="20" height="20" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
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
          <svg width="20" height="20" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
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
            <svg width="20" height="20" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
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
    padding: 1.5rem 1.5rem 1.25rem;
    background: var(--bg-dark);
    border-bottom: 2px solid var(--border-default);
    overflow: visible;
  }

  .carousel-layout {
    display: flex;
    align-items: center;
    gap: 1rem;
    overflow: visible;
  }

  /* Carousel navigation buttons - uses Skeleton's Control wrapper */
  .banks-panel :global(.carousel-nav-btn) {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    padding: 0;
    background: var(--bg-card);
    border: 2px solid var(--border-default);
    border-radius: 8px;
    cursor: pointer;
    color: #e2e8f0;
    transition: all 0.2s ease;
    flex-shrink: 0;
    box-shadow: var(--shadow-sm);
  }

  .banks-panel :global(.carousel-nav-btn:hover:not(:disabled)) {
    border-color: var(--accent-primary);
    background: var(--bg-input);
    color: var(--accent-primary);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md), var(--glow-cyan-sm);
  }

  .banks-panel :global(.carousel-nav-btn:disabled) {
    cursor: not-allowed;
    opacity: 0.3;
  }

  /* Carousel items container */
  .banks-panel :global(.carousel-items) {
    flex: 1;
    display: flex;
    overflow: visible;
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
    gap: 0.375rem;
    padding: 1rem 1.5rem;
    cursor: pointer;
    border-radius: 10px;
    transition: all 0.2s ease;
    width: 100%;
    max-width: 280px;
    background: var(--bg-card);
    border: 2px solid var(--border-default);
    box-shadow: var(--shadow-sm);
  }

  .bank-display:hover {
    background: var(--bg-input);
    border-color: var(--accent-primary);
    transform: translateY(-2px);
    box-shadow: var(--shadow-md), var(--glow-cyan-sm);
  }

  .bank-name {
    font-size: var(--text-xl);
    font-weight: 700;
    color: var(--text-primary);
    text-align: center;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    width: 100%;
    letter-spacing: -0.01em;
  }

  .bank-counter {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .bank-rename-input {
    width: 100%;
    max-width: 280px;
    padding: 1rem 1.5rem;
    border: 2px solid var(--accent-primary);
    border-radius: 10px;
    font-size: var(--text-xl);
    font-weight: 700;
    background: var(--bg-card);
    color: var(--text-primary);
    text-align: center;
    letter-spacing: -0.01em;
    box-shadow: var(--shadow-md), var(--glow-cyan);
  }

  .bank-rename-input:focus {
    outline: none;
    box-shadow: var(--shadow-lg), var(--glow-cyan), 0 0 0 4px var(--accent-primary-dim);
  }

  /* Action buttons */
  .action-buttons {
    display: flex;
    gap: 0.75rem;
    flex-shrink: 0;
  }

  .action-btn {
    display: flex;
    align-items: center;
    justify-content: center;
    width: 48px;
    height: 48px;
    padding: 0;
    background: var(--bg-card);
    border: 2px solid var(--border-default);
    border-radius: 8px;
    cursor: pointer;
    color: var(--text-secondary);
    transition: all 0.2s ease;
    box-shadow: var(--shadow-sm);
  }

  .action-btn:hover:not(:disabled) {
    border-color: var(--accent-primary);
    color: var(--accent-primary);
    background: var(--bg-input);
    transform: translateY(-1px);
    box-shadow: var(--shadow-md), var(--glow-cyan-sm);
  }

  .action-btn.delete:hover:not(:disabled) {
    border-color: #ef4444;
    color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
    box-shadow: var(--shadow-md), 0 0 8px rgba(239, 68, 68, 0.3);
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
    background: var(--bg-card);
    border: 2px solid var(--border-default);
    border-radius: 12px;
    padding: 2rem;
    max-width: 440px;
    width: 90%;
    box-shadow: var(--shadow-lg);
  }

  :global(.delete-modal-title) {
    margin: 0 0 1rem 0;
    font-size: var(--text-2xl);
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.01em;
  }

  :global(.delete-modal-description) {
    margin: 0.5rem 0;
    color: var(--text-secondary);
    font-size: var(--text-base);
    line-height: 1.6;
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
    padding: 0.625rem 1.25rem;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
    border: none;
    font-size: var(--text-sm);
  }

  .btn-secondary {
    background: var(--bg-input);
    color: var(--text-primary);
    border: 2px solid var(--border-default);
  }

  .btn-secondary:hover {
    background: var(--bg-card);
    border-color: var(--accent-primary);
    transform: translateY(-1px);
    box-shadow: var(--shadow-sm);
  }

  .btn-danger {
    background: #ef4444;
    color: white;
    border: 2px solid #ef4444;
  }

  .btn-danger:hover {
    background: #dc2626;
    border-color: #dc2626;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
  }
</style>
