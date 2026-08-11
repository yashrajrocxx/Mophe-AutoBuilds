# yresearch. — Design System (v2)

A precise, implementation-ready spec for the `yresearch.` (DeepSeek clone with
a Claude-style response engine) UI. Every value below is already wired in
`frontend/src/index.css`, Tailwind, shadcn primitives, and custom components —
build any new element from the recipes here and it will feel native.

---

## 0. Product Overview

`yresearch.` is a local-first personal digital twin. The UI is composed of:

- **ChatPage** — empty state welcomer, in-composer model selector, animated
  activity timeline (thinking + web search + sources + done), Claude-style
  markdown response with inline citation chips.
- **MemoryPage** — knowledge graph (neurons + synapses) and episodic log.
- **SettingsPage** — LLM endpoint, provider, keys, appearance.
- **Sidebar** — collapsible on desktop (floating toolbar in collapsed state),
  drawer overlay on mobile, session groups with hover context menus.
- **SearchDialog** — global command-palette style search over all sessions
  (⌘/Ctrl + K).

---

## 1. Brand Identity

| Token | Value | Purpose |
|---|---|---|
| Product name | `yresearch.` (lowercase + terminal period) | Wordmark always ends with an accent-coloured period |
| Wordmark font | `Space Grotesk`, 700, tracking `-0.02em` | Logo + all H1s / mode titles (utility class `.yr-brand`) |
| Body font | `Inter`, 400/500/600, feature-settings `'ss01','cv11'` | Everything else |
| Mono font | `JetBrains Mono` (fallback: source-code-pro) | Code blocks + inline `code` |
| Accent (Claude terracotta) | `hsl(17 60% 59%)` (~`#D97757`) | Single hero colour — used sparingly |
| Accent soft | `hsl(17 70% 94%)` light / `hsl(17 40% 22%)` dark | Chip backgrounds, active-item wash |

**Emblem** — a circular gradient disc (accent → accent 75%) with a white
"Y"-styled stroke and a small dot. Component: `<YrEmblem size={n} />`.
Uses: 24 px (chat header on mobile), 26–28 px (sidebar logo, collapsed toolbar,
search dialog rows), 36–40 px (empty-state greeting).

**Wordmark** — `<YrWordmark />` renders emblem + `yresearch.` where the final
`.` is accent-coloured. Used in expanded sidebar, mobile top bar, and Memory /
Settings mobile page headers.

**Claude Sparkle** — a bespoke 8-point burst SVG (`<ClaudeSparkle />`).
- `animated` prop enables a 2.4 s rotate + scale + soft glow (`yr-sparkle-anim`).
- Used in three places: active timeline header, in-message post-response pulse
  (`.yr-final-pulse`), and elsewhere as the "AI is working" mark.

---

## 2. Colour Tokens

All colours are **HSL triples** on CSS variables. Use `hsl(var(--x))` or
`hsl(var(--x) / 0.4)` for alpha. Defined in `:root` (light) and `.dark`.

### Base (shadcn-compatible)

| Variable | Light | Dark | Use |
|---|---|---|---|
| `--background` | `0 0% 100%` | `220 10% 8%` | Page canvas |
| `--foreground` | `220 15% 12%` | `30 15% 92%` | Primary text |
| `--card` | `0 0% 100%` | `220 10% 10%` | Card surfaces |
| `--muted` | `220 14% 96%` | `220 10% 14%` | Neutral fills |
| `--muted-foreground` | `220 10% 45%` | `220 8% 60%` | Secondary text |
| `--border` | `220 13% 91%` | `220 10% 18%` | Hairline dividers |
| `--input` | same as border | same as border | Form outlines |
| `--ring` | `17 60% 59%` | `17 60% 59%` | Focus ring |
| `--destructive` | `0 72% 51%` | `0 62% 40%` | Delete / error |
| `--radius` | `0.75rem` | `0.75rem` | Base radius token |

### `yresearch.`-specific

| Variable | Light | Dark | Use |
|---|---|---|---|
| `--yr-accent` | `17 60% 59%` | `17 65% 62%` | Primary brand colour |
| `--yr-accent-soft` | `17 70% 94%` | `17 40% 22%` | Chip / hover wash tinted with brand |
| `--yr-sidebar` | `30 20% 97%` | `220 10% 6%` | Sidebar background |
| `--yr-surface` | `0 0% 100%` | `220 10% 8%` | Elevated surfaces (dialogs) |
| `--yr-hover` | `220 14% 94%` | `220 10% 14%` | Row hover, chip idle fill |
| `--yr-composer` | `0 0% 100%` | `220 10% 12%` | Composer background |
| `--yr-text-subtle` | `220 8% 55%` | `220 8% 55%` | Metadata (dates, hints) |

