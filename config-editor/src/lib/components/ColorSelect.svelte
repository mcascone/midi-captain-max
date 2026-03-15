<script lang="ts">
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

  function select(color: ButtonColor) {
    onchange(color);
  }
</script>

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

<style>
  .color-picker-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 8px;
    max-width: 200px;
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
