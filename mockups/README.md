# Gemba UI Mockups

> Five-screen SVG mockup set. Marker example project. Generated **2026-04-22** by polecat **jasper** against bead **gm-als** (resolves DD-17 UI vocabulary + DD-19/DD-20 personas + DD-21 checkpoints chrome + DD-34 PPPP axes).

## Overview

This is a self-contained, offline-openable visual artifact of Gemba's five primary UI surfaces, populated with consistent data from a single example project ("Marker"). Open `index.html` in any modern browser — no server needed. The SVGs render at 16:10 (`0 0 1920 1200`) and scale to container width.

The intent is a **human-reviewable visual proof of the ratified `ui-spec.md`**. Deviations should be caught in this artifact before component implementation beads dispatch.

## Screen inventory

| # | File | Purpose |
|---|---|---|
| 1 | `01-gemba-board.svg` | The Gemba — home screen / Epic Kanban with drag-to-stage in progress |
| 2 | `02-gemba-walk.svg` | Gemba walk in session — agenda left, PM-framed decision right, Ratify CTA hovered |
| 3 | `03-epic-drawer.svg` | Drill-down into mk-e2 Web UI — mini-kanban with stage swimlanes, stale popover |
| 4 | `04-plan-view.svg` | Plan / staging surface — parallel-group clusters, drag-to-merge-group |
| 5 | `05-persona-roster.svg` | 11 personas, PM card expanded showing PPPP axes + skills + TOML edit |

## The Marker example-project spec (fixtures)

For re-rendering and future mockup extensions, the Marker fixtures are fixed as:

### Workspace & operator
- Name: `marker`
- Operator: Mike
- Phase: **building**; Mode: **supervised**
- Adaptors: Beads (work plane) + Gas Town (orchestration plane)
- Budget position: Agents 23% · Advisors 6% (of daily caps) · $18.42 agent / $1.51 advisor spent today

### Epic roster

| ID | Title | State | Priority | Members | Rendering flags |
|---|---|---|---|---|---|
| `mk-e1` | Core API + persistence | Done | P0 | 5 (all closed) | green-stripe top; token-cost 23,412 ($0.31) |
| `mk-e2` | Web UI (Next.js + Tailwind) | In Progress | P0 | 7 (2 done, 3 ip, 2 ready) | parallel group A; 62% token-budget; stale worker on mk-e2.4 |
| `mk-e3` | CLI (`marker` binary) | Staged | P1 | 4 (all ready) | parallel group A; file sig `cmd/marker/*` |
| `mk-e4` | Browser extension | Next Up | P1 | 5 (3 ready, 2 blocked on e1) | blocks-on-done cleared indicator |
| `mk-e5` | Full-text search | Next Up | P1 | 3 (all ready) | 3/3 ready, eligible to stage; file sig `internal/search/*` |
| `mk-e6` | Pocket / Raindrop import | Backlog | P2 | 4 (all open) | escalation dot · "Pocket API v1 deprecated" |
| `mk-e7` | PWA / mobile polish | Backlog | P2 | 6 (all open) | — |
| `mk-e8` | Team sharing | Backlog | P3 | 4 (all open) | purview-violation dot (yellow-outlined) · Security Purview blocking stage |

### Stage swimlanes for `mk-e2`

- Stage 0 · Scaffolding: `mk-e2.1` Next.js scaffold (done), `mk-e2.2` Tailwind + shadcn (done)
- Stage 1 · Feature surfaces: `mk-e2.3` BookmarkList (in progress, worker=obsidian), `mk-e2.4` BookmarkDetail (in progress, worker=jasper, stale), `mk-e2.5` Search bar (in progress, worker=onyx)
- Stage 2 · Polish: `mk-e2.6` Keyboard navigation (ready), `mk-e2.7` Empty states (ready)

### Personas (11, from CTO pack)

