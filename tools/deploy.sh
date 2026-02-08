#!/bin/bash
# Deploy firmware to MIDI Captain device
#
# Usage: ./tools/deploy.sh [options] [mount_point]
#
# Options:
#   --install     Full install: check/install libraries first
#   --libs-only   Only install libraries (no firmware copy)
#   --eject       Eject device after deploy (for performance mode)
#   --no-reset    Don't send soft reset after deploy
#   --force       Overwrite files without prompting
#
# Examples:
#   ./tools/deploy.sh                    # Quick deploy (dev mode)
#   ./tools/deploy.sh --install          # Full install with libraries
#   ./tools/deploy.sh --libs-only        # Just install CircuitPython libs
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
DO_INSTALL=false
LIBS_ONLY=false
FORCE=false

# Required CircuitPython libraries
REQUIRED_LIBS=(
    "adafruit_midi"
    "adafruit_display_text"
    "adafruit_st7789"
    "neopixel"
    "adafruit_debouncer"
)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Parse arguments
for arg in "$@"; do
    case $arg in
        --install)
            DO_INSTALL=true
            ;;
        --libs-only)
            LIBS_ONLY=true
            DO_INSTALL=true
            ;;
        --eject)
            DO_EJECT=true
            DO_RESET=false
            ;;
        --no-reset)
            DO_RESET=false
            ;;
        --force)
            FORCE=true
            ;;
        --help|-h)
            echo "Usage: ./tools/deploy.sh [options] [mount_point]"
            echo ""
            echo "Options:"
            echo "  --install     Full install: check/install libraries first"
            echo "  --libs-only   Only install libraries (no firmware copy)"
            echo "  --eject       Eject device after deploy"
            echo "  --no-reset    Don't send soft reset after deploy"
            echo "  --force       Overwrite without prompting"
            exit 0
            ;;
        /*)
            MOUNT_POINT="$arg"
            ;;
    esac
done

echo -e "${BLUE}=== MIDI Captain Firmware Deploy ===${NC}"
echo ""

# Auto-detect mount point if not specified
if [ ! -d "$MOUNT_POINT" ]; then
    if [ -d "/Volumes/MIDICAPTAIN" ]; then
        MOUNT_POINT="/Volumes/MIDICAPTAIN"
    fi
fi

# Check if device is mounted
if [ ! -d "$MOUNT_POINT" ]; then
    echo -e "${RED}❌ Device not found at $MOUNT_POINT${NC}"
    echo ""
    echo "Make sure your MIDI Captain is:"
    echo "  1. Connected via USB"
    echo "  2. Running CircuitPython (not in bootloader mode)"
    echo "  3. Mounted as CIRCUITPY or MIDICAPTAIN"
    echo ""
    echo "If CircuitPython is not installed:"
    echo "  1. Hold BOOTSEL while plugging in USB"
    echo "  2. Copy CircuitPython .uf2 to RPI-RP2 drive"
    echo "  3. Run this script again"
    exit 1
fi

echo -e "${GREEN}✓ Device found at $MOUNT_POINT${NC}"

# Install libraries if requested
if [ "$DO_INSTALL" = true ]; then
    echo ""
    echo -e "${YELLOW}📦 Installing CircuitPython libraries...${NC}"
    
    # Check for circup
    if ! command -v circup &> /dev/null; then
        echo "  circup not found. Installing..."
        pip install circup --quiet
        if ! command -v circup &> /dev/null; then
            echo -e "${RED}✗ Failed to install circup${NC}"
            echo "  Try: pip install circup"
            exit 1
        fi
    fi
    echo -e "${GREEN}✓ circup available${NC}"
    
    # Install each library
    for lib in "${REQUIRED_LIBS[@]}"; do
        echo -n "  Installing $lib... "
        if circup install "$lib" --py 2>/dev/null; then
            echo -e "${GREEN}✓${NC}"
        else
            # Try without --py flag for compiled libs
            if circup install "$lib" 2>/dev/null; then
                echo -e "${GREEN}✓${NC}"
            else
                echo -e "${YELLOW}(already installed)${NC}"
            fi
        fi
    done
    echo -e "${GREEN}✓ Libraries installed${NC}"
    
    # Exit early if libs-only mode
    if [ "$LIBS_ONLY" = true ]; then
        echo ""
        echo -e "${GREEN}✅ Library installation complete!${NC}"
        exit 0
    fi
fi

echo ""
echo "📁 Source: $DEV_DIR"
echo "📱 Target: $MOUNT_POINT"

# Detect device type from existing config on device, or by mount point
DEVICE_TYPE=""
if [ -f "$MOUNT_POINT/config.json" ]; then
    # Try to read device type from existing config
    DETECTED=$(grep -o '"device"[[:space:]]*:[[:space:]]*"[^"]*"' "$MOUNT_POINT/config.json" 2>/dev/null | sed 's/.*"\([^"]*\)"$/\1/')
    if [ -n "$DETECTED" ]; then
        DEVICE_TYPE="$DETECTED"
    fi
fi

# Fallback: use mount point as heuristic
if [ -z "$DEVICE_TYPE" ]; then
    if [ "$MOUNT_POINT" = "/Volumes/MIDICAPTAIN" ]; then
        DEVICE_TYPE="mini6"
    else
        DEVICE_TYPE="std10"
    fi
fi

echo "🎛️  Device type: $DEVICE_TYPE"
echo ""

# Select appropriate config file
if [ "$DEVICE_TYPE" = "mini6" ]; then
    CONFIG_FILE="$DEV_DIR/config-mini6.json"
else
    CONFIG_FILE="$DEV_DIR/config.json"
fi

echo "🚀 Deploying changed files..."

# Deploy dependencies first, code.py last. This ensures all imports are
# in place before the main entry point lands on the device.
#
# rsync flags:
# --checksum: compare by content, not just timestamp (more reliable for USB drives)
# --inplace: minimize file rewrites
# --itemize-changes: show what changed

# 1. boot.py first (keeps autoreload disabled)
rsync -av --checksum --inplace --itemize-changes \
    "$DEV_DIR/boot.py" \
    "$MOUNT_POINT/"

# 2. Core modules, device definitions, and fonts
rsync -av --checksum --inplace --itemize-changes \
    --exclude='.DS_Store' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    "$DEV_DIR/core/" "$MOUNT_POINT/core/"

rsync -av --checksum --inplace --itemize-changes \
    --exclude='.DS_Store' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    "$DEV_DIR/devices/" "$MOUNT_POINT/devices/"

rsync -av --checksum --inplace --itemize-changes \
    --exclude='.DS_Store' \
    "$DEV_DIR/fonts/" "$MOUNT_POINT/fonts/"

sync

# 3. Deploy config (use device-specific if available)
if [ -f "$CONFIG_FILE" ]; then
    rsync -av --checksum --inplace --itemize-changes \
        "$CONFIG_FILE" "$MOUNT_POINT/config.json"
else
    rsync -av --checksum --inplace --itemize-changes \
        "$DEV_DIR/config.json" "$MOUNT_POINT/config.json"
fi

# 4. Deploy device-specific fallback config
rsync -av --checksum --inplace --itemize-changes \
    "$DEV_DIR/config-mini6.json" "$MOUNT_POINT/config-mini6.json"

# 5. code.py LAST (all dependencies are now in place)
rsync -av --checksum --inplace --itemize-changes \
    --exclude='.DS_Store' \
    --exclude='*.pyc' \
    --exclude='__pycache__' \
    --exclude='experiments' \
    "$DEV_DIR/code.py" \
    "$MOUNT_POINT/"

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
        # Kill any screen sessions using this port (they block access)
        SCREEN_PIDS=$(lsof -t "$SERIAL_PORT" 2>/dev/null || true)
        if [ -n "$SCREEN_PIDS" ]; then
            echo "   Closing existing serial connection..."
            kill $SCREEN_PIDS 2>/dev/null || true
            sleep 0.5
        fi
        # Send Ctrl+C (interrupt) then Ctrl+D (soft reload)
        # Use timeout to prevent hanging if port is unresponsive
        if command -v gtimeout &>/dev/null; then
            TIMEOUT_CMD="gtimeout"
        elif command -v timeout &>/dev/null; then
            TIMEOUT_CMD="timeout"
        else
            TIMEOUT_CMD=""
        fi
        
        if [ -n "$TIMEOUT_CMD" ]; then
            $TIMEOUT_CMD 3 bash -c "printf '\x03\x04' > '$SERIAL_PORT'" 2>/dev/null || true
        else
            # No timeout available, try with backgrounding
            ( printf '\x03\x04' > "$SERIAL_PORT" 2>/dev/null ) &
            RESET_PID=$!
            sleep 1
            kill $RESET_PID 2>/dev/null || true
        fi
        echo "✅ Deploy complete! Device is reloading."
    else
        echo "⚠️  No serial port found. Power-cycle device to reload."
    fi
else
    echo "✅ Deploy complete!"
    echo "   Send Ctrl+D in serial console to reload, or eject device."
fi
