#!/bin/bash
# Deploy firmware to MIDI Captain device
#
# Usage: ./tools/deploy.sh [options] [mount_point]
#
# Options:
#   --eject       Eject device after deploy (for performance mode)
#   --no-reset    Don't send soft reset after deploy
#
# Examples:
#   ./tools/deploy.sh                    # Deploy + soft reset (dev mode)
#   ./tools/deploy.sh --eject            # Deploy + eject (clean disconnect)
#   ./tools/deploy.sh /Volumes/MIDICAPT  # Custom mount point
#
# Requires boot.py on device with autoreload disabled for best results.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
DEV_DIR="$PROJECT_ROOT/firmware/dev"
MOUNT_POINT="/Volumes/CIRCUITPY"
DO_EJECT=false
DO_RESET=true

# Parse arguments
for arg in "$@"; do
    case $arg in
        --eject)
            DO_EJECT=true
            DO_RESET=false
            ;;
        --no-reset)
            DO_RESET=false
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
cp "$DEV_DIR/boot.py" "$STAGING/" 2>/dev/null || true
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
    --exclude='BOOTEX.LOG' \
    --exclude='.fseventsd' \
    --exclude='.Trashes' \
    "$STAGING/" "$MOUNT_POINT/"

# Sync filesystem
sync

echo ""

if [ "$DO_EJECT" = true ]; then
    echo "⏏️  Ejecting device..."
    diskutil eject "$MOUNT_POINT" 2>/dev/null || true
    echo "✅ Deploy complete! Reconnect device to start firmware."
elif [ "$DO_RESET" = true ]; then
    echo "🔄 Sending soft reset..."
    # Find CircuitPython serial port and send Ctrl+C then Ctrl+D
    SERIAL_PORT=$(ls /dev/tty.usbmodem* 2>/dev/null | head -1)
    if [ -n "$SERIAL_PORT" ]; then
        # Send Ctrl+C (interrupt running code) then Ctrl+D (soft reload)
        # Small delay between to ensure REPL is ready
        printf '\x03' > "$SERIAL_PORT"
        sleep 0.2
        printf '\x04' > "$SERIAL_PORT"
        echo "✅ Deploy complete! Device is reloading."
    else
        echo "⚠️  No serial port found. Device may need manual reset."
        echo "   Press Ctrl+C then Ctrl+D in serial console, or eject device."
    fi
else
    echo "✅ Deploy complete!"
    echo "   Send Ctrl+D in serial console to reload, or eject device."
fi
