#!/bin/bash
# Deploy firmware to MIDI Captain device
#
# Usage: ./tools/deploy.sh [mount_point]
#   mount_point: Optional. Defaults to /Volumes/CIRCUITPY
#
# Example:
#   ./tools/deploy.sh                    # Deploy to default mount
#   ./tools/deploy.sh /Volumes/MIDICAPT  # Deploy to custom mount

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEV_DIR="$PROJECT_ROOT/firmware/dev"
MOUNT_POINT="${1:-/Volumes/CIRCUITPY}"

echo "=== MIDI Captain Firmware Deploy ==="
echo ""

# Check if device is mounted
if [ ! -d "$MOUNT_POINT" ]; then
    echo "❌ Device not found at $MOUNT_POINT"
    echo "   Make sure the MIDI Captain is connected and mounted."
    exit 1
fi

echo "📁 Source: $DEV_DIR"
echo "📱 Target: $MOUNT_POINT"
echo ""

# Deploy files
echo "Copying code.py..."
cp "$DEV_DIR/code.py" "$MOUNT_POINT/"

echo "Copying config.json..."
cp "$DEV_DIR/config.json" "$MOUNT_POINT/"

echo "Copying devices/..."
rm -rf "$MOUNT_POINT/devices"
cp -r "$DEV_DIR/devices" "$MOUNT_POINT/"

echo "Copying fonts/..."
rm -rf "$MOUNT_POINT/fonts"
cp -r "$DEV_DIR/fonts" "$MOUNT_POINT/"

# Sync to ensure writes complete
sync

echo ""
echo "✅ Deploy complete!"
echo "   Device will auto-reload."
