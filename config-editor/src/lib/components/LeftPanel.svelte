<script lang="ts">
  import { Tabs } from '@skeletonlabs/skeleton-svelte';
  import BanksPanel from './BanksPanel.svelte';
  import DeviceLayout from './DeviceLayout.svelte';
  import DisplaySection from './DisplaySection.svelte';
  import SplashScreenSection from './SplashScreenSection.svelte';
  import DeviceSection from './DeviceSection.svelte';
  import EncoderSection from './EncoderSection.svelte';
  import ExpressionSection from './ExpressionSection.svelte';
  import BankSettingsPanel from './BankSettingsPanel.svelte';
  import { isMultiBankMode, bankCount } from '$lib/formStore';

  // Show banks panel if multi-bank mode and more than 1 bank
  let showBanksPanel = $derived($isMultiBankMode && $bankCount > 0);
</script>

<div class="left-panel-container">
  <!-- Tabs for all content -->
  <div class="tabs-container">
    <Tabs defaultValue="buttons" class="tabs-root">
      <Tabs.List class="tabs-list">
        <Tabs.Trigger value="buttons" class="tab-trigger">Buttons</Tabs.Trigger>
        <Tabs.Trigger value="display" class="tab-trigger">Display</Tabs.Trigger>
        <Tabs.Trigger value="boot" class="tab-trigger">Boot</Tabs.Trigger>
        <Tabs.Trigger value="device" class="tab-trigger">Device</Tabs.Trigger>
        {#if showBanksPanel}
        <Tabs.Trigger value="banks" class="tab-trigger">Banks</Tabs.Trigger>
        {/if}
        <Tabs.Trigger value="encoder" class="tab-trigger">Encoder</Tabs.Trigger>
        <Tabs.Trigger value="expression" class="tab-trigger">Expression</Tabs.Trigger>
        <Tabs.Indicator />
      </Tabs.List>
      <Tabs.Content value="buttons" class="tab-content tab-content-buttons">
        {#if showBanksPanel}
        <div class="banks-panel-section">
          <BanksPanel />
        </div>
        {/if}
        <div class="device-layout-section">
          <DeviceLayout />
        </div>
      </Tabs.Content>
      <Tabs.Content value="display" class="tab-content">
        <DisplaySection />
      </Tabs.Content>
      <Tabs.Content value="boot" class="tab-content">
        <SplashScreenSection />
      </Tabs.Content>
      <Tabs.Content value="device" class="tab-content">
        <DeviceSection />
      </Tabs.Content>
      {#if showBanksPanel}
      <Tabs.Content value="banks" class="tab-content">
        <BankSettingsPanel />
      </Tabs.Content>
      {/if}
      <Tabs.Content value="encoder" class="tab-content">
        <EncoderSection />
      </Tabs.Content>
      <Tabs.Content value="expression" class="tab-content">
        <ExpressionSection />
      </Tabs.Content>
    </Tabs>
  </div>
</div>

<style>
  .left-panel-container {
    display: flex;
    flex-direction: column;
    height: 100%;
    overflow: hidden;
  }

  .tabs-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    border-top: 1px solid #333333;
    background: #121212;
    overflow: hidden;
  }

  .tabs-container :global(.tabs-root) {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .tabs-container :global(.tabs-list) {
    display: flex;
    gap: 0;
    border-bottom: 1px solid var(--border-default);
    background: var(--bg-dark);
    align-items: center;
  }

  .tabs-container :global(.tab-trigger) {
    padding: 12px 24px;
    background: transparent;
    border: none;
    color: #9ca3af;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
    font-family: inherit;
  }

  .tabs-container :global(.tab-trigger:hover) {
    color: #e5e7eb;
    background: var(--bg-input);
  }

  .tabs-container :global(.tab-trigger[data-state="active"]),
  .tabs-container :global(.tab-trigger[aria-selected="true"]) {
    color: var(--accent-primary);
    border-bottom-color: var(--accent-primary);
    background: var(--bg-dark);
  }

  .tabs-container :global(.tab-content) {
    padding: 16px;
    flex: 1;
    overflow-y: auto;
    background: var(--bg-dark);
    color: #e5e7eb;
  }

  /* Special styling for buttons tab */
  .tabs-container :global(.tab-content-buttons) {
    display: flex;
    flex-direction: column;
    padding: 0;
    gap: 0;
  }

  .banks-panel-section {
    flex-shrink: 0;
    padding: 16px;
    background: var(--bg-input);
    border-bottom: 1px solid var(--border-default);
  }

  .device-layout-section {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 24px;
    overflow-y: auto;
  }

  .tabs-container :global(.tab-content) :global(label),
  .tabs-container :global(.tab-content) :global(select),
  .tabs-container :global(.tab-content) :global(input) {
    color: #e5e7eb;
  }

  .tabs-container :global(.tab-content) :global(select),
  .tabs-container :global(.tab-content) :global(input[type="text"]),
  .tabs-container :global(.tab-content) :global(input[type="number"]) {
    background: #333333;
    border: 1px solid #444444;
  }

  .tabs-container :global(.tab-content) :global(select:hover),
  .tabs-container :global(.tab-content) :global(input[type="text"]:hover),
  .tabs-container :global(.tab-content) :global(input[type="number"]:hover) {
    background: #444444;
  }
</style>
