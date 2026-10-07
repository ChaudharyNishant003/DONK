# Data model (1.1.0-test1)

## Database

SQLite, migrations tracked in `_migration (version, applied_at)`. One migration
(version 1) creates everything. Ids are 24 hex chars (`randomUUID` without dashes).
Times are Unix milliseconds. Money is stored in **paise** (`amount_paise`).

```sql
CREATE TABLE person (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  relation TEXT,
  circle TEXT NOT NULL DEFAULT 'close',
  cadence_days INTEGER,
  last_contact_at INTEGER,
  birthday TEXT,
  phone TEXT,
  email TEXT,
  notes TEXT,
  tags TEXT NOT NULL DEFAULT '[]',
  data TEXT NOT NULL DEFAULT '{}',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX person_name ON person (name);

CREATE TABLE item (
  id TEXT PRIMARY KEY,
  domain TEXT NOT NULL,
  kind TEXT NOT NULL,
  title TEXT NOT NULL,
  notes TEXT,
  status TEXT NOT NULL DEFAULT 'open',
  priority INTEGER NOT NULL DEFAULT 2,
  due_at INTEGER,
  start_at INTEGER,
  end_at INTEGER,
  amount_paise INTEGER,
  direction TEXT,
  location TEXT,
  tags TEXT NOT NULL DEFAULT '[]',
  data TEXT NOT NULL DEFAULT '{}',
  person_id TEXT REFERENCES person (id) ON DELETE SET NULL,
  parent_id TEXT REFERENCES item (id) ON DELETE SET NULL,
  source TEXT NOT NULL DEFAULT 'manual',
  completed_at INTEGER,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX item_domain_status ON item (domain, status);
CREATE INDEX item_due ON item (due_at);
CREATE INDEX item_start ON item (start_at);
CREATE INDEX item_person ON item (person_id);
CREATE INDEX item_parent ON item (parent_id);

CREATE TABLE interaction (
  id TEXT PRIMARY KEY,
  person_id TEXT NOT NULL REFERENCES person (id) ON DELETE CASCADE,
  at INTEGER NOT NULL,
  channel TEXT NOT NULL,
  note TEXT
);
CREATE INDEX interaction_person_at ON interaction (person_id, at);

CREATE TABLE metric (
  id TEXT PRIMARY KEY,
  key TEXT NOT NULL,
  value REAL NOT NULL,
  unit TEXT,
  at INTEGER NOT NULL,
  note TEXT
);
CREATE INDEX metric_key_at ON metric (key, at);

CREATE TABLE memory (
  id TEXT PRIMARY KEY,
  text TEXT NOT NULL,
  topic TEXT,
  created_at INTEGER NOT NULL
);

CREATE TABLE turn (
  id TEXT PRIMARY KEY,
  role TEXT NOT NULL,
  text TEXT NOT NULL,
  ui TEXT,
  mode TEXT NOT NULL DEFAULT 'voice',
  created_at INTEGER NOT NULL
);
CREATE INDEX turn_created ON turn (created_at);

CREATE TABLE canvas (
  key TEXT PRIMARY KEY,
  doc TEXT NOT NULL,
  composed_by TEXT NOT NULL,
  generated_at INTEGER NOT NULL
);

-- Imported ChatGPT and Claude conversations.
CREATE TABLE chat_conversation (
  id TEXT PRIMARY KEY,
  source TEXT NOT NULL,
  external_id TEXT NOT NULL,
  title TEXT NOT NULL,
  created_at INTEGER,
  updated_at INTEGER,
  message_count INTEGER NOT NULL DEFAULT 0,
  UNIQUE (source, external_id)
);
CREATE TABLE chat_message (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  conversation_id TEXT NOT NULL REFERENCES chat_conversation (id) ON DELETE CASCADE,
  role TEXT NOT NULL,
  text TEXT NOT NULL,
  created_at INTEGER
);
CREATE INDEX chat_message_conversation ON chat_message (conversation_id);
-- docid = chat_message.id. FTS4: it is in every SQLite build we ship on.
CREATE VIRTUAL TABLE chat_fts USING fts4 (text);
-- Meaning search: one vector per chunk of a conversation.
CREATE TABLE chat_chunk (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  conversation_id TEXT NOT NULL REFERENCES chat_conversation (id) ON DELETE CASCADE,
  text TEXT NOT NULL,
  embedding BLOB,
  model TEXT
);
CREATE INDEX chat_chunk_conversation ON chat_chunk (conversation_id);

-- Settings that are not secrets. Keys and tokens live in the Android keystore.
CREATE TABLE setting (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
```

