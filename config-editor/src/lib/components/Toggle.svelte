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
    display: flex;
    align-items: center;
    gap: 10px;
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
    width: 48px;
    height: 26px;
    background: #1a1a1a;
    border: 2px solid #333333;
    border-radius: 13px;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .toggle-track:hover:not(.disabled) {
    border-color: #444444;
  }

  .toggle-track.checked {
    background: var(--accent-primary);
    border-color: var(--accent-primary);
    box-shadow: 0 0 12px rgba(0, 212, 170, 0.4);
  }

  .toggle-track:focus-visible {
    outline: 2px solid var(--accent-primary);
    outline-offset: 2px;
  }

  .toggle-thumb {
    position: absolute;
    top: 2px;
    left: 2px;
    width: 18px;
    height: 18px;
    background: #666666;
    border-radius: 50%;
    transition: all 0.2s ease;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  }

  .toggle-thumb.checked {
    transform: translateX(22px);
    background: var(--bg-dark);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.5);
  }

  .toggle-label {
    font-size: 14px;
    color: var(--text-primary);
    font-weight: 500;
  }

  .disabled .toggle-track,
  .disabled .toggle-thumb {
    cursor: not-allowed;
  }
</style>
