# Android side (1.1.0-test1)

Decompiled with jadx. Four app classes plus `MainActivity` (registers `DonkBrainPlugin`).

## `DonkBrain` Capacitor plugin

| Method | Arguments | Result |
|---|---|---|
| `device()` | – | `{ramTotal, ramFree, diskFree, cores, loaded}` |
| `fileState({id, archive?, fileName?})` | | `{ready, downloading}`; resumes progress events |
| `download({id, url, archive?, fileName?, title?})` | https only | Starts a DownloadManager download |
| `cancelDownload({id})`, `deleteFile({id, archive?, fileName?})` | | Unloads the brain first if it is the loaded file |
| `loadBrain({fileName, contextSize = 4096})` | | `{template, bos, eos, description, contextSize}` |
| `unloadBrain()` | | |
| `generate({prompt, maxTokens = 512, temperature = .7, topP = .8, topK = 20, minP = 0, streamId})` | | `{text, stop: end|length|stopped|too_long, promptTokens, reusedTokens, generatedTokens, promptMs, generateMs}` |
| `stopGenerate()` | | Aborts generation |
| `listen({prefix})` | needs RECORD_AUDIO | `{text, lang, seconds, decodeMs}` |
| `stopListening()`, `speak({text, hindiId, englishId, speed})`, `stopSpeaking()` | | |
| `warmVoice({prefix?, hindiId?, englishId?})` | | Loads ears and voices in the background |

Events: `download {id, state: downloading|paused|unpacking|ready|error, done, total, error?}`,
`brainText {streamId, text}` (per token piece; unused by the UI), `voiceLevel {level}`,
`speakLevel {level}`.

## LlamaEngine (`libdonk_llm.so`)

Single worker thread ("donk-brain", max priority). JNI: `nativeInit(nativeLibraryDir)`
(loads ggml CPU variants with `ggml_backend_load_all_from_path`, so native libraries
must be extracted: `extractNativeLibs=true`), `nativeLoad(path, nCtx, threads)` with
threads = clamp(cores / 2, 2, 4), `nativeGenerate(...)` with a text sink callback,
`nativeInfo` (chat template, BOS, EOS, description, context size separated by U+001F),
`nativeStats` (prompt, reused, generated tokens; prompt and generate ms),
`nativeAbort`, `nativeFree`. Prompt reuse: common prefix with the previous prompt is
kept in the KV cache (`llama_memory_seq_rm`).

## ModelStore

Downloads through Android DownloadManager into `getExternalFilesDir("models")`
(falls back to internal storage), visible to the user as "DONK download". Archives
(`.tar.bz2`) are unpacked with a path-traversal check and marked with `.done`.
Progress is polled every 700 ms. **No integrity check** (F11, SE-3). Downloads are
allowed on metered and roaming networks (PRD wants Wi-Fi only by default).

## VoiceEngine (sherpa-onnx)

- **Ears**: Whisper (offline recognizer), files `<prefix>-encoder.int8.onnx`,
  `<prefix>-decoder.int8.onnx`, `<prefix>-tokens.txt`, language auto, 4 threads,
  greedy search. Recording: 16 kHz mono, 100 ms frames, energy VAD (threshold
  max(2.5 × noise floor from the first 5 frames, 0.012)); stops after 1.2 s of silence
  once speech started, or 8 s with no speech; maximum 30 s. Decoding happens only after
  recording ends (F6).
- **Voices**: Piper VITS (`*.onnx`, `tokens.txt`, `espeak-ng-data`), 2 threads,
  sentence by sentence, Hindi voice for sentences containing Devanagari, English voice
  otherwise. Playback through AudioTrack (usage assistant).

## Model registry

| Id | Files | Size |
|---|---|---|
| `qwen35-0.8b` (brain) | `unsloth/Qwen3.5-0.8B-GGUF` → `Qwen3.5-0.8B-Q4_K_M.gguf`; sampling temp .7, top-p .8, top-k 20, min-p 0; context 4096 | ~560 MB |
| `ears-whisper-small` | `csukuangfj/sherpa-onnx-whisper-small`: `small-encoder.int8.onnx`, `small-decoder.int8.onnx`, `small-tokens.txt` | ~371 MB |
| `voice-hi-priyamvada` | sherpa-onnx tts-models `vits-piper-hi_IN-priyamvada-medium.tar.bz2` | ~67 MB |
| `voice-en-lessac` | sherpa-onnx tts-models `vits-piper-en_US-lessac-medium.tar.bz2` | ~67 MB |

## Manifest

Permissions: INTERNET, RECORD_AUDIO, MODIFY_AUDIO_SETTINGS, USE_BIOMETRIC,
USE_FINGERPRINT. Queries: speech recognition service, TTS service, Custom Tabs.
`allowBackup=false`, `fullBackupContent=false`, data extraction rules set.
Deep link `com.kumarsahilrs.donk://oauth` for MCP OAuth. No notification permission
and no scheduler (F10).
