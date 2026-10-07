# Building DONK

## Toolchain

| Tool | Version | Notes |
|---|---|---|
| Node.js | 24.x | npm workspaces (`web/`) |
| JDK | 21 (Temurin) | Required by Capacitor 8 / AGP 8.13 |
| Android SDK | platform 36, build-tools 36.1.0 | |
| Android NDK | r29 (29.0.14206865) | Produces 16 KB aligned libraries by default |
| CMake | 3.31.6 (SDK package) | |

All paths are set in `scripts/env.local.sh` (copy of `scripts/env.example.sh`,
never committed). It also keeps the Gradle and npm caches off the system drive.

## Commands

```bash
npm install                  # once
npm run web:dev              # UI in a desktop browser at http://localhost:3000
npm run android:debug        # web export -> cap sync -> debug APK -> 16 KB check
npm run android:release      # same, signed with the release key
npm run check:16kb -- path/to/app.apk
```

APKs land in `android/app/build/outputs/apk/<debug|release>/`.

## Release signing

The release keystore is **not** in the repo. `DONK_KEYSTORE_PROPERTIES` points at a
`keystore.properties` file:

```properties
storeFile=D:/Donk/keys/donk-release.jks
storePassword=...
keyAlias=donk
keyPassword=...
```

Losing the keystore means the app can never be updated under the same ID. Keep two
offline backups of both files.

## Installing on the test phone

```bash
adb devices
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```
