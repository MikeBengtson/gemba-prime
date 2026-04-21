# Gemba UI Spec Input Template

> **Purpose.** Fill this out and the answers become the authoritative UI spec (Deliverable 2 for `gm-p27`). Claude (or any designer) will generate the full UI spec from your answers. Skip sections you don't care about — Claude will propose reasonable defaults and flag them as **PROPOSED** for your later review.
>
> **Shorthand.** Most questions offer bracketed suggestions `[like this]` — pick one, cross it out and write your own, or write "propose" to have Claude suggest.
>
> **When in doubt.** Err toward specific answers. Ambiguity becomes drift. "Propose" is always a valid answer.

---

## §1 — Project vibe + brand

### 1.1 Overall aesthetic
- [ ] Minimalist / utilitarian (like Linear, early Notion)
- [ ] Dense / information-rich (like Jira, Datadog)
- [ ] Playful / illustrative (like Basecamp, GitHub in a friendly mood)
- [ ] Technical / terminal-adjacent (like Grafana, early Vercel)
- [ ] Other: ___________

### 1.2 Density preference
- [ ] Dense (more info, smaller type, tighter spacing)
- [ ] Comfortable (balanced)
- [ ] Sparse (generous whitespace, large type)

### 1.3 Voice + tone
Pick one-to-three adjectives for UI copy: [confident / terse / friendly / formal / playful / blunt / warm / precise / wry]