**Colour rules**
- Never use a raw hex in components; always reference `hsl(var(--…))`.
- Accent is used **sparingly**: send button, active nav row, brand period,
  active model in the selector, tier badge under chat title, `1px` focus ring,
  active citation chip hover.
- Never as a page background. Never as a saturated gradient on buttons.
- Backgrounds must contrast text by ≥ 4.5:1 (WCAG AA).

---

## 3. Typography Scale

| Token | Size / Line | Weight | Where |
|---|---|---|---|
| Display H1 (`.yr-brand`) | `30 px / 1.15` | 700 | Empty-state greeting ("Fast mode") |
| Page H1 (`.yr-brand`) | `22–24 px / 1.2` | 700 | Memory / Settings titles |
| Markdown H2 (`.yr-brand`) | `22 px / 1.2` | 700 | Response headings (`## ...`) |
| Markdown H3 | `15.5 px / 1.3` | 600 | Sub-headings (`### ...`) |
| Response body | `15 px / 1.75` | 400 | Assistant markdown output |
| Chat message | `14.5 px / 1.6` | 400 | User bubbles, generic paragraphs |
| Compact | `13.5 px / 1.4` | 400 / 500 | Sidebar rows, dropdown items, timeline text |
| Metadata | `12.5 px / 1.4` | 400 | Descriptions, timestamps, chip labels |
| Label | `11.5 px` uppercase, `tracking-wider` | 500 | Sidebar section headers, stat labels |
| Citation chip | `10.5 px` uppercase, `tracking-wide` | 500 | Inline `[[Label\|domain]]` markers |
| Micro | `11 px` | 400 | Footer disclaimers ("AI-generated…") |

Line-height defaults: **1.75** inside response markdown, **1.6** for reading
paragraphs elsewhere, **1.4** for UI chrome.

---

## 4. Spacing & Layout

Base unit **4 px**. Prefer these steps: `4 · 8 · 12 · 16 · 20 · 24 · 32 · 48 · 64`.

| Region | Spec |
|---|---|
| App shell | `flex h-[100dvh] w-screen overflow-hidden bg-background` |
| Sidebar (desktop expanded) | Fixed width **268 px**, `border-r border-border/60`, bg `--yr-sidebar` |
| Sidebar (desktop collapsed) | Not rendered — replaced by `<CollapsedToolbar />` positioned at `top-3 left-4 z-30` (emblem + rounded icon capsule) |
| Sidebar (mobile) | Fixed drawer `w-[86vw] max-w-[300px]`, slides in with 300 ms `cubic-bezier(0.32,0.72,0,1)`, dim backdrop `bg-black/50 backdrop-blur-sm` |
| Main content | `flex-1 flex flex-col overflow-hidden relative min-w-0` |
| Chat max-width | `max-w-3xl mx-auto` (never wider than 768 px) |
| Page max-width | `max-w-5xl` (Memory) / `max-w-3xl` (Settings) |
| Composer inner padding | Textarea `px-5 pt-4 pb-2`; bottom row `px-3 pb-3` |
| Chat header | `min-h-14 px-3 sm:px-4 py-2 flex gap-2 flex-wrap sm:flex-nowrap` |
| Timeline node offset | Text starts at `pl-9` (36 px), rail at `left-[11px]`, icon square `w-[22px] h-[22px]` centred on rail |
| Card padding | `p-4` (compact) / `p-6` (Settings sections) |

**Radius scale** (`--radius = 0.75rem`)

| Class | Use |
|---|---|
| `rounded-sm` (`0.375 rem`) | Tiny chips, metadata |
| `rounded-md` (`0.5 rem`) | Icon hover targets, dropdown items |
| `rounded-lg` (`0.5 rem`) | Session rows, sidebar toggles |
| `rounded-xl` (`0.75 rem`) | Cards, reasoning block, dialog panels, source-cards container |
| `rounded-2xl` (`1 rem`) | Composer, dialog shell |
| `rounded-3xl` (`1.5 rem`) | User message bubble |
| `rounded-full` | Chips, pills, New-chat CTA, model selector, send button, avatars, source-list card domain letter dots |

---

## 5. Elevation & Shadows

| Utility class | Definition | Use |
|---|---|---|
| `yr-composer-shadow` | Light: `0 1px 2px .04 / 0 4px 12px .05 / 0 12px 32px .06`. Dark: `0 1px 2px .4 / 0 8px 24px .35`. | Composer |
| `shadow-2xl` | Tailwind default | SearchDialog panel |
| Backdrop | `bg-black/50 backdrop-blur-sm` | Dialogs, mobile drawer overlay |
| Chip active border | `border-[hsl(var(--yr-accent)/0.4)]` — border-only, no glow | Toggle chips |

