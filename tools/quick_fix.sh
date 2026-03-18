#!/bin/bash
# Quick fix script - copies the fixed boot.py to device

# Resolve script directory for path-independent execution
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "📌 MIDI Captain Quick Fix"
echo ""
echo "This will copy the fixed boot.py to your device"
echo ""
echo "Steps:"
echo "1. Hold Switch 1 (top-left footswitch)"
echo "2. While holding, plug in USB cable"
echo "3. Wait for /Volumes/MIDICAPTAIN to appear"
echo "4. Press Enter here"
echo ""
read -p "Press Enter when device is mounted... "

if [ ! -d "/Volumes/MIDICAPTAIN" ]; then
    echo "❌ Device not found at /Volumes/MIDICAPTAIN"
    exit 1
fi

echo "✓ Device found!"
echo "📝 Copying fixed boot.py..."

cp "$REPO_ROOT/firmware/circuitpython/boot.py" /Volumes/MIDICAPTAIN/boot.py

echo "✓ Fixed boot.py copied!"
echo "💾 Syncing..."
sync

echo "📤 Ejecting device..."
diskutil eject /Volumes/MIDICAPTAIN

echo ""
echo "✅ Done! Now:"
echo "1. Unplug the USB cable"
echo "2. Plug it back in (WITHOUT holding any button)"
echo "3. The firmware should now run!"