### 1.4 Color palette
- [ ] System-theme-respecting (defaults to user's OS light/dark)
- [ ] Dark-first with light-mode option
- [ ] Light-first with dark-mode option
- Primary accent color preference: ___________
- Reserved colors (what semantics do you want locked):
  - Red = [error / blocked / critical]
  - Yellow = [warning / stale / degraded]
  - Green = [passed / ready / healthy]
  - Blue = [in-progress / info]
  - Purple = [persona-related / advisory]

### 1.5 Typography
- Body font preference: [system-sans / Inter / SF Pro / IBM Plex / propose]
- Monospace font preference: [SF Mono / JetBrains Mono / Fira Code / propose]

---

## §2 — Navigation + chrome

### 2.1 Primary nav sidebar — what's in it, in what order?
Check / reorder (drag-and-drop in your head):
- [ ] Board (Epic Kanban — home)
- [ ] Plan (staging + execute-all)
- [ ] Backlog
- [ ] Grid (power-user work grid)
- [ ] Graph (dep graph)
- [ ] Insights
- [ ] QA Health
- [ ] Escalations
- [ ] Gemba walks
- [ ] Personas (roster)
- [ ] Capabilities (adaptor/pack browser)
- [ ] Checkpoints
- [ ] Project Config
- [ ] Settings
- Other: ___________

### 2.2 Top bar — what's always visible?
Check:
- [ ] Workspace switcher
- [ ] Current mode indicator (unsupervised/supervised/managed)
- [ ] Budget gauge (advisor + agent separately, or combined)
- [ ] PM panel trigger
- [ ] Gemba walk trigger (when a Gemba walk is active)
- [ ] Search / command palette (Cmd-K)
- [ ] User menu
- [ ] Active-guardrail-unmet banner slot
- [ ] Other: ___________

### 2.3 PM panel (always-available)
- Position: [right side / left side / bottom / overlay]
- Default state: [collapsed / open-persistent / open-last-state]
- When content-overlap: [push content / overlay content / user-config]
- Quick-keystroke to toggle: [j / p / cmd-; / other]

### 2.4 Deep-link conventions
- URL shape preference: [/board/:epicId / /epics/:id / /w/:workspace/epics/:id]
- Workspace-in-URL: [required / optional / subdomain]
- Query-param filters: [URL-persisted / session-persisted / both]

---

## §3 — Core screens

For each screen below, answer: **primary entity**, **first-viewport priorities**, **primary action**, **empty state**, **loading state**, **error state**. Skip screens not in v1.

### 3.1 Epic Kanban (home)
- **Primary entity:** Epic
- First-viewport priorities (what must be visible without scrolling?): ___________
- Primary action the user takes from here: ___________
- Card anatomy — what's on an Epic card? (Check):
  - [ ] Title
  - [ ] Readiness counts (e.g., "3/7 ready")
  - [ ] Priority stripe/badge
  - [ ] Parallel-group glyph
  - [ ] Escalation dot
  - [ ] Token-budget gauge
  - [ ] Age since state change
  - [ ] Assignee (if any single assignee)
  - [ ] Labels
  - Other: ___________
- Column treatment — names for the six states:
  - Backlog = [Backlog / Ideas / Icebox / Not Now]
  - OnDeck = [On Deck / Ready / Next Up]
  - InScope = [In Scope / Staged / This Sprint]
  - InProgress = [In Progress / Active / Doing]
  - Completed = [Done / Shipped / Completed]
  - Canceled = [Canceled / Dropped / Won't Do]
- Swimlane default: [by parent-epic / by parallel-group / by assignee / none]
- Drag-to-reorder affordance: [visible handle / whole-card-draggable / drag-with-modifier]
- Drill-down: [double-click / single-click / hover-button / Enter key on focused card]
- Empty state (no Epics): copy + primary CTA: ___________
- WorkItem-granular view: [/board?view=workitem / toggle in header / Cmd-toggle]

### 3.2 Plan view
- Primary action: **Execute all in-scope** button placement: [top-right / bottom-floating / inline / cmd-Enter]
- Parallel-group visualization: [color-coding / spatial grouping / glyph-only / outlined cluster]
- Scope toggle UI: [checkbox / toggle switch / drag-between-columns]
- Cost preview before execute: [always visible / on-hover / click-to-preview / never]
- Post-execute behavior: [stay on page / navigate to Board / modal confirming dispatch / dashboard view]

### 3.3 PM panel content
- Opening state content (no active conversation): [roster of personas / recent consults / quick-action buttons / blank-with-prompt]
- Persona selection: [dropdown / tabs / roster-grid / search]
- Chat turn style: [chat-bubbles / alternating-indent / terminal-style]
- SuggestedAction rendering: [inline buttons under turn / grouped at bottom / modal-on-click]
- ExecutedAction differentiation (distinguish from suggested): [different icon / different color / "applied" badge / timestamped history]
- Cost display per-consult: [inline-per-turn / running-total-in-header / on-hover]

### 3.4 Gemba walk surface
- Layout: [three-pane (agenda/chat/escalations) / two-pane / stacked]
- Agenda item visual: [list / cards / kanban-mini]
- Decision recording: [inline action on item / bottom-of-chat / dedicated "decide" button]
- Pause/Resume discoverability: [prominent button / menu / cmd-only]
- Active-Gemba walk indicator in chrome: [banner / topbar-badge / pm-panel-hijack]

### 3.5 Persona roster
- Layout: [grid-of-cards / list / sidebar-tree]
- Per-persona info shown: [icon / role / variety / model / last-used / cost-to-date / enabled-toggle]
- Variety distinction (Coach vs Manager): [color / badge / section / mouseover-only]
- Persona config edit UX: [inline / modal / dedicated-page / toml-editor]

### 3.6 WorkItem grid
- Default columns: ___________
- Column preset system: [saved-views / per-workspace / per-user]
- Bulk-action access: [space-select then toolbar / right-click / keyboard-only]
- Inline edit: [click-to-edit / focus-then-edit / never]
- Row virtualization expectation: up to [1k / 10k / 100k] rows

### 3.7 Epic detail drawer (drill-down from Kanban)
- Primary surface: [member list / stage graph / activity log]
- Member WorkItems rendered as: [list / cards / mini-kanban / sortable-table]
- Stage visualization: [numbered groups / swimlanes / timeline]
- Inline state-change on members: [click state pill / drag / dropdown]
- Actions available from drawer: [reorder / split / merge / cancel / add member]

### 3.8 WorkItem detail drawer
- Tab structure: [summary / description / edges / evidence / DoD / activity / comments]
- Edges display: [graphical mini-map / typed lists / both]
- Evidence tab: [timeline / table / grouped-by-kind]

### 3.9 Escalations inbox (`/escalations`)
- Grouping: [by severity / by kind / by persona / flat-chronological]
- Bulk-triage: [multi-select / no / only-critical]
- Sort default: [severity / age / persona]
- Escalation card primary CTA: [open context / ack / resolve / hand-off]

### 3.10 Capability browser
- Layout: [adaptor-per-row / feature-matrix / tree-by-plane]
- Visible info per adaptor: [declared caps / last-conformance-run / transport / health]
- Drill-down: [expand-in-place / drawer / dedicated-page]

### 3.11 Dep graph (`/graph`)
- Render engine: [React Flow / dagre / d3-hierarchy / custom]
- Core edge visual distinction from extensions: [solid-vs-dashed / color / width]
- Zoom default: [fit-all / focus-selected / persist-last]
- Critical-path mode: [toggle / always-on-highlighted / on-hover]

### 3.12 Insights panel
- Chart library: [recharts / Chart.js / visx / propose]
- Default time window: [7d / 14d / sprint / custom]
- Key metrics to surface first-viewport: [spawn-rate / burn-down / escalation-backlog / token-cost / other]
- Advisor-cost vs agent-cost: [separate charts / single stacked / toggleable]

### 3.13 QA Health (`/qa/health`)
- Suite list visual: [cards / table / grouped-by-scope]
- Run-now access: [per-suite button / bulk-run-all / depth-selector]
- Gate status surfacing: [inline badge / dedicated column / separate view]

### 3.14 QA Gates (`/qa/gates`)
- Primary visual: [list / kanban-by-status / matrix]
- Override flow access: [dropdown / dedicated "request override" button / forbidden-in-ui]

### 3.15 Checkpoints timeline
- Visualization: [vertical timeline / horizontal timeline / log / calendar]
- Per-checkpoint display: [label / trigger / size / age / restore-button]
- Restore UX: [three-pane review / wizard / confirm-dialog]
- Typing-guard copy for restore: "Type [checkpoint ID / 'restore' / project name] to confirm"

### 3.16 Bootstrap wizard (`/bootstrap`)
- Steps: [source → analysis → goals-and-values → plan-review → ratify]
- Source tiles: [Jira / Beads / Source-code / Fresh]
- Consistency report visual: [passed/failed/warn rows / summary-then-details / traffic-light]

### 3.17 Project config (`/project/config`)
- Layout: [sidebar-sections / tabs / single-scroll]
- Sections: [Values / Guardrails / Goals / Modes / Adaptors / Personas / Packs / Integrations]
- Values editor: [inline / modal / dedicated-page / toml-editor-mode]

### 3.18 Pack browser
- Layout: [marketplace-grid / list / installed-vs-available tabs]
- Install UX: [one-click / signature-review-first / typing-guard-for-unsigned]

### 3.19 Agent session detail
- Workspace.kind-specific affordances (ratified from gm-e12.15):
  - tmux → [Attach / xterm embed / both]
  - k8s_pod → [Peek + pod status / kubectl-exec button / logs stream]
  - container → [Docker logs stream / docker-exec button]
  - subprocess → [Process tree / log stream]
  - exec → [Last command + exit code / full transcript]

### 3.20 Additional screens you want specified
- [ ] Retakes lane (gm-8h9)
- [ ] Session history timeline (gm-3dp)
- [ ] Lease dashboard (gm-a3p)
- [ ] HITL inbox (subset of Escalations or standalone?)
- [ ] Any others: ___________

---

## §4 — Shared interaction conventions

### 4.1 Modal vs drawer vs page
When do we use each?
- Modal (blocks everything): ___________
- Drawer (pushes/overlays, dismissible): ___________
- Full page (navigation change): ___________

### 4.2 Confirmation patterns (mutations)
- Nonce-confirmed actions: [inline confirm / dialog / typing-guard for destructive / configurable]
- Auto-approve in unsupervised mode: [batch dialog at end / no dialog / toast-only]
- Managed mode every-step: [blocking dialog / summary-then-confirm / sidebar-queue]

### 4.3 Loading states
- Skeleton screens: [yes / only-on-slow / never]
- Spinner placement: [inline / top-of-view / never (just skeletons)]
- Streaming indicators (SSE arriving): ___________

### 4.4 Empty states
Tone: [instructive (here's what to do) / welcoming / minimal / quirky]
Primary CTA rule: ___________

### 4.5 Error states
- API errors: [inline alert / toast / full-page]
- Adaptor-degraded (gm-b1): [persistent banner / degraded-badge-on-affected-surfaces / both]
- Rate-limit: [queue-visible / backoff-toast / transparent]

### 4.6 Keyboard-first ergonomics
Refer to ratified gm-7hj hotkey system — 26+ shortcuts. Any overrides or additions:
- Global: ___________
- Kanban: ___________
- Grid: ___________
- Drawer: ___________
- Persona chat: ___________
- Gemba walk: ___________

### 4.7 Search + command palette (Cmd-K)
- Content indexed: [beads / personas / artifacts / commands / all]
- Result ranking preference: [recency / relevance / mixed]
- Action-vs-navigation split: [tabs / no-split / keyboard-hint]

### 4.8 Filtering + saved views
- Filter persistence: [URL / localStorage / server-synced]
- Saved views visibility: [personal / workspace-shared / both]
- Default views shipped: ___________

### 4.9 Multi-select + bulk actions
- Selection affordance: [checkboxes / click-range / space-to-toggle]
- Bulk bar: [top-of-list / bottom-floating / sidebar]

### 4.10 Responsive behavior
- Minimum viewport: [1024 / 1280 / 1440]
- Touch optimization: [yes / only-for-passive-views / no-mobile]
- iPad support: [first-class / nice-to-have / out-of-scope]

---

## §5 — Vocabulary + copy primitives

For each term, pick one or write your own.

### 5.1 Entity nouns
- Unit of work generically: [WorkItem / Task / Issue / Card / Item]
- Parent grouping for Kanban cards: [Epic — already ratified]
- Agent: [Agent / Worker / Bot / Session]
- Agent grouping: [AgentGroup / Convoy / Pool / Crew]
- Workspace boundary: [Workspace / Rig / Project / Repo]
- Sprint analog: [Sprint / Cycle / Iteration / Interval]

### 5.2 Action verbs for state transitions
- Move to In Scope: [Stage / Queue / Schedule / Pick up]
- Move to In Progress: [Launch / Start / Dispatch / Execute / Begin]
- Move to Completed: [Complete / Close / Ship / Done]
- Move to Backlog: [Defer / Hold / Backlog / Icebox]
- Reopen: [Reopen / Unclose / Re-queue]

### 5.3 Persona action verbs
- Coach interaction: [Ask / Consult / Talk to / Chat with]
- Manager interaction: [Consult / Delegate to / Invoke / Assign task to]
- Persona output-apply: [Apply / Accept / Confirm / Execute]
- Persona output-dismiss: [Dismiss / Discard / Skip / Ignore]

### 5.4 Gemba walk verbs
- Start: [Start Gemba walk / Begin session / Open Gemba walk]
- End: [Wrap up / Close Gemba walk / End session]
- Pause: [Pause / Hold / Table]
- Decision-kinds in agenda: [Ratify / Modify / Reject / Defer — already ratified]

### 5.5 Checkpoint verbs
- Create: [Checkpoint / Snapshot / Save point / Capture]
- Restore: [Restore / Roll back / Revert to / Undo to]
- Label: [Label / Tag / Bookmark]

### 5.6 Values + guardrails copy
- Values header: [Project Values / Guiding Principles / Our Values]
- Guardrails header: [Guardrails / Rules / Constraints / Boundaries]
- Unmet-guardrail banner copy pattern: "Guardrail '<name>' is unmet: <reason>. [action]"

### 5.7 Values injected at top (ratified as innovation / transparency / execution / empathy)
For each, write the statement you want actually injected into prompts:
- Innovation: "___________"
- Transparency: "___________"
- Execution: "___________"
- Empathy: "___________"

---

## §6 — Cross-cutting UX conventions

### 6.1 Always-on elements
- PM panel: ratified always-available. Override per screen: ___________
- Active-Gemba walk banner: ___________
- Unmet-guardrail banner: ___________
- Mode indicator: ___________
- Budget gauge: [top-bar / in-settings-only / mode-dependent]

### 6.2 Persona invocation feedback
- Pre-invocation: [cost-preview modal / inline estimate / nothing]
- In-flight: [spinner / streaming-text / progress-phases]
- Completed: [render-in-place / scroll-into-view / notification]

### 6.3 Citations rendering
Every persona response carries Citations. Render as:
- [ ] Inline superscript links
- [ ] Footnote-style at turn end
- [ ] Side panel
- [ ] Hover-reveal

### 6.4 Audit log surface
- `/insights/personas` — visible to: [workspace-admin / all-users / configurable]
- Filter default: [last-7d / all / current-session]

### 6.5 External-tool handoffs
- Jira link behavior: [open-new-tab / embed-widget / in-app-preview]
- XRay link behavior: same as Jira?
- GitHub PR link behavior: ___________

---

## §7 — Adaptor + pack UX

### 7.1 Adaptor switching
- Where is the active adaptor pair shown: [settings / topbar / capability-browser / nowhere]
- Switch-adaptor UX: [config-file-only / in-app wizard / forbidden]

### 7.2 Pack management
- Install flow: [from URL / marketplace-browse / local-path / all-three]
- Signed-vs-unsigned: [block unsigned / warn + checkbox / allow-silently]
- Enable/disable granularity: [per-pack / per-persona-within-pack / both]

### 7.3 Extension widgets (`web/src/extensions/<adaptor-id>/`)
- Discoverability in UI: [badge-on-adaptor-views / dedicated-section / no-marker]
- Adaptor-specific copy: [inline / section-labeled / forbidden-in-core-views]

---

## §8 — Accessibility + i18n

### 8.1 WCAG target
- [ ] AA (recommended; covers most orgs' compliance needs)
- [ ] AAA (strictest)
- [ ] Best-effort / no-formal-target

### 8.2 Keyboard-only coverage
- [ ] Every action keyboard-reachable
- [ ] Most actions keyboard-reachable, some mouse-only
- [ ] Keyboard for power-user flows; mouse for discovery

### 8.3 Screen reader support
- [ ] First-class (ARIA throughout, tested with NVDA/VoiceOver)
- [ ] Reasonable (semantic HTML, no custom ARIA focus)
- [ ] Not prioritized for v1

### 8.4 Languages
- [ ] English only for v1
- [ ] English + plan for i18n (no translations shipped)
- [ ] Specific second language: ___________

### 8.5 RTL
- [ ] Designed RTL-ready from day one
- [ ] Not considered for v1

---

## §9 — What NOT to build (negative space)

Check what's explicitly out of scope:
- [ ] Mobile native apps
- [ ] Offline mode
- [ ] Real-time collaborative editing (Google Docs-style cursors)
- [ ] Built-in chat between humans
- [ ] Native calendar integration
- [ ] Time-tracking / billable-hours features
- [ ] PDF / printable exports beyond release notes
- [ ] Multi-workspace federation in the UI (v1)
- Other: ___________

---

## §10 — Open questions to flag for the generator

Anything you want Claude to **propose** rather than decide: ___________

Anything you want Claude to **defer** with a clear follow-up bead: ___________

Anything you want Claude to **flag for your next review** rather than implement: ___________

---

## §11 — Non-functional priorities

Rank (1 = highest):
- ___ Performance (60fps, <100ms interactions)
- ___ Visual polish
- ___ Keyboard ergonomics
- ___ Cognitive-load minimization (side-of-the-desk positioning)
- ___ Extensibility (adaptor/pack/persona surface)
- ___ Mutation safety (nonce + audit + guardrails)
- ___ Accessibility
- ___ Testability / automatable
- ___ Internationalization readiness

---

*End of template. Fill at your pace; partial answers are useful. When ready, hand back to Claude and the full UI spec (Deliverable 2 for `gm-p27`) will be generated from your answers.*