Never use coloured drop shadows. Never stack more than 3 shadow layers.

---

## 6. Motion

**Curves**
- **Standard**: `cubic-bezier(0.32, 0.72, 0, 1)` — Apple/Vercel-style ease.
- **Ease-out**: `ease-out` — entrances.
- **Ease** (default): hover colour swaps.

**Utility animations** (in `index.css`)

| Class | Duration | Purpose |
|---|---|---|
| `transition-colors` | 150 ms | Hover / active on chips, rows, icon buttons |
| `transition-shadow` | 200 ms | Composer focus-within |
| `transition-opacity` | default | Session row overflow menu reveal |
| Sidebar / drawer width or transform | 300 ms `cubic-bezier(.32,.72,0,1)` | Collapse / expand / slide |
| `.yr-fade-up` | 350 ms `ease-out both` | Message bubbles, timeline nodes, dialogs, collapsed toolbar |
| `.yr-dot` | 1.4 s infinite | Loading dots (delayed per-dot) |
| `.yr-sparkle-anim` | 2.4 s `cubic-bezier(.4,.0,.2,1)` infinite | Claude sparkle rotate + scale + soft accent glow |
| `.yr-thinking-word` | 2.4 s linear infinite | Shimmer gradient across the "Thinking / Analyzing / …" word |
| `.yr-final-pulse` | 2 s ease-in-out infinite | Small sparkle pulse below completed responses |
| Streaming caret | Tailwind `animate-pulse` | `w-1.5 h-4 bg-[hsl(var(--yr-accent))]` — trailing cursor |

**Rules**
- Never use `transition: all` — target the exact property to preserve transforms.
- Motion reinforces meaning; never decoration. Reduce-motion users must still
  be able to complete every task (Settings → **Reduce motion** must disable
  `.yr-fade-up`, `.yr-sparkle-anim`, and `.yr-thinking-word`).

---

## 7. Icons

- Library: **`lucide-react`**. Never emojis. Never raw SVG *except* for the
  bespoke `<ClaudeSparkle />` (8-point burst).
- Size scale: `11 · 13 · 14 · 15 · 16 · 22 px`.
- Colour: inherit — `text-muted-foreground` idle → `text-foreground` hover.
- Stroke width: default `2`. Use `1.75` for timeline / activity icons for a
  finer feel.
- Hit area is always ≥ 28 × 28, rendered inside a `rounded-lg` / `rounded-full`
  container with `hover:bg-[hsl(var(--yr-hover))]`.

### Canonical uses

| Meaning | Icon |
|---|---|
| Send message | `ArrowUp` (circular accent button) |
| Stop streaming | `Square` (filled, `size 12`, foreground bg) |
| Attach | `Paperclip` |
| Share | `Share2` |
| Copy / Regen / Feedback | `Copy`, `RotateCcw`, `ThumbsUp`, `ThumbsDown` |
| Model — Fast | `Zap` |
| Model — Mid | `Gauge` |
| Model — Long | `BookOpen` |
| Model — Reasoning | `Sparkles` |
| Timeline — Thinking step | `Clock` (stroke 1.75) |
| Timeline — Search step | `Globe` (stroke 1.75) |
| Timeline — Done step | `CheckCircle2` (stroke 1.75) |
| External link on source card | `ExternalLink` (`size 11`) |
| Memory page + nav | `Waypoints` |
| Memory node — Concept | `Lightbulb` |
| Memory node — Episode | `MessageSquare` |
| Memory node — Process | `GitBranch` |
| Memory node — Source | `BookOpen` |
| Sidebar collapse toggle | `PanelLeft` |
| Search chats | `Search` |
| New chat | `Plus` |
| Session row menu | `MoreHorizontal` |
| Session pin / rename / delete | `Pin` / `PinOff` / `Pencil` / `Trash2` |
| Theme | `Sun` / `Moon` |
| Sign out | `LogOut` |
| Settings sections | `Server`, `KeyRound`, `Globe`, `Cpu` |
| Dialog close | `X` |
| Dropdown chevron | `ChevronDown` |
| Confirmation tick | `Check` |

**Do not use**: `Brain`, `BrainCircuit` (visually noisy, over-used for AI).

---

## 8. Component Recipes

### 8.1 Primary CTA (Send)

```jsx
<button className="w-9 h-9 rounded-full bg-[hsl(var(--yr-accent))] text-white
                   flex items-center justify-center
                   hover:brightness-105 transition
                   disabled:bg-[hsl(var(--yr-hover))]
                   disabled:text-muted-foreground/60 disabled:cursor-not-allowed">
  <ArrowUp size={16} />
</button>
```

