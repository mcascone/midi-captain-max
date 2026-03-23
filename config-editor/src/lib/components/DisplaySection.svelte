<script lang="ts">
  import { config, updateField } from '$lib/formStore';

  let display = $derived($config.display);

  function handleDisplayField(path: string, e: Event) {
    const target = e.target as HTMLSelectElement;
    updateField(`display.${path}`, target.value);
  }
</script>

<div class="display-section">
  <label>
    <span class="field-label">Button text size:</span>
    <select
      value={display?.button_text_size ?? 'medium'}
      onchange={(e) => handleDisplayField('button_text_size', e)}
    >
      <option value="small">Small</option>
      <option value="medium">Medium</option>
      <option value="large">Large</option>
    </select>
  </label>

  <label>
    <span class="field-label">Status text size:</span>
    <select
      value={display?.status_text_size ?? 'medium'}
      onchange={(e) => handleDisplayField('status_text_size', e)}
    >
      <option value="small">Small</option>
      <option value="medium">Medium</option>
      <option value="large">Large</option>
    </select>
  </label>

  <label>
    <span class="field-label">Expression text size:</span>
    <select
      value={display?.expression_text_size ?? 'medium'}
      onchange={(e) => handleDisplayField('expression_text_size', e)}
    >
      <option value="small">Small</option>
      <option value="medium">Medium</option>
      <option value="large">Large</option>
    </select>
  </label>

  <label>
    <span class="field-label">Button name text size:</span>
    <select
      value={display?.button_name_text_size ?? 'large'}
      onchange={(e) => handleDisplayField('button_name_text_size', e)}
    >
      <option value="small">Small</option>
      <option value="medium">Medium</option>
      <option value="large">Large</option>
    </select>
  </label>
</div>

<style>
  .display-section {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1rem;
    padding: 1rem;
    background: var(--bg-input);
    border-radius: 4px;
  }

  .display-section label {
    display: grid;
    grid-template-columns: 140px 1fr;
    align-items: center;
    gap: 0.75rem;
    color: #e5e7eb;
  }

  .field-label {
    font-size: 0.875rem;
    color: #9ca3af;
    text-align: right;
    font-weight: 500;
  }

  .display-section select {
    padding: 0.5rem 0.75rem;
    border: 1px solid #444444;
    border-radius: 4px;
    font-size: 0.875rem;
    background: #333333;
    color: #e5e7eb;
    width: 100%;
    cursor: pointer;
  }

  .display-section select:hover {
    background: #444444;
  }

  .display-section select:focus {
    outline: 2px solid var(--accent-primary);
    outline-offset: 1px;
  }
</style>
