<script lang="ts">
  interface Props {
    checked?: boolean;
    disabled?: boolean;
    label?: string;
    onchange?: (checked: boolean) => void;
  }

  let {
    checked = $bindable(false),
    disabled = false,
    label = '',
    onchange
  }: Props = $props();

  function handleChange(e: Event) {
    if (disabled) return;
    const target = e.target as HTMLInputElement;
    checked = target.checked;
    onchange?.(checked);
  }
</script>

<label class="toggle-container" class:disabled>
  <span class="toggle-wrapper">
    <input
      type="checkbox"
      bind:checked
      {disabled}
      class="toggle-input"
      onchange={handleChange}
    />
    <div
      class="toggle-track"
      class:checked
      role="presentation"
    >
      <div class="toggle-thumb" class:checked></div>
    </div>
  </span>
  {#if label}
    <span class="toggle-label">{label}</span>
  {/if}
</label>

<style>
  .toggle-container {
    display: inline-flex;
    align-items: center;
    gap: 12px;
    cursor: pointer;
    user-select: none;
  }

  .toggle-container.disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .toggle-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }

  .toggle-input {
    position: absolute;
    opacity: 0;
    width: 0;
    height: 0;
  }

  .toggle-track {
    position: relative;
    width: 52px;
    height: 28px;
    background: #1a1a1a;
    border: 2px solid #333333;
    border-radius: 14px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .toggle-track:hover:not(.disabled) {
    border-color: #444444;
    background: #222222;
  }

  .toggle-track.checked {
    background: var(--accent-primary);
    border-color: var(--accent-primary);
    box-shadow: 0 0 8px rgba(0, 212, 170, 0.3);
  }

  .toggle-input:focus-visible + .toggle-track {
    outline: none;
    box-shadow: 0 0 0 3px rgba(0, 212, 170, 0.1);
  }

  .toggle-thumb {
    position: absolute;
    top: 2px;
    left: 2px;
    width: 20px;
    height: 20px;
    background: #666666;
    border-radius: 50%;
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  }

  .toggle-thumb.checked {
    transform: translateX(24px);
    background: #0a0a0a;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
  }

  .toggle-label {
    font-size: 15px;
    color: #e5e7eb;
    font-weight: 500;
  }

  .disabled .toggle-track,
  .disabled .toggle-thumb {
    cursor: not-allowed;
  }
</style>