| Persona | Variety | Model | Icon | Last used | Spend today |
|---|---|---|---|---|---|
| Project Manager | Manager | claude-opus-4-7 | 📋 | 2m ago | $0.73 |
| Architect | Coach | claude-opus-4-7 | 📐 | 18m ago | $0.24 |
| Code Reviewer | Coach | claude-sonnet-4-6 | 🔍 | 1h ago | $0.11 |
| UX Expert | Coach | claude-opus-4-7 | 🎨 | 4h ago | $0.07 |
| QA | Manager | claude-sonnet-4-6 | ✅ | 12m ago | $0.18 |
| Technical Writer | Coach | claude-haiku-4-5 | ✍️ | 6h ago | $0.02 |
| DevOps / SRE | Manager | claude-sonnet-4-6 | 🛠️ | 2d ago | $0.03 |
| Deployment Engineer | Manager | claude-sonnet-4-6 | 🚢 | never | $0.00 |
| Security | Manager | claude-opus-4-7 | 🔒 | 1h ago | $0.09 |
| Documentarian | Coach | claude-sonnet-4-6 | 📚 | 30m ago | $0.04 |
| Onboarder | Coach | claude-sonnet-4-6 | 👋 | — | $0.00 |

Totals: **11 personas · 6 Coaches · 5 Managers**. Advisor spend: **$1.51** · Agent spend: **$18.42**.

### Active escalations (3)

1. `mk-e6` Pocket API v1 deprecation — `adaptor_degraded` · HIGH · Code Reviewer Coach (perspective-triggered)
2. `mk-e2.4` session stale — `stale_session` · MEDIUM · Witness (decided ratify: restart worker)
3. `mk-e8` auth-surface Security Purview — `purview_violation` · HIGH · Security Manager (blocks staging)

### Active Gemba walk

- Started 6m ago by Mike · $0.04 accumulated · 2 of 5 agenda items decided
- Agenda items (in order): stale_session (decided), sprint placement for mk-e5 (decided), Pocket API deprecation (**active**), Security Purview violation (queued), "review mk-e2 EOD" (queued, user-added)

---

## Visual language

The SVGs pick concrete values from ui-spec PROPOSED items so the review has something specific to ratify or modify:

- **Primary navy:** `#3B5B7A` (per §1.2 proposal for light theme)
- **Tan secondary:** `#C9A878` (warm neutral, surfaces)
- **Reserved semantics:** red `#C84747` (blocked) · yellow `#D4A437` (warn/stale) · green `#5A9E6F` (done) · blue `#3B82C9` (in-progress) · purple `#8B6FB3` (persona/Coach)
- **Coach badge:** purple fill, navy text; **Manager badge:** blue fill, navy text (Coach/Manager distinction per §1.2 + §3.4)
- **Body font:** Inter (CSS fallback stack so SVGs render without installing Inter)
- **Monospace:** JetBrains Mono (with SF Mono / Menlo fallbacks) for bead IDs, file signatures, skill slugs, model names
- **Corner radii:** 8px base, 12px cards, 16px modals, 6px badges/inputs (per §1.4)

No external assets are loaded; every SVG is fully standalone text.

---

## Audit findings

For each screen, findings against `ui-spec.md` and `product-description.md`. Grading: **Pass** (ships as-is) / **Warn** (documented caveat, non-blocking) / **Fail** (must fix).

### Screen 1 — `01-gemba-board.svg` — **Pass**

