<script lang="ts">
  import { profiles, getProfileActions, resolveProfileAction } from '$lib/profiles';
  import type { ButtonConfig, MidiCommand } from '$lib/types';

  interface Props {
    button: ButtonConfig;
    onUpdate: (field: string, value: any) => void;
  }

  let { button, onUpdate }: Props = $props();

  // Selected profile and action (reactive to button changes)
  let selectedProfileId = $state('');
  let selectedActionId = $state('');
  let targetEvent = $state<'press' | 'release' | 'long_press' | 'long_release'>('press');

  // Profile mode toggle - independent of profile/action selection
  let profileMode = $state(false);

  // Initialize from button props only once
  $effect(() => {
    selectedProfileId = button.profile_id || '';
    selectedActionId = button.action_id || '';
    // Only set profileMode to true if we have profile data from config
    // Don't set it to false - let the user control it with the checkbox
    if (button.profile_id) {
      profileMode = true;
    }
  });

  // Available actions for selected profile
  let availableActions = $derived(
    selectedProfileId ? getProfileActions(selectedProfileId) : []
  );

  // Get the commands for the selected target event
  let targetCommands = $derived(
    button[targetEvent] as MidiCommand[] | undefined
  );

  function handleProfileModeToggle() {
    profileMode = !profileMode;
    if (!profileMode) {
      // Disable profile mode - clear profile fields
      onUpdate('profile_id', undefined);
      onUpdate('action_id', undefined);
      selectedProfileId = '';
      selectedActionId = '';
    }
  }

  function handleActionChange(actionId: string) {
    selectedActionId = actionId;
    onUpdate('action_id', actionId);

    // Resolve and preview the MIDI commands
    if (selectedProfileId && actionId) {
      const commands = resolveProfileAction(selectedProfileId, actionId);
      if (commands) {
        // Update button's selected event array with resolved commands
        onUpdate(targetEvent, commands);
        console.log(`[ProfileSelector] Resolved MIDI commands for ${targetEvent}:`, commands);
      }
    }
  }
</script>

