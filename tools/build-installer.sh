#!/bin/bash
# MIDI Captain Firmware Installer Build Script
# Creates a macOS .pkg installer with an interactive GUI app
#
# This installer:
# 1. Installs firmware files to /usr/local/share/midicaptain-firmware/
# 2. Installs an interactive GUI app to /Applications/
# 3. Installs a CLI tool to /usr/local/bin/midicaptain-install
# 4. The GUI app watches for device connection and provides one-click install

set -e

# Get version from git or environment
if [ -n "$MIDICAPTAIN_VERSION" ]; then
    VERSION="$MIDICAPTAIN_VERSION"
    echo "Using version from environment: $VERSION"
else
    GIT_DESCRIBE=$(git describe --tags --always 2>/dev/null || echo "")
    if [ -n "$GIT_DESCRIBE" ]; then
        VERSION="${GIT_DESCRIBE#v}"
        echo "Using version from git: $VERSION"
    else
        VERSION="dev"
        echo "Warning: No git info found, using fallback: $VERSION"
    fi
fi

IDENTIFIER="com.mcmusicworkshop.midicaptain"
PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TOOLS_DIR="$PROJECT_ROOT/tools"
DEV_DIR="$PROJECT_ROOT/firmware/dev"
OUTPUT_DIR="$PROJECT_ROOT/build/installer"
COMPONENT_PKGS="$OUTPUT_DIR/components"

echo "Building MIDI Captain Firmware Installer v${VERSION}"
echo "====================================================="

# Clean and create directories
echo "Setting up installer directories..."
rm -rf "$OUTPUT_DIR"
mkdir -p "$COMPONENT_PKGS"

# Compile the AppleScript app
echo "Compiling interactive installer app..."
APPLESCRIPT_SRC="$TOOLS_DIR/MIDICaptainInstaller.applescript"
APP_OUTPUT="$OUTPUT_DIR/MIDI Captain Installer.app"

if [ -f "$APPLESCRIPT_SRC" ]; then
    osacompile -o "$APP_OUTPUT" "$APPLESCRIPT_SRC"
    echo "  ✓ AppleScript app compiled"
else
    echo "  ⚠ AppleScript source not found, skipping GUI app"
fi

# Create the firmware payload directory
echo "Preparing firmware payload..."
PAYLOAD_ROOT="$OUTPUT_DIR/payload-root"
PAYLOAD_DIR="$PAYLOAD_ROOT/usr/local/share/midicaptain-firmware"
SCRIPTS_DIR="$OUTPUT_DIR/scripts"

mkdir -p "$PAYLOAD_DIR"
mkdir -p "$SCRIPTS_DIR"
mkdir -p "$PAYLOAD_ROOT/Applications"

# Copy firmware files to payload
cp "$DEV_DIR/code.py" "$PAYLOAD_DIR/"
cp "$DEV_DIR/boot.py" "$PAYLOAD_DIR/"
cp "$DEV_DIR/config.json" "$PAYLOAD_DIR/"
cp "$DEV_DIR/config-mini6.json" "$PAYLOAD_DIR/"
cp -R "$DEV_DIR/devices" "$PAYLOAD_DIR/"
cp -R "$DEV_DIR/fonts" "$PAYLOAD_DIR/"

# Copy the GUI installer app if it was built
if [ -d "$APP_OUTPUT" ]; then
    cp -R "$APP_OUTPUT" "$PAYLOAD_ROOT/Applications/"
    echo "  ✓ GUI app added to payload"
fi

# Create the install script that will be placed in /usr/local/bin
mkdir -p "$PAYLOAD_ROOT/usr/local/bin"
cat > "$PAYLOAD_ROOT/usr/local/bin/midicaptain-install" << 'INSTALLSCRIPT'
#!/bin/bash
# MIDI Captain Firmware Installation Script
# Copies firmware files to a mounted CIRCUITPY device

set -e

FIRMWARE_DIR="/usr/local/share/midicaptain-firmware"
MOUNT_POINT="${1:-/Volumes/CIRCUITPY}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== MIDI Captain Firmware Installer ===${NC}"
echo ""

# Auto-detect mount point
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
    echo "Usage: midicaptain-install [mount_point]"
    exit 1
fi

echo -e "${GREEN}✓ Device found at $MOUNT_POINT${NC}"
echo ""

# Copy firmware files
echo "Installing firmware files..."

echo -n "  code.py... "
cp "$FIRMWARE_DIR/code.py" "$MOUNT_POINT/" && echo -e "${GREEN}✓${NC}"

echo -n "  boot.py... "
cp "$FIRMWARE_DIR/boot.py" "$MOUNT_POINT/" && echo -e "${GREEN}✓${NC}"

echo -n "  config.json... "
if [ ! -f "$MOUNT_POINT/config.json" ]; then
    cp "$FIRMWARE_DIR/config.json" "$MOUNT_POINT/" && echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}(preserved existing)${NC}"
fi

echo -n "  devices/... "
rm -rf "$MOUNT_POINT/devices"
cp -R "$FIRMWARE_DIR/devices" "$MOUNT_POINT/" && echo -e "${GREEN}✓${NC}"

echo -n "  fonts/... "
rm -rf "$MOUNT_POINT/fonts"
cp -R "$FIRMWARE_DIR/fonts" "$MOUNT_POINT/" && echo -e "${GREEN}✓${NC}"

