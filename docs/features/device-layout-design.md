# Device Layout Design

## Visual Editor Component Specification

This document defines the SVG layout specifications for the interactive device view in the config editor.

---

## Goals

1. Replace card grid with visual device representation
2. Interactive buttons clickable on device layout
3. LED colors visible in hardware positions
4. Labels displayed on buttons
5. Selected button highlighted
6. Device-accurate scale and proportions

---

## STD10 Layout

**Physical layout:** 10 buttons in 2 rows × 5 columns

### Button Grid

```
Row 1:  [1] [2] [3] [4] [5]
Row 2:  [6] [7] [8] [9] [10]
```

### SVG Specifications

- **Viewbox:** 0 0 800 400
- **Button size:** 120×120px (with rounded corners)
- **Button spacing:** 40px horizontal, 40px vertical
- **Row 1 Y:** 60
- **Row 2 Y:** 220
- **LED indicator:** Circle positioned above button center
- **Label:** Text centered on button

### Button Positions

| Button | X   | Y   |
|--------|-----|-----|
| 1      | 40  | 60  |
| 2      | 200 | 60  |
| 3      | 360 | 60  |
| 4      | 520 | 60  |
| 5      | 680 | 60  |
| 6      | 40  | 220 |
| 7      | 200 | 220 |
| 8      | 360 | 220 |
| 9      | 520 | 220 |
| 10     | 680 | 220 |

---

## Mini6 Layout

**Physical layout:** 6 buttons in 2 rows × 3 columns

### Button Grid

```
Row 1:  [1] [2] [3]
Row 2:  [4] [5] [6]
```

### SVG Specifications

- **Viewbox:** 0 0 520 400
- **Button size:** 120×120px (with rounded corners)
- **Button spacing:** 40px horizontal, 40px vertical
- **Row 1 Y:** 60
- **Row 2 Y:** 220
- **LED indicator:** Circle positioned above button center
- **Label:** Text centered on button

### Button Positions

| Button | X   | Y   |
|--------|-----|-----|
| 1      | 40  | 60  |
| 2      | 200 | 60  |
| 3      | 360 | 60  |
| 4      | 40  | 220 |
| 5      | 200 | 220 |
| 6      | 360 | 220 |

---

## Visual States

### Default Button
- Border: 2px solid #4b5563
- Fill: #1f2937
- LED: Off (gray #6b7280)
- Label: white text

### Selected Button
- Border: 3px solid #8b5cf6 (purple)
- Fill: #2d1b4e (purple tint)
- LED: Shows configured color
- Label: white text

### Hover Button
- Border: 2px solid #6b7280
- Fill: #374151
- LED: Shows configured color (dimmed)
- Label: white text

### Multi-command Indicator
- Badge overlay showing command count (e.g., "×3")
- Gradient background on button

---

## LED Color Display

Each button shows its configured LED color:
- Position: Small circle above button
- Size: 20px diameter
- Glow effect: box-shadow with color
- Off state: Gray (#6b7280)

---

## Label Display

- Font: 14px bold
- Position: Centered on button
- Max length: 6 characters (truncate with …)
- Color: White (#ffffff)

---

## Interaction

### Click
- Select button for editing in right panel
- Highlight selected button
- Update ButtonSettingsPanel

### Hover
- Show tooltip with command summary
- Highlight hover state
- Show LED preview

### Multi-command Badge
- Display command count if > 1 command
- Position: Top-right corner of button
- Style: Purple badge with white text

---

## Component Structure

```
DeviceLayout.svelte
├── SVG Container
│   ├── Background/frame
│   ├── Button group (for each button)
│   │   ├── Button rect (clickable)
│   │   ├── LED indicator circle
│   │   ├── Label text
│   │   └── Multi-command badge (if applicable)
│   └── Selection highlight
```

---

## Responsive Behavior

- Scale SVG to fit container width
- Maintain aspect ratio
- Min width: 400px
- Max width: 100% of container

---

## Accessibility

- Each button has aria-label with button number
- Selected button has aria-selected="true"
- Keyboard navigation support (arrow keys)
- Focus indicator for keyboard users

---

## Implementation Notes

- Use Svelte's reactive $derived for button positions based on device type
- Extract button data from config store
- Handle click events to update selectedButtonIndex
- Preserve existing DeviceGrid tooltip functionality
- Animate selection changes (smooth highlight transition)
