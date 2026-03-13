<script lang="ts">
  import type { Snippet } from 'svelte';
  
  interface Props {
    title: string;
    defaultOpen?: boolean;
    disabled?: boolean;
    message?: string;
    children: Snippet;
  }
  
  let { title, defaultOpen = true, disabled = false, message, children }: Props = $props();
  
  let isOpen = $state(defaultOpen);
  
  function toggle() {
    if (!disabled) {
      isOpen = !isOpen;
    }
  }
</script>

<div class="accordion">
  <button 
    class="accordion-header" 
    class:disabled 
    onclick={toggle}
    type="button"
  >
    <span class="triangle">{isOpen ? '▼' : '▶'}</span>
    <span class="title">{title}</span>
    {#if message}
      <span class="message">({message})</span>
    {/if}
  </button>
  
  {#if isOpen}
    <div class="accordion-content">
      {@render children()}
    </div>
  {/if}
</div>

<style>
  .accordion {
    margin-bottom: 1rem;
    border: 1px solid #374151;
    border-radius: 4px;
    background: #1f2937;
  }
  
  .accordion-header {
    width: 100%;
    padding: 0.75rem 1rem;
    background: #374151;
    border: none;
    border-radius: 4px 4px 0 0;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1rem;
    font-weight: 600;
    text-align: left;
    color: #e5e7eb;
  }
  
  .accordion-header:hover {
    background: #4b5563;
  }
  
  .accordion-header.disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  .accordion-header.disabled:hover {
    background: #374151;
  }
  
  .triangle {
    font-size: 0.75rem;
    color: #9ca3af;
  }
  
  .title {
    flex: 1;
  }
  
  .message {
    color: #9ca3af;
    font-size: 0.875rem;
    font-weight: 400;
  }
  
  .accordion-content {
    padding: 1rem;
    background: #1f2937;
    color: #e5e7eb;
  }
</style>