- **Correctness:** 6 columns in ratified order with 6 state-category labels (Backlog · Next Up · Staged · In Progress · Done · Canceled) per §4.3. Top bar carries workspace / mode pill / phase pill / dual budget gauge / search / active-walk trigger / PM toggle / user menu per §2.3. Sidebar collapsed to 56px rail by default on Board per §4.1; 7 nav icons in ratified order (Board / Gemba walks / Backlog / Grid / Escalations / Project Config / Settings). PM panel at bottom in context-sensitive quick-action state per §2.4.
- **Vocabulary:** "the Gemba" heading (§3.1). "Staged" (not "In Scope"), "Next Up" (not "OnDeck") per §3.2. No "assignee" concept rendered anywhere (§3.1 — ratified absence). Stage / Start / Defer verbs on buttons and keyboard cheats.
- **Data consistency:** Every Epic from the roster renders in its correct column with correct readiness counts and flags: escalation-dot on `mk-e6`, purview-violation-dot on `mk-e8`, parallel-group-A glyph on `mk-e2` and `mk-e3`, token-budget gauge at 62% on `mk-e2`, green-stripe on `mk-e1` (Done), stale indicator on `mk-e2` (because mk-e2.4 is stale). Dual agent/advisor budget gauges are consistent with the separation ratified by `gm-e11.2`.
- **Primary interaction:** mk-e4 mid-drag with ghost in Staged column · cursor with dragged-card preview · drop affirmation copy that honestly names nonce-gating (§6.2 supervised-mode inline confirm).
- **Missing per spec:** WIP limits rendered on Staged (1/3) and In Progress (1/3) per §4.3 — included. Column empty-state on Canceled is rendered (§4.6 pattern).
- **PROPOSED items surfaced:** navy + tan palette (§1.2) applied concretely; Inter/JetBrains Mono font stacks applied; readiness counts use the "N ready · M blocked · K in progress · L done" shorthand proposed by §4.2.

### Screen 2 — `02-gemba-walk.svg` — **Pass**

- **Correctness:** Two-pane content — agenda left (360px) + chat right — with PM panel at bottom acting as the walk's chat-input surface per §2.4 / §5.4. Agenda mini-kanban sub-layout shows Queued / Active / Decided / Deferred columns (vertical tabs) per §5.4. Chat pane leads with active-item framing ("Agenda #3 · ACTIVE"), PM turn with three options, volunteered perspectives as inset quote-style sub-turns (three visible, two collapsed per §5.4 "up to 3 per item by default"), and Suggested-Action buttons aligned with ratified walk verbs (§3.5). Typing-indicator for in-flight PM consult per §7.2.
- **Vocabulary:** Ratify / Modify / Reject / Defer buttons on active item. Coach vs Manager vs "dormant-Purview" role tags rendered correctly (Architect = Coach, Deployment Engineer = Manager, Documentarian = Coach). Escalation kinds use the ratified snake-case names (`adaptor_degraded`, `stale_session`, `purview_violation`, `hitl_question`).
- **Data consistency:** All 5 agenda items from the Marker fixture render with correct state + source icon (● open escalation, ◉ HITL question, ★ user-added). Active item (mk-e6 Pocket API v1 deprecation) is highlighted; 2 decided items carry green checkmarks. Cost ($0.04 this walk · 6m elapsed) is consistent with the operator's activity so far.
- **Primary interaction:** Cursor hovering the navy "Ratify (a): Update mk-e6 to v2" primary CTA with tooltip confirming nonce-gating and supervised-mode behaviour.
- **Keyboard:** R/M/X/D cheat-sheet rendered in agenda pane footer per §6.6.
- **PROPOSED items surfaced:** inset-quote perspective rendering — this is a concrete choice on top of §5.4's "not separate messages" language, and should be ratified or adjusted.

### Screen 3 — `03-epic-drawer.svg` — **Pass**

