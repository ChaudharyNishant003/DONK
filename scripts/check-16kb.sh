#!/usr/bin/env bash
# Fails if any native library in the given APK(s) is not 16 KB page aligned
# (PRD ST-3; required by Google Play for apps targeting Android 15+).
# Usage: scripts/check-16kb.sh path/to/app.apk [...]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ -f "$ROOT/scripts/env.local.sh" ] && source "$ROOT/scripts/env.local.sh"

READELF="$(ls "$ANDROID_NDK_HOME"/toolchains/llvm/prebuilt/*/bin/llvm-readelf* 2>/dev/null | head -1)"
if [ -z "$READELF" ]; then
  echo "llvm-readelf not found under ANDROID_NDK_HOME=$ANDROID_NDK_HOME" >&2
  exit 1
fi

status=0
for apk in "$@"; do
  tmp="$(mktemp -d)"
  unzip -qo "$apk" 'lib/*' -d "$tmp" 2>/dev/null || true
  count=0
  while IFS= read -r so; do
    count=$((count + 1))
    align="$("$READELF" -lW "$so" | awk '/LOAD/ {print $NF; exit}')"
    if [ "$align" != "0x4000" ] && [ "$align" != "0x10000" ]; then
      echo "NOT 16 KB aligned ($align): ${so#"$tmp"/}"
      status=1
    fi
  done < <(find "$tmp/lib" -name '*.so' 2>/dev/null)
  echo "$(basename "$apk"): checked $count native libraries"
  rm -rf "$tmp"
done

if [ "$status" -eq 0 ]; then
  echo "16 KB alignment: OK"
fi
exit "$status"
