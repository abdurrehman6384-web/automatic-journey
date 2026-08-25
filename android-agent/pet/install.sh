#!/usr/bin/env bash
# Installs the Toni pet into a cloned OpenDroid tree.
#
#   ./install.sh [path-to-opendroid]
#
# Defaults to ../opendroid (the layout this repo uses).
#
# This only COPIES files -- it never edits OpenDroid's existing sources. The
# three-line wiring change in OpenDroidAccessibilityService is manual and
# documented in APPLY.md, because a blind sed on someone else's service is how
# you get a build that fails in a way you cannot see.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-$HERE/../opendroid}"

if [ ! -d "$TARGET/app/src/main/java/com/opendroid/ai" ]; then
  echo "error: '$TARGET' does not look like an OpenDroid checkout." >&2
  echo "       expected: $TARGET/app/src/main/java/com/opendroid/ai" >&2
  exit 1
fi

DEST="$TARGET/app/src/main/java/com/opendroid/ai/pet"
mkdir -p "$DEST"

for f in ToniPetView.kt ToniPetController.kt ToniPetBridge.kt; do
  if [ ! -f "$HERE/$f" ]; then
    echo "error: missing $HERE/$f" >&2
    exit 1
  fi
  cp "$HERE/$f" "$DEST/$f"
  echo "  copied $f -> ${DEST#$TARGET/}"
done

# The patcher must sit at pet/apply_patch.py in the app repo, because the CI
# workflow calls it as `python3 pet/apply_patch.py .`.
mkdir -p "$TARGET/pet"
cp "$HERE/apply_patch.py" "$TARGET/pet/apply_patch.py"
chmod +x "$TARGET/pet/apply_patch.py"
echo "  copied apply_patch.py -> pet/apply_patch.py"

# CI workflow: builds the APK on GitHub's runners, no local toolchain needed.
mkdir -p "$TARGET/.github/workflows"
cp "$HERE/build-apk.yml" "$TARGET/.github/workflows/build-apk.yml"
echo "  copied build-apk.yml -> .github/workflows/build-apk.yml"

echo
echo
echo "Now apply the wiring patch:"
echo "    cd '$TARGET' && python3 pet/apply_patch.py ."
echo
echo "Or push to GitHub and let .github/workflows/build-apk.yml build the APK"
echo "for you -- no local JDK, Android SDK or Gradle required."
