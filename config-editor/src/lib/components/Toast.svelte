<script lang="ts">
  import { onMount } from 'svelte';
  
  interface Props {
    message: string;
    type?: 'success' | 'error' | 'info';
    duration?: number;
    onClose: () => void;
  }
  
  let { message, type = 'success', duration = 3000, onClose }: Props = $props();
  
  let visible = $state(false);
  
  onMount(() => {
    // Trigger animation
    setTimeout(() => visible = true, 10);
    
    // Auto-close
    const timer = setTimeout(() => {
      visible = false;
      setTimeout(onClose, 300); // Wait for fade out
    }, duration);
    
    return () => clearTimeout(timer);
  });
  
  function handleClose() {
    visible = false;
    setTimeout(onClose, 300);
  }
</script>

<div class="toast" class:visible class:success={type === 'success'} class:error={type === 'error'} class:info={type === 'info'}>
  <div class="toast-icon">
    {#if type === 'success'}✓{:else if type === 'error'}✕{:else}ℹ{/if}
  </div>
  <span class="toast-message">{message}</span>
  <button class="toast-close" onclick={handleClose}>✕</button>
</div>

<style>
  .toast {
    position: fixed;
    bottom: 20px;
    right: 20px;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 16px;
    background: var(--bg-card);
    border: 1px solid var(--border-default);
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    min-width: 280px;
    max-width: 400px;
    z-index: 10000;
    opacity: 0;
    transform: translateY(20px);
    transition: opacity 0.3s, transform 0.3s;
  }
  
  .toast.visible {
    opacity: 1;
    transform: translateY(0);
  }
  
  .toast.success {
    border-left: 3px solid #22c55e;
  }
  
  .toast.error {
    border-left: 3px solid #ef4444;
  }
  
  .toast.info {
    border-left: 3px solid #3b82f6;
  }
  
  .toast-icon {
    flex-shrink: 0;
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
    font-weight: bold;
  }
  
  .toast.success .toast-icon {
    color: #22c55e;
  }
  
  .toast.error .toast-icon {
    color: #ef4444;
  }
  
  .toast.info .toast-icon {
    color: #3b82f6;
  }
  
  .toast-message {
    flex: 1;
    font-size: 13px;
    color: #e5e7eb;
    line-height: 1.4;
  }
  
  .toast-close {
    flex-shrink: 0;
    background: none;
    border: none;
    color: #6b7280;
    font-size: 14px;
    cursor: pointer;
    padding: 2px 4px;
    border-radius: 4px;
    transition: color 0.15s, background 0.15s;
  }
  
  .toast-close:hover {
    color: #e5e7eb;
    background: var(--bg-input);
  }
</style>
