# Boot Splash Screen

The firmware supports displaying a custom boot splash image while the device initializes.

## Quick Start

1. Create a **240×240 pixel** BMP image (24-bit RGB recommended)
2. Name it `splash.bmp`
3. Copy it to the root of the MIDICAPTAIN drive
4. Reboot the device

The splash will display for 1.5 seconds by default during boot.

## Configuration

Add to your `config.json`:

```json
{
  "splash_screen": {
    "enabled": true,
    "duration_ms": 1500,
    "idle_timeout_seconds": 60
  }
}
```

### Options

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `true` | Whether to show splash screen |
| `duration_ms` | integer | `1500` | How long to display splash during boot (milliseconds) |
| `idle_timeout_seconds` | integer | `0` | Show splash after N seconds of inactivity (0 = disabled) |

### Idle Timeout (Screensaver)

When `idle_timeout_seconds` is set to a value greater than 0, the splash image acts as a screensaver:
- After the configured period of inactivity, the splash image displays automatically
- Any button press, encoder turn, or expression pedal movement wakes the display
- The main screen resumes immediately, showing your last active state

This feature is useful for:
- Protecting the display from burn-in during long idle periods
- Showing branding during breaks in your performance
- Saving power by reducing display activity

## Creating Your Splash Image

### Requirements

- **Dimensions**: 240×240 pixels (square)
- **Format**: BMP (bitmap)
- **Color depth**: 24-bit RGB recommended (8-bit indexed also works)
- **File size**: ~115KB for 24-bit, ~58KB for 8-bit

### Design Tips

- Use high contrast for visibility on the ST7789 display
- Keep important content centered (safe area: 220×220)
- Test on device - colors may look different than on your monitor
- Avoid very fine details (240px is relatively low resolution)

### Tools

**Python (using Pillow):**
```python
from PIL import Image, ImageDraw, ImageFont

# Create 240x240 image
img = Image.new('RGB', (240, 240), color='black')
draw = ImageDraw.Draw(img)

# Add your design (text, shapes, logo, etc.)
font = ImageFont.truetype('/path/to/font.ttf', 60)
text = "MIDI CAPTAIN"
# Center text
bbox = draw.textbbox((0, 0), text, font=font)
text_width = bbox[2] - bbox[0]
text_height = bbox[3] - bbox[1]
x = (240 - text_width) // 2
y = (240 - text_height) // 2
draw.text((x, y), text, fill='white', font=font)

# Save as BMP
img.save('splash.bmp', 'BMP')
```

**GIMP:**
1. File → New → 240×240 pixels
2. Design your splash screen
3. File → Export As → `splash.bmp`
4. Select "24-bit" in BMP export options

**Photoshop:**
1. File → New → 240×240 pixels
2. Design your splash screen
3. File → Save As → BMP format
4. Choose "24-bit" depth

**Online Tools:**
- [Photopea](https://www.photopea.com/) (free Photoshop alternative)
- [Pixlr](https://pixlr.com/editor/)

## Helper Script

Use the included `tools/generate_splash.py` script to create a simple text-based splash:

```bash
python3 tools/generate_splash.py "MIDI CAPTAIN" "Custom Text"
```

This generates `splash.bmp` ready to copy to your device.

## Troubleshooting

### Splash doesn't appear
- Verify `splash.bmp` is in the root directory (not in a subfolder)
- Check file is exactly 240×240 pixels
- Ensure it's a valid BMP format (not PNG/JPG renamed)
- Check config.json has `"enabled": true`

### Display shows garbage/corruption
- File may be corrupt - try re-exporting
- Ensure 24-bit or 8-bit BMP format (not 32-bit or other exotic formats)
- CircuitPython supports uncompressed BMP only (no RLE compression)

### Boot is slower
- Normal - loading and displaying the image adds ~0.5-1s to boot time
- Reduce `duration_ms` if needed
- Set `"enabled": false` to disable

### Want to see boot messages
- Set `"enabled": false` temporarily
- Or remove/rename `splash.bmp`
- Serial console still shows all messages regardless of splash

## Technical Details

- Format: Windows BMP (uncompressed)
- Color space: RGB (no alpha channel needed)
- Orientation: Top-down (standard BMP)
- Storage: FAT32 filesystem on device
- Display: ST7789 240×240 LCD
- Load time: ~200-500ms depending on file size
