<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { 
    devices, selectedDevice, currentConfigRaw, 
    hasUnsavedChanges, validationErrors, statusMessage, isLoading 
  } from '$lib/stores';
  import { 
    scanDevices, startDeviceWatcher, readConfigRaw, writeConfigRaw,
    onDeviceConnected, onDeviceDisconnected 
  } from '$lib/api';
  import type { DetectedDevice } from '$lib/types';
  import JsonEditor from '$lib/components/JsonEditor.svelte';

  let editorContent = $state('');
  
  // Event listener cleanup functions
  let unlistenConnect: (() => void) | undefined;
  let unlistenDisconnect: (() => void) | undefined;
  
  onMount(async () => {
    try {
      // Initial device scan
      $devices = await scanDevices();
      
      // Start watching for device changes
      await startDeviceWatcher();
      
      // Listen for device events (store cleanup functions)
      unlistenConnect = await onDeviceConnected((device) => {
        $devices = [...$devices, device];
        $statusMessage = `Device connected: ${device.name}`;
      });
      
      unlistenDisconnect = await onDeviceDisconnected((name) => {
        $devices = $devices.filter(d => d.name !== name);
        if ($selectedDevice?.name === name) {
          $selectedDevice = null;
          $currentConfigRaw = '';
        }
        $statusMessage = `Device disconnected: ${name}`;
      });
      
      // Auto-select if only one device
      if ($devices.length === 1) {
        await selectDevice($devices[0]);
      }
    } catch (e: any) {
      $statusMessage = `Error initializing: ${e.message || e}`;
    }
  });
  
  onDestroy(() => {
    // Clean up event listeners to prevent memory leaks
    unlistenConnect?.();
    unlistenDisconnect?.();
  });
  
  async function selectDevice(device: DetectedDevice) {
    if ($hasUnsavedChanges) {
      if (!confirm('You have unsaved changes. Discard them?')) {
        return;
      }
    }
    
    $selectedDevice = device;
    $isLoading = true;
    
    try {
      if (device.has_config) {
        $currentConfigRaw = await readConfigRaw(device.config_path);
        editorContent = $currentConfigRaw;
      } else {
        $currentConfigRaw = '';
        editorContent = '';
        $statusMessage = 'No config.json found on device';
      }
      $hasUnsavedChanges = false;
      $validationErrors = [];
    } catch (e: any) {
      $statusMessage = `Error reading config: ${e.message || e}`;
    } finally {
      $isLoading = false;
    }
  }
  
  async function saveToDevice() {
    if (!$selectedDevice) return;
    
    $isLoading = true;
    try {
      await writeConfigRaw($selectedDevice.config_path, editorContent);
      $currentConfigRaw = editorContent;
      $hasUnsavedChanges = false;
      $validationErrors = [];
      $statusMessage = 'Config saved to device!';
    } catch (e: any) {
      if (e.details) {
        $validationErrors = e.details;
      }
      $statusMessage = `Error: ${e.message || e}`;
    } finally {
      $isLoading = false;
    }
  }
  
  function handleEditorChange(newValue: string) {
    editorContent = newValue;
    $hasUnsavedChanges = editorContent !== $currentConfigRaw;
  }
</script>

<main>
  <header>
    <h1>MIDI Captain MAX Config Editor</h1>
    <div class="device-selector">
      {#if $devices.length === 0}
        <span class="no-device">No device connected</span>
      {:else}
        <select 
          value={$selectedDevice?.name ?? ''} 
          onchange={(e) => {
            const device = $devices.find(d => d.name === e.currentTarget.value);
            if (device) selectDevice(device);
          }}
        >
          <option value="" disabled>Select device...</option>
          {#each $devices as device}
            <option value={device.name}>{device.name}</option>
          {/each}
        </select>
      {/if}
    </div>
  </header>
  
  <div class="editor-container">
    {#if $selectedDevice}
      <JsonEditor 
        value={editorContent} 
        onchange={handleEditorChange}
      />
    {:else}
      <div class="placeholder">
        <p>Connect a MIDI Captain device or select one from the dropdown.</p>
        <p>Watching for devices: CIRCUITPY, MIDICAPTAIN</p>
      </div>
    {/if}
  </div>
  
  {#if $validationErrors.length > 0}
    <div class="errors">
      <strong>Validation Errors:</strong>
      <ul>
        {#each $validationErrors as error}
          <li>{error}</li>
        {/each}
      </ul>
    </div>
  {/if}
  
  <footer>
    <div class="status">{$statusMessage}</div>
    <div class="actions">
      {#if $hasUnsavedChanges}
        <span class="unsaved">● Unsaved changes</span>
      {/if}
      <button 
        onclick={saveToDevice} 
        disabled={!$selectedDevice || !$hasUnsavedChanges || $isLoading}
      >
        Save to Device
      </button>
    </div>
  </footer>
</main>

<style>
  :global(body) {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #1e1e1e;
    color: #d4d4d4;
  }
  
  main {
    display: flex;
    flex-direction: column;
    height: 100vh;
  }
  
  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    background: #2d2d2d;
    border-bottom: 1px solid #404040;
  }
  
  h1 {
    margin: 0;
    font-size: 18px;
    font-weight: 500;
  }
  
  .device-selector select {
    padding: 6px 12px;
    font-size: 14px;
    background: #3c3c3c;
    color: #d4d4d4;
    border: 1px solid #555;
    border-radius: 4px;
  }
  
  .no-device {
    color: #888;
    font-style: italic;
  }
  
  .editor-container {
    flex: 1;
    padding: 20px;
    overflow: hidden;
  }
  
  .placeholder {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #888;
  }
  
  .errors {
    padding: 12px 20px;
    background: #3c1f1f;
    border-top: 1px solid #5c2f2f;
    color: #f48771;
  }
  
  .errors ul {
    margin: 8px 0 0 0;
    padding-left: 20px;
  }
  
  footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 20px;
    background: #2d2d2d;
    border-top: 1px solid #404040;
  }
  
  .status {
    color: #888;
    font-size: 13px;
  }
  
  .actions {
    display: flex;
    align-items: center;
    gap: 16px;
  }
  
  .unsaved {
    color: #dcdcaa;
    font-size: 13px;
  }
  
  button {
    padding: 8px 16px;
    font-size: 14px;
    background: #0078d4;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  button:hover:not(:disabled) {
    background: #1084d8;
  }
  
  button:disabled {
    background: #555;
    cursor: not-allowed;
  }
</style>
