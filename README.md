# DONK

A private, voice-first life assistant for Android (Hindi, English, Hinglish).
Tasks, meetings, money, promises, people, health and ideas: just say it.

This branch (`v2`) rebuilds DONK 1.1.0-test1 from its APK with the same design,
then implements the **DONK v2 PRD: Speed First** (see [docs/PLAN.md](docs/PLAN.md)).

## Layout

| Path | What lives there |
|---|---|
| `web/` | The UI: Next.js 16 (static export) + Tailwind v4, shown in the Capacitor WebView |
| `android/` | Capacitor 8 Android app and DONK's native core (Kotlin) |
| `native/` | C++: the on-device brain wrapper around llama.cpp |
| `tools/` | Eval set, System 1 training scripts, benchmarks |
| `docs/` | Plan, architecture decisions, recovered 1.1.0-test1 spec |
| `scripts/` | Build helpers |

## Build

See [docs/BUILD.md](docs/BUILD.md). Short version:

```bash
cp scripts/env.example.sh scripts/env.local.sh   # then edit paths
npm install
npm run android:debug
```

App IDs: `com.chaudharynishant.donk` (release), `com.chaudharynishant.donk.dev` (debug).