echo ""
echo -e "${GREEN}✓ Firmware installation complete!${NC}"
echo ""
echo "The device will restart automatically."
echo "If it doesn't, disconnect and reconnect USB."

# Sync to ensure files are written
sync

echo ""
INSTALLSCRIPT
chmod +x "$PAYLOAD_ROOT/usr/local/bin/midicaptain-install"

# Create postinstall script for the package
cat > "$SCRIPTS_DIR/postinstall" << 'EOF'
#!/bin/bash
# Post-installation: make script executable, de-quarantine app, show instructions
chmod +x /usr/local/bin/midicaptain-install 2>/dev/null || true

# De-quarantine the GUI app
xattr -cr "/Applications/MIDI Captain Installer.app" 2>/dev/null || true

# Open the installer app automatically
open -a "/Applications/MIDI Captain Installer.app" 2>/dev/null || true

exit 0
EOF
chmod +x "$SCRIPTS_DIR/postinstall"

# Build the component package
echo "Building component package..."
pkgbuild --root "$PAYLOAD_ROOT" \
         --identifier "${IDENTIFIER}" \
         --version "$VERSION" \
         --scripts "$SCRIPTS_DIR" \
         --install-location "/" \
         "$COMPONENT_PKGS/firmware.pkg"

# Create distribution XML
echo "Creating distribution definition..."
cat > "$OUTPUT_DIR/distribution.xml" << EOF
<?xml version="1.0" encoding="utf-8"?>
<installer-gui-script minSpecVersion="1">
    <title>MIDI Captain Firmware ${VERSION}</title>
    <organization>com.mcmusicworkshop</organization>
    <domains enable_localSystem="true"/>
    <options customize="never" require-scripts="false" rootVolumeOnly="true" />
    
    <welcome file="welcome.html" mime-type="text/html" />
    <conclusion file="conclusion.html" mime-type="text/html" />
    
    <choices-outline>
        <line choice="firmware.choice"/>
    </choices-outline>
    
    <choice id="firmware.choice" title="MIDI Captain Firmware" description="Install firmware and helper script" start_selected="true" enabled="false">
        <pkg-ref id="${IDENTIFIER}"/>
    </choice>
    
    <pkg-ref id="${IDENTIFIER}" version="${VERSION}" auth="root">components/firmware.pkg</pkg-ref>
</installer-gui-script>
EOF

# Create welcome HTML
cat > "$OUTPUT_DIR/welcome.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <meta name="color-scheme" content="light">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; }
        h1 { font-size: 24px; margin-bottom: 10px; }
        p { font-size: 14px; line-height: 1.5; }
    </style>
</head>
<body>
    <h1>MIDI Captain Firmware</h1>
    <p>Version ${VERSION}</p>
    <p>This installer will install the MIDI Captain custom firmware and an interactive installer app.</p>
    
    <p><strong>What gets installed:</strong></p>
    <ul>
        <li><strong>MIDI Captain Installer.app</strong> in /Applications/</li>
        <li>Firmware files in /usr/local/share/midicaptain-firmware/</li>
        <li>CLI tool "midicaptain-install" in /usr/local/bin/</li>
    </ul>
    
    <p><strong>After installation:</strong> The MIDI Captain Installer app will open automatically. Connect your device and click Install!</p>
</body>
</html>
EOF

# Create conclusion HTML
cat > "$OUTPUT_DIR/conclusion.html" << EOF
<!DOCTYPE html>
<html>
<head>
    <meta name="color-scheme" content="light">
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, sans-serif; padding: 20px; }
        h1 { font-size: 24px; margin-bottom: 10px; }
        p { font-size: 14px; line-height: 1.5; }
        a { color: #0066cc; }
    </style>
</head>
<body>
    <h1>Installation Complete!</h1>
    
    <p>✓ MIDI Captain Firmware ${VERSION} has been installed.</p>
    
    <p><strong>The MIDI Captain Installer app should open automatically.</strong></p>
    
    <p>If it doesn't, you can find it in /Applications/MIDI Captain Installer.app</p>
    
    <p>Or use the command line: midicaptain-install</p>
    
    <p><strong>Need help?</strong> Visit 
    <a href="https://github.com/mcascone/midi-captain-max">github.com/mcascone/midi-captain-max</a></p>
</body>
</html>
EOF

# Build the product package
echo "Building product installer..."
productbuild --distribution "$OUTPUT_DIR/distribution.xml" \
             --package-path "$COMPONENT_PKGS" \
             --resources "$OUTPUT_DIR" \
             "$OUTPUT_DIR/MIDICaptain-Firmware-${VERSION}.pkg"

echo ""
echo "✓ Installer created: $OUTPUT_DIR/MIDICaptain-Firmware-${VERSION}.pkg"
echo ""
echo "The installer will:"
echo "  1. Install 'MIDI Captain Installer.app' to /Applications/"
echo "  2. Install firmware files to /usr/local/share/midicaptain-firmware/"
echo "  3. Install 'midicaptain-install' CLI to /usr/local/bin/"
echo "  4. Auto-launch the GUI installer app after installation"
echo ""
echo "The GUI app features:"
echo "  • Scans all mounted volumes for CircuitPython devices"
echo "  • Detects CIRCUITPY, MIDICAPTAIN, or any volume with boot_out.txt"
echo "  • Browse button to manually select any volume"
echo "  • One-click install with config preservation"
echo ""
echo "File size:"
du -h "$OUTPUT_DIR/MIDICaptain-Firmware-${VERSION}.pkg"