- **Correctness:** Drawer overlays a dimmed Board at ~30% opacity + 25% scrim darkening per §5.6 / §6.1 "drawer is dismissible, overlays content". Drawer is 40% of viewport width (768 of 1920). Header carries Epic title, state pill, priority badge, parallel-group glyph, labels, collapse + close controls per §5.6. Actions toolbar covers Stage / Start / Complete (dimmed) / Defer / Split / Merge / + member / Open in graph + overflow kebab — the **Complete button is explicitly dimmed** because the Epic isn't Review-complete, per the bead's rendering instruction. Mini-kanban with 4 thin columns × 3 stage swimlanes per §5.6. Tabs under kanban: Description active, DoD / Activity / Comments ghosted.
- **Vocabulary:** "Ready / In Progress / Review / Done" column labels (§5.6). "Stage 0: Scaffolding", "Stage 1: Feature surfaces", "Stage 2: Polish" swimlane headers. Worker-reference copy ("polecat obsidian", "polecat jasper") uses the ratified Worker term (§3.1).
- **Data consistency:** All 7 member WorkItems present in correct stage-and-column cells: mk-e2.1/.2 done in Stage 0; mk-e2.3/.4/.5 in-progress with correct worker names in Stage 1; mk-e2.6/.7 ready in Stage 2. mk-e2.4 rendered with stale-marker styling (amber-outlined card, animated stale dot inside the card, "stale · idle 14m" copy) consistent with §6.5 error-state surfacing.
- **Primary interaction:** Cursor positioned on mk-e2.4's stale dot, revealing a dark popover with the three Witness-triaged options (Restart worker primary, Peek session, Escalate to Gemba walk).
- **Metadata chips:** 3 comments · 2 evidence · 8 events rendered on the tab bar right edge; evidence is on Summary table per §5.7, not a separate tab — consistent.
- **Token budget posture:** 62% · ~87k / 140k rendered in Description tab panel body, matches Board card on screen 1. "~4h wall-clock remaining · $1.12 more spend" preview is a render-only projection not in the spec — **Warn (minor):** treat as illustrative, not yet ratified.

### Screen 4 — `04-plan-view.svg` — **Pass**

