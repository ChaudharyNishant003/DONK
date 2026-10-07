# Agent (1.1.0-test1)

`runAgent({utterance, mode, signal, confirm})` is an async generator yielding
`status`, `ui`, `changed`, `error` and `done` events. Modes: `voice`, `text`,
`canvas` (compose the Today screen).

## Turn, step by step

1. Load settings. If "DONK's own brain" is enabled, use the on-device brain; otherwise
   the chosen cloud provider, model and key (error if any is missing).
2. Gather in parallel: `snapshot(now)` (life context), recent turns (10 cloud / 4
   on-device; none for canvas), and MCP tools from enabled servers (cloud only).
3. Build the user message: `<context>…</context>\n\n<request>…</request>`.
4. Save the user turn (not for canvas).
5. Loop up to 10 steps: `session.step()` → text and tool calls. Own tools run locally
   (`show` returns a UI doc). MCP tools named `<service>__<tool>`; anything without
   `readOnlyHint` asks the user first (`confirm`), and a refusal is reported to the model.
6. Save the agent turn (with its UI doc) or, for canvas, save the doc as
   `canvas.today`. Emit `done`.

Errors are mapped to plain messages: 401 key refused, 403 key cannot use model, 404
model not on key, 429 rate limited, 5xx provider trouble, network → "Can't reach the AI
provider".

## Context block

`Now`, `Mode`, `Connected services`, then: today's schedule, overdue, open promises,
money (owed to me / I owe / by person, top 8), due to reconnect, birthdays soon,
active projects (with child task progress), latest ideas, latest health readings,
all remembered facts, recent conversation. Item lines read
`[id] title · domain/kind · at … · due … · person · ₹amount · direction · status`.

This is PRD finding F3: it precedes the request and changes every call, so little of
the prompt can be reused from the KV cache. v2 replaces it with retrieval (S2-3).

## System prompts

Two prompts, ported verbatim into `web/src/lib/agent/prompts.ts`:

- **Cloud** (~70 lines): role, SAY vs SHOW, language mirroring (English, Hindi,
  Hinglish; Latin or Devanagari as used), the domain list with kinds generated from
  `DOMAINS`, metrics list, how to act (capture first, classify by meaning with worked
  examples, resolve relative times to local `YYYY-MM-DDTHH:mm`, rupees in tool input,
  people matching, ConfirmCard before bulk or irreversible changes, remember facts),
  past AI chats, connected services (writes need approval; "@claude" GitHub issues for
  coding work), answer style for voice and text, the `show` screen grammar, binds and
  stats, and the generated component catalog (`catalogForPrompt()`). Compose-today
  instructions for canvas mode.
- **On-device** (~10 lines, about 1,200 characters): the same essentials, compact.

## Tools

| Tool | Input (beyond the obvious) | Notes |
|---|---|---|
| `add_item` | `domain`, `title`, kind, notes, status, priority 1–3, due/start/end, `amount_rupees`, direction, person / person_id, location, tags, project_id | Unknown person names are created in circle `wider`; ambiguous names return an error asking which one |
| `update_item` | `id`, any add_item field, `clear: [due,start,end,person,amount,location,notes,project]` | |
| `delete_item` | `id` | Only when clearly asked |
| `find_items` | `ItemQuery` (domain, kind, status, due, starts, direction, person, search, sort, limit…) | |
| `add_person` | `name`, relation, circle, cadence_days 1–730, birthday `MM-DD` or `YYYY-MM-DD`, phone, email, notes, tags | Rejects exact-name duplicates |
| `update_person` | `id` + person fields | |
| `find_people` | `name` (fuzzy) or `filter` | |
| `log_contact` | person / person_id, `channel`, note, at | Resets the reconnect clock |
| `log_metric` | `metric`, `value`, at, note | Range-checked |
| `get_metrics` | `metric`, days 2–120 | |
| `get_agenda` | days 1–31 | |
| `remember` / `forget` | text, topic / memory_id | |
| `search_chats` | query, source, mode auto/keyword/meaning, limit | |
| `read_chat` | conversation_id, from, limit | |
| `show` | `{title?, subtitle?, nodes: [{type, props?, children?}]}` | Validated; invalid nodes dropped and reported |

Times accept local `YYYY-MM-DD` / `YYYY-MM-DDTHH:mm` or ISO instants. A date-only
`due` means end of that day; date-only start means start of day.

Canvas mode only offers `find_items, find_people, get_metrics, get_agenda, show`.

The on-device brain gets six tools with trimmed fields: `add_item` (domain, kind,
title, notes, due, start, end, amount_rupees, direction, person, priority),
`update_item` (id, title, status, due, start, notes, amount_rupees, person),
`find_items`, `add_person` (name, relation, circle, cadence_days, birthday, phone),
`log_contact`, `remember`.

## On-device brain session (`ownSession`)

`ensureBrain` loads the GGUF on first use (F5). Each step renders the whole
conversation with the model's Jinja chat template (`renderPrompt`), calls
`DonkBrain.generate` with `maxTokens` 400 and waits for the full text (F1; the native
side already emits `brainText` events that nobody listens to). `parseReply` extracts
tool calls from the text. After tools run, another full step runs to produce the
spoken reply (F2). A `too_long` stop throws "This conversation is too long…" (F4).

## Cloud providers

| Id | API | Notes |
|---|---|---|
| claude | Anthropic Messages (beta), `max_tokens` 16000, system prompt cached (`ephemeral`) | Adaptive thinking with effort low/medium/high for Opus/Sonnet 4.6+, 5.x, Fable, Mythos; server-side fallback beta for Opus 5/5.5, Sonnet 5.5, Fable 5.1; continues on `pause_turn` |
| openai | Chat Completions, `https://api.openai.com/v1` | `reasoning_effort` for reasoning models |
| gemini | OpenAI-compatible, `https://generativelanguage.googleapis.com/v1beta/openai/` | Schemas sanitised (nullable types) |
| openrouter | OpenAI-compatible, `https://openrouter.ai/api/v1`, header `X-Title: DONK` | Only models that support tools |

Thinking setting: fast / balanced / deep → low / medium / high. Model lists are
fetched from each provider's `/models`.

## MCP connectors

Hand-written Streamable HTTP client, protocol `2025-06-18`, client `DONK 0.1.0`.
Session per server (`mcp-session-id`), re-initialised on 404. `tools/list` paginated
(max 500, cached 10 minutes). `tools/call` output flattened to text, cut at 30,000
characters. Auth: none, bearer token, or OAuth 2.1 with PKCE (S256), protected-resource
and authorization-server discovery, dynamic client registration (`client_name`
"DONK", public client), redirect `com.kumarsahilrs.donk://oauth/callback` (v2:
`com.chaudharynishant.donk://oauth/callback`), refresh when under 60 s to expiry.
Built-in presets include GitHub Copilot MCP and Railway MCP.

## Imported chats

`parseExport(bytes, fileName)` accepts a ChatGPT or Claude export (`.zip` containing
`conversations.json`, or the JSON itself). ChatGPT: walk `mapping` from
`current_node` up through parents. Claude: `chat_messages` with `sender`
human/assistant. Import upserts by `(source, external_id)` in batches of 50, filling
`chat_fts`. Keyword search: FTS4 prefix match, newest first, one hit per conversation,
plus the first assistant reply after a user hit. Meaning search: conversations split
into ~1,500-character chunks, embedded with the user's OpenAI or Gemini embedding model
(256 dimensions when supported), normalised, stored base64; cosine ranking, one hit per
conversation.
