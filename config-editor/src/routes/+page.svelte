<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { get } from 'svelte/store';
  import { message } from '@tauri-apps/plugin-dialog';
  import { getVersion } from '@tauri-apps/api/app';
  import {
    devices, selectedDevice, currentConfigRaw,
    hasUnsavedChanges, validationErrors, statusMessage, isLoading,
    toasts, showToast, removeToast
  } from '$lib/stores';
  import {
    scanDevices, startDeviceWatcher, readConfigRaw, writeConfigRaw,
    onDeviceConnected, onDeviceDisconnected
  } from '$lib/api';
  import type { DetectedDevice } from '$lib/types';
  import LeftPanel from '$lib/components/LeftPanel.svelte';
  import ButtonSettingsPanel from '$lib/components/ButtonSettingsPanel.svelte';
  import Toast from '$lib/components/Toast.svelte';
  import { loadConfig, validate, normalizeConfig, config, isDirty, canUndo, canRedo, undo, redo, updateField } from '$lib/formStore';

  let appVersion = $state('');
  let showJsonModal = $state(false);
  let jsonText = $state('');
  let unlistenConnect: (() => void) | undefined;
  let unlistenDisconnect: (() => void) | undefined;
  let leftPanelCollapsed = $state(false);
  let leftPanelWidth = $state(780);
  let isResizing = $state(false);

  let devMode = $derived($config.dev_mode ?? false);
  let hasErrors = $derived($validationErrors.length > 0);
  let statusDot = $derived(
    $statusMessage.toLowerCase().includes('error') ? 'error'
    : $statusMessage.toLowerCase().includes('saved') || $statusMessage.toLowerCase().includes('success') ? 'success'
    : 'idle'
  );

  function startResize(e: MouseEvent) {
    isResizing = true;
    e.preventDefault();
  }

  function handleMouseMove(e: MouseEvent) {
    if (isResizing && !leftPanelCollapsed) {
      const newWidth = e.clientX;
      if (newWidth >= 300 && newWidth <= 1000) {
        leftPanelWidth = newWidth;
      }
    }
  }

  function stopResize() {
    isResizing = false;
  }

  onMount(async () => {
    try {
      appVersion = await getVersion();
      $devices = await scanDevices();
      await startDeviceWatcher();

      unlistenConnect = await onDeviceConnected(async (device) => {
        const exists = $devices.some(d => d.path === device.path);
        if (!exists) {
          $devices = [...$devices, device];
          $statusMessage = `Device connected: ${device.name}`;
          const shouldAutoSelect = $devices.length === 1 ||
            ($selectedDevice && $selectedDevice.path === device.path);
          if (shouldAutoSelect) {
            await new Promise(resolve => setTimeout(resolve, 500));
            $selectedDevice = device;
            $isLoading = true;
            try {
              const configRaw = await readConfigRaw(device.config_path);
              loadConfig(JSON.parse(configRaw));
              $currentConfigRaw = configRaw;
              $hasUnsavedChanges = false;
              $validationErrors = [];
              $statusMessage = 'Config reloaded from device';
            } catch (e: any) {
              $currentConfigRaw = '';
              $statusMessage = `Error loading config: ${e.message || e}`;
            } finally {
              $isLoading = false;
            }
          }
        }
      });

      unlistenDisconnect = await onDeviceDisconnected(async (name) => {
        const wasSelected = $selectedDevice?.name === name;
        $devices = $devices.filter(d => d.name !== name);
        if (wasSelected) {
          if ($hasUnsavedChanges) {
            await message(`Device "${name}" was disconnected. Unsaved changes lost.`,
              { title: 'Device Disconnected', kind: 'warning' });
          }
          $currentConfigRaw = '';
          $hasUnsavedChanges = false;
        }
        $statusMessage = `Device disconnected: ${name}`;
      });

      if ($devices.length === 1) await selectDevice($devices[0]);

      const handleKeydown = async (e: KeyboardEvent) => {
        const isCmd = e.metaKey || e.ctrlKey;
        if (isCmd && e.key === 's') {
          e.preventDefault();
          if ($selectedDevice && $isDirty) await saveToDevice();
        } else if (isCmd && e.key === 'z') {
          e.preventDefault();
          if (e.shiftKey && $canRedo) redo();
          else if ($canUndo) undo();
        }
      };
      document.addEventListener('keydown', handleKeydown);
      return () => document.removeEventListener('keydown', handleKeydown);
    } catch (e: any) {
      $statusMessage = `Error initializing: ${e.message || e}`;
    }
  });

  onDestroy(() => {
    unlistenConnect?.();
    unlistenDisconnect?.();
  });

  async function selectDevice(device: DetectedDevice) {
    if ($hasUnsavedChanges && !confirm('You have unsaved changes. Discard them?')) return;
    $selectedDevice = device;
    $isLoading = true;
    try {
      if (device.has_config) {
        const configRaw = await readConfigRaw(device.config_path);
        loadConfig(JSON.parse(configRaw));
        $currentConfigRaw = configRaw;
        $hasUnsavedChanges = false;
        $validationErrors = [];
        $statusMessage = 'Config loaded successfully';
      } else {
        $currentConfigRaw = '';
        $statusMessage = 'No config.json found on device';
      }
    } catch (e: any) {
      $statusMessage = `Error reading config: ${e.message || e}`;
    } finally {
      $isLoading = false;
    }
  }

  async function saveToDevice() {
    if (!$selectedDevice) return;
    if (!validate()) {
      showToast('Please fix validation errors before saving', 'error');
      return;
    }
    $isLoading = true;
    try {
      const configObj = normalizeConfig(get(config));
      const configJson = JSON.stringify(configObj, null, 2);
      await writeConfigRaw($selectedDevice.config_path, configJson);
      $currentConfigRaw = configJson;
      $hasUnsavedChanges = false;
      $statusMessage = 'Config saved successfully';
      showToast('Config saved successfully', 'success');
    } catch (e: any) {
      $statusMessage = `Error saving config: ${e.message || e}`;
      showToast($statusMessage, 'error', 5000);
    } finally {
      $isLoading = false;
    }
  }

  async function reloadFromDevice() {
    if (!$selectedDevice) return;
    $isLoading = true;
    try {
      if ($selectedDevice.has_config) {
        const configRaw = await readConfigRaw($selectedDevice.config_path);
        loadConfig(JSON.parse(configRaw));
        $currentConfigRaw = configRaw;
        $hasUnsavedChanges = false;
        $validationErrors = [];
        $statusMessage = 'Config reloaded from device';
      }
    } catch (e: any) {
      $statusMessage = `Error reloading config: ${e.message || e}`;
    } finally {
      $isLoading = false;
    }
  }

  async function resetDevice() {
    if (!$selectedDevice) return;
    await message(
      'To apply config changes, reset your MIDI Captain device:\n\n' +
      '1. Unplug the USB cable\n2. Wait 2 seconds\n3. Plug it back in',
      { title: 'Reset Device', kind: 'info' }
    );
    $statusMessage = 'Waiting for device to reconnect...';
  }

  function loadDemoConfig() {
    try {
      // Load demo STD10 config
      const demoConfig = {
        "device": "std10",
        "global_channel": 0,
        "usb_drive_name": "MIDICAPTAIN",
        "dev_mode": false,
        "display": {
          "button_text_size": "medium",
          "status_text_size": "medium",
          "expression_text_size": "medium"
        },
        "buttons": [
          {"label": "TSC", "press": [{"type": "cc", "cc": 20, "value": 127}], "release": [{"type": "cc", "cc": 20, "value": 0}], "color": "green", "mode": "normal"},
          {"label": "CHOR", "press": [{"type": "cc", "cc": 21, "value": 127}], "release": [{"type": "cc", "cc": 21, "value": 0}], "color": "blue", "mode": "normal"},
          {"label": "DELAY", "press": [{"type": "cc", "cc": 22, "value": 127}], "release": [{"type": "cc", "cc": 22, "value": 0}], "color": "yellow", "mode": "select", "select_group": "fx"},
          {"label": "SHIM", "press": [{"type": "cc", "cc": 23, "value": 127}], "release": [{"type": "cc", "cc": 23, "value": 0}], "color": "magenta", "mode": "normal"},
          {"label": "TREM", "press": [{"type": "cc", "cc": 24, "value": 127}], "release": [{"type": "cc", "cc": 24, "value": 0}], "color": "white", "mode": "momentary"},
          {"label": "WOW", "press": [{"type": "cc", "cc": 25, "value": 127}], "release": [{"type": "cc", "cc": 25, "value": 0}], "color": "orange", "mode": "normal", "off_mode": "off"},
          {"label": "OCT", "press": [{"type": "cc", "cc": 26, "value": 127}], "release": [{"type": "cc", "cc": 26, "value": 0}], "color": "cyan", "mode": "normal"},
          {"label": "FREQ", "press": [{"type": "cc", "cc": 27, "value": 127}], "release": [{"type": "cc", "cc": 27, "value": 0}], "color": "red", "mode": "normal", "off_mode": "off"},
          {"label": "PLATE", "press": [{"type": "cc", "cc": 28, "value": 127}, {"type": "pc", "program": 5}], "release": [{"type": "cc", "cc": 28, "value": 0}], "color": "purple", "mode": "normal"},
          {"label": "TAP", "press": [{"type": "cc", "cc": 29, "value": 127}], "release": [{"type": "cc", "cc": 29, "value": 0}], "color": "white", "mode": "tap"}
        ],
        "encoder": {
          "enabled": true,
          "cc": 11,
          "label": "ENC",
          "min": 0,
          "max": 127,
          "initial": 64,
          "channel": 0,
          "push": {
            "enabled": true,
            "cc": 14,
            "label": "PUSH",
            "mode": "momentary",
            "channel": 0
          }
        },
        "expression": {
          "exp1": {
            "enabled": true,
            "cc": 12,
            "label": "EXP1",
            "min": 0,
            "max": 127,
            "polarity": "normal",
            "threshold": 2,
            "channel": 0
          },
          "exp2": {
            "enabled": false,
            "cc": 13,
            "label": "EXP2",
            "min": 0,
            "max": 127,
            "polarity": "normal",
            "threshold": 2,
            "channel": 0
          }
        }
      };

      loadConfig(demoConfig);
      currentConfigRaw.set(JSON.stringify(demoConfig, null, 2));
      hasUnsavedChanges.set(false);
      validationErrors.set([]);
      statusMessage.set('Demo config loaded (STD10)');

      showToast('Demo config loaded - no device required', 'info');
    } catch (error) {
      statusMessage.set(`Error loading demo: ${error}`);
    }
  }

  function viewJson() {
    jsonText = JSON.stringify($config, null, 2);
    showJsonModal = true;
  }
