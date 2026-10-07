# Copy to scripts/env.local.sh and adjust paths for this machine.
# Every build script sources env.local.sh, so caches never land on a small C: drive.
export JAVA_HOME="D:/Android/jdk21"
export ANDROID_HOME="D:/Android/sdk"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
export ANDROID_NDK_HOME="$ANDROID_HOME/ndk/29.0.14206865"
export GRADLE_USER_HOME="D:/Android/gradle-home"
export npm_config_cache="D:/Android/npm-cache"
export NEXT_TELEMETRY_DISABLED=1
export PLAYWRIGHT_BROWSERS_PATH="D:/Android/playwright"
# PATH entries must use POSIX form under Git Bash ("D:/x" would split at the colon).
if command -v cygpath >/dev/null 2>&1; then
  export PATH="$(cygpath -u "$JAVA_HOME")/bin:$(cygpath -u "$ANDROID_HOME")/platform-tools:$PATH"
else
  export PATH="$JAVA_HOME/bin:$ANDROID_HOME/platform-tools:$PATH"
fi

# Release signing: path to a keystore.properties file kept outside the repo.
export DONK_KEYSTORE_PROPERTIES="D:/Donk/keys/keystore.properties"
