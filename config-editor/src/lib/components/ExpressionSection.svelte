<script lang="ts">
  import ExpressionPedal from './ExpressionPedal.svelte';
  import { config, updateField } from '$lib/formStore';

  let deviceType = $derived($config.device);
  let expression = $derived($config.expression);
  let isDisabled = $derived(deviceType === 'mini6');

  function handlePedalUpdate(pedal: 'exp1' | 'exp2', field: string, value: any) {
    updateField(`expression.${pedal}.${field}`, value);
  }
</script>

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
  <div class="empty-state">
    {#if isDisabled}
      <p class="empty-message">
        <strong>Expression pedals not available</strong><br/>
        Expression pedals are not supported on Mini6 devices. Only STD10 devices have encoder and expression pedal support.
      </p>
    {:else}
      <p class="empty-message">
        <strong>Expression pedals not configured</strong><br/>
        The expression pedal configuration is missing from your config file. This typically happens when relying on firmware defaults.
      </p>
      <p class="empty-help">
        To configure expression pedals, add an "expression" section to your config.json file or reload the config to initialize default settings.
      </p>
    {/if}
  </div>
{/if}

<style>
  .pedals-list {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
  }

  .empty-state {
    padding: 2rem;
    background: var(--bg-input);
    border-radius: 4px;
    text-align: center;
  }

  .empty-message {
    color: #e5e7eb;
    font-size: 0.95rem;
    line-height: 1.6;
    margin: 0 0 1rem 0;
  }

  .empty-message strong {
    display: block;
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
    color: #f9fafb;
  }

  .empty-help {
    color: #9ca3af;
    font-size: 0.875rem;
    line-height: 1.5;
    margin: 0;
  }
</style>