</script>

<svelte:window onmousemove={handleMouseMove} onmouseup={stopResize} />

<div class="app">
  <!-- header -->
  <header class="header">
    <div class="header-left">
      <h1 class="app-title">MIDI Captain MAX Config Editor</h1>
      {#if appVersion}<span class="version">v{appVersion}</span>{/if}
    </div>
    <div class="header-right">
      {#if $devices.length === 0}
        <span class="no-device-text">No device connected</span>
      {:else}
        <div class="device-pill">
          <select class="device-select"
            value={$selectedDevice?.name ?? ''}
            onchange={(e) => {
              const d = $devices.find(x => x.name === e.currentTarget.value);
              if (d) selectDevice(d);
            }}>
            <option value="" disabled>Select device…</option>
            {#each $devices as d}
              <option value={d.name}>{d.name}</option>
            {/each}
          </select>
          <span class="device-chevron">⌄</span>
        </div>
      {/if}
    </div>
  </header>

  <!-- toolbar -->
  <div class="toolbar">
    <div class="toolbar-left">
      <button class="tool-btn" onclick={() => undo()} disabled={!$canUndo}>Undo</button>
      <button class="tool-btn" onclick={() => redo()} disabled={!$canRedo}>Redo</button>
      <div class="dev-mode-row">
        <input type="checkbox" id="dev-mode" class="dev-cb" checked={devMode}
          onchange={(e) => updateField('dev_mode', (e.target as HTMLInputElement).checked)} />
        <label for="dev-mode" class="dev-label">Development mode</label>
        <span class="dev-hint">for iterative testing: USB drive mounts always on device boot. (Not recommendded for live use.)</span>
      </div>
    </div>
    <div class="toolbar-right">
      <button class="tool-btn secondary" onclick={viewJson}>View JSON</button>
      <button class="tool-btn primary" onclick={saveToDevice}
        disabled={!$selectedDevice || $isLoading || hasErrors}>
        Save to Device <span class="arrow">▾</span>
      </button>
    </div>
  </div>

  <!-- main content -->
  <div class="main">
    {#if ($selectedDevice || $currentConfigRaw) && !$isLoading}
      <div class="left-panel" class:collapsed={leftPanelCollapsed} style="width: {leftPanelCollapsed ? '40px' : leftPanelWidth + 'px'}">
        <button class="collapse-toggle" onclick={() => leftPanelCollapsed = !leftPanelCollapsed} title={leftPanelCollapsed ? 'Expand panel' : 'Collapse panel'}>
          {leftPanelCollapsed ? '▶' : '◀'}
        </button>
        <LeftPanel />
      </div>
      {#if !leftPanelCollapsed}
      <div class="resizer" onmousedown={startResize} class:resizing={isResizing}></div>
      {/if}
      <div class="right-panel"><ButtonSettingsPanel /></div>
    {:else if $isLoading}
      <div class="center-state"><div class="spinner"></div><span>Loading…</span></div>
    {:else}
      <div class="center-state">
        <p class="center-title">No device selected</p>
        <p class="center-sub">Connect a MIDI Captain and select it above, or try demo mode</p>
        <button class="tool-btn primary demo-btn" onclick={loadDemoConfig}>
          Load Demo Config (STD10)
        </button>
      </div>
    {/if}
  </div>

  <!-- status bar -->
  <footer class="statusbar">
    <div class="status-left">
      <span class="dot {statusDot}"></span>
      <span class="status-text">{$statusMessage}</span>
    </div>
    <div class="status-right">
      <button class="ghost-btn" onclick={reloadFromDevice} disabled={!$selectedDevice || $isLoading}>Reload</button>
      <button class="ghost-btn" onclick={resetDevice} disabled={!$selectedDevice || $isLoading}>Reset Device</button>
    </div>
  </footer>
</div>

<!-- JSON modal -->
{#if showJsonModal}
  <div class="modal-backdrop" role="dialog" aria-modal="true" tabindex="0"
    onclick={() => showJsonModal = false}
    onkeydown={(e) => e.key === 'Escape' && (showJsonModal = false)}>
    <div class="modal" role="document"
      onclick={(e) => e.stopPropagation()}
      onkeydown={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <span class="modal-title">Configuration JSON</span>
        <button class="modal-close" onclick={() => showJsonModal = false}>✕</button>
      </div>
      <pre class="json-view">{jsonText}</pre>
      <div class="modal-footer">
        <button class="tool-btn secondary" onclick={() => navigator.clipboard.writeText(jsonText)}>Copy</button>
        <button class="tool-btn" onclick={() => showJsonModal = false}>Close</button>
      </div>
    </div>
  </div>
{/if}

<!-- Toast notifications -->
{#each $toasts as toast (toast.id)}
  <Toast
    message={toast.message}
    type={toast.type}
    duration={toast.duration}
    onClose={() => removeToast(toast.id)}
  />
{/each}

<style>
  :global(*) { box-sizing: border-box; margin: 0; padding: 0; }
  :global(body) {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    background: #0f0f1a;
    color: #e5e7eb;
    height: 100vh;
    overflow: hidden;
  }
  :global(input,select,button) { font-family: inherit; font-size: inherit; }

  .app { display: flex; flex-direction: column; height: 100vh; background: #0f0f1a; }

  /* Header */
  .header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 20px; background: #12121f;
    border-bottom: 1px solid #1e1e2e; flex-shrink: 0; min-height: 48px;
  }
  .header-left { display: flex; align-items: baseline; gap: 8px; }
  .app-title { font-size: 15px; font-weight: 600; color: #f3f4f6; }
  .version { font-size: 11px; color: #6b7280; }
  .header-right { display: flex; align-items: center; gap: 10px; }
  .device-pill { position: relative; display: flex; align-items: center; }
  .device-select {
    appearance: none; background: #1a1a2e; border: 1px solid #2a2a40;
    border-radius: 8px; color: #e5e7eb; padding: 6px 32px 6px 12px;
    font-size: 13px; font-weight: 500; cursor: pointer;
  }
  .device-select:focus { outline: none; border-color: #6366f1; }
  .device-chevron { position: absolute; right: 10px; font-size: 12px; color: #6b7280; pointer-events: none; }
  .no-device-text { font-size: 13px; color: #6b7280; font-style: italic; }

  /* Toolbar */
  .toolbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 16px; background: #12121f;
    border-bottom: 1px solid #1e1e2e; flex-shrink: 0; gap: 12px;
  }
  .toolbar-left, .toolbar-right { display: flex; align-items: center; gap: 8px; }
  .tool-btn {
    display: inline-flex; align-items: center; gap: 5px;
    padding: 6px 14px; background: #1a1a2e; border: 1px solid #2a2a40;
    border-radius: 6px; color: #d1d5db; font-size: 13px; cursor: pointer;
    transition: background 0.15s;
  }
  .tool-btn:hover:not(:disabled) { background: #222238; border-color: #3d3d5c; color: #f3f4f6; }
  .tool-btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .tool-btn.primary { background: #4f46e5; border-color: #4f46e5; color: #fff; font-weight: 600; }
  .tool-btn.primary:hover:not(:disabled) { background: #5a52f0; }
  .tool-btn.secondary { background: transparent; color: #9ca3af; }
  .tool-btn.secondary:hover:not(:disabled) { background: #1a1a2e; color: #e5e7eb; }
  .arrow { font-size: 11px; }
  .dev-mode-row { display: flex; align-items: center; gap: 6px; margin-left: 4px; }
  .dev-cb { width: 15px; height: 15px; accent-color: #4f46e5; cursor: pointer; }
  .dev-label { font-size: 13px; color: #d1d5db; cursor: pointer; user-select: none; }
  .dev-hint { font-size: 11px; color: #6b7280; }

  /* Main */
  .main { display: flex; flex: 1; overflow: hidden; }
  .left-panel {
    position: relative;
    flex-shrink: 0;
    min-width: 0;
    overflow-y: auto;
    border-right: 1px solid #1e1e2e;
    background: #0f0f1a;
    transition: width 0.3s ease;
  }

  .left-panel.collapsed {
    overflow: hidden;
  }

  .resizer {
    width: 4px;
    background: #1e1e2e;
    cursor: col-resize;
    flex-shrink: 0;
    transition: background 0.2s ease;
    position: relative;
  }

  .resizer:hover,
  .resizer.resizing {
    background: #4f46e5;
  }

  .resizer::before {
    content: '';
    position: absolute;
    left: -2px;
    right: -2px;
    top: 0;
    bottom: 0;
  }

  .collapse-toggle {
    position: absolute;
    top: 8px;
    right: 8px;
    z-index: 10;
    width: 32px;
    height: 32px;
    padding: 0;
    background: #1f2937;
    border: 1px solid #374151;
    border-radius: 6px;
    color: #9ca3af;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    transition: all 0.2s ease;
  }

  .collapse-toggle:hover {
    background: #374151;
    color: #ffffff;
    border-color: #4b5563;
  }

  .collapsed .collapse-toggle {
    right: 4px;
  }

  .right-panel {
    flex: 1;
    overflow-y: auto;
    background: #0f0f1a;
  }

  .center-state { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; gap: 8px; }
  .center-title { font-size: 15px; font-weight: 500; color: #6b7280; }
  .center-sub { font-size: 13px; color: #4b5563; }
  .spinner {
    width: 28px; height: 28px; border: 3px solid #1e1e2e;
    border-top-color: #4f46e5; border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Status bar */
  .statusbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 16px; background: #0d0d18;
    border-top: 1px solid #1e1e2e; flex-shrink: 0; min-height: 40px;
  }
  .status-left { display: flex; align-items: center; gap: 7px; }
  .dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
  .dot.success { background: #22c55e; }
  .dot.error { background: #ef4444; }
  .dot.idle { background: #374151; }
  .status-text { font-size: 12px; color: #6b7280; }
  .status-right { display: flex; gap: 8px; }
  .ghost-btn {
    background: transparent; border: 1px solid #2a2a40; border-radius: 6px;
    color: #9ca3af; padding: 4px 12px; font-size: 12px; cursor: pointer;
  }
  .ghost-btn:hover:not(:disabled) { background: #1a1a2e; color: #e5e7eb; }
  .ghost-btn:disabled { opacity: 0.3; cursor: not-allowed; }

  /* JSON Modal */
  .modal-backdrop {
    position: fixed; inset: 0; background: rgba(0,0,0,0.7);
    display: flex; align-items: center; justify-content: center; z-index: 1000;
  }
  .modal {
    background: #14141f; border: 1px solid #2a2a40; border-radius: 12px;
    width: 560px; max-height: 80vh; display: flex; flex-direction: column; overflow: hidden;
  }
  .modal-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 18px; border-bottom: 1px solid #1e1e2e;
  }
  .modal-title { font-size: 14px; font-weight: 600; color: #e5e7eb; }
  .modal-close { background: none; border: none; color: #6b7280; font-size: 16px; cursor: pointer; padding: 2px 6px; border-radius: 4px; }
  .modal-close:hover { color: #e5e7eb; background: #1e1e2e; }
  .json-view {
    flex: 1; overflow-y: auto; padding: 16px 18px;
    font-size: 12px; line-height: 1.6;
    font-family: 'SF Mono', 'Fira Mono', monospace;
    color: #a5b4fc; white-space: pre;
  }
  .modal-footer {
    display: flex; justify-content: flex-end; gap: 8px;
    padding: 12px 18px; border-top: 1px solid #1e1e2e;
  }
</style>
