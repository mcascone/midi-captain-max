<script lang="ts">
  import { config, updateField } from '$lib/formStore';

  let splashScreen = $derived($config.splash_screen);

  function handleSplashEnabled(e: Event) {
    const target = e.target as HTMLInputElement;
    updateField('splash_screen.enabled', target.checked);
  }

  function handleSplashDuration(e: Event) {
    const target = e.target as HTMLInputElement;
    const value = parseInt(target.value, 10);
    if (!isNaN(value)) {
      // Clamp to match UI constraints (max 5000ms)
      const clamped = Math.max(0, Math.min(value, 5000));
      updateField('splash_screen.duration_ms', clamped);
    }
  }

  function handleIdleTimeout(e: Event) {
    const target = e.target as HTMLInputElement;
    const value = parseInt(target.value, 10);
    if (!isNaN(value)) {
      // Clamp to match UI constraints (max 600 seconds)
      const clamped = Math.max(0, Math.min(value, 600));
      updateField('splash_screen.idle_timeout_seconds', clamped);
    }
  }
</script>

<div class="splash-section">
  <div class="section-header">
    <span class="header-text">Boot Splash Screen</span>
    <span class="header-description">Display a custom image during device startup</span>
  </div>

  <label class="checkbox-label">
    <input
      type="checkbox"
      checked={splashScreen?.enabled ?? true}
      onchange={handleSplashEnabled}
    />
    <span class="field-label-left">Show splash on boot</span>
  </label>

  <label>
    <span class="field-label">Splash duration (ms):</span>
    <input
      type="number"
      min="0"
      max="5000"
      step="100"
      value={splashScreen?.duration_ms ?? 1500}
      oninput={handleSplashDuration}
    />
  </label>

  <label>
    <span class="field-label">Idle timeout (seconds):</span>
    <input
      type="number"
      min="0"
      max="600"
      step="10"
      value={splashScreen?.idle_timeout_seconds ?? 0}
      oninput={handleIdleTimeout}
    />
    <span class="field-hint">Show splash after inactivity (0 = disabled)</span>
  </label>

  <div class="info-card">
    <div class="info-header">📁 Setup Instructions</div>
    <ol class="info-list">
      <li>Create a 240×240 pixel BMP image</li>
      <li>Name it <code>splash.bmp</code></li>
      <li>Copy to the root of your device drive</li>
      <li>Power cycle to see it on boot</li>
    </ol>
  </div>

  <div class="info-card">
    <div class="info-header">🛠️ Generate a Splash</div>
    <p class="info-text">Use the included script to create a text-based splash:</p>
    <code class="code-block">python3 tools/generate_splash.py "MY BAND" "Live Setup"</code>
    <p class="info-text info-note">
      See <code>firmware/circuitpython/SPLASH_README.md</code> for detailed design tips
    </p>
  </div>
</div>

<style>
  .splash-section {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    padding: 1.5rem;
    background: #0f172a;
    border-radius: 4px;
  }

  .section-header {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    padding-bottom: 1rem;
    border-bottom: 2px solid #8b5cf6;
  }

  .header-text {
    font-size: 1.125rem;
    font-weight: 600;
    color: #e5e7eb;
  }

  .header-description {
    font-size: 0.875rem;
    color: #9ca3af;
  }

  .checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    padding: 1rem;
    background: #1e293b;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.2s ease;
  }

  .checkbox-label:hover {
    background: #334155;
  }

  .checkbox-label input[type="checkbox"] {
    width: 20px;
    height: 20px;
    cursor: pointer;
    accent-color: #8b5cf6;
  }

  .field-label-left {
    font-size: 0.9375rem;
    color: #e5e7eb;
    font-weight: 500;
  }

  .splash-section label:not(.checkbox-label) {
    display: grid;
    grid-template-columns: 160px 1fr;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 1rem;
    background: #1e293b;
    border-radius: 6px;
    color: #e5e7eb;
  }

  .field-label {
    font-size: 0.875rem;
    color: #9ca3af;
    text-align: right;
    font-weight: 500;
  }

  .field-hint {
    grid-column: 2;
    font-size: 0.75rem;
    color: #6b7280;
    margin-top: 0.25rem;
  }

  .splash-section input[type="number"] {
    padding: 0.5rem 0.75rem;
    border: 1px solid #4b5563;
    border-radius: 4px;
    font-size: 0.875rem;
    background: #374151;
    color: #e5e7eb;
    width: 100%;
  }

  .splash-section input[type="number"]:focus {
    outline: 2px solid #8b5cf6;
    outline-offset: 1px;
  }

  .info-card {
    padding: 1.25rem;
    background: #1e293b;
    border-radius: 8px;
    border-left: 4px solid #8b5cf6;
  }

  .info-header {
    font-size: 0.9375rem;
    font-weight: 600;
    color: #e5e7eb;
    margin-bottom: 0.75rem;
  }

  .info-list {
    margin: 0;
    padding-left: 1.5rem;
    color: #d1d5db;
    font-size: 0.875rem;
    line-height: 1.7;
  }

  .info-list li {
    margin-bottom: 0.5rem;
  }

  .info-text {
    margin: 0 0 0.75rem 0;
    color: #d1d5db;
    font-size: 0.875rem;
    line-height: 1.6;
  }

  .info-note {
    margin-bottom: 0;
    font-size: 0.8125rem;
    color: #9ca3af;
  }

  code {
    padding: 0.125rem 0.375rem;
    background: #111827;
    border: 1px solid #374151;
    border-radius: 3px;
    color: #c084fc;
    font-size: 0.8125rem;
    font-family: 'Monaco', 'Courier New', monospace;
  }

  .code-block {
    display: block;
    padding: 0.75rem;
    margin: 0.5rem 0;
    background: #111827;
    border: 1px solid #374151;
    border-radius: 6px;
    color: #a5b4fc;
    font-size: 0.8125rem;
    overflow-x: auto;
    white-space: nowrap;
  }
</style>
