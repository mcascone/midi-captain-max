<script lang="ts">
  import { Tabs } from '@skeletonlabs/skeleton-svelte';
  import DeviceLayout from './DeviceLayout.svelte';
  import DisplaySection from './DisplaySection.svelte';
  import DeviceSection from './DeviceSection.svelte';
  import EncoderSection from './EncoderSection.svelte';
  import ExpressionSection from './ExpressionSection.svelte';
</script>

<div class="left-panel-container">
  <!-- Device Layout (visual representation) -->
  <div class="layout-container">
    <DeviceLayout />
  </div>

  <!-- Tabs for settings -->
  <div class="tabs-container">
    <Tabs defaultValue="display">
      <Tabs.List class="tabs-list">
        <Tabs.Trigger value="display" class="tab-trigger">Display</Tabs.Trigger>
        <Tabs.Trigger value="device" class="tab-trigger">Device</Tabs.Trigger>
        <Tabs.Trigger value="encoder" class="tab-trigger">Encoder</Tabs.Trigger>
        <Tabs.Trigger value="expression" class="tab-trigger">Expression</Tabs.Trigger>
        <Tabs.Indicator />
      </Tabs.List>
      <Tabs.Content value="display" class="tab-content">
        <DisplaySection />
      </Tabs.Content>
      <Tabs.Content value="device" class="tab-content">
        <DeviceSection />
      </Tabs.Content>
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

  .layout-container {
    flex: 1;
    overflow-y: auto;
    min-height: 400px;
  }

  .tabs-container {
    flex-shrink: 0;
    border-top: 1px solid #374151;
    background: #111827;
  }

  .tabs-container :global(.tabs-list) {
    display: flex;
    gap: 0;
    border-bottom: 1px solid #374151;
    background: #1f2937;
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
    background: #374151;
  }

  .tabs-container :global(.tab-trigger[data-state="active"]),
  .tabs-container :global(.tab-trigger[aria-selected="true"]) {
    color: #8b5cf6;
    border-bottom-color: #8b5cf6;
    background: #1f2937;
  }

  .tabs-container :global(.tab-content) {
    padding: 16px;
    max-height: 300px;
    overflow-y: auto;
    background: #1f2937;
    color: #e5e7eb;
  }

  .tabs-container :global(.tab-content) :global(label),
  .tabs-container :global(.tab-content) :global(select),
  .tabs-container :global(.tab-content) :global(input) {
    color: #e5e7eb;
  }

  .tabs-container :global(.tab-content) :global(select),
  .tabs-container :global(.tab-content) :global(input[type="text"]),
  .tabs-container :global(.tab-content) :global(input[type="number"]) {
    background: #374151;
    border: 1px solid #4b5563;
  }

  .tabs-container :global(.tab-content) :global(select:hover),
  .tabs-container :global(.tab-content) :global(input[type="text"]:hover),
  .tabs-container :global(.tab-content) :global(input[type="number"]:hover) {
    background: #4b5563;
  }
</style>
