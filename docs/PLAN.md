# DONK v2 plan

Source documents: *DONK v2 PRD: Speed First* (3 Oct 2026, in `docs/prd/`) and the
static teardown of the 1.0.0 and 1.1.0-test1 APKs. The original source code was not
available, so phases R0 to R4 rebuild 1.1.0-test1 from its APK first; phases P0 to P4
then implement the PRD. There is no timeline: each phase ends with a build on the
test phone (CMF Phone) and a push of the `v2` branch.

## Decisions

| # | Decision | Why |
|---|---|---|
| D1 | Rebuild from the APK into this repo, full feature parity (MCP connectors and chat import included) | No source available; owner's permission |
| D2 | New app ID `com.chaudharynishant.donk`, new release key; debug builds use `.dev` | Original signing key not available; old and new apps can run side by side for speed comparisons |
| D3 | Same stack: Next.js static export + Tailwind v4 in a Capacitor WebView | Only way to keep visuals identical; class names and tokens are recovered from the 1.1.0-test1 bundle |
| D4 | A native Kotlin core owns the database, AI pipeline, network, reminders and model files; the WebView only renders | PRD AP-1/2 (speed) and SE-1/2/5 (security) are the same piece of work |
| D5 | The WebView has no network access. All egress goes through a native SecureFetch layer, which injects keys, enforces Private mode and writes the egress log | Keys never enter JavaScript (SE-2); Private mode is provable (SE-5) |
| D6 | Keys are typed into a native, screenshot-blocked entry sheet styled with DONK tokens; stored in the SQLCipher database, each sealed with AES-256-GCM under a non-exportable Android Keystore key (StrongBox when available); optional "Include keys in backup" (off by default, re-encrypted with the backup password) | User asked for keys in the app and in the encrypted DB, never exposed |
| D7 | Database: SQLCipher from the first rebuilt version, random key wrapped by the Keystore | SE-1 without a later migration |
| D8 | On-device brain: new JNI wrapper on pinned llama.cpp, NDK r29 (16 KB aligned) | F9, ST-3; old wrapper only had 7 entry points |
| D9 | Voice: sherpa-onnx 1.13.8 (same as 1.1.0-test1) plus Silero VAD; STT engine chosen by benchmark (VO-3) | |
| D10 | System 1 runs natively (Kotlin): normaliser, rules, embedding classifier heads; heads trained on this PC from the eval set | Decision must take ~150 ms and sit next to STT and the DB |
| D11 | Jev: TypeSafe `POST /v1/systemone`, pinned model version, or the OpenRouter route if the key is an OpenRouter key; off by default, BYOK, minimised payload | PRD 7.2 |
| D12 | Old data comes over through the 1.1.0-test1 backup file (old format restore) | New app ID cannot read the old app's storage |

## Phases

### R0 Setup
- [x] Toolchain on D: (SDK 36, build-tools 36.1, NDK r29, CMake 3.31.6, JDK 21)
- [x] Repo layout, workspaces, Capacitor 8 Android project, build scripts
- [x] Release keystore outside the repo; debug and release APKs build
- [x] 16 KB alignment check script
- [ ] llama.cpp NDK r29 smoke build (16 KB)

### R1 Spec from the APK
- [ ] Design tokens, fonts, radii, shadows (light and dark)
- [ ] Component catalog (Gallery page) and every screen's structure and class names
- [ ] DB schema and migrations, backup file format
- [ ] Agent: system prompts, tool schemas, model registry, providers, MCP and OAuth flows, chat import
- [ ] Reference screenshots of every old screen (light and dark, 375 px wide)
- [ ] Eval set: 400 labelled utterances (40% Hinglish, 35% Hindi, 25% English)

### R2 UI rebuild
- [ ] Today, Talk, Life (9 domains), Settings, Gallery, lock screen
- [ ] Screenshot-diff tests against the reference screenshots

### R3 Native core
- [ ] SQLCipher database + data API (one call per screen)
- [ ] Backup and restore (new format + 1.1.0-test1 format)
- [ ] Biometric lock, key storage (D6), SecureFetch (D5)

### R4 AI parity
- [ ] On-device brain (new JNI), model downloads with SHA-256 pinning (SE-3)
- [ ] Ears and voices (sherpa-onnx)
- [ ] Cloud providers (Claude, OpenAI, Gemini, OpenRouter), agent and tools
- [ ] AI-composed Today, memory, people, chat import, MCP connectors (GitHub, Railway)

### P0 Stabilise and baseline (PRD 7.0)
- [ ] ST-1, ST-2: reproduce and explain 1.1.0-test1 failures on the CMF Phone
- [ ] ST-3 (done by D8), ST-4 Diagnostics screen, ST-5 never "too long"
- [ ] Baseline timings with the stopwatch points (PRD section 10)

### P1 Quick wins
- [ ] S2-1 streaming, S2-5 single pass, S2-6 preload, S2-4 caps and grammar, VO-1 VAD, VO-4 warm models

### P2 Native speed core and System 1
- [ ] AP-1 to AP-4; normaliser; S1-1 to S1-8; S2-2, S2-3, S2-7, S2-8, S2-9; VO-2, VO-3, VO-5

### P3 Jev, reminders, remaining security
- [ ] JV-1 to JV-9 (with ship gate), RE-1 to RE-6, SE-3, SE-4, EX-1, EX-5

### P4 Explore and beta readiness
- [ ] EX-2 to EX-6, RE-4, RE-5; non-functional checks (memory, battery, thermal, size, accessibility); release build
