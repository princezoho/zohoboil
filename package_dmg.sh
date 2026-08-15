#!/bin/bash
# Wraps an already-built, already-stapled dist/Boiler.app into a DMG, then
# notarizes and staples the DMG itself.
#
# Order matters: the app must be notarized and stapled BEFORE it goes into the
# DMG, otherwise the DMG carries an unstapled app and the person you shared it
# with needs to be online for Gatekeeper to clear it.
set -euo pipefail
cd "$(dirname "$0")"
VERSION="${1:-1.0.0}"
APP="dist/Boiler.app"
DMG="dist/Boiler-$VERSION.dmg"

# Notarization credentials come from the environment, so this stays shareable.
#   export ASC_KEY_ID=...  ASC_ISSUER=...  ASC_KEY=~/path/AuthKey_XXXX.p8
KEY="${ASC_KEY:-$HOME/.appstoreconnect/private_keys/AuthKey_$ASC_KEY_ID.p8}"
KEY_ID="${ASC_KEY_ID:?set ASC_KEY_ID to your App Store Connect key id}"
ISSUER="${ASC_ISSUER:?set ASC_ISSUER to your App Store Connect issuer id}"

[ -d "$APP" ] || { echo "no app bundle; run ./build_dmg.sh first"; exit 1; }

STAGE="dist/dmg-stage"
rm -rf "$STAGE"; mkdir -p "$STAGE"
cp -R "$APP" "$STAGE/"
ln -s /Applications "$STAGE/Applications"
rm -f "$DMG"
hdiutil create -volname "Boiler" -srcfolder "$STAGE" -ov -format UDZO "$DMG" >/dev/null
rm -rf "$STAGE"

echo "==> Notarizing DMG"
xcrun notarytool submit "$DMG" --key "$KEY" --key-id "$KEY_ID" --issuer "$ISSUER" --wait
xcrun stapler staple "$DMG"

echo "DMG: $DMG ($(du -h "$DMG" | cut -f1))"
