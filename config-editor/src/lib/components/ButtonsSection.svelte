<script lang="ts">
  import Accordion from './Accordion.svelte';
  import ButtonRow from './ButtonRow.svelte';
  import { config, updateField, activeBank, activeBankIndex, isMultiBankMode } from '$lib/formStore';
  
  let deviceType = $derived($config.device);
  
  // Get buttons from active bank if multi-bank mode, otherwise from top-level
  let buttons = $derived(
    $isMultiBankMode && $activeBank
      ? $activeBank.buttons
      : $config.buttons ?? []
  );
  
  let globalChannel = $derived($config.global_channel ?? 0);
  let visibleCount = $derived(buttons.length);
  
  function handleButtonUpdate(index: number, field: string, value: any) {
    // Update path based on mode
    if ($isMultiBankMode) {
      updateField(`banks[${$activeBankIndex}].buttons[${index}].${field}`, value);
    } else {
      updateField(`buttons[${index}].${field}`, value);
    }
  }
</script>

<Accordion title="Buttons ({visibleCount} of {visibleCount})">
  <div class="buttons-list">
    {#each buttons as button, index}
      {@const isDisabled = deviceType === 'mini6' && index >= 6}
      <ButtonRow 
        {button}
        {index}
        disabled={isDisabled}
        globalChannel={globalChannel}
        onUpdate={(field, value) => handleButtonUpdate(index, field, value)}
      />
    {/each}
  </div>
</Accordion>

<style>
  .buttons-list {
    display: flex;
    flex-direction: column;
  }
</style>
