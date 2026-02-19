<script lang="ts">
  import Accordion from './Accordion.svelte';
  import ButtonRow from './ButtonRow.svelte';
  import { config, updateField } from '$lib/formStore';
  
  let deviceType = $derived($config.device);
  let buttons = $derived($config.buttons);
  let globalChannel = $derived($config.global_channel ?? 0);
  let visibleCount = $derived(buttons.length);
  
  function handleButtonUpdate(index: number, field: string, value: any) {
    updateField(`buttons[${index}].${field}`, value);
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
