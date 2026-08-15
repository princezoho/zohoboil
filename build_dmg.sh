#!/bin/bash
# Builds Boiler.app and a shareable DMG. Run from the repo root.
set -euo pipefail
cd "$(dirname "$0")"
ROOT="$PWD"
VERSION="${1:-1.0.0}"
APP="$ROOT/dist/Boiler.app"
DMG="$ROOT/dist/Boiler-$VERSION.dmg"

echo "==> Building Boiler.app"
rm -rf build/Boiler dist/Boiler dist/Boiler.app
./venv/bin/pyinstaller --noconfirm Boiler.spec

[ -d "$APP" ] || { echo "build failed: no app bundle"; exit 1; }

# The bundled ffmpeg loses its exec bit through the packaging step.
chmod +x "$APP/Contents/Frameworks/bin/ffmpeg" 2>/dev/null || \
  chmod +x "$APP/Contents/Resources/bin/ffmpeg" 2>/dev/null || true

echo "==> Signing"
# Ad-hoc is enough for a shared build; a Developer ID is used when present.
IDENTITY="$(security find-identity -v -p codesigning 2>/dev/null \
  | grep -o '"Developer ID Application[^"]*"' | head -1 | tr -d '"' || true)"
if [ -n "$IDENTITY" ]; then
  codesign --force --deep --options runtime -s "$IDENTITY" "$APP"
else
  codesign --force --deep -s - "$APP"
fi

echo "==> Building DMG"
STAGE="$ROOT/dist/dmg-stage"
rm -rf "$STAGE"; mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
# Unsigned apps are quarantined on download; the note tells people the fix.
cp "$ROOT/docs/FIRST-RUN.txt" "$STAGE/READ ME FIRST.txt" 2>/dev/null || true
rm -f "$DMG"
hdiutil create -volname "Boiler" -srcfolder "$STAGE" -ov -format UDZO "$DMG" >/dev/null
rm -rf "$STAGE"

echo "App: $APP"
echo "DMG: $DMG ($(du -h "$DMG" | cut -f1))"
