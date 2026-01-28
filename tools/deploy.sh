#!/bin/bash
# Deploy firmware to MIDI Captain device
#
# Usage: ./tools/deploy.sh [mount_point]
#   mount_point: Optional. Defaults to /Volumes/CIRCUITPY
#
# Options:
#   --no-eject    Don't eject after deploy (device resets on each file)
#
# Example:
#   ./tools/deploy.sh                    # Deploy to default mount
#   ./tools/deploy.sh /Volumes/MIDICAPT  # Deploy to custom mount

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEV_DIR="$PROJECT_ROOT/firmware/dev"
MOUNT_POINT="/Volumes/CIRCUITPY"
DO_EJECT=true

# Parse arguments
for arg in "$@"; do
    case $arg in
        --no-eject)
            DO_EJECT=false
            ;;
        /*)
            MOUNT_POINT="$arg"
            ;;
    esac
done

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

# Create a staging area to batch all files
STAGING=$(mktemp -d)
trap "rm -rf $STAGING" EXIT

echo "📦 Staging files..."

# Stage all files
cp "$DEV_DIR/code.py" "$STAGING/"
cp "$DEV_DIR/config.json" "$STAGING/"
cp -r "$DEV_DIR/devices" "$STAGING/"
cp -r "$DEV_DIR/fonts" "$STAGING/"

# Remove __pycache__ from staging
find "$STAGING" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "🚀 Deploying to device..."

# Use rsync for efficient atomic-ish copy
# The --inplace flag minimizes file rewrites
rsync -av --delete \
    --exclude='.DS_Store' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    "$STAGING/" "$MOUNT_POINT/"

# Sync filesystem
sync

echo ""

if [ "$DO_EJECT" = true ]; then
    echo "⏏️  Ejecting to trigger clean reset..."
    diskutil eject "$MOUNT_POINT" 2>/dev/null || true
    echo ""
    echo "✅ Deploy complete! Reconnect device or wait for auto-remount."
else
    echo "✅ Deploy complete!"
    echo "   Device will auto-reload on each file change."
fi
