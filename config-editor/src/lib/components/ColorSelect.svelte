<script lang="ts">
  import { Popover, Portal } from '@skeletonlabs/skeleton-svelte';
  import { BUTTON_COLORS, type ButtonColor } from '$lib/types';

  interface Props {
    value: ButtonColor;
    onchange: (color: ButtonColor) => void;
  }

  let { value, onchange }: Props = $props();

  const colors: ButtonColor[] = [
    'red', 'green', 'blue', 'yellow', 'cyan',
    'magenta', 'orange', 'purple', 'white', 'pink',
    'lime', 'amber', 'teal', 'violet', 'gold'
  ];

  let isOpen = $state(false);

  function select(color: ButtonColor) {
    onchange(color);
    isOpen = false;
  }
</script>

<Popover open={isOpen} onOpenChange={(details) => isOpen = details.open} positioning={{ placement: 'bottom-start' }}>
  <Popover.Trigger class="color-select-trigger" aria-label="Select color">
    <span class="selected-color" style="background-color: {BUTTON_COLORS[value]}"></span>
    <span class="color-label">{value}</span>
    <span class="chevron">{isOpen ? '▲' : '▼'}</span>
  </Popover.Trigger>

  <Portal>
    <Popover.Positioner class="color-popover-positioner">
      <Popover.Content class="color-picker-popover">
        <div class="color-picker-grid">
          {#each colors as color}
            <button
              class="color-circle"
              class:selected={color === value}
              onclick={() => select(color)}
              type="button"
              title={color}
              aria-label={`Select ${color} color`}
            >
              <span class="color-inner" style="background-color: {BUTTON_COLORS[color]}"></span>
              {#if color === value}
                <span class="checkmark">✓</span>
              {/if}
            </button>
          {/each}
        </div>
      </Popover.Content>
    </Popover.Positioner>
  </Portal>
</Popover>

<style>
  :global(.color-select-trigger) {
    display: flex;
    align-items: center;
    gap: 8px;
    width: 100%;
    padding: 8px 12px;
    background: #1a1a2e;
    border: 1px solid #2a2a40;
    border-radius: 6px;
    color: #e5e7eb;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  :global(.color-select-trigger:hover) {
    border-color: #3a3a55;
  }

  :global(.color-select-trigger[data-state="open"]) {
    border-color: #6366f1;
  }

  .selected-color {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    border: 2px solid #2a2a40;
  }

  .color-label {
    flex: 1;
    text-align: left;
    font-size: 13px;
    text-transform: capitalize;
  }

  .chevron {
    font-size: 10px;
    color: #9ca3af;
  }

  :global(.color-popover-positioner) {
    z-index: 100;
  }

  :global(.color-picker-popover) {
    background: #1a1a2e;
    border: 1px solid #2a2a40;
    border-radius: 8px;
    padding: 12px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3), 0 2px 4px -1px rgba(0, 0, 0, 0.2);
  }

  .color-picker-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 8px;
  }

  .color-circle {
    position: relative;
    width: 32px;
    height: 32px;
    padding: 3px;
    background: #1a1a2e;
    border: 2px solid #2a2a40;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .color-circle:hover {
    border-color: #4b5563;
    transform: scale(1.1);
  }

  .color-circle.selected {
    border-color: #6366f1;
    border-width: 3px;
    padding: 2px;
  }

  .color-inner {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    display: block;
  }

  .checkmark {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: white;
    font-size: 14px;
    font-weight: bold;
    text-shadow: 0 0 3px rgba(0,0,0,0.8);
    pointer-events: none;
  }
</style>
