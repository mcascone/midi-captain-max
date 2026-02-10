<script lang="ts">
  import Accordion from './Accordion.svelte';
  import { config, updateField } from '$lib/formStore';
  
  let display = $derived($config.display);
  
  function handleField(path: string, e: Event) {
    const target = e.target as HTMLSelectElement;
    updateField(`display.${path}`, target.value);
  }
</script>

<Accordion title="Display Settings">
  {#if display}
    <div class="display-section">
      <div class="field-row">
        <label>Button text size:</label>
        <select 
          value={display.button_text_size}
          onchange={(e) => handleField('button_text_size', e)}
        >
          <option value="small">Small</option>
          <option value="medium">Medium</option>
          <option value="large">Large</option>
        </select>
      </div>
      
      <div class="field-row">
        <label>Status text size:</label>
        <select 
          value={display.status_text_size}
          onchange={(e) => handleField('status_text_size', e)}
        >
          <option value="small">Small</option>
          <option value="medium">Medium</option>
          <option value="large">Large</option>
        </select>
      </div>
      
      <div class="field-row">
        <label>Expression text size:</label>
        <select 
          value={display.expression_text_size}
          onchange={(e) => handleField('expression_text_size', e)}
        >
          <option value="small">Small</option>
          <option value="medium">Medium</option>
          <option value="large">Large</option>
        </select>
      </div>
    </div>
  {/if}
</Accordion>

<style>
  .display-section {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }
  
  .field-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .field-row label {
    min-width: 160px;
    font-size: 0.875rem;
  }
  
  .field-row select {
    padding: 0.375rem 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 0.875rem;
    background: white;
    min-width: 120px;
  }
</style>
