<script lang="ts">
  import { config, setDevice, updateField } from '$lib/formStore';
  import type { DeviceType, MidiTransport } from '$lib/types';

  function handleDeviceChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    setDevice(target.value as DeviceType);
  }

  function handleGlobalChannelChange(e: Event) {
    const target = e.target as HTMLInputElement;
    const value = parseInt(target.value);
    // Clamp to valid MIDI channel range (1-16), store as 0-15
    const clamped = Math.max(1, Math.min(16, value));
    updateField('global_channel', clamped - 1);
  }

  function handleUsbDriveNameChange(e: Event) {
    const target = e.target as HTMLInputElement;
    updateField('usb_drive_name', target.value || undefined);
  }

  function handleDevModeChange(e: Event) {
    const target = e.target as HTMLInputElement;
    updateField('dev_mode', target.checked);
  }

  function handleMidiTransportChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    updateField('midi_transport', target.value as MidiTransport);
  }

  // Display channel as 1-16 (stored internally as 0-15)
  let globalChannel = $derived(($config.global_channel ?? 0) + 1);
  let devMode = $derived($config.dev_mode ?? false);
  let usbDriveName = $derived($config.usb_drive_name ?? '');
  let midiTransport = $derived(($config.midi_transport ?? 'usb') as MidiTransport);

</script>

<div class="device-section">
  <div class="device-fields">
    <div class="field-with-help">
      <label>
        <span class="field-label">Device Type:</span>
        <select
          id="device-type"
          value={$config.device}
          onchange={handleDeviceChange}
        >
          <option value="std10">STD10 (10 buttons)</option>
          <option value="mini6">Mini6 (6 buttons)</option>
        </select>
      </label>
      <p class="help-text">
        {#if $config.device === 'mini6'}
          Mini6 supports 6 buttons only. Encoder and expression pedals are not available.
        {:else}
          STD10 supports 10 buttons, encoder, and expression pedals.
        {/if}
      </p>
    </div>

    <div class="field-with-help">
      <label>
        <span class="field-label">Global MIDI Channel:</span>
        <input
          id="global-channel"
          type="number"
          value={globalChannel}
          onblur={handleGlobalChannelChange}
          min="1"
          max="16"
        />
      </label>
      <p class="help-text">
        Default MIDI channel for all buttons (1-16).
        Individual buttons can override this setting.
      </p>
    </div>

    <div class="field-with-help">
      <label>
        <span class="field-label">MIDI Output:</span>
        <select
          id="midi-transport"
          value={midiTransport}
          onchange={handleMidiTransportChange}
        >
          <option value="usb">USB only</option>
          <option value="trs">TRS / Serial only</option>
          <option value="both">USB + TRS (both)</option>
        </select>
      </label>
      <p class="help-text">
        {#if midiTransport === 'trs'}
          TRS/Serial MIDI only — GP16/GP17 at 31250 baud. No USB MIDI output.
        {:else if midiTransport === 'both'}
          Sends to USB and TRS simultaneously. Use when connecting to both a DAW and a hardware device.
        {:else}
          USB MIDI only. Default for use with a computer or DAW.
        {/if}
      </p>
    </div>

    <div class="field-with-help full-width">
      <label class="checkbox-label">
        <input
          id="dev-mode"
          type="checkbox"
          checked={devMode}
          onchange={handleDevModeChange}
        />
        <span>Development Mode</span>
      </label>
      <p class="help-text">
        {#if devMode}
          <strong>Dev mode:</strong> USB drive always mounts on boot. Convenient for iterating on firmware, but not recommended for live use.
        {:else}
          <strong>Performance mode:</strong> USB drive is hidden on boot. Hold Switch 1 while powering on to temporarily enable it for file updates.
        {/if}
      </p>
    </div>
  </div>
</div>

<style>
  .device-section {
    display: flex;
    flex-direction: column;
  }

  .device-fields {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.5rem;
    padding: 1rem;
    background: #0f172a;
    border-radius: 4px;
  }

  .field-with-help {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .field-with-help.full-width {
    grid-column: 1 / -1;
  }

  .device-fields label {
    display: grid;
    grid-template-columns: 140px 1fr;
    align-items: center;
    gap: 0.75rem;
    color: #e5e7eb;
  }

  .checkbox-label {
    display: flex !important;
    align-items: center;
    gap: 0.5rem;
    font-weight: 500;
    color: #e5e7eb;
    font-size: 0.95rem;
  }

  .checkbox-label input[type="checkbox"] {
    width: 18px;
    height: 18px;
    cursor: pointer;
  }

  .field-label {
    font-size: 0.875rem;
    color: #9ca3af;
    text-align: right;
    font-weight: 500;
  }

  .device-fields select,
  .device-fields input[type="number"] {
    padding: 0.5rem 0.75rem;
    border: 1px solid #4b5563;
    border-radius: 4px;
    font-size: 0.875rem;
    background: #374151;
    color: #e5e7eb;
    width: 100%;
  }

  .device-fields select:hover,
  .device-fields input[type="number"]:hover {
    background: #4b5563;
  }

  .device-fields select {
    cursor: pointer;
  }

  .device-fields select:focus,
  .device-fields input:focus {
    outline: 2px solid #8b5cf6;
    outline-offset: 1px;
  }

  .help-text {
    font-size: 0.8rem;
    color: #9ca3af;
    margin: 0;
    line-height: 1.4;
  }

  .help-text strong {
    color: #e5e7eb;
  }
</style>
