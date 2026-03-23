<script lang="ts">
  import { config, setDevice, updateField } from '$lib/formStore';
  import Toggle from './Toggle.svelte';
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
    <div class="field-group">
      <div class="field-row">
        <div class="field">
          <label for="device-type" class="field-label">Device Type</label>
          <select
            id="device-type"
            value={$config.device}
            onchange={handleDeviceChange}
          >
            <option value="std10">STD10 (10 buttons)</option>
            <option value="mini6">Mini6 (6 buttons)</option>
          </select>
          <p class="help-text">
            {#if $config.device === 'mini6'}
              Mini6 supports 6 buttons only. Encoder and expression pedals are not available.
            {:else}
              STD10 supports 10 buttons, encoder, and expression pedals.
            {/if}
          </p>
        </div>

        <div class="field">
          <label for="global-channel" class="field-label">Global MIDI Channel</label>
          <input
            id="global-channel"
            type="number"
            value={globalChannel}
            onblur={handleGlobalChannelChange}
            min="1"
            max="16"
          />
          <p class="help-text">
            Default MIDI channel for all buttons (1-16). Individual buttons can override this setting.
          </p>
        </div>
      </div>

      <div class="field">
        <label for="midi-transport" class="field-label">MIDI Output</label>
        <select
          id="midi-transport"
          value={midiTransport}
          onchange={handleMidiTransportChange}
        >
          <option value="usb">USB only</option>
          <option value="trs">TRS / Serial only</option>
          <option value="both">USB + TRS (both)</option>
        </select>
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

      <div class="field toggle-field">
        <Toggle
          checked={devMode}
          label="Development Mode"
          onchange={(checked) => updateField('dev_mode', checked)}
        />
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
</div>

<style>
  .device-section {
    display: flex;
    flex-direction: column;
  }

  .device-fields {
    padding: 2rem;
  }

  .field-group {
    display: flex;
    flex-direction: column;
    gap: 2rem;
    max-width: 800px;
  }

  .field-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .toggle-field {
    padding-top: 0.5rem;
  }

  .field-label {
    font-size: 0.875rem;
    color: #9ca3af;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  input[type="number"] {
    max-width: 120px;
  }

  .help-text {
    font-size: 0.8125rem;
    color: #6b7280;
    margin: 0;
    line-height: 1.5;
  }

  .help-text strong {
    color: #9ca3af;
    font-weight: 600;
  }
</style>