Rules: circular 36 × 36, `brightness-105` on hover (never a lighter accent),
disabled uses `--yr-hover`, never grey text on grey.

### 8.2 Secondary pill (New chat)

```jsx
<button className="w-full h-10 rounded-full flex items-center justify-center gap-2
                   bg-[hsl(var(--yr-hover))] hover:bg-[hsl(var(--border))]
                   text-foreground text-[13.5px] font-medium
                   border border-border/50 transition-colors">
  <span className="w-4 h-4 rounded-full border border-current
                   flex items-center justify-center">
    <Plus size={11} strokeWidth={2.5} />
  </span>
  <span>New chat</span>
</button>
```

### 8.3 Icon button

```jsx
<button className="w-8 h-8 rounded-lg flex items-center justify-center
                   text-muted-foreground hover:text-foreground
                   hover:bg-[hsl(var(--yr-hover))] transition-colors">
  <Icon size={16} />
</button>
```

Variants: circular (`rounded-full`) inside pills/toolbars; ghost (no bg on
hover); destructive (`text-destructive hover:bg-destructive/10`).

### 8.4 Toggle chip

```jsx
// Idle
"h-8 px-3 rounded-full flex items-center gap-1.5 text-[12.5px]
 bg-transparent text-muted-foreground border border-border/60
 hover:bg-[hsl(var(--yr-hover))] hover:text-foreground/80
 transition-colors"

// Active
"h-8 px-3 rounded-full flex items-center gap-1.5 text-[12.5px]
 bg-[hsl(var(--yr-accent-soft))] text-[hsl(var(--yr-accent))]
 border border-[hsl(var(--yr-accent)/0.4)] transition-colors"
```

Height locked to 32 px so chips align with the model selector.

### 8.5 Model selector (in composer)

**Trigger pill**

```jsx
<button className="h-8 px-2.5 rounded-full flex items-center gap-1.5
                   text-[12.5px] font-medium
                   bg-[hsl(var(--yr-hover))] hover:bg-[hsl(var(--border))]
                   text-foreground/85 border border-border/60
                   focus:outline-none focus:ring-1 focus:ring-[hsl(var(--yr-accent)/0.4)]
                   transition-colors">
  <Icon size={13} className="text-[hsl(var(--yr-accent))]" />
  <span>{label}</span>
  <ChevronDown size={12} className="text-muted-foreground" />
</button>
```

**Menu row** (shadcn `DropdownMenuItem`, `sideOffset={8}`, container `w-64 p-1 rounded-xl`)

```jsx
<div className="flex items-start gap-3 px-2.5 py-2.5 rounded-lg">
  <div className={`w-7 h-7 rounded-lg flex items-center justify-center mt-0.5
                   ${isActive
                     ? 'bg-[hsl(var(--yr-accent-soft))] text-[hsl(var(--yr-accent))]'
                     : 'bg-[hsl(var(--muted))] text-muted-foreground'}`}>
    <Icon size={14} />
  </div>
  <div className="flex-1">
    <div className="flex items-center gap-1.5">
      <span className={`text-[13.5px] font-medium
                        ${isActive ? 'text-[hsl(var(--yr-accent))]' : 'text-foreground'}`}>
        {label}
      </span>
      {isActive && <Check size={12} className="text-[hsl(var(--yr-accent))]" />}
    </div>
    <p className="text-[11.5px] text-muted-foreground leading-snug mt-0.5">
      {hint}
    </p>
  </div>
</div>
```

**Tier catalogue** (source of truth is `TIERS` in `pages/ChatPage.jsx`)

| Key | Label | Icon | Hint |
|---|---|---|---|
| `fast` | Fast | `Zap` | Snappy answers for quick questions |
| `mid` | Mid | `Gauge` | Balanced speed and depth |
| `long` | Long | `BookOpen` | Long context — great for documents |
| `reasoning` | Reasoning | `Sparkles` | Deep step-by-step thinking |

### 8.6 Composer

```jsx
<div className="bg-[hsl(var(--yr-composer))] border border-border rounded-2xl
                yr-composer-shadow overflow-hidden transition-shadow
                focus-within:border-[hsl(var(--yr-accent)/0.5)]">
  <textarea className="yr-textarea w-full resize-none bg-transparent outline-none
                       px-5 pt-4 pb-2 text-[15px] leading-relaxed
                       placeholder:text-muted-foreground/70" />
  <div className="flex items-center justify-between gap-2 px-3 pb-3">
    <div className="flex items-center gap-1.5">
      <ModelSelector />
    </div>
    <div className="flex items-center gap-1">
      <IconButton icon={Paperclip} />
      <SendButton />  {/* or StopButton while streaming */}
    </div>
  </div>
</div>
```

