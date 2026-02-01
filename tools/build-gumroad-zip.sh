#!/usr/bin/env bash
# Build Gumroad distribution ZIP with stable "latest" alias
# Usage: ./tools/build-gumroad-zip.sh YYYY-MM
set -euo pipefail

MONTH="${1:-}"
if [[ -z "$MONTH" ]]; then
  echo "Usage: $0 YYYY-MM" >&2
  exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

if [[ -n "$(git status --porcelain)" ]]; then
  echo "Error: working tree not clean. Commit or stash changes first." >&2
  git status --porcelain >&2
  exit 1
fi

SHA="$(git rev-parse HEAD)"
PRODUCT_DIR="midi-captain-max-early-access-${MONTH}"
OUT_DIR="$REPO_ROOT/dist"
STAGE_ROOT="$OUT_DIR/stage"
STAGE_DIR="$STAGE_ROOT/$PRODUCT_DIR"

ZIP_DATED="$OUT_DIR/${PRODUCT_DIR}.zip"
ZIP_LATEST="$OUT_DIR/midi-captain-max-latest.zip"

rm -rf "$STAGE_ROOT"
mkdir -p "$STAGE_DIR"

# ---- COPY FIRMWARE (excluding dev-only content) ----
mkdir -p "$STAGE_DIR/firmware"
cp "$REPO_ROOT/firmware/dev/code.py" "$STAGE_DIR/firmware/"
cp "$REPO_ROOT/firmware/dev/boot.py" "$STAGE_DIR/firmware/"
cp "$REPO_ROOT/firmware/dev/config.json" "$STAGE_DIR/firmware/"
cp "$REPO_ROOT/firmware/dev/config-mini6.json" "$STAGE_DIR/firmware/"
cp -R "$REPO_ROOT/firmware/dev/devices" "$STAGE_DIR/firmware/"
cp -R "$REPO_ROOT/firmware/dev/fonts" "$STAGE_DIR/firmware/"

# ---- COPY DOCS ----
mkdir -p "$STAGE_DIR/docs"
cp -R "$REPO_ROOT/docs/." "$STAGE_DIR/docs/"

# ---- VERSION INFO ----
cat > "$STAGE_DIR/VERSION.txt" <<EOF
mcm-early-access-${MONTH}
git-sha: ${SHA}
EOF

cat > "$STAGE_DIR/README.txt" <<EOF
MIDI Captain MAX — Early Access Package

Build: ${MONTH}
Commit: ${SHA}

Contents:
  firmware/   CircuitPython firmware files (copy to CIRCUITPY volume)
  docs/       Documentation and hardware reference

For source code and issues: https://github.com/mcascone/midi-captain-max
EOF

mkdir -p "$OUT_DIR"
rm -f "$ZIP_DATED" "$ZIP_LATEST"

(
  cd "$STAGE_ROOT"
  zip -r "$ZIP_DATED" "$PRODUCT_DIR" >/dev/null
)

cp -f "$ZIP_DATED" "$ZIP_LATEST"

echo "Built:"
echo "  $ZIP_DATED"
echo "  $ZIP_LATEST"
echo "SHA: $SHA"
