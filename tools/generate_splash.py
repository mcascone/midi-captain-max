#!/usr/bin/env python3
"""
Generate a simple splash screen BMP for MIDI Captain.

Usage:
    python3 generate_splash.py ["LINE 1" ["LINE 2" [output.bmp]]]

Creates a 240×240 BMP with centered text on black background.

Requires: Pillow (install with: pip3 install Pillow)
"""

import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("Error: Pillow library not found")
    print("Install with: pip3 install Pillow")
    print("Or: python3 -m pip install Pillow")
    sys.exit(1)

def generate_splash(line1="MIDI CAPTAIN", line2="", output="splash.bmp"):
    """Generate a simple splash screen BMP."""

    # Create 240×240 black image
    img = Image.new('RGB', (240, 240), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fall back to default if not available
    try:
        # Try common font locations
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
    except OSError:
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 48)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        except OSError:
            # Fall back to default font
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()

    # Draw line 1 (large, centered)
    if line1:
        bbox = draw.textbbox((0, 0), line1, font=font_large)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (240 - text_width) // 2
        y = 80 if line2 else (240 - text_height) // 2
        draw.text((x, y), line1, fill=(255, 255, 255), font=font_large)

    # Draw line 2 (smaller, centered below line 1)
    if line2:
        bbox = draw.textbbox((0, 0), line2, font=font_small)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (240 - text_width) // 2
        y = 150
        draw.text((x, y), line2, fill=(200, 200, 200), font=font_small)

    # Save as uncompressed 24-bit BMP
    img.save(output, 'BMP')
    print(f"[OK] Created {output}")
    print(f"     Size: {img.size}")
    print(f"     Mode: {img.mode}")

    # Get file size
    import os
    size_kb = os.path.getsize(output) / 1024
    print(f"     File: {size_kb:.1f} KB")
    print(f"\nCopy {output} to the root of your MIDICAPTAIN drive")


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No args - use defaults
        generate_splash()
    elif len(sys.argv) == 2:
        # One arg - line 1 only
        generate_splash(line1=sys.argv[1])
    elif len(sys.argv) == 3:
        # Two args - both lines
        generate_splash(line1=sys.argv[1], line2=sys.argv[2])
    elif len(sys.argv) == 4:
        # Three args - both lines + output file
        generate_splash(line1=sys.argv[1], line2=sys.argv[2], output=sys.argv[3])
    else:
        print("Usage: python3 generate_splash.py [\"LINE 1\" [\"LINE 2\" [output.bmp]]]")
        print("")
        print("Examples:")
        print("  python3 generate_splash.py")
        print('  python3 generate_splash.py "MY BAND"')
        print('  python3 generate_splash.py "MY BAND" "Live Setup"')
        print('  python3 generate_splash.py "MY BAND" "Live Setup" custom_splash.bmp')
        sys.exit(1)
