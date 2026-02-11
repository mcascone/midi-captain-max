<script lang="ts">
  import { BUTTON_COLORS, type ButtonColor } from '$lib/types';
  
  interface Props {
    value: ButtonColor;
    onchange: (color: ButtonColor) => void;
  }
  
  let { value, onchange }: Props = $props();
  
  let isOpen = $state(false);
  
  const colors: ButtonColor[] = [
    'red', 'green', 'blue', 'yellow',
    'cyan', 'magenta', 'orange', 'purple', 'white'
  ];
  
  function select(color: ButtonColor) {
    onchange(color);
    isOpen = false;
  }
  
  function toggle() {
    isOpen = !isOpen;
  }
  
  function handleClickOutside(event: MouseEvent) {
    const target = event.target as HTMLElement;
    if (!target.closest('.color-select')) {
      isOpen = false;
    }
  }
  
  $effect(() => {
    if (isOpen) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  });
</script>

<div class="color-select">
  <button 
    class="color-trigger" 
    onclick={toggle}
    type="button"
  >
    <span class="color-dot" style="background-color: {BUTTON_COLORS[value]}"></span>
    <span class="color-name">{value}</span>
    <span class="arrow">▼</span>
  </button>
  
  {#if isOpen}
    <div class="color-dropdown">
      {#each colors as color}
        <button
          class="color-option"
          class:selected={color === value}
          onclick={() => select(color)}
          type="button"
        >
          <span class="color-dot" style="background-color: {BUTTON_COLORS[color]}"></span>
          <span class="color-name">{color}</span>
          {#if color === value}
            <span class="checkmark">✓</span>
          {/if}
        </button>
      {/each}
    </div>
  {/if}
</div>

<style>
  .color-select {
    position: relative;
    display: inline-block;
  }
  
  .color-trigger {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.75rem;
    background: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;
  }
  
  .color-trigger:hover {
    border-color: #999;
  }
  
  .color-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 1px solid #666;
  }
  
  .color-name {
    text-transform: capitalize;
  }
  
  .arrow {
    font-size: 0.625rem;
    color: #666;
  }
  
  .color-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    margin-top: 2px;
    background: white;
    border: 1px solid #ccc;
    border-radius: 4px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.15);
    z-index: 1000;
    min-width: 140px;
  }
  
  .color-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.5rem 0.75rem;
    background: white;
    border: none;
    cursor: pointer;
    font-size: 0.875rem;
    text-align: left;
  }
  
  .color-option:hover {
    background: #f5f5f5;
  }
  
  .color-option.selected {
    background: #e8f4fd;
  }
  
  .checkmark {
    margin-left: auto;
    color: #0066cc;
    font-weight: bold;
  }
</style>