<div class="profile-selector">
  <div class="profile-mode-toggle">
    <label>
      <input
        type="checkbox"
        checked={profileMode}
        onchange={handleProfileModeToggle}
      />
      Use Device Profile
    </label>
  </div>

  {#if profileMode}
    <div class="profile-fields">
      <!-- Profile Cards Grid -->
      <div class="section-label">Select Device</div>
      <div class="profile-cards">
        {#each profiles as profile}
          <button
            type="button"
            class="profile-card"
            class:active={selectedProfileId === profile.id}
            onclick={() => {
              selectedProfileId = profile.id;
              selectedActionId = '';
              onUpdate('profile_id', profile.id);
              onUpdate('action_id', undefined);
            }}
          >
            <div class="profile-card-header">
              <span class="profile-name">{profile.manufacturer}</span>
              <span class="profile-type-badge" class:fixed={profile.type === 'fixed'}>
                {profile.type}
              </span>
            </div>
            <div class="profile-model">{profile.name}</div>
          </button>
        {/each}
      </div>

      <!-- Event Target Selector -->
      {#if selectedProfileId}
        <div class="event-selector">
          <div class="section-label">Assign To Event</div>
          <div class="event-buttons">
            <button
              type="button"
              class="event-button"
              class:active={targetEvent === 'press'}
              onclick={() => targetEvent = 'press'}
            >
              Press
            </button>
            <button
              type="button"
              class="event-button"
              class:active={targetEvent === 'release'}
              onclick={() => targetEvent = 'release'}
            >
              Release
            </button>
            <button
              type="button"
              class="event-button"
              class:active={targetEvent === 'long_press'}
              onclick={() => targetEvent = 'long_press'}
            >
              Long Press
            </button>
            <button
              type="button"
              class="event-button"
              class:active={targetEvent === 'long_release'}
              onclick={() => targetEvent = 'long_release'}
            >
              Long Release
            </button>
          </div>
        </div>
      {/if}

      <!-- Actions Grid -->
      {#if selectedProfileId && availableActions}
        <div class="section-label">Select Action</div>
        <div class="actions-grid">
          {#each availableActions as action}
            <button
              type="button"
              class="action-button"
              class:active={selectedActionId === action.id}
              title={action.description}
              onclick={() => handleActionChange(action.id)}
            >
              {action.label}
            </button>
          {/each}
        </div>
      {/if}

      <!-- Resolved MIDI Preview -->
      {#if selectedProfileId && selectedActionId && targetCommands}
        <div class="midi-preview">
          <div class="preview-header">
            <span class="preview-icon">⚡</span>
            <strong>Resolved MIDI ({targetEvent.replace('_', ' ')})</strong>
          </div>
          <div class="midi-commands">
            {#each targetCommands as cmd}
              <span class="midi-chip">
                {#if cmd.type === 'cc'}
                  CC{cmd.cc}={cmd.value}
                {:else if cmd.type === 'note'}
                  Note {cmd.note} vel={cmd.velocity}
                {:else if cmd.type === 'pc'}
                  PC {cmd.program}
                {:else if cmd.type === 'pc_inc'}
                  PC+{cmd.pc_step || 1}
                {:else if cmd.type === 'pc_dec'}
                  PC-{cmd.pc_step || 1}
                {/if}
                {#if cmd.channel !== undefined}
                  <span class="midi-channel">Ch{cmd.channel + 1}</span>
                {/if}
              </span>
            {/each}
          </div>
        </div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .profile-selector {
    margin-bottom: 1rem;
    padding: 1rem;
    background: #1a1a2e;
    border: 1px solid #2a2a3e;
    border-radius: 6px;
  }

  .profile-mode-toggle {
    margin-bottom: 1rem;
  }

  .profile-mode-toggle label {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 600;
    color: #e0e0e0;
    cursor: pointer;
  }

  .profile-fields {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .section-label {
    font-size: 11px;
    font-weight: 700;
    color: #6b7280;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: -0.5rem;
  }

  /* Profile Cards Grid */
  .profile-cards {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 0.75rem;
  }

  .profile-card {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.875rem;
    background: #13131f;
    border: 2px solid #2a2a3e;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.15s ease;
    text-align: left;
  }

  .profile-card:hover {
    border-color: #3a3a4e;
    background: #1a1a2e;
  }

  .profile-card.active {
    border-color: #6366f1;
    background: rgba(99, 102, 241, 0.1);
  }

  .profile-card-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .profile-name {
    font-size: 10px;
    font-weight: 700;
    color: #9ca3af;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .profile-type-badge {
    font-size: 9px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 3px;
    background: #2a2a3e;
    color: #9ca3af;
    text-transform: uppercase;
  }

  .profile-type-badge.fixed {
    background: rgba(34, 197, 94, 0.15);
    color: #22c55e;
  }

  .profile-model {
    font-size: 14px;
    font-weight: 600;
    color: #e5e7eb;
  }

  /* Event Selector */
  .event-selector {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .event-buttons {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
  }

  .event-button {
    padding: 0.625rem 0.75rem;
    background: #13131f;
    border: 1px solid #2a2a3e;
    border-radius: 4px;
    color: #d1d5db;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
    text-align: center;
  }

  .event-button:hover {
    border-color: #3a3a4e;
    background: #1a1a2e;
    color: #e5e7eb;
  }

  .event-button.active {
    background: rgba(249, 115, 22, 0.15);
    border-color: #f97316;
    color: #fb923c;
    font-weight: 600;
  }

  /* Actions Grid */
  .actions-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 0.5rem;
  }

  .action-button {
    padding: 0.625rem 0.75rem;
    background: #13131f;
    border: 1px solid #2a2a3e;
    border-radius: 4px;
    color: #d1d5db;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
    text-align: center;
  }

  .action-button:hover {
    border-color: #3a3a4e;
    background: #1a1a2e;
    color: #e5e7eb;
  }

  .action-button.active {
    background: rgba(99, 102, 241, 0.15);
    border-color: #6366f1;
    color: #818cf8;
    font-weight: 600;
  }

  /* MIDI Preview */
  .midi-preview {
    padding: 0.875rem;
    background: #13131f;
    border: 1px solid #2a2a3e;
    border-radius: 6px;
  }

  .preview-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.625rem;
  }

  .preview-icon {
    font-size: 16px;
  }

  .preview-header strong {
    font-size: 11px;
    font-weight: 700;
    color: #818cf8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .midi-commands {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .midi-chip {
    display: inline-flex;
    align-items: center;
    gap: 0.375rem;
    padding: 0.375rem 0.625rem;
    background: #1a1a2e;
    border: 1px solid #2a2a3e;
    border-radius: 4px;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    font-weight: 600;
    color: #a5b4fc;
  }

  .midi-channel {
    padding: 0.125rem 0.375rem;
    background: rgba(99, 102, 241, 0.2);
    border-radius: 3px;
    font-size: 10px;
    color: #c7d2fe;
  }
</style>
