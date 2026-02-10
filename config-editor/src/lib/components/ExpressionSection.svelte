<script lang="ts">
  import Accordion from './Accordion.svelte';
  import ExpressionPedal from './ExpressionPedal.svelte';
  import { config, updateField } from '$lib/formStore';
  
  $: expression = $config.expression;
  
  function handlePedalUpdate(pedal: 'exp1' | 'exp2', field: string, value: any) {
    updateField(`expression.${pedal}.${field}`, value);
  }
</script>

<Accordion title="Expression Pedals">
  {#if expression}
    <div class="pedals-list">
      <ExpressionPedal 
        pedal={expression.exp1}
        name="Expression 1"
        onUpdate={(field, value) => handlePedalUpdate('exp1', field, value)}
      />
      <ExpressionPedal 
        pedal={expression.exp2}
        name="Expression 2"
        onUpdate={(field, value) => handlePedalUpdate('exp2', field, value)}
      />
    </div>
  {:else}
    <div class="no-expression">
      <p>No expression pedal configuration available</p>
    </div>
  {/if}
</Accordion>

<style>
  .pedals-list {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }
  
  .no-expression {
    color: var(--text-secondary, #666);
    font-style: italic;
    padding: 1rem;
  }
</style>