- **Correctness:** Sidebar expanded to 220px per §2.2 (Plan is not Board). Primary action "Execute all Staged" top-right navy-filled with inset "2 Epics · ~$2.40" sub-badge per §5.1 + bead spec. Cost preview row across top displays total $2.40 · ~142k tokens · ~3h wall-clock · parallel workers — and a stacked share-of-sprint-budget bar for agent vs advisor breakdown. Clustered groups: Group A (blue outline, parallel-safe-verified checkmark), Group B (tan dashed outline, "eligible to merge into A"), and a third red-X cluster "Not parallel-safe with A" with file-space-overlap explanation. Each Epic row has drag handle · priority stripe · title / readiness counts / token-budget gauge / est-cost column / unstage icon per §5.1 "Per-Epic row" enumeration. Bottom "Next candidates" showing mk-e7 with "Stage when ready" guidance.
- **Vocabulary:** "Staged" / "Next Up" / "Execute all Staged" / "Stage when ready" / "running now" (for in-progress Epics inside a cluster). Worker-type copy consistent.
- **Data consistency:** mk-e3 Staged ~60k est · cmd/marker/* · $1.20 est cost · 4/4 ready. mk-e2 running · 62% budget · $0.41 spend-to-date · 2/7 done + 3 ip + 2 ready. mk-e5 3/3 ready · ~42k · $0.84 est. mk-e4 3/5 ready · 2 blocked (by mk-e1, cleared) · ~40k est. mk-e7 in "Next candidates" because Backlog + not-ready per roster. All cross-screen data matches Board + Epic drawer.
- **Primary interaction:** Drag of mk-e5 from Group B → Group A with dashed motion path, ghost row carrying "Join Group A" affirmation chip, source row dimmed + italic ("dragging to group A…").
- **Guardrail surface:** "Every Epic requires DoD before Start" guardrail shows up as the "Stage when ready — needs DoD review" action on mk-e7 + an "Add DoD" button. Consistent with §3.7 + ratified guardrail list.

### Screen 5 — `05-persona-roster.svg` — **Pass (1 × Warn)**

- **Correctness:** Grid of 4-per-row cards (11 slots + 1 placeholder), each closed-state showing icon / role / variety badge / enabled toggle / model line per §5.5. Expanded PM card is pinned with a connector arrow to a full-width drawer below that renders PPPP axes, a Prompt Preview block, Skills opt-in list, Budget Policy, and Context Providers per the bead spec. The Edit button is navy + amber-ringed (focused/hovered), primary-action pattern consistent with §5.5 "Edit config: modal with TOML editor".
- **Vocabulary:** Coach (purple badge) / Manager (navy badge) per §1.2 + §3.4. PPPP terms (Personality, Perspective, Purview, Skills opt-in) match `gm-uf7` + `gm-9rv` ratifications. "CTO pack" label + "active · installed 3d ago" metadata anchors the pack system per §5.17.
- **Data consistency:** All 11 personas render with the correct icon / variety / model / last-used / spend-today from the fixture. PM drawer content matches the bead: Personality, Perspective, and explicit Purview invariant "(none — PM is orchestrator, not domain-owner)" with "INVARIANT: PM never gates state transitions" reminder. Skills opt-in list enumerates all 12 ratified skill slugs in `mono` badges. Budget policy shows $0.25/invocation + $20/day + 3.7% cap-pressure derived from $0.73 spend-today / $20 cap. Context providers: 5 of 7 enabled, with `code_summary` and `call_graph` rendered as available-but-off per product-description's "per-persona opt-in" pattern.
- **Primary interaction:** Cursor on Edit button with tooltip "Open TOML editor · .gemba/personas/pm.toml" — consistent with §5.5 modal TOML editor.
- **Warn:** The roster grid shows a 12th "+ add another persona / or install a Role Pack" placeholder tile to close the 4×3 layout. The footer correctly states "11 personas"; the tile is clearly a CTA, not a persona. Preserve or remove during review — current state is intentional but could be read as a roster inconsistency on fast scan.

---

## PROPOSED items rendered concretely

The mockups resolve several `PROPOSED` items in `ui-spec.md` by picking specific values. These are candidates for review/ratification:

- **§1.2 primary accent** — navy `#3B5B7A` + tan `#C9A878` combination rendered across all 5 screens.
- **§1.3 typography** — Inter body + JetBrains Mono monospace with CSS fallback stacks.
- **§1.4 shape/radii** — 8px base / 12px cards / 16px (unused in set) / 6px badges applied.
- **§4.6 empty-state Board** — empty-state micro-copy for the Canceled column renders "Nothing canceled yet. Canceled Epics land here."
- **§6.4 primary-CTA rule for empty states** — Canceled-column empty state is intentionally a reflective sentence (no CTA) because cancellation is not an action-target for a user on the Gemba; mk-e7 "Next candidate" has an "Add DoD" CTA per the rule. Treat as preliminary; UX Expert review welcome.

---

## Known limitations / deferrals (v1.1)

Per bead scope and `ui-spec.md §5.19`, additional surfaces are deferred. Not rendered in this set:

- Insights panel · Graph · Capability browser · QA Health · QA Gates
- Checkpoints timeline · Bootstrap wizard · Project Config · Pack browser
- Worker session detail · Retakes lane · Session history timeline · Lease dashboard
- Grid (WorkItem-granular table) — only alluded to by the "WorkItem" view toggle in screen 1's header strip

The footer of `index.html` carries this same deferral list.

---

## Regenerate

To re-render against updated specs:

1. Re-read `ui-spec.md` + `product-description.md` in full.
2. Re-read this bead's example-project spec (above in README).
3. Re-run bead **gm-als** through a single polecat session (single polecat for consistency — do **not** split across workers).
4. Author the 5 SVGs as text; embed via `index.html`; audit against both specs; write findings into this README.
5. Commit all under `gemba_prime/crew/mike/mockups/` with message `feat(mockups): five-screen Marker UI mockup set (gm-als)`.

---

## Provenance

- **Bead:** `gm-als` (owner `gemba_prime/crew/mike`, assignee `gemba/polecats/jasper`)
- **Parent gate:** `gm-p27` (UI spec gate)
- **Resolves (via visual proof):** DD-17 UI vocabulary · DD-19 / DD-20 personas · DD-21 checkpoints chrome · DD-34 PPPP axes
- **Formula:** `mol-polecat-work` · `base_branch=main`
- **Polecat session:** jasper @ 2026-04-22

---

## Animated mockups audit (gm-gst · 2026-04-22)

Four autoplay-looping SVG + CSS animations augment the static set under `animated/`, integrated below the matching static embed in `index.html`. Authored by polecat **obsidian** in a single session against bead `gm-gst`.

### Files

| # | File | Augments | Loop | Size |
|---|---|---|---|---|
| A1 | `animated/01-board-drag.svg` | `01-gemba-board.svg` | 4.0s | 19.3 KB |
| A2 | `animated/02-walk-ratify.svg` | `02-gemba-walk.svg` | 5.0s | 19.6 KB |
| A3 | `animated/03-pm-consult.svg` | `01-gemba-board.svg` (second motion block on Screen 1) | 5.0s | 15.9 KB |
| A4 | `animated/04-drawer-stale.svg` | `03-epic-drawer.svg` | 3.0s | 14.0 KB |

All four are under the 50 KB-per-file budget. No external resources; no `<script>`; no GIF/APNG/MP4.

### Audit findings (static verification — no live browser observation in the authoring session)

| Check | A1 | A2 | A3 | A4 |
|---|---|---|---|---|
| File renders as well-formed XML | **pass** | **pass** | **pass** | **pass** |
| viewBox `0 0 1920 1200` matches static | **pass** | **pass** | **pass** | **pass** |
| Uses only CSS `@keyframes` + `animation-iteration-count: infinite` | **pass** | **pass** | **pass** | **pass** |
| `prefers-reduced-motion` freezes to a coherent end state | **pass** | **pass** | **pass** | **pass** |
| Color tokens reused verbatim from the matching static SVG | **pass** | **pass** | **pass** | **pass** |
| Font stack matches (`Inter` body, `JetBrains Mono` mono) | **pass** | **pass** | **pass** | **pass** |
| `<object>` carries a descriptive `aria-label` (in `index.html`) | **pass** | **pass** | **pass** | **pass** |
| Text caption explains the animation | **pass** | **pass** | **pass** | **pass** |
| Served over `python3 -m http.server` (HTTP 200) | **pass** | **pass** | **pass** | **pass** |

Known limitation: the authoring session verified XML, token reuse, and serving, but **did not run a browser** to confirm loop smoothness at the cycle boundary or confirm reduced-motion rendering visually. Downstream reviewer should spot-check:

- A1 ghost outline returns in sync with the dragged card reset.
- A2 agenda item 3 `active → decided` transition and item 4 `queued → active` promotion line up with the executed-action row and PM follow-up.
- A3 caret blink continues smoothly across the typing→sent boundary; cost ticker hand-off is visible.
- A4 pulse cycle (2s) is gentle, not strobing.

### Integration into `index.html`

Each motion block sits below its matching static SVG frame, using the structure specified in bead `gm-gst`:

- Screen 1 (The Gemba) has **two** motion blocks — A1 (board drag) then A3 (PM consult).
- Screen 2 (Gemba walk) has A2 (walk ratify).
- Screen 3 (Epic drawer) has A4 (drawer stale popover).
- Screens 4 and 5 have no motion block in this round (deferred per bead scope).

Styling: new `.motion-block` + `.svg-frame-motion` + `.motion-caption` + `.motion-hint` rules, keyed to the existing `--border` / `--navy-700` / `--muted` tokens so the treatment inherits the dark-mode palette automatically.

### What is NOT in this round (deferred to v1.2)

- Motion block on Screen 4 (Plan view) — the "drag mk-e5 between parallel-groups" interaction is a natural next animation.
- Motion block on Screen 5 (Persona roster) — expanding the PM card's PPPP drawer would visualize §3.4 Ask/Consult well.
- Play / pause / restart controls — deliberately omitted per bead scope; autoplay + loop + reduced-motion fallback is sufficient for v1.
- Audio / video / GIF / APNG — none used; SVG + CSS only.