`.yr-textarea` handles autoresize: `min-height 44 px`, `max-height 220 px`,
JS snaps to `scrollHeight` on every input.

### 8.7 Sidebar row

```jsx
<div className={`group relative flex items-center gap-2
                 pl-3 pr-1.5 py-2 rounded-lg cursor-pointer transition-colors
                 ${active ? 'bg-[hsl(var(--yr-hover))]'
                          : 'hover:bg-[hsl(var(--yr-hover))]'}`}>
  {isPinned && <Pin size={10} className="text-[hsl(var(--yr-accent))]" />}
  <span className={`flex-1 text-[13.5px] truncate
                    ${active ? 'text-foreground font-medium'
                             : 'text-foreground/85'}`}>
    {title}
  </span>
  <button className="w-6 h-6 rounded-md opacity-0 group-hover:opacity-100
                     data-[state=open]:opacity-100
                     hover:bg-black/10 dark:hover:bg-white/10
                     transition-opacity">
    <MoreHorizontal size={14} />
  </button>
</div>
```

- Active row uses `--yr-hover` (accent-soft is reserved for chips/CTAs).
- Overflow menu appears only on `group-hover` or when the dropdown is open.
- Section headers above rows: `px-3 pt-1 pb-2 text-[11.5px] text-muted-foreground`.
- Groups (in order): **Pinned → Today → Yesterday → 30 days → Older**, hidden
  when empty.

### 8.8 Collapsed toolbar (floating, desktop only)

```jsx
<div className="absolute top-3 left-4 z-30 flex items-center gap-3 yr-fade-up">
  <YrEmblem size={28} />
  <div className="flex items-center gap-0.5 rounded-full
                  bg-[hsl(var(--yr-hover))] border border-border/60
                  px-1 py-1 backdrop-blur-sm">
    <CollapsedIconBtn icon={PanelLeft} title="Expand sidebar" />
    <CollapsedIconBtn icon={Search}    title="Search chats" />
    <CollapsedIconBtn icon={Plus}      title="New chat" />
  </div>
</div>
```

Each `CollapsedIconBtn` is `w-8 h-8 rounded-full` with hover
`bg-black/10 dark:bg-white/10`.

### 8.9 Mobile drawer

Sidebar renders inside a `fixed inset-y-0 left-0 z-50 w-[86vw] max-w-[300px]`
translated `-translate-x-full ↔ translate-x-0` with a 300 ms
`cubic-bezier(.32,.72,0,1)`. A dim backdrop (`bg-black/50 backdrop-blur-sm`,
`z-40`) closes on click. On mobile pages a **brand button** replaces any
hamburger — either `<YrWordmark />` (empty state / Memory / Settings) or
`<YrEmblem size={24} />` (compact chat header).

### 8.10 Chat header

Two-line block on the left, Share on the right. No bottom border.

```jsx
<div className="shrink-0 min-h-14 px-3 sm:px-4 py-2 flex items-center gap-2
                flex-wrap sm:flex-nowrap">
  {!isDesktop && <MobileBrandButton />}   {/* opens mobile drawer */}
  <div className="min-w-0 flex-1">
    <div className="text-[13px] sm:text-[14px] font-medium truncate leading-tight">
      {title}
    </div>
    <div className="flex items-center gap-1 mt-0.5 text-[11.5px]
                    text-[hsl(var(--yr-accent))]">
      <TierIcon size={11} /> <span>{tierLabel}</span>
    </div>
  </div>
  <button className="w-9 h-9 rounded-full hover:bg-[hsl(var(--yr-hover))]">
    <Share2 size={15} />
  </button>
</div>
```

### 8.11 Chat message

**User** — max 75 % width, rounded pill, `--yr-hover` background:

```jsx
<div className="flex justify-end mb-8 yr-fade-up">
  <div className="max-w-[75%] bg-[hsl(var(--yr-hover))] px-5 py-3
                  rounded-3xl text-[14.5px] leading-relaxed whitespace-pre-wrap">
    {content}
  </div>
</div>
```

**Assistant** — no avatar, no bubble. Structure:

```jsx
<div className="mb-10 yr-fade-up">
  <ActivityTimeline activity={msg.activity} streaming={msg.streaming} />
  <MarkdownRenderer text={msg.content} />
  {streaming && content && <StreamingCaret />}
  {!streaming && content && (
    <>
      <ClaudeSparkle size={16} className="yr-final-pulse mt-4" />
      <ActionRow>
        <IconTinyBtn icon={Copy} />
        <IconTinyBtn icon={RotateCcw} />
        <IconTinyBtn icon={ThumbsUp} />
        <IconTinyBtn icon={ThumbsDown} />
      </ActionRow>
    </>
  )}
</div>
```

