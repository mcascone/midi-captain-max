<script lang="ts">
  import { config, updateField } from '$lib/formStore';
  
  let display = $derived($config.display);
  
  function handleField(path: string, e: Event) {
    const target = e.target as HTMLSelectElement;
    updateField(`display.${path}`, target.value);
  }
</script>

<div class="display-section">
  <label>
    <span class="field-label">Button text size:</span>
    <select
      value={display?.button_text_size ?? 'medium'}
      onchange={(e) => handleField('button_text_size', e)}
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
      onchange={(e) => handleField('status_text_size', e)}
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
      onchange={(e) => handleField('expression_text_size', e)}
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
      onchange={(e) => handleField('button_name_text_size', e)}
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
    background: #0f172a;
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
    border: 1px solid #4b5563;
    border-radius: 4px;
    font-size: 0.875rem;
    background: #374151;
    color: #e5e7eb;
    width: 100%;
    cursor: pointer;
  }
  
  .display-section select:hover {
    background: #4b5563;
  }

  .display-section select:focus {
    outline: 2px solid #8b5cf6;
    outline-offset: 1px;
  }
</style>