Backups include: `person, item, interaction, metric, memory, turn, canvas,
chat_conversation, chat_message, chat_chunk, setting` (not `chat_fts`, rebuilt on restore).

v2: same schema in SQLCipher (D7). New tables for v2 features (secrets, reminders,
egress log, timings, System 1 corrections) are added as migration 2+.

## Domains and kinds

`people` is a domain in the UI but people live in `person`, not `item`.

| Domain | Label | Kinds (key: label, direction) |
|---|---|---|
| work | Work | project, deliverable, goal, followup |
| task | Tasks | todo, errand, call, chore, admin |
| meeting | Meetings | work (Work meeting), personal (Catch-up) |
| idea | Ideas | business, product, content, personal, someday |
| promise | Promises | by_me (by_me), to_me (to_me) |
| money | Money | lent (owed_to_me), borrowed (i_owe), split (owed_to_me), bill (i_owe) |
| health | Health | appointment, medication, routine, symptom |
| people | People | circles: inner, close, wider |
| misc | Everything else | note, list, purchase, travel, document |

Statuses: `open, doing, waiting, done, dropped` (open set: open, doing, waiting).
Channels: `call, meet, message, video, other`. Circles: `inner, close, wider`.

## Metrics

| Key | Label | Unit | Goal | Better | Aggregate | Range |
|---|---|---|---|---|---|---|
| sleep_hours | Sleep | h | 8 | higher | last | 0–16 |
| steps | Steps | steps | 8000 | higher | sum | 0–100000 |
| water_ml | Water | ml | 2500 | higher | sum | 0–10000 |
| workout_min | Workout | min | 30 | higher | sum | 0–600 |
| weight_kg | Weight | kg | – | range | last | 20–300 |
| mood | Mood | /5 | 4 | higher | avg | 1–5 |
| bp_sys | BP (systolic) | mmHg | 120 | lower | last | 60–250 |
| bp_dia | BP (diastolic) | mmHg | 80 | lower | last | 30–160 |
| resting_hr | Resting heart rate | bpm | – | lower | last | 30–200 |

## Settings (`setting` table, JSON values)

| Key | Default |
|---|---|
| `ai` | `{own: {enabled: false, brain: null}, provider: null, models: {}, thinking: "balanced"}` |
| `voice` | `{lang: "en-IN", speak: true, handsFree: false, rate: 1, engine: "builtin", openaiVoice: "alloy", openaiSttModel: null, openaiTtsModel: null}` |
| `search` | `{embeddingProvider: null, embeddingModel: null}` |
| `mcp` | `[]` (connected servers: `{id, name, url, auth: none|token|oauth, enabled}`) |
| `lock` | `true` |
| `theme` | `"system"` |

## Secrets (1.1.0-test1: SecureStorage plugin)

| Name | Holds |
|---|---|
| `key.<provider>` | API key for claude, openai, gemini, openrouter |
| `mcp.<id>.token` | Bearer token for a token-auth MCP server |
| `mcp.<id>.oauth` | `{clientId, tokenEndpoint, accessToken, refreshToken, expiresAt}` |

v2: secrets move to the native vault (D6); the WebView only ever sees names and
"saved, ends in ab12" hints.

## Money

Stored in paise. `formatINR` uses `en-IN` grouping, `−` (U+2212) for negatives, optional
`+` sign. `formatINRCompact`: K (thousand), L (lakh), Cr (crore).
