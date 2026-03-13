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
    background: #1a1a2e;
    border: 1px solid #2a2a40;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.875rem;
    color: #e5e7eb;
  }

  .color-trigger:hover {
    border-color: #3d3d5c;
    background: #222238;
  }

  .color-dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    border: 1px solid #4b5563;
  }

  .color-name {
    text-transform: capitalize;
    color: #e5e7eb;
  }

  .arrow {
    font-size: 0.625rem;
    color: #9ca3af;
  }

  .color-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    margin-top: 2px;
    background: #14141f;
    border: 1px solid #2a2a40;
    border-radius: 6px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.4);
    z-index: 1000;
    min-width: 140px;
  }

  .color-option {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    width: 100%;
    padding: 0.5rem 0.75rem;
    background: transparent;
    border: none;
    cursor: pointer;
    font-size: 0.875rem;
    text-align: left;
    color: #d1d5db;
  }

  .color-option:hover {
    background: #1e1e2e;
  }

  .color-option.selected {
    background: #1e1e38;
    color: #e5e7eb;
  }

  .checkmark {
    margin-left: auto;
    color: #6366f1;
    font-weight: bold;
  }
</style>
