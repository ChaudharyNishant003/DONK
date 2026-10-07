#!/usr/bin/env bash
# Build the DONK APK: web export -> Capacitor sync -> Gradle.
# Usage: scripts/build-android.sh [debug|release]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TYPE="${1:-debug}"
case "$TYPE" in
  debug) TASK=assembleDebug ;;
  release) TASK=assembleRelease ;;
  *) echo "usage: $0 [debug|release]" >&2; exit 2 ;;
esac

if [ -f "$ROOT/scripts/env.local.sh" ]; then
  # shellcheck disable=SC1091
  source "$ROOT/scripts/env.local.sh"
else
  echo "Missing scripts/env.local.sh (copy scripts/env.example.sh)" >&2
  exit 1
fi

cd "$ROOT"
npm run web:build
npx cap sync android

cd "$ROOT/android"
if [[ "${OS:-}" == "Windows_NT" ]]; then
  ./gradlew.bat "$TASK" --console=plain
else
  ./gradlew "$TASK" --console=plain
fi

APK_DIR="$ROOT/android/app/build/outputs/apk/$TYPE"
echo
echo "APK(s):"
ls -la "$APK_DIR"/*.apk
bash "$ROOT/scripts/check-16kb.sh" "$APK_DIR"/*.apk
