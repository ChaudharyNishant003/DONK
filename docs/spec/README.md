# 1.1.0-test1 recovered spec

How DONK 1.1.0-test1 works, recovered from its APK (3 to 7 Oct 2026). The original
source was not available. The web layer was read from the Turbopack bundle (module
and export names survive minification); the Android layer was decompiled with jadx.

These documents describe what v2 must reproduce. Where v2 deliberately differs, the
difference is listed in [../PLAN.md](../PLAN.md) and in the "v2" notes below.

| Document | Contents |
|---|---|
| [design.md](design.md) | Tokens (light, dark, stage), typography, radii, shadows, icon, layout rules |
| [data.md](data.md) | Database schema, domains and kinds, metrics, settings, secrets, backups |
| [agent.md](agent.md) | Agent loop, system prompts, tools, context block, providers, MCP, chat import |
| [components.md](components.md) | The 65-component kit the agent designs screens from |
| [screens.md](screens.md) | Routes and screen structure |
| [native.md](native.md) | Android side: DonkBrain plugin, llama.cpp wrapper, voice, model downloads |

## Stack (1.1.0-test1)

- Next.js 16.3.8 static export, React 19.3 canary, Tailwind v4, Turbopack
- Capacitor (Android), AGP 8.13.0, minSdk 24, target/compile 36
- Plugins: biometric auth, secure storage, speech recognition, SQLite (SQLCipher bundled
  but `androidIsEncryption: false`), text-to-speech, app, browser, filesystem, share
- Custom plugin `DonkBrain` (Java) + `libdonk_llm.so` (llama.cpp JNI, 4 KB aligned)
- sherpa-onnx 1.13.8 with ONNX Runtime 1.28.2 (Whisper small, Piper VITS voices)
- In-bundle: Anthropic SDK, OpenAI SDK, zod 4, motion, a Jinja template engine
  (for GGUF chat templates), fflate (zip), a hand-written MCP client

## Module map

Web modules by Turbopack id (ids are build-specific; listed for traceability).

| Module | Exports | v2 home |
|---|---|---|
| 54113 | `db`, `MIGRATIONS`, `BACKUP_TABLES`, `newId`, `onDataChanged`, `dataChanged` | `web/src/lib/db` (SQL runs natively) |
| 92751 / 45623 | `openNative` (CapacitorSQLite), `openWeb` (jeep-sqlite) | replaced by the native `DonkDb` plugin |
| 16148 | data layer: `createItem`, `updateItem`, `queryItems`, `snapshot`, `agenda`, `balance`, `stat`, `counts`, people, metrics, memory, turns, canvas, settings | `web/src/lib/data` |
| 49766 | `DOMAINS`, `DOMAIN_KEYS`, `ITEM_DOMAINS`, `METRICS`, `CHANNELS`, `CIRCLES`, `STATUSES` | `web/src/lib/domains.ts` |
| 84496 | dates and zones: `parseWhen`, `fmtWhen`, `agentNow`, `greeting`, ... | `web/src/lib/dates.ts` |
| 93903 | `formatINR`, `formatINRCompact`, `rupeesToPaise` | `web/src/lib/money.ts` |
| 43668 | `loadSettings`, `saveSettings`, `useSettings` | `web/src/lib/settings.ts` |
| 6690 | `runAgent`, `UIDocSchema`, tools, prompts, context block | `web/src/lib/agent` |
| 19855 | `ensureBrain`, `ownSession` (on-device brain session) | `web/src/lib/agent/own.ts` |
| 16053 | `renderPrompt` (Jinja), `parseReply`, `toLocalTools` | `web/src/lib/agent/local-format.ts` |
| 28615 | `BRAINS`, `EARS`, `VOICE_HINDI`, `VOICE_ENGLISH` (model registry) | `web/src/lib/models.ts` (+ SHA-256) |
| 13722 (tail) | `PROVIDERS` (Claude, OpenAI, Gemini, OpenRouter), secrets, MCP OAuth, MCP client, chat import | `web/src/lib/{providers,mcp,chats}` (network via SecureFetch) |
| 13927 | component catalog, `Bind`, `ItemQuery`, `validateDoc`, `resolveDoc`, `catalogForPrompt` | `web/src/kit/catalog.ts` |
| 88653 | `Renderer` (all 65 components) | `web/src/kit/` |
| 95104 | kit helpers: `Avatar`, `Panel`, `Empty`, `tint`, `fmtValue`, ... | `web/src/kit/helpers.tsx` |
| 51514 | `Icon` (inline SVG set) | `web/src/kit/Icon.tsx` |
| 11846 | `useResolvedDoc`, `defaultToday`, `domainDoc`, `lifeDoc` | `web/src/screens/docs.ts` |
| 46008 | `TodayView` | `web/src/screens/Today.tsx` |
| 72043 | Talk page | `web/src/screens/Talk.tsx` |
| 936 | `DomainView` (Life area screen + edit form) | `web/src/screens/Domain.tsx` |
| 69042 | Life overview page | `web/src/screens/Life.tsx` |
| 15088 | `SettingsView` (AI, voice, connections, chats, backups, lock, theme) | `web/src/screens/Settings.tsx` |
| 84834 | `Nav`, `PageHeader` | `web/src/components/Nav.tsx` |
| 36058 | `useListener`, `useSpeaker` (mic and speech) | `web/src/lib/voice.ts` |
| 4593 | `lockAvailable`, `unlock` (biometric) | `web/src/lib/lock.ts` |
