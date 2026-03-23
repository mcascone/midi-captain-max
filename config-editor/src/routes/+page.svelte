<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { get } from 'svelte/store';
  import { message } from '@tauri-apps/plugin-dialog';
  import { getVersion } from '@tauri-apps/api/app';
  import { Toast } from '@skeletonlabs/skeleton-svelte';
  import {
    devices, selectedDevice, currentConfigRaw,
    hasUnsavedChanges, validationErrors, statusMessage, isLoading, isReloadingDevice,
    showToast, lastSavedTimestamp, firmwareVersion, saveFeedback
  } from '$lib/stores';
  import { toaster } from '$lib/toaster';
  import {
    scanDevices, startDeviceWatcher,
    onDeviceConnected, onDeviceDisconnected,
    listMidiPorts
  } from '$lib/api';
  import type { DetectedDevice } from '$lib/types';
  import LeftPanel from '$lib/components/LeftPanel.svelte';
  import ButtonSettingsPanel from '$lib/components/ButtonSettingsPanel.svelte';
  import { loadConfig, validate, normalizeConfig, config, isDirty, canUndo, canRedo, undo, redo, updateField } from '$lib/formStore';
  import * as deviceService from '$lib/services/deviceService';

  let appVersion = $state('');
  let showJsonModal = $state(false);
  let jsonText = $state('');
  let unlistenConnect: (() => void) | undefined;
  let unlistenDisconnect: (() => void) | undefined;
  let leftPanelCollapsed = $state(false);
  let leftPanelWidth = $state(780);
  let isResizing = $state(false);
  let reloadDevicePath = $state<string | null>(null); // Track device during reload cycle

  let devMode = $derived($config.dev_mode ?? false);
  let hasErrors = $derived($validationErrors.length > 0);
  let statusDot = $derived(
    $statusMessage.toLowerCase().includes('error') ? 'error'
    : $statusMessage.toLowerCase().includes('saved') || $statusMessage.toLowerCase().includes('success') ? 'success'
    : 'idle'
  );

  // Config complexity metrics
  let configStats = $derived.by(() => {
    const buttons = $config.buttons?.length ?? 0;
    const configured = $config.buttons?.filter(b =>
      (b.press && b.press.length > 0) ||
      (b.release && b.release.length > 0)
    ).length ?? 0;
    const totalCommands = $config.buttons?.reduce((sum, b) => {
      return sum +
        (b.press?.length ?? 0) +
        (b.release?.length ?? 0) +
        (b.long_press?.length ?? 0) +
        (b.long_release?.length ?? 0);
    }, 0) ?? 0;
    return { buttons, configured, totalCommands };
  });

  // Format last saved time
  let lastSavedText = $derived.by(() => {
    if (!$lastSavedTimestamp) return 'Never';
    const now = new Date();
    const diff = Math.floor((now.getTime() - $lastSavedTimestamp.getTime()) / 1000);

    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    return $lastSavedTimestamp.toLocaleDateString();
  });

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

      // Test MIDI ports detection
      console.log('[APP] Testing MIDI ports...');
      try {
        const midiPorts = await listMidiPorts();
        console.log('[APP] MIDI ports available:', midiPorts);
        if (midiPorts.length === 0) {
          console.warn('[APP] No MIDI ports detected!');
        }
      } catch (midiErr) {
        console.error('[APP] Failed to list MIDI ports:', midiErr);
      }

      $devices = await scanDevices();
      await startDeviceWatcher();

      unlistenConnect = await onDeviceConnected(async (device) => {
        const exists = $devices.some(d => d.path === device.path);
        if (!exists) {
          $devices = [...$devices, device];
          $statusMessage = `Device connected: ${device.name}`;

          // Auto-select if: only device, was previously selected, or reconnecting after reload
          const shouldAutoSelect = $devices.length === 1 ||
            ($selectedDevice && $selectedDevice.path === device.path) ||
            (reloadDevicePath && reloadDevicePath === device.path);

          if (shouldAutoSelect) {
            await new Promise(resolve => setTimeout(resolve, 500));
            await deviceService.selectDevice(device);

            // Clear reload tracking after successful reconnect
            if (reloadDevicePath === device.path) {
              reloadDevicePath = null;
            }
          }
        }
      });

      unlistenDisconnect = await onDeviceDisconnected(async (name) => {
        const wasSelected = $selectedDevice?.name === name;
        const disconnectedDevice = $devices.find(d => d.name === name);

        $devices = $devices.filter(d => d.name !== name);

        if (wasSelected) {
          // If disconnecting during reload cycle, save path for reconnect
          if ($isReloadingDevice && disconnectedDevice) {
            reloadDevicePath = disconnectedDevice.path;
          } else if ($hasUnsavedChanges) {
            // Only warn about unsaved changes if NOT during expected reload
            await message(`Device "${name}" was disconnected. Unsaved changes lost.`,
              { title: 'Device Disconnected', kind: 'warning' });
          }

          // Clear selection and config state
          $selectedDevice = null;
          $currentConfigRaw = '';
          $hasUnsavedChanges = false;
        }

        // Suppress disconnect message during expected reload cycle
        if (!$isReloadingDevice) {
          $statusMessage = `Device disconnected: ${name}`;
        }
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

      // Cleanup in onDestroy instead of returning from async onMount
    } catch (e: any) {
      $statusMessage = `Error initializing: ${e.message || e}`;
    }
  });

  onDestroy(() => {
    // Clean up keyboard event listener
    const handleKeydown = (e: KeyboardEvent) => {
      const isCmd = e.metaKey || e.ctrlKey;
      if (isCmd && e.key === 's') {
        e.preventDefault();
      } else if (isCmd && e.key === 'z') {
        e.preventDefault();
      }
    };
    document.removeEventListener('keydown', handleKeydown);

    // Clean up device watchers
    unlistenConnect?.();
    unlistenDisconnect?.();
  });

  // Device selection delegated to deviceService
  const selectDevice = deviceService.selectDevice;

  // Save only (auto-reload if dev mode)
  const saveToDevice = deviceService.saveToDevice;

  // Eject logic delegated to deviceService

  // Reload delegated to deviceService
  const reloadFromDevice = deviceService.reloadFromDevice;

  // Reset instructions delegated to deviceService
  const resetDevice = deviceService.resetDevice;

  function loadDemoConfig() {
    try {
      // Load demo STD10 config
      const demoConfig: import('$lib/types').MidiCaptainConfig = {
        "device": "std10" as import('$lib/types').DeviceType,
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
      <button
        class="tool-btn primary save-btn"
        class:saving={$saveFeedback === 'saving'}
        class:success={$saveFeedback === 'success'}
        onclick={saveToDevice}
        disabled={!$selectedDevice || $isLoading || hasErrors}>
        {#if $saveFeedback === 'saving'}
          <span class="btn-spinner"></span>
          Saving…
        {:else if $saveFeedback === 'success'}
          <span class="checkmark">✓</span>
          Saved!
        {:else}
          Save to Device <span class="arrow">▾</span>
        {/if}
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
      <div class="center-state">
        <div class="loading-container">
          <div class="spinner-modern"></div>
          <div class="loading-text">Loading configuration…</div>
        </div>
      </div>
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
      {#if $selectedDevice && configStats.buttons > 0}
        <span class="status-divider">•</span>
        <span class="status-stat" title="Configured buttons / Total buttons">
          {configStats.configured}/{configStats.buttons} buttons
        </span>
        <span class="status-stat" title="Total MIDI commands across all buttons">
          {configStats.totalCommands} commands
        </span>
      {/if}
    </div>
    <div class="status-right">
      {#if $lastSavedTimestamp}
        <span class="status-info" title="Last saved: {$lastSavedTimestamp.toLocaleString()}">
          Saved {lastSavedText}
        </span>
      {/if}
      {#if $firmwareVersion}
        <span class="status-info" title="Application version">v{$firmwareVersion}</span>
      {/if}
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
<Toast.Group {toaster}>
  {#snippet children(toast)}
    <Toast {toast} class={`toast-item toast-${toast.type}`}>
      <Toast.Message class="toast-message">
        <Toast.Title class="toast-title">{toast.title}</Toast.Title>
        {#if toast.description}
          <Toast.Description class="toast-description">{toast.description}</Toast.Description>
        {/if}
      </Toast.Message>
      <Toast.CloseTrigger class="toast-close">✕</Toast.CloseTrigger>
    </Toast>
  {/snippet}
</Toast.Group>

<style>
  :global(*) { box-sizing: border-box; margin: 0; padding: 0; }
  :global(body) {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    font-size: 14px;
    background: var(--bg-dark);
    color: #e5e7eb;
    height: 100vh;
    overflow: hidden;
  }
  :global(input,select,button) { font-family: inherit; font-size: inherit; }

  .app { display: flex; flex-direction: column; height: 100vh; background: var(--bg-dark); }

  /* Header */
  .header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 14px 24px; background: #0d0d0d;
    border-bottom: 1px solid var(--border-default); flex-shrink: 0; min-height: 56px;
  }
  .header-left { display: flex; align-items: baseline; gap: 8px; }
  .app-title { font-size: var(--text-xl); font-weight: 700; color: var(--text-primary); letter-spacing: -0.01em; }
  .version { font-size: var(--text-xs); color: var(--text-tertiary); font-weight: 500; }
  .header-right { display: flex; align-items: center; gap: 10px; }
  .device-pill { position: relative; display: flex; align-items: center; }
  .device-select {
    appearance: none; background: var(--bg-input); border: 1px solid var(--border-default);
    border-radius: 8px; color: var(--text-primary); padding: 8px 36px 8px 14px;
    font-size: var(--text-sm); font-weight: 500; cursor: pointer;
    transition: all 0.2s ease;
  }
  .device-select:focus { outline: none; border-color: var(--accent-primary); box-shadow: var(--glow-cyan-sm); }
  .device-chevron { position: absolute; right: 10px; font-size: 12px; color: var(--text-tertiary); pointer-events: none; }
  .no-device-text { font-size: var(--text-sm); color: var(--text-secondary); font-style: italic; }

  /* Toolbar */
  .toolbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 12px 24px; background: #0d0d0d;
    border-bottom: 1px solid var(--border-default); flex-shrink: 0; gap: 16px;
  }
  .toolbar-left, .toolbar-right { display: flex; align-items: center; gap: 12px; }
  .tool-btn {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 8px 16px; background: var(--bg-input); border: 1px solid var(--border-default);
    border-radius: 8px; color: #d1d5db; font-size: 13px; cursor: pointer;
    transition: all 0.2s ease; height: 38px;
  }
  .tool-btn:hover:not(:disabled) { background: var(--bg-card); border-color: var(--accent-primary); color: #f3f4f6; box-shadow: var(--glow-cyan-sm); }
  .tool-btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .tool-btn.primary { background: var(--accent-primary); border-color: var(--accent-primary); color: var(--bg-dark); font-weight: 600; }
  .tool-btn.primary:hover:not(:disabled) { background: var(--accent-primary-hover); }
  .tool-btn.secondary { background: transparent; color: #9ca3af; }
  .tool-btn.secondary:hover:not(:disabled) { background: var(--bg-input); color: #e5e7eb; }
  .arrow { font-size: 11px; }
  .dev-mode-row { display: flex; align-items: center; gap: 6px; margin-left: 4px; }
  .dev-cb { width: 15px; height: 15px; accent-color: var(--accent-primary); cursor: pointer; }
  .dev-label { font-size: 13px; color: #d1d5db; cursor: pointer; user-select: none; }
  .dev-hint { font-size: 11px; color: #6b7280; }

  /* Save button animations */
  .save-btn {
    position: relative;
    overflow: hidden;
  }

  .save-btn.saving {
    pointer-events: none;
  }

  .save-btn.success {
    background: #10b981;
    border-color: #10b981;
  }

  .btn-spinner {
    display: inline-block;
    width: 14px;
    height: 14px;
    border: 2px solid rgba(0, 0, 0, 0.3);
    border-top-color: var(--bg-dark);
    border-radius: 50%;
    animation: spin 0.6s linear infinite;
  }

  .checkmark {
    font-size: 16px;
    animation: checkmark-pop 0.3s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  }

  @keyframes checkmark-pop {
    0% { transform: scale(0); }
    50% { transform: scale(1.2); }
    100% { transform: scale(1); }
  }

  /* Main */
  .main { display: flex; flex: 1; overflow: hidden; }
  .left-panel {
    position: relative;
    flex-shrink: 0;
    min-width: 0;
    overflow-y: auto;
    border-right: 1px solid var(--border-default);
    background: var(--bg-dark);
    transition: width 0.3s ease;
  }

  .left-panel.collapsed {
    overflow: hidden;
  }

  .resizer {
    width: 4px;
    background: var(--border-default);
    cursor: col-resize;
    flex-shrink: 0;
    transition: background 0.2s ease;
    position: relative;
  }

  .resizer:hover,
  .resizer.resizing {
    background: var(--accent-primary);
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
    border: 1px solid #333333;
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
    background: #333333;
    color: #ffffff;
    border-color: #444444;
  }

  .collapsed .collapse-toggle {
    right: 4px;
  }

  .right-panel {
    flex: 1;
    overflow-y: auto;
    background: var(--bg-dark);
  }

  .center-state { display: flex; flex-direction: column; align-items: center; justify-content: center; flex: 1; gap: 8px; }
  .center-title { font-size: 15px; font-weight: 500; color: #6b7280; }
  .center-sub { font-size: 13px; color: #444444; }

  /* Enhanced loading state */
  .loading-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 20px;
  }

  .spinner-modern {
    width: 48px;
    height: 48px;
    border: 4px solid #1a1a1a;
    border-top-color: var(--accent-primary);
    border-radius: 50%;
    animation: spin 0.8s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
    filter: drop-shadow(0 0 8px rgba(0, 212, 170, 0.3));
  }

  .loading-text {
    font-size: 14px;
    color: #6b7280;
    animation: pulse 2s ease-in-out infinite;
  }

  @keyframes pulse {
    0%, 100% { opacity: 0.5; }
    50% { opacity: 1; }
  }

  .spinner {
    width: 28px; height: 28px; border: 3px solid var(--border-default);
    border-top-color: var(--accent-primary); border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* Status bar */
  .statusbar {
    display: flex; align-items: center; justify-content: space-between;
    padding: 8px 16px; background: #0d0d0d;
    border-top: 1px solid var(--border-default); flex-shrink: 0; min-height: 40px;
  }
  .status-left { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
  .dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
  .dot.success { background: #22c55e; box-shadow: 0 0 6px rgba(34, 197, 94, 0.4); }
  .dot.error { background: #ef4444; box-shadow: 0 0 6px rgba(239, 68, 68, 0.4); }
  .dot.idle { background: #333333; }
  .status-text { font-size: 12px; color: #6b7280; }
  .status-divider { color: #333333; font-size: 10px; }
  .status-stat {
    font-size: 11px;
    color: #6b7280;
    background: #1a1a1a;
    padding: 2px 8px;
    border-radius: 4px;
    border: 1px solid #2a2a2a;
  }
  .status-right { display: flex; gap: 12px; align-items: center; }
  .status-info {
    font-size: 11px;
    color: #6b7280;
    padding: 2px 8px;
    background: #1a1a1a;
    border-radius: 4px;
  }
  .ghost-btn {
    background: transparent; border: 1px solid var(--border-default); border-radius: 6px;
    color: #9ca3af; padding: 4px 12px; font-size: 12px; cursor: pointer;
  }
  .ghost-btn:hover:not(:disabled) { background: var(--bg-input); color: #e5e7eb; }
  .ghost-btn:disabled { opacity: 0.3; cursor: not-allowed; }

  /* JSON Modal */
  .modal-backdrop {
    position: fixed; inset: 0; background: rgba(0,0,0,0.8);
    display: flex; align-items: center; justify-content: center; z-index: 1000;
    backdrop-filter: blur(4px);
  }
  .modal {
    background: var(--bg-card); border: 1px solid var(--border-default); border-radius: 12px;
    width: 560px; max-height: 80vh; display: flex; flex-direction: column; overflow: hidden;
    box-shadow: var(--shadow-lg);
  }
  .modal-header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 20px 24px; border-bottom: 1px solid var(--border-default);
  }
  .modal-title { font-size: 16px; font-weight: 600; color: #e5e7eb; }
  .modal-close { background: none; border: none; color: #6b7280; font-size: 16px; cursor: pointer; padding: 2px 6px; border-radius: 4px; }
  .modal-close:hover { color: #e5e7eb; background: var(--bg-input); }
  .json-view {
    flex: 1; overflow-y: auto; padding: 16px 18px;
    font-size: 12px; line-height: 1.6;
    font-family: 'SF Mono', 'Fira Mono', monospace;
    color: var(--accent-primary); white-space: pre;
  }
  .modal-footer {
    display: flex; justify-content: flex-end; gap: 8px;
    padding: 12px 18px; border-top: 1px solid var(--border-default);
  }

  /* Toast Notifications */
  :global(.toast-item) {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    min-width: 300px;
    max-width: 400px;
    background: #1f2937;
    border: 1px solid #333333;
  }

  :global(.toast-item.toast-success) {
    border-left: 4px solid #10b981;
  }

  :global(.toast-item.toast-error) {
    border-left: 4px solid #ef4444;
  }

  :global(.toast-item.toast-info) {
    border-left: 4px solid #3b82f6;
  }

  :global(.toast-message) {
    flex: 1;
  }

  :global(.toast-title) {
    font-size: 14px;
    font-weight: 600;
    color: #f3f4f6;
    margin: 0;
  }

  :global(.toast-description) {
    font-size: 12px;
    color: #d1d5db;
    margin: 4px 0 0 0;
  }

  :global(.toast-close) {
    background: transparent;
    border: none;
    color: #9ca3af;
    font-size: 18px;
    cursor: pointer;
    padding: 0;
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 4px;
    transition: all 0.15s ease;
  }

  :global(.toast-close:hover) {
    background: rgba(255, 255, 255, 0.1);
    color: #f3f4f6;
  }
</style>
