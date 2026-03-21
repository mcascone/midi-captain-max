<script lang="ts">
  import { Accordion as SkeletonAccordion } from '@skeletonlabs/skeleton-svelte';
  import type { Snippet } from 'svelte';
  
  interface Props {
    title: string;
    defaultOpen?: boolean;
    disabled?: boolean;
    message?: string;
    children: Snippet;
  }
  
  let { title, defaultOpen = true, disabled = false, message, children }: Props = $props();
  
  // Generate a unique value for this accordion item
  const itemValue = `accordion-${Math.random().toString(36).substr(2, 9)}`;
  
  // Control the open state
  let value = $state<string[]>(defaultOpen ? [itemValue] : []);
</script>

<SkeletonAccordion {value} collapsible={true} {disabled} class="accordion-wrapper">
  <SkeletonAccordion.Item value={itemValue} class="accordion-item">
    <SkeletonAccordion.ItemTrigger class="accordion-header">
      <span class="indicator">
        {#if value.includes(itemValue)}▼{:else}▶{/if}
      </span>
      <span class="title">{title}</span>
      {#if message}
        <span class="message">({message})</span>
      {/if}
    </SkeletonAccordion.ItemTrigger>
    
    <SkeletonAccordion.ItemContent class="accordion-content">
      {@render children()}
    </SkeletonAccordion.ItemContent>
  </SkeletonAccordion.Item>
</SkeletonAccordion>

<style>
  :global(.accordion-wrapper) {
    margin-bottom: 1rem;
  }

  :global(.accordion-item) {
    border: 1px solid #333333;
    border-radius: 4px;
    background: #1f2937;
  }
  
  :global(.accordion-header) {
    width: 100%;
    padding: 0.75rem 1rem;
    background: #333333;
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
    transition: background 0.2s ease;
  }
  
  :global(.accordion-header:hover) {
    background: #444444;
  }
  
  :global(.accordion-header:disabled) {
    opacity: 0.6;
    cursor: not-allowed;
  }
  
  :global(.accordion-header:disabled:hover) {
    background: #333333;
  }
  
  .indicator {
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
  
  :global(.accordion-content) {
    padding: 1rem;
    background: #1f2937;
    color: #e5e7eb;
  }
</style>
