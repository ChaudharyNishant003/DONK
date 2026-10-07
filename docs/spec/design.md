# Design (1.1.0-test1)

The design is frozen for v2 (PRD section 5). Values below were read from the
1.1.0-test1 stylesheet.

## Colour tokens

| Token | Light | Dark | Stage |
|---|---|---|---|
| `--bg` | #f6f6f9 | #0b0b12 | #05050a |
| `--bg-2` | #eeeef4 | #11111a | – |
| `--surface` | #ffffff | #15151f | #ffffff0f |
| `--surface-2` | #f3f3f8 | #1c1c28 | #ffffff17 |
| `--line` | #e4e4ec | #2a2a3a | #ffffff1f |
| `--ink` | #12121a | #f2f2f7 | #f5f5fa |
| `--ink-2` | #4c4c5c | #b4b4c4 | #c3c3d3 |
| `--ink-3` | #8a8a9a | #7c7c90 | #8a8aa0 |
| `--accent` | #6d5dfc | #8b7dff | (inherits) |
| `--work` | #5b5bf0 | #8a8aff | #8a8aff |
| `--task` | #0a8fd6 | #3fb4f0 | #3fb4f0 |
| `--meeting` | #8b5cf6 | #a98bff | #a98bff |
| `--idea` | #d98a00 | #f5b13d | #f5b13d |
| `--promise` | #ea6a16 | #ff8a44 | #ff8a44 |
| `--money` | #0a9a6e | #2fcf98 | #2fcf98 |
| `--health` | #e5484d | #ff6b70 | #ff6b70 |
| `--people` | #d6409f | #f06cbc | #f06cbc |
| `--misc` | #64748b | #94a3b8 | #94a3b8 |
| `--success` | #0a9a6e | #2fcf98 | #2fcf98 |
| `--warning` | #d98a00 | #f5b13d | #f5b13d |
| `--danger` | #e5484d | #ff6b70 | #ff6b70 |
| `--info` | #0a8fd6 | #3fb4f0 | #3fb4f0 |

Shadows: light `0 1px 2px #1010200d, 0 8px 24px -12px #1010201f`; dark
`0 1px 2px #0006, 0 12px 32px -16px #0009` (`--shadow`, used by `shadow-card`).

Theme selection: `:root` is light; dark applies under `prefers-color-scheme: dark`
unless `data-theme="light"`, and always with `data-theme="dark"`. The `.stage` class
(full-screen voice/talk surface) forces its own dark palette.

Extra Tailwind colours used: red-300, amber-200/300/400, cyan-300/500,
fuchsia-400/500, black, white.

## Typography

Inter Variable (100–900, self-hosted woff2 subsets: latin, latin-ext, cyrillic,
cyrillic-ext, greek, greek-ext, vietnamese) with `ui-sans-serif, system-ui,
-apple-system, "Segoe UI", Roboto, sans-serif` fallback. Body uses
`font-feature-settings: "cv11", "ss01"`. `.tnum` sets tabular numbers. Tailwind
default type scale (xs .75rem … 4xl 2.25rem), weights medium 500 and semibold 600,
tracking tight/wide/wider, leading tight/snug/relaxed.

## Shape and motion

Radii (Tailwind): md 6px, lg 8px, xl 12px, 2xl 16px, 3xl 24px. Blur sm 8px, xl 24px,
2xl 40px. Default transition 150 ms `cubic-bezier(.4, 0, .2, 1)`. Animations: spin,
pulse; `motion` (Framer Motion) for presence and layout animations. Reduced motion
collapses all transitions and animations.

## Base

`body`: `background: var(--bg); color: var(--ink); min-height: 100dvh`; no tap
highlight. `.scrollbar-none` hides scrollbars.

## Layout

Phone: bottom navigation (Today, a central mic orb button, Life). Wide screens: left
sidebar with Today, Talk, Life and Settings. Content max widths use Tailwind
containers (xs to 5xl).

## App icon

Gradient orb (cyan to violet to pink) on black, adaptive icon with separate
foreground layer; all densities recovered from the APK (`res/o-.png` etc.).