### 8.12 Activity timeline (Claude-style thinking + search + done)

State shape:

```ts
activity = {
  phase: 'thinking' | 'searching' | 'sourced' | 'done',
  thinkingSteps: string[],           // shown inside the Clock node
  searchQuery: string | null,        // shown inside the Globe node
  sources: [{ title, url, domain }],
  searchesWeb: boolean
}
```

**Header** — plain text row while done; shows animated
`<ClaudeSparkle animated />` + shimmer word while active.

```jsx
<button className="group flex items-center gap-2 text-[13.5px]">
  {active && <ClaudeSparkle size={15} animated />}
  <span className={active ? 'yr-thinking-word font-medium'
                          : 'text-muted-foreground hover:text-foreground'}>
    {headerLabel /* e.g. "Searched the web", or cycling "Thinking / Analyzing / Triangulating…" */}
  </span>
  {!active && <ChevronDown size={13}
    className={`text-muted-foreground opacity-60 group-hover:opacity-100
                transition-transform ${expanded ? 'rotate-180' : ''}`} />}
</button>
```

**Body** — a single vertical rail with three possible nodes stacked on it:

```jsx
<div className="relative mt-3">
  {/* Vertical rail */}
  <div className="absolute left-[11px] top-3 bottom-3 w-px bg-border/80
                  pointer-events-none" />

  {/* Node — Clock (Thinking) */}
  <div className="relative pl-9 pb-6">
    <span className="absolute left-0 top-0 w-[22px] h-[22px] bg-background
                     flex items-center justify-center">
      <Clock size={13} strokeWidth={1.75} className="text-muted-foreground" />
    </span>
    <div className="space-y-2 pt-[2px] yr-fade-up">
      {thinkingSteps.map(step => <p className="text-[13.5px] text-muted-foreground leading-relaxed">{step}</p>)}
    </div>
  </div>

  {/* Node — Globe (Search) */}
  {/* Same structure. When phase === 'searching', show three animated dots.
      When 'sourced' or 'done', show a max-h-[176px] source list card. */}

  {/* Node — CheckCircle2 (Done) */}
</div>
```

**Rail rules**
- Rail sits at `left-[11px]`, `top-3 bottom-3`, hairline `w-px bg-border/80`.
- Each node's icon lives in a `22 × 22` square with `bg-background` — this
  visually **breaks the rail** where the icon sits (icons appear to sit on
  the line, matching Claude).
- Icons use `strokeWidth={1.75}` and `size 13` for a fine, editorial feel.
- Text is offset `pl-9` (36 px) so it never crowds the rail.
- Auto-collapse ~400 ms after `phase === 'done'`.

**Source card** (inside the Globe node)

```jsx
<a className="flex items-center gap-2.5 px-3 py-2
              hover:bg-[hsl(var(--yr-hover))] transition-colors
              border-b border-border/40 last:border-b-0">
  <DomainDot domain={s.domain} />                {/* accent-soft circle w/ first letter */}
  <span className="flex-1 text-[12.5px] text-foreground/85 truncate">{s.title}</span>
  <span className="text-[11.5px] text-muted-foreground hidden sm:inline truncate max-w-[180px]">{s.url}</span>
  <ExternalLink size={11} className="text-muted-foreground shrink-0" />
</a>
```

Container: `rounded-xl border border-border bg-[hsl(var(--muted))]/25 overflow-hidden` with a `max-h-[176px] overflow-y-auto yr-scroll` inner scroll region.

### 8.13 Markdown renderer

Component: `<MarkdownRenderer text={string} />`. A lightweight in-house
parser (no `react-markdown` dep). Supported syntax:

| Syntax | Rendered as |
|---|---|
| `## Heading` | `<h2 class="yr-brand text-[22px] mt-1 mb-3">` |
| `### Heading` | `<h3 class="text-[15.5px] font-semibold mt-5 mb-2">` |
| `> quote` | `<blockquote>` with `border-l-2 border-[hsl(var(--yr-accent))]` |
| `- item` / `* item` | `<ul>` with `w-1 h-1 bg-foreground/60` dot markers |
| `1. item` | `<ol>` with muted numeric markers |
| `**bold**` | `<strong class="font-semibold">` |
| `*italic*` | `<em>` |
| `` `code` `` | Inline `<code>` with `bg-[hsl(var(--yr-hover))] font-mono` |
| `[[Label\|domain]]` | Inline citation chip — uppercase, tracking-wide, tiny pill with tooltip |

**Container class** (root of the renderer):
`text-[15px] leading-[1.75] text-foreground/95`.

