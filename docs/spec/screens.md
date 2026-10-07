# Screens (1.1.0-test1)

Reference screenshots of every route, light and dark, live in
`tools/ui-ref/ref/` (captured with `tools/ui-ref/capture.mjs`: 375x812, Asia/Kolkata,
clock frozen at 7 Oct 2026 09:30, reduced motion, empty database). v2 must match them.

## Navigation

Phone: fixed bottom bar with **Today** (sun), the central gradient **orb** button
(opens Talk), and **Life** (grid). The active tab shows an accent bar above its icon.
Wide screens: left sidebar (orb, Today, Talk, Life; theme and settings at the bottom).

## Routes

| Route | Screen | Contents |
|---|---|---|
| `/` | Talk | Same as `/talk/`: DONK opens on the voice stage |
| `/talk/` | Talk (`.stage` dark theme in both modes) | "DONK" label, swap-layout, speaker and history buttons; animated orb; "TAP TO TALK", "What's on your mind?", hint line; setup callout when no AI is configured ("Set up your AI to start talking: Settings → AI. Everything else already works."); suggestion chips; keyboard and mic buttons |
| `/today/` | Today | "Standard layout" toggle (AI-composed vs default) and settings; Greeting; KpiRow (Due today, Overdue, Meetings, Net balance); sections Schedule (→ Week), To do (→ All), Promises (I promised / Promised to me), Reach out (→ People), Body (→ Health: Sleep, Steps, Water metric cards), QuickLog water, MoodPicker, Suggestions. The AI-composed version replaces this with the saved `canvas.today` doc |
| `/life/` | Life overview | "Everything / Your life / Nine areas, one picture." KpiRow (Open tasks, Promises I owe, Net balance, To reconnect), DomainTiles for the nine areas, WeekStrip "Next 7 days" (→ Meetings), StackedBar "Open by area", ReconnectList "Due a call" |
| `/life/<domain>/` | Domain view (9) | Back link to Life, title, blurb, domain-specific blocks (e.g. Money: net position card, Owed to me, I owe, Settled collapsible), floating add button opening the add/edit form |
| `/settings/` | Settings | Cards: DONK's own brain (downloads, test), AI (provider, key, model, thinking), Connections (MCP servers, presets, sign-in), Chats (import, meaning search), Voice (language, engine, speed, test, speak replies, hands-free), Lock, Backup (password, back up now, restore), Look (System/Light/Dark), What DONK remembers; footer "DONK 0.1.0 · everything stays on this phone" |
| `/gallery/` | Component gallery | All 65 components with sample data, grouped (see components.md) |
| 404 | Not found | Next.js default not-found page |

Domain screens are documents built by `domainDoc(domain)` from the same component kit
(module 11846), so most of their structure is defined by the catalog components.
