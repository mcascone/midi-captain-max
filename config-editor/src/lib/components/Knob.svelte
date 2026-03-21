<script lang="ts">
  interface Props {
    value: number;
    min?: number;
    max?: number;
    step?: number;
    label?: string;
    unit?: string;
    disabled?: boolean;
    onchange?: (value: number) => void;
  }

  let {
    value = $bindable(0),
    min = 0,
    max = 127,
    step = 1,
    label = '',
    unit = '',
    disabled = false,
    onchange
  }: Props = $props();

  let isDragging = $state(false);
  let startY = $state(0);
  let startValue = $state(0);

  // Calculate angle based on value (270 degree range, -135 to +135)
  let angle = $derived(((value - min) / (max - min)) * 270 - 135);

  // Calculate arc path for the value indicator
  let arcPath = $derived.by(() => {
    const radius = 40;
    const cx = 50;
    const cy = 50;

    // Starting at -135 degrees (bottom left)
    const startAngleDeg = -135;
    const endAngleDeg = angle;

    // Use same coordinate system as indicator line:
    // x = cx + r * sin(angle), y = cy - r * cos(angle)
    const toCartesian = (deg: number) => {
      const rad = deg * Math.PI / 180;
      return {
        x: cx + radius * Math.sin(rad),
        y: cy - radius * Math.cos(rad)
      };
    };

    const start = toCartesian(startAngleDeg);
    const end = toCartesian(endAngleDeg);

    // Large arc flag: 1 if arc spans > 180°
    const sweep = endAngleDeg - startAngleDeg;
    const largeArc = sweep > 180 ? 1 : 0;

    // Sweep flag is always 1 (clockwise)
    return `M ${start.x.toFixed(2)} ${start.y.toFixed(2)} A ${radius} ${radius} 0 ${largeArc} 1 ${end.x.toFixed(2)} ${end.y.toFixed(2)}`;
  });

  // Format display value
  let displayValue = $derived(`${value}${unit}`);

  function handleMouseDown(e: MouseEvent) {
    if (disabled) return;
    isDragging = true;
    startY = e.clientY;
    startValue = value;
    e.preventDefault();
  }

  function handleMouseMove(e: MouseEvent) {
    if (!isDragging || disabled) return;

    const deltaY = startY - e.clientY; // Inverted: up = increase
    const sensitivity = 0.5;
    const range = max - min;
    const deltaValue = (deltaY * sensitivity * range) / 100;

    let newValue = startValue + deltaValue;
    newValue = Math.max(min, Math.min(max, newValue));

    // Apply step
    newValue = Math.round(newValue / step) * step;

    if (newValue !== value) {
      value = newValue;
      onchange?.(newValue);
    }
  }

  function handleMouseUp() {
    isDragging = false;
  }

  function handleWheel(e: WheelEvent) {
    if (disabled) return;
    e.preventDefault();

    const delta = -Math.sign(e.deltaY) * step;
    let newValue = value + delta;
    newValue = Math.max(min, Math.min(max, newValue));

    if (newValue !== value) {
      value = newValue;
      onchange?.(newValue);
    }
  }

  $effect(() => {
    if (isDragging) {
      window.addEventListener('mousemove', handleMouseMove);
      window.addEventListener('mouseup', handleMouseUp);

      return () => {
        window.removeEventListener('mousemove', handleMouseMove);
        window.removeEventListener('mouseup', handleMouseUp);
      };
    }
  });
</script>

<svelte:window onmouseup={handleMouseUp} />

<div class="knob-container" class:disabled>
  {#if label}
    <div class="knob-label">{label}</div>
  {/if}

  <div
    class="knob"
    class:dragging={isDragging}
    onmousedown={handleMouseDown}
    onwheel={handleWheel}
    role="slider"
    aria-valuemin={min}
    aria-valuemax={max}
    aria-valuenow={value}
    aria-label={label}
    tabindex={disabled ? -1 : 0}
  >
    <svg viewBox="0 0 100 100" class="knob-svg">
      <!-- Background circle -->
      <circle
        cx="50"
        cy="50"
        r="40"
        fill="none"
        stroke="#1a1a1a"
        stroke-width="3"
      />

      <!-- Track arc -->
      <path
        d="M 15.85 84.15 A 40 40 0 1 1 84.15 84.15"
        fill="none"
        stroke="#333333"
        stroke-width="3"
        stroke-linecap="round"
      />

      <!-- Value arc -->
      <path
        d="M 15.85 84.15 A 40 40 0 {angle > 0 ? '1' : '0'} 1 {50 + 40 * Math.cos((angle + 90) * Math.PI / 180)} {50 + 40 * Math.sin((angle + 90) * Math.PI / 180)}"
        fill="none"
        stroke="var(--accent-primary)"
        stroke-width="3"
        stroke-linecap="round"
        class="value-arc"
      />

      <!-- Center circle -->
      <circle cx="50" cy="50" r="32" fill="#0a0a0a" />

      <!-- Indicator line -->
      <line
        x1="50"
        y1="50"
        x2={50 + 28 * Math.sin(angle * Math.PI / 180)}
        y2={50 - 28 * Math.cos(angle * Math.PI / 180)}
        stroke="var(--accent-primary)"
        stroke-width="3"
        stroke-linecap="round"
        class="indicator"
      />
    </svg>
  </div>

  <div class="knob-value">{displayValue}</div>
</div>

<style>
  .knob-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    min-width: 80px;
  }

  .knob-container.disabled {
    opacity: 0.4;
    pointer-events: none;
  }

  .knob-label {
    font-size: var(--text-sm);
    color: var(--text-secondary);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .knob {
    width: 80px;
    height: 80px;
    cursor: pointer;
    user-select: none;
    transition: transform 0.1s ease;
  }

  .knob:hover {
    transform: scale(1.05);
  }

  .knob.dragging {
    cursor: grabbing;
  }

  .knob:focus-visible {
    outline: 2px solid var(--accent-primary);
    outline-offset: 4px;
    border-radius: 50%;
  }

  .knob-svg {
    width: 100%;
    height: 100%;
    filter: drop-shadow(0 2px 8px rgba(0, 0, 0, 0.3));
  }

  .value-arc {
    filter: drop-shadow(0 0 4px currentColor);
  }

  .indicator {
    filter: drop-shadow(0 0 3px currentColor);
  }

  .knob-value {
    font-size: var(--text-sm);
    color: var(--text-primary);
    font-weight: 600;
    font-variant-numeric: tabular-nums;
    min-width: 50px;
    text-align: center;
  }
</style>