Streaming safety: when consuming stream chunks, chunk the text with
`[\s\S]{1,5}` (never `.{1,5}` — the dot in JS regex does **not** match
newlines and would silently strip markdown structure).

### 8.14 Search dialog (command palette)

```
Modal shell:
  fixed inset-0 z-50
  bg-black/50 backdrop-blur-sm
  flex items-start justify-center pt-16 sm:pt-24 px-3 sm:px-4
  .yr-fade-up

Panel:
  w-full max-w-2xl rounded-2xl
  bg-[hsl(var(--yr-surface))] border border-border shadow-2xl
  overflow-hidden

Input row (h-14 border-b border-border/60):
  Search icon (muted) · <input> · vertical divider · X close (Esc)

Result row:
  w-9 h-9 rounded-lg bg-[hsl(var(--muted))] MessageSquare 15
  Title 13.5 / 500  +  right-aligned date 11.5 muted
  Preview 12.5 muted truncate
  Row hover: bg-[hsl(var(--yr-hover))], rounded-xl, p-3
```

Global shortcut: **⌘/Ctrl + K** opens, **Esc** closes, backdrop click closes.
Match highlights use `font-semibold text-foreground` inside otherwise muted
text (see `SearchDialog.jsx`).

### 8.15 Card / Settings section

```jsx
<div className="rounded-2xl border border-border bg-card p-6">
  <div className="flex items-start gap-3 mb-5">
    <div className="w-9 h-9 rounded-lg bg-[hsl(var(--yr-accent-soft))]
                    text-[hsl(var(--yr-accent))]
                    flex items-center justify-center shrink-0">
      <Icon size={16} />
    </div>
    <div>
      <h3 className="text-[15px] font-semibold">{title}</h3>
      <p className="text-[12.5px] text-muted-foreground mt-0.5">{description}</p>
    </div>
  </div>
  <div className="space-y-4">{/* Field rows */}</div>
</div>
```

Field row: `grid grid-cols-1 sm:grid-cols-[220px,1fr] gap-2 sm:gap-6 items-start`.

### 8.16 Stat card

```jsx
<div className="rounded-xl border border-border bg-card p-4">
  <div className="text-[11.5px] uppercase tracking-wider text-muted-foreground">LABEL</div>
  <div className="yr-brand text-[26px] leading-tight mt-1">{value}</div>
  <div className="text-[12px] text-muted-foreground">{sub}</div>
</div>
```

### 8.17 Tabs

Use shadcn `<Tabs>` with default styling. Panel content sits directly under
tabs — no border, no card wrapper unless the tab content is itself a card.

### 8.18 Toast

Use `sonner` via `<Toaster />` in `App.js`.
- `toast.success('…')` — discreet.
- `toast.error('…')` — 3 s red-bordered.

Never write inline notification banners in page body.

### 8.19 Memory graph

Absolutely-positioned coloured circles (Concept / Episode / Process / Source)
on a `440 px` rounded card with a soft `yr-grid-bg` grid backdrop and dashed
`<line>` edges. Node size scales with `strength` (`24 + s * 24 px`). A legend
row sits in the bottom-left `absolute` corner with domain-coloured dots.
Icons come from §7 (Lightbulb, MessageSquare, GitBranch, BookOpen).

---

## 9. Focus, Selection & Accessibility

- **Focus ring** — `focus:outline-none focus:ring-1 focus:ring-[hsl(var(--yr-accent)/0.4)]` on interactive elements that don't already have a hover bg.
- **Keyboard**
  - `⌘/Ctrl + K` → search
  - `Esc` → close dialog / cancel edit
  - `Enter` → submit / commit rename
  - `Shift + Enter` → newline in composer
- **Contrast** — minimum 4.5:1 for text, 3:1 for large text / icons.
- **ARIA** — rely on Radix primitives (used by shadcn); do not roll custom roles unless there is no Radix primitive.
- **Reduced motion** — Settings switch (§ 12) disables `.yr-fade-up`, `.yr-sparkle-anim`, `.yr-thinking-word`.

---

## 10. Responsiveness

- Breakpoint: `md ≥ 768 px`. Managed via `UIContext` (`isDesktop`), updated on
  `window.resize`, and via Tailwind's `sm:` / `md:` classes.
- **Desktop**: inline sidebar (268 px) or collapsed floating toolbar.
- **Tablet**: same as desktop (starts at 768 px).
- **Mobile (< 768 px)**: sidebar is a drawer opened via a **brand button**
  (never a hamburger). Padding tightens (`px-3` instead of `px-6`), title
  fonts scale down, source card URL column hides (`hidden sm:inline`),
  search dialog moves closer to the top (`pt-16 sm:pt-24`).
