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

  // Profile mode toggle
  let profileMode = $state(false);

  // Initialize from button props
  $effect(() => {
    selectedProfileId = button.profile_id || '';
    selectedActionId = button.action_id || '';
    profileMode = Boolean(button.profile_id && button.action_id);
  });

  // Available actions for selected profile
  let availableActions = $derived(
    selectedProfileId ? getProfileActions(selectedProfileId) : []
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

  function handleProfileChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    selectedProfileId = target.value;
    selectedActionId = ''; // Reset action when profile changes
    onUpdate('profile_id', target.value || undefined);
    onUpdate('action_id', undefined);
  }

  function handleActionChange(event: Event) {
    const target = event.target as HTMLSelectElement;
    selectedActionId = target.value;
    onUpdate('action_id', target.value || undefined);

    // Resolve and preview the MIDI commands
    if (selectedProfileId && target.value) {
      const commands = resolveProfileAction(selectedProfileId, target.value);
      if (commands) {
        // Update button's press array with resolved commands
        onUpdate('press', commands);
        console.log('[ProfileSelector] Resolved MIDI commands:', commands);
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
      <!-- Profile Selection -->
      <div class="form-group">
        <label for="profile-select">Device Profile</label>
        <select
          id="profile-select"
          value={selectedProfileId}
          onchange={handleProfileChange}
        >
          <option value="">Select a device...</option>
          {#each profiles as profile}
            <option value={profile.id}>
              {profile.manufacturer} {profile.name}
              {#if profile.type !== 'fixed'}({profile.type}){/if}
            </option>
          {/each}
        </select>
      </div>

      <!-- Action Selection -->
      {#if selectedProfileId}
        <div class="form-group">
          <label for="action-select">Action</label>
          <select
            id="action-select"
            value={selectedActionId}
            onchange={handleActionChange}
          >
            <option value="">Select an action...</option>
            {#each availableActions || [] as action}
              <option value={action.id} title={action.description}>
                {action.label}
              </option>
            {/each}
          </select>
        </div>
      {/if}

      <!-- Resolved MIDI Preview -->
      {#if selectedProfileId && selectedActionId && button.press}
        <div class="midi-preview">
          <strong>Resolved MIDI:</strong>
          <ul>
            {#each button.press as cmd}
              <li>
                {#if cmd.type === 'cc'}
                  CC{cmd.cc} = {cmd.value}
                {:else if cmd.type === 'note'}
                  Note {cmd.note} vel={cmd.velocity}
                {:else if cmd.type === 'pc'}
                  PC {cmd.program}
                {:else if cmd.type === 'pc_inc'}
                  PC+ (step {cmd.pc_step || 1})
                {:else if cmd.type === 'pc_dec'}
                  PC- (step {cmd.pc_step || 1})
                {/if}
                {#if cmd.channel !== undefined}
                  (Ch {cmd.channel + 1})
                {/if}
              </li>
            {/each}
          </ul>
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
    border-radius: 4px;
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

  .form-group {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .form-group label {
    font-size: 0.875rem;
    font-weight: 600;
    color: #e0e0e0;
  }

  .form-group select {
    padding: 0.5rem;
    border: 1px solid #3a3a55;
    border-radius: 4px;
    font-size: 0.875rem;
    font-weight: 500;
    color: #e0e0e0;
    background: #13131f;
  }

  .form-group select:focus {
    outline: none;
    border-color: #6366f1;
    box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
  }

  .midi-preview {
    padding: 0.75rem;
    background: #13131f;
    border: 1px solid #2a2a3e;
    border-radius: 4px;
    font-size: 0.875rem;
  }

  .midi-preview strong {
    display: block;
    margin-bottom: 0.5rem;
    color: #818cf8;
    font-weight: 700;
  }

  .midi-preview ul {
    margin: 0;
    padding-left: 1.25rem;
    list-style-type: disc;
  }

  .midi-preview li {
    margin: 0.25rem 0;
    font-family: 'Courier New', monospace;
    color: #d0d0d0;
    font-weight: 500;
  }
</style>
