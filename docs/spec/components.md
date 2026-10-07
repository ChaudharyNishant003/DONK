# Component kit (1.1.0-test1)

The agent designs screens from these 65 components (`show` tool). Each node is
`{type, props, children?}`; only [container] components take children. The Gallery
page renders every component with sample data. v2 reproduces each one with the same
props, markup and classes.

## Layout (8)

| Component | What it is | Props |
|---|---|---|
| Stack [container] | Vertical stack of children. | `{gap?: 'sm'\|'md'\|'lg'}` |
| Grid [container] | Responsive grid; collapses to fewer columns on a phone. | `{cols?: 1-4}` |
| Row [container] | Horizontal row that wraps. | `{align?: 'start'\|'center'\|'between'}` |
| Section [container] | Titled block grouping related components. | `{title: string, subtitle?, domain?, link?: {label, href}}` |
| Card [container] | Surface that frames its children; tinted by domain. | `{title?, subtitle?, domain?, href?}` |
| Tabs [container] | Tabbed panels; child N is panel N. | `{tabs: string[]}` |
| Collapsible [container] | Folded section for detail the user may not need. | `{title, open?: boolean}` |
| Divider | Thin rule, optionally labelled. | `{label?}` |

## Text (10)

| Component | What it is | Props |
|---|---|---|
| Greeting | Large time-aware hello with the date. Top of a day screen. | `{line?: string}` |
| Heading | Heading with optional eyebrow label. | `{text, level?: 1\|2\|3, eyebrow?}` |
| Text | A paragraph. | `{text, tone?: 'muted'\|'default'\|'strong', size?: 'sm'\|'md'\|'lg'}` |
| Markdown | Light markdown: **bold**, *italic*, lists, links. | `{text}` |
| Callout | Highlighted message: a warning, a nudge, a success. | `{text, title?, tone?: 'info'\|'success'\|'warning'\|'danger'\|'agent'}` |
| Insight | The agent's own observation or advice, visually signed. | `{text, title?}` |
| Quote | A quotation or a line to remember. | `{text, by?}` |
| Badge | Small label. | `{text, tone?, domain?}` |
| ChipList | Row of labelled chips (tags, attendees, options). | `{chips: [{label, domain?, tone?}]}` |
| KeyValue | Label/value rows, e.g. details of one record. | `{rows: [{label, value}]}` |

## Time (6)

| Component | What it is | Props |
|---|---|---|
| Agenda | Day-grouped schedule: meetings, appointments, due items, birthdays, reconnects. Bind to agenda. | `{title?, entries?, bind?: agenda}` |
| DayPlan | Hour grid of one day with time blocks — for planning or time-blocking a day. | `{blocks: [{start: ISO, end: ISO, title, domain?}], from?: hour, to?: hour}` |
| WeekStrip | Seven-day strip with a dot per entry. Bind to agenda (days 7). | `{entries?, bind?: agenda}` |
| MonthCalendar | Month grid marking busy days. Bind to agenda (days 31). | `{entries?, bind?: agenda}` |
| Timeline | Vertical timeline of past or planned events (history with a person, a project's milestones). | `{title?, events: [{at: ISO, title, subtitle?, domain?}]}` |
| NextUp | Big card for the very next meeting or appointment, with a countdown. Bind to items {starts:'upcoming', limit:1}. | `{items?, bind?: items}` |

## Life (12)

| Component | What it is | Props |
|---|---|---|
| MeetingCard | Meetings as rich cards: time, with whom, where, prep notes. Bind to items {domain:'meeting', starts:…}. | `{items?, bind?: items}` |
| PersonCard | People as cards: circle, last contact, when to reconnect, buttons to log a call or meet-up. Bind to people. | `{people?, bind?: people}` |
| PeopleOrbit | Visual of inner/close/wider circles; people glow when it is time to reconnect. Bind to people {filter:'all'}. | `{people?, bind?: people}` |
| ReconnectList | Who is due a call or visit, with one-tap 'spoke today'. Bind to people {filter:'reconnect'}. | `{title?, people?, bind?: people}` |
| BalanceCard | Net money position: owed to me vs I owe, top people. Bind to balance. | `{balance?, bind?: balance}` |
| Ledger | Debts and credits as a ledger with settle buttons. Bind to items {domain:'money'}. | `{title?, items?, bind?: items}` |
| PromiseList | Promises split into 'I promised' and 'promised to me', with keep buttons. Bind to items {domain:'promise'}. | `{items?, bind?: items}` |
| IdeaBoard | Ideas as a wall of sticky notes coloured by kind. Bind to items {domain:'idea'}. | `{items?, bind?: items}` |
| MetricCard | Latest health reading vs goal with a 2-week trend. Bind to a metric. | `{bind: metric}` |
| MoodPicker | Five faces; tapping one logs today's mood. | `{prompt?}` |
| QuickLog | Preset buttons that log a health reading in one tap (water +250 ml, steps…). | `{metric: key, presets: number[], label?}` |
| DomainTiles | One tile per life area with its live headline numbers; each opens that area. Bind to domains. | `{tiles?, bind?: domains}` |

(unlisted group stat: StatTile, KpiRow, ProgressBar, ProgressRing, ActivityRings, Gauge, Countdown, Streak, Comparison, StackedBar)

(unlisted group chart: Sparkline, LineChart, BarChart, DonutChart, Heatmap, Radar, HabitGrid)

(unlisted group list: TaskList, ItemList, Checklist, Kanban, PriorityMatrix, ProjectList)

(unlisted group action: ActionRow, Suggestions, ConfirmCard, QuickAdd, LinkCard, EmptyState)