- Use `h-[100dvh]` for the app shell so mobile browsers with dynamic UI
  chrome don't clip the viewport.

---

## 11. State (Contexts)

| Context | Provider | Fields |
|---|---|---|
| `AppContext` | `context/AppContext.jsx` | `sessions`, `activeSessionId`, session CRUD (`create/rename/delete/togglePin`), message ops (`appendMessage`, `updateLastMessage`), `theme`, `setTheme`, `settings`, `setSettings`. Persists `sessions`, `theme`, `settings` in `localStorage`. |
| `UIContext` | `context/UIContext.jsx` | `collapsed`, `setCollapsed` (desktop), `searchOpen`, `setSearchOpen`, `mobileOpen`, `setMobileOpen`, `isDesktop`. |

Add new global UI state (drawer, modal, banner) to `UIContext`, not to
individual pages.

---

## 12. Do / Don't Cheatsheet

| ✅ Do | ❌ Don't |
|---|---|
| Use accent for **one** thing per section | Paint entire sections in accent |
| `hsl(var(--x) / 0.4)` for alpha | Hardcode `rgba` / hex |
| Cap reading width at `max-w-3xl` | Stretch text edge-to-edge |
| Show overflow menu on `group-hover` | Permanent `⋮` icons on every row |
| Circular buttons for Send / Attach / Menu icon-only | Square corners on primary CTAs |
| `--yr-hover` for row highlight | Tint every hover in accent |
| `lucide-react` icons only (plus `<ClaudeSparkle />`) | Emojis, custom SVG, or `Brain` |
| Animate one property at a time | `transition: all` |
| Use shadcn/Radix primitives | Custom dropdowns / dialogs / tabs from scratch |
| Preserve `--radius = 0.75rem` | Override radius per-component |
| Chunk streams with `[\s\S]{1,5}` | `.{1,5}` (strips newlines) |
| Brand button on mobile top | Hamburger menu icon |

---

## 13. File Map

```
frontend/src/
├── App.js                        # Router + AppProvider + Toaster
├── App.css                       # Minimal shell (do not centre-align)
├── index.css                     # Tokens + .yr-* utilities   ← source of truth
├── context/
│   ├── AppContext.jsx            # Sessions, theme, settings (localStorage)
│   └── UIContext.jsx             # Sidebar collapse / mobile drawer / search modal / isDesktop
├── components/
│   ├── Brand.jsx                 # <YrEmblem />, <YrWordmark />
│   ├── ClaudeSparkle.jsx         # 8-point burst SVG + spin animation
│   ├── Layout.jsx                # Shell w/ Sidebar + CollapsedToolbar + mobile drawer + Outlet + SearchDialog
│   ├── Sidebar.jsx               # Expanded aside + <CollapsedToolbar /> export (mobile-aware)
│   ├── SearchDialog.jsx          # Command-palette style modal (⌘/Ctrl + K)
│   ├── ActivityTimeline.jsx      # Claude-style thinking + web search + done rail
│   ├── MarkdownRenderer.jsx      # In-house markdown w/ H2/H3, lists, quotes, code, citation chips
│   └── ui/                       # shadcn primitives (do not modify)
├── pages/
│   ├── ChatPage.jsx              # Composer, ModelSelector, ChatHeader, streaming orchestration
│   ├── MemoryPage.jsx            # Knowledge graph + episodic log
│   └── SettingsPage.jsx          # LLM / keys / theme
└── mock/mock.js                  # Seed sessions + buildActivityPlan + mockCFAResponse / mockGenericReply
```

---

## 14. Building a New Component — Checklist

Before merging any new UI:

1. Sizes come from the **spacing scale** (§ 4).
2. Colours reference **CSS variables only** (§ 2).
3. Text uses the **typography scale** (§ 3).
4. Icons come from **`lucide-react`** at sizes in (§ 7) — or the bespoke
   `<ClaudeSparkle />`. **No `Brain` / `BrainCircuit`**.
5. Interactive elements have a **hover state** and a **focus ring** (§ 9).
6. Motion uses **exactly one property** and one of the durations in (§ 6).
7. Radius picks from the **radius scale** (§ 4).
8. Any menu / dialog / tooltip is built on **shadcn / Radix**.
9. Both **light + dark** are visually reviewed.
10. Component works **inline on desktop, drawered on mobile** (§ 10).
11. New global UI state lives in `UIContext`, not the page (§ 11).
12. If the component streams text, it must use `[\s\S]{1,n}` chunking.
13. If the component renders assistant output, it uses `<MarkdownRenderer />`
    — not `<pre>`, not `dangerouslySetInnerHTML`.

If all 13 boxes tick, it will feel like a first-class `yresearch.` element.
