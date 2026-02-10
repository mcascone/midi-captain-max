<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { message } from '@tauri-apps/plugin-dialog';
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
      
      unlistenDisconnect = await onDeviceDisconnected(async (name) => {
        const wasSelected = $selectedDevice?.name === name;
        
        $devices = $devices.filter(d => d.name !== name);
        
        if (wasSelected) {
          if ($hasUnsavedChanges) {
            await message(
              `Device "${name}" was disconnected. Your unsaved changes have been lost.`,
              { title: 'Device Disconnected', kind: 'warning' }
            );
          }
          $selectedDevice = null;
          $currentConfigRaw = '';
          $hasUnsavedChanges = false;
        }
        
        $statusMessage = `Device disconnected: ${name}`;
      });
      
      // Auto-select if only one device
      if ($devices.length === 1) {
        await selectDevice($devices[0]);
      }
      
      // Add keyboard shortcut handler (⌘S to save)
      const handleKeydown = async (e: KeyboardEvent) => {
        if (e.metaKey && e.key === 's') {
          e.preventDefault();
          if ($selectedDevice && $hasUnsavedChanges) {
            await saveToDevice();
          }
        }
      };
      
      document.addEventListener('keydown', handleKeydown);
      
      // Clean up keyboard listener
      return () => {
        document.removeEventListener('keydown', handleKeydown);
      };
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
  
  function resetChanges() {
    editorContent = $currentConfigRaw;
    $hasUnsavedChanges = false;
    $validationErrors = [];
    $statusMessage = 'Changes reset to device version';
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
        class="secondary"
        onclick={resetChanges} 
        disabled={!$selectedDevice || !$hasUnsavedChanges || $isLoading}
      >
        Reset
      </button>
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
    
    /* Light mode defaults */
    --bg-primary: #ffffff;
    --bg-secondary: #f5f5f5;
    --bg-tertiary: #e0e0e0;
    --text-primary: #1e1e1e;
    --text-secondary: #666666;
    --border-color: #d0d0d0;
    --accent: #0078d4;
    --accent-hover: #1084d8;
    --success: #4a7c4e;
    --warning: #f0ad4e;
    --error-bg: #fce4e4;
    --error-border: #f5c6cb;
    --error-text: #a94442;
    --disabled-bg: #cccccc;
    
    background: var(--bg-primary);
    color: var(--text-primary);
  }

  @media (prefers-color-scheme: dark) {
    :global(body) {
      --bg-primary: #1e1e1e;
      --bg-secondary: #2d2d2d;
      --bg-tertiary: #3c3c3c;
      --text-primary: #d4d4d4;
      --text-secondary: #888888;
      --border-color: #404040;
      --accent: #0078d4;
      --accent-hover: #1084d8;
      --success: #4a7c4e;
      --warning: #f0ad4e;
      --error-bg: #3c1f1f;
      --error-border: #5c2f2f;
      --error-text: #f48771;
      --disabled-bg: #555555;
    }
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
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-color);
  }
  
  h1 {
    margin: 0;
    font-size: 18px;
    font-weight: 500;
  }
  
  .device-selector select {
    padding: 6px 12px;
    font-size: 14px;
    background: var(--bg-tertiary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    border-radius: 4px;
  }
  
  .no-device {
    color: var(--text-secondary);
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
    color: var(--text-secondary);
  }
  
  .errors {
    padding: 12px 20px;
    background: var(--error-bg);
    border-top: 1px solid var(--error-border);
    color: var(--error-text);
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
    background: var(--bg-secondary);
    border-top: 1px solid var(--border-color);
  }
  
  .status {
    color: var(--text-secondary);
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
    background: var(--accent);
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }
  
  button.secondary {
    background: transparent;
    color: var(--text-secondary);
    border: 1px solid var(--border-color);
  }
  
  button:hover:not(:disabled) {
    background: var(--accent-hover);
  }
  
  button.secondary:hover:not(:disabled) {
    background: var(--bg-tertiary);
    color: var(--text-primary);
  }
  
  button:disabled {
    background: var(--disabled-bg);
    cursor: not-allowed;
  }
  
  button.secondary:disabled {
    background: transparent;
    color: var(--text-secondary);
    opacity: 0.5;
  }
</style>
