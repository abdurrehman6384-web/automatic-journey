#!/usr/bin/env bash
# One command: OpenDroid + Toni -> installable APK.
#
#   ./build-apk.sh                debug APK (no signing needed)
#   ./build-apk.sh --release      signed release APK (needs keystore + creds)
#
# What it does, and why each step is checked rather than assumed:
#   1. verifies JDK is exactly 21      (OpenDroid pins jvmToolchain(21); 17/25 fail)
#   2. verifies an Android SDK exists  (writes local.properties if you set ANDROID_HOME)
#   3. copies Toni in and applies the wiring patch (idempotent, anchor-verified)
#   4. builds and prints the APK path + sha256
#
# If you would rather not install any of this, push to GitHub and let
# .github/workflows/build-apk.yml build it on their runners instead.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${OPENDROID_DIR:-$HERE/../opendroid}"
MODE="debug"
[ "${1:-}" = "--release" ] && MODE="release"

say() { printf '\n\033[1m== %s\033[0m\n' "$1"; }
die() { printf '\n\033[31merror:\033[0m %s\n' "$1" >&2; exit 1; }

[ -d "$TARGET/app/src/main/java/com/opendroid/ai" ] \
  || die "'$TARGET' is not an OpenDroid checkout. Clone it, or set OPENDROID_DIR."

# ---------------------------------------------------------------- 1. JDK 21
say "Checking JDK"
command -v java >/dev/null || die "java not found. Install JDK 21 (e.g. 'sudo apt install openjdk-21-jdk')."
JV="$(java -version 2>&1 | head -1)"
echo "  $JV"
# Extract the major version: handles both "21.0.2" and "1.8.0" legacy formats.
JMAJOR="$(java -version 2>&1 | head -1 | sed -E 's/.*version "([0-9]+)(\.([0-9]+))?.*/\1 \3/' \
          | awk '{ if ($1 == 1) print $2; else print $1 }')"
[ "$JMAJOR" = "21" ] \
  || die "JDK 21 required, found major version '$JMAJOR'. OpenDroid pins jvmToolchain(21); other versions fail to build."

# ---------------------------------------------------------- 2. Android SDK
say "Checking Android SDK"
if [ -f "$TARGET/local.properties" ]; then
  echo "  using existing local.properties"
elif [ -n "${ANDROID_HOME:-}" ] && [ -d "$ANDROID_HOME" ]; then
  echo "sdk.dir=$ANDROID_HOME" > "$TARGET/local.properties"
  echo "  wrote local.properties -> $ANDROID_HOME"
elif [ -d "$HOME/Android/Sdk" ]; then
  echo "sdk.dir=$HOME/Android/Sdk" > "$TARGET/local.properties"
  echo "  wrote local.properties -> $HOME/Android/Sdk"
else
  die "No Android SDK found. Install Android Studio (or cmdline-tools) with
       'Android SDK Platform 36' + 'Build-Tools 36', then either set ANDROID_HOME
       or create $TARGET/local.properties containing 'sdk.dir=/path/to/sdk'.

       Alternatively: push to GitHub and use .github/workflows/build-apk.yml --
       their runners already have the SDK."
fi

# ------------------------------------------------------- 3. Toni + patch
say "Installing Toni"
"$HERE/install.sh" "$TARGET"

say "Verifying and applying the wiring patch"
python3 "$TARGET/pet/apply_patch.py" "$TARGET" --check
python3 "$TARGET/pet/apply_patch.py" "$TARGET"

# ------------------------------------------------------------- 4. Build
cd "$TARGET"
chmod +x ./gradlew 2>/dev/null || true

if [ "$MODE" = "release" ]; then
  say "Building signed release APK"
  [ -f "$TARGET/opendroid-release.keystore" ] \
    || die "release mode needs '$TARGET/opendroid-release.keystore'.
       Create one:
         keytool -genkeypair -v -keystore opendroid-release.keystore -alias opendroid \\
           -keyalg RSA -keysize 2048 -validity 10000
       Then put the three credentials in ~/.gradle/gradle.properties:
         RELEASE_STORE_PASSWORD=...
         RELEASE_KEY_ALIAS=opendroid
         RELEASE_KEY_PASSWORD=..."
  ./gradlew :app:assembleRelease --stacktrace
  APK="app/build/outputs/apk/release/app-release.apk"
else
  say "Building debug APK"
  ./gradlew :app:assembleDebug --stacktrace
  APK="app/build/outputs/apk/debug/app-debug.apk"
fi

# ---------------------------------------------------------- 5. Report
say "Done"
[ -f "$APK" ] || die "gradle reported success but no APK at $APK"
ls -lh "$APK"
echo "  sha256: $(sha256sum "$APK" | cut -d' ' -f1)"
echo
echo "Install it:"
echo "  adb install -r $APK"
echo
echo "Then: Settings -> Accessibility -> OpenDroid -> enable,"
echo "and turn on the floating-button setting. Toni appears at the right edge."
