# RFC: Gemba — an Kanban-style web UI for Gas Town, designed for the Gas City transition

**Status:** Proposal / seeking feedback

**Author:** Mike Bengtson (@mikebengtson)

**Target audience:** Gas Town v1.0 users today, Gas City maintainers for sequencing input

**Type:** Sidecar tool (standalone, not upstream)

Posting this to gather feedback before committing to the build. Looking for architectural gut-checks, prior-art I've missed, and "don't do that" signals from people deeper in the ecosystem than I am — particularly from the Gas City team, since the design hinges on aligning with Gas City's declarative philosophy even though the v1 runtime is Gas Town.

## TL;DR

**Gemba** (`gemba`) is a browser-based Kanban-style UI for multi-agent orchestration. Single Go binary, embedded React SPA. **The v1 primary target is Gas Town 1.0** — the stable, production-ready runtime the community is using today. The architecture is designed around Gas City's declarative philosophy so that when Gas City reaches GA, switching the primary backend from `gt` to `gc` is a configuration change, not a rewrite.

Pack-agnostic — it renders whatever agents the active topology declares, so one binary serves Gas Town's built-in roles today and (once Gas City is stable) will serve `gastown`, `ccat`, `ralph`, `wasteland-feeder`, and user-authored packs without UI changes.

Key surfaces: work grid (10k beads, virtualized, saved filters); Kanban where drag-drop round-trips through mutations; dep graph over all Beads edge types; molecule progress; **desired-vs-actual view** (shipping with Gas City support; designed from day one so it's ready when Gas City stabilizes).

```
brew install YOUR_ORG/tap/gemba
cd ~/gt         # Gas Town today
gemba serve
# -> http://localhost:7666
```

Phase 1 scaffold (foundation + CI) builds and tests clean locally. Before I commit to Phase 2, I want to know if the framing is right, and — most importantly — whether the Gas City team has a preference on sequencing.

## What it looks like in practice — three concrete use cases

Before the architectural detail, here's what Gemba is actually for. Every other decision in this RFC exists to make these three workflows fast.

### 1. Planning & Refinement — work the backlog like a PM tool, not an agent console

Review the backlog — stories, tasks, epics, bugs — across every rig in the town (or city, at Gas City GA) from one screen.

- **Cross-rig work grid** — 10k beads, virtualized, column presets, saved filters. Jira/Linear ergonomics sized for agent-generated bead volume.
- **Edit inline or bulk-import** — update descriptions, labels (`surface:*`, `tier:*`, `risk:*`, `fed:*`, `provider:*`), priorities, acceptance criteria directly; import whole epics from JSONL for RFC-driven work packages.
- **Dep graph over all seven Beads edge types** — `blocks`, `related`, `parent-child`, `discovered-from`, `waits-for`, `replies-to`, `conditional-blocks`, each visually distinct, with cycle highlighting and critical-path mode.
- **Molecule formula authoring** — build multi-step checkpoint-recoverable workflow DAGs before a single agent is dispatched; per-step prompt rendering so work is legible, not opaque.

Every mutation round-trips through `bd --json`. Dolt is never written directly.

### 2. Scrum / Day-of Ops — drive the standup from one screen instead of tailing tmux panes

Review current state across all rigs and push work forward without context-switching between terminals.

- **Convoy Kanban** — drag Planned → In Progress; status round-trips through `bd update --status`. Multi-select to "create convoy" and dispatch a batch. Slinging goes through `gt sling` today, `gc` at Gas City GA — same UI, adapter flips via config.
- **Desired-vs-actual view** — on Gas City: `city.toml` declared state alongside `.gc/agents/` running sessions, drift highlighted, per-drift or global "reconcile" action. On Gas Town v1: useful-but-partial, derived from the implicit fixed-role structure. The component tree does not change when Gas City arrives.
- **Provider-aware agent detail** — tmux session, k8s pod, subprocess, exec script all render differently. Peek into a running agent, read its session, see its elastic-pool check output. Pluggable from day one.
- **Confirmation-gated mutations** — every state change requires a server-enforced `X-GEMBA-Confirm` nonce; duplicate confirmations rejected so retries don't double-mutate. `--dangerously-skip-permissions` (name copied verbatim from Claude Code) unlocks a session.

### 3. Retro & Release — close the loop after work lands

Finished convoys, shipped molecules, and completed releases are first-class objects, not an afterthought in a log file.

- **Completed-work filters** — saved queries for "past sprint," "last release," "landed convoys by rig," "molecules that failed a step." Same grid, scoped by time window and status.
- **Molecule replay** — walk a completed formula step-by-step: per-step prompts, outputs, checkpoint state, failure modes. Informs rework without archaeology.
- **Insights panel** — fed from OTEL metrics plus `bd stats`: spawn rate, completion rate, stuck-agent minutes, token cost, merge-queue latency. The signals retros actually need.
- **Truthful audit log** — nonce-idempotent mutations mean history is comparable across runs and safe to replay. Retro conclusions rest on data, not reconstructed narrative.

## Stability posture: Gas Town now, Gas City ready

Gas Town hit **v1.0 on April 3, 2026** after 14 releases of iterative hardening. It's stable, it's what people are running in production, and it's what v1 of Gemba ships against. Gas City is **in alpha, on track for a fast GA** but not stable today — so I'm not going to hand users a UI whose primary runtime is still-in-flux.

At the same time, I don't want to build a Gas Town-shaped UI and then have to rip it apart when Gas City stabilizes. The Gas City architecture — pack-agnostic agents, declarative `city.toml`, pluggable providers, progressive capability levels — tells me exactly what shape the UI needs to be so it survives the transition.

So: **Gas Town is the stable runtime Gemba runs against today. Gas City is the architectural compass.** Every locked decision is derived from Gas City's design principles (ZFC, GUPP, NDI, SDK Self-Sufficiency, Bitter Lesson exclusions) applied to the UI layer. The adapter at `internal/adapter/gc/` is designed but thin in v1; its counterpart `internal/adapter/gt/` is the one that does real work while Gas City is pre-GA. When `gc` goes stable, Gemba flips which adapter is primary — no UI rework.

This pivots from my first draft, which framed this as "a UI for Gas Town" with Gas City as a future concern. That was too shallow. Gas City's declarative architecture is different enough from Gas Town's imperative one that retrofitting would be painful. Building to Gas City's shape now, running against Gas Town today, is the right ordering.

## Why another UI?

`gt dashboard` was intentionally htmx-light and Gas Town is in maintenance mode at v1.0 — the in-tree dashboard won't grow drag-drop Kanban or a graph view. More importantly, nothing I've found is designed to survive the Gas City transition:

- **Desired-vs-actual view.** Kubernetes has had this for a decade; Gas City's architecture implies it; no existing tool ships it. When Gas City stabilizes, read `city.toml`, show declared agents alongside what's actually running, highlight drift. The view can be stubbed against Gas Town's implicit role structure in the meantime.
- **Pack picker + pack-scoped views.** Browse `packs/`, stamp a pack onto a rig, see overrides as diffs against the base. This is Kustomize-for-agents. Only meaningful against Gas City, but the UI shell renders today against Gas Town's single "built-in pack."
- **Provider-aware agent detail.** A tmux session is not a k8s pod is not a subprocess is not an exec script. Gas Town runs agents in tmux today; Gas City generalizes the model. Designing the detail view for pluggable providers now means zero rework when Gas City arrives.
- **Elastic pool visualization.** `[agents.pool]` with a shell `check` command is a Gas City primitive — live graph of check-result versus actual count, queue-depth overlay. Stub-renders against Gas Town's fixed polecat pool; comes fully alive with Gas City.

There's real prior art in the sidecar lane already:

| Existing | Strength | What's missing |
|---|---|---|
| `gt dashboard` | Zero install, upstream-canonical | Intentionally light; no boards, graph, saved filters; won't grow further |
| [gvid](https://github.com/intent-solutions-io/gastown-viewer-intent) | Single binary, dep graph, serves Gas Town v1 well today | Observability focus, not PM workflow; Gas Town vocabulary hardwired in the UI layer (harder to migrate when Gas City arrives) |
| [Smorgasbord](https://smorgasbord.pm) | Kanban + polished | Next.js footprint; Gas Town vocabulary hardwired |

(Other projects exist — gastown-gui, m1chael-pappas/gastown-ui, Beadbox, beads-ui, bigsky77/gastown-frontend, Mardi Gras, Foolery, BeadBoard, perles, bdui. Worth looking at, but none target the pack-agnostic PM + declarative-reconciliation surface.)

## Locked decisions

These went through a design pass against the Gas City README. Flagging the ones most likely to get pushback:

1. **Standalone sidecar, not a `gt` plugin or a `gc` plugin.** Neither runtime's plugin surface is for HTTP servers. Sidecar is the idiomatic path for both. In v1: talks to `gt --json` and `bd --json` against a Gas Town workspace; reads `~/gt/` state for low-latency views. The `internal/adapter/gc/` package is designed from day one so that when Gas City reaches GA, the primary runtime flips via configuration, not code surgery.

2. **Pack-agnostic UI.** This is the decision that keeps the design honest. No hardcoded role names, no Gas Town-specific vocabulary in the UI layer. Agents are `[[agents]]` entries. Columns are derived from config. This matches Gas City's own "configured roles, not concepts" philosophy.

3. **Declarative-reconciliation as a first-class surface (stubbed on Gas Town, full on Gas City).** Once Gas City stabilizes, the UI shows `city.toml` desired state alongside `.gc/agents/` actual state, and edits round-trip through `gc config`. On Gas Town v1, the view renders the implicit "desired" derived from Gas Town's fixed role set — useful but not the full surface. This is the single biggest new thing Gemba brings that nothing else does, and designing for it now means no rework when Gas City arrives.

4. **Provider-aware agent views.** Agent detail page renders differently for tmux / k8s / subprocess / exec. Respects Gas City's `session.Provider` abstraction all the way up.

5. **Go + embedded React/TS SPA.** Single binary, `go:embed` for the SPA, shadcn + Tailwind + TanStack + @dnd-kit + React Flow + cmdk. Richness htmx can't deliver; install footprint Next.js can't match.

6. **Full mutation surface, confirmation-gated.** Every mutation requires a server-enforced `X-GEMBA-Confirm` nonce. `--dangerously-skip-permissions` (name copied verbatim from Claude Code — not softened) disables it for the session.

7. **Never write Dolt/JSONL/`.gc/`/controller.sock/`.gt/` internals directly.** All state changes round-trip through `gt`/`gc`/`bd` CLIs, or through a watched config file edit the controller reconciles. Applies to both runtimes.

8. **ZFC for the UI.** No decision logic in the UI layer. Present data, surface actions, let the operator decide. Same principle Gas City applies to its Go code, applied to our TypeScript.

9. **Multi-rig, single workspace for v1.** Not Wasteland-federated, but no decision precludes federation. Every identity carries `WorkspaceID + RigID` (workspace = town today, city tomorrow); labels mark `fed:safe` / `fed:bridge` / `fed:blocked`.

10. **Auth.** Localhost-bound by default. Binding non-loopback without `--auth` is a startup error. Token auth: 256-bit, argon2id, printed once. TLS via user cert or `--tls-self-signed`. OIDC interface stubbed for v1.1.

## Architectural alignment with Gas City

I walked through the Gas City README section by section and checked each of its design principles against Gemba's design. Result:

- **Zero Framework Cognition.** Gas City's principle — Go handles transport, not reasoning. Gemba's application: the UI shows state and actions; it does not embed judgments. No "agent looks stuck, restart it for the user" shortcuts. The operator reads the peek output and decides.
- **GUPP (if you find work, run it).** Applies to agents, not UIs. Gemba is a viewer, not a dispatcher; it can *surface* that a polecat has idle slots, but the decision to sling stays with the human or the Mayor agent.
- **Nondeterministic Idempotence.** Every Gemba mutation must be safely retryable. The `X-GEMBA-Confirm` nonce design already supports this — duplicate confirmations are rejected, so client retries don't double-mutate.
- **SDK Self-Sufficiency.** Gas City functions with only its controller running. Gemba must function with zero specific agent roles present — a Level 1 city (one agent) should render usefully. The pack-agnostic UI decision derives directly from this.
- **Bitter Lesson exclusions.** Gas City explicitly rejects skill systems, capability flags, MCP/tool registration, decision logic in Go, and hardcoded role names. Gemba mirrors this: no UI-layer skill catalog, no capability badges beyond what's declared in config, no MCP-aware tool panel, no decision trees, no role-name `switch` statements anywhere.

## Auth posture

Design I'm least sure about; would love critique.

- **Default bind**: `127.0.0.1:7666`, no auth. The 99% case.
- **Remote access**: `--listen 0.0.0.0 --auth token` generates a 256-bit token, prints once, stores argon2id hash at `~/.bc/tokens/primary`. Bearer header or signed session cookie.
- **Non-loopback without auth is a startup error** — not a warning. Implemented and tested in the scaffold.
- **TLS**: user certs, or `--tls-self-signed` with 1-year validity, SANs for localhost + bind IP, SHA-256 fingerprint printed at startup.
- **OIDC**: interface + mock for v1, real providers (GitHub, Google) v1.1.

Open questions:

- Is one-shot token printed to stdout the right UX, or should it round-trip through a Gas City config mechanism so tokens live next to the rest of the city's configuration?
- For teams sharing a bc instance, do we need multi-user auth day 1 or can it wait for OIDC?

## New surfaces (differentiators)

The **Convoy Kanban is the home screen** — it's what opens on `gemba serve`, and it's where day-of orchestration happens. Everything else is a destination reached from the board's nav or from a bead's detail view. All of these are things I think genuinely don't exist yet and are worth building:

- **Convoy Kanban (home).** The primary interface. Columns derive from detected agents / rigs / statuses — pack-agnostic per locked decision #2, so no hardcoded Mayor/Witness/Polecat even on Gas Town v1. Drag-drop status changes round-trip through `bd update --status`; multi-select cards to "create convoy" and batch-dispatch via `gt sling` (or `gc` at GA). Swimlanes by rig, assignee, or label; WIP limits per column; filter chips (priority, tier, provider, `fed:*`). Quick-edit inline; keyboard-first via cmdk palette. Every mutation `X-GEMBA-Confirm`-gated.
- **Bead detail.** Opens from a card click or at `/beads/:id`. Description, labels, linked PRs, parent/child hierarchy, all seven edge types, activity log, and quick actions (sling, assign, change status, add dep, open in graph) — same mutation-gating as the board. The second-most-used surface after the Kanban.
- **Work grid (power-user view).** 10k beads, virtualized, column presets, saved filters, cross-rig. Jira/Linear table ergonomics for triage, bulk-edit, and JSONL import of RFC-driven work packages. Same data as the Kanban, different ergonomics — use the board for flow, the grid for triage.
- **Dep graph.** All 7 Beads edge types (blocks, related, parent-child, discovered-from, waits-for, replies-to, conditional-blocks), each visually distinct. Cycle highlighting, critical-path mode. Reached from the board's nav or "show in graph" on bead detail.
- **Molecule progress.** Formulas rendered as first-class workflow DAGs with step-level status and per-step prompt rendering. Reached from a bead's detail when its convoy carries a formula; standalone at `/molecules/:formula`. Hardest to build on any other PM tool because the data model is Gas-City-native.
- **Desired-vs-actual.** The Kubernetes-dashboard surface for multi-agent systems. Reads `city.toml`, diffs against running sessions, highlights drift, offers "reconcile" per-drift or globally. Available as a standalone page and as a board-level overlay that tints rig/column headers when drift is present. On Gas Town v1, stubbed against the implicit fixed-role structure.
- **Provider-aware agent detail.** Renders differently for tmux / k8s / subprocess / exec (locked decision #4). Reached from a rig or agent reference on the board or in a bead's activity log; shows session peek, elastic-pool check output, recent log.
- **Pack browser.** Enumerate `packs/`, preview `pack.toml`, show per-rig overrides as a diff against the base pack. Kustomize-for-agents rendered as a UI. Standalone page.
- **Elastic pool visualization.** For `[agents.pool]` with a `check` command — live plot of desired vs actual, queue-depth overlay, check-output log. Surfaces in agent detail and as a standalone page.
- **Insights panel.** Fed from OTEL metrics + `bd stats`: spawn rate, completion rate, stuck-agent minutes, token cost, merge-queue latency. Available as a collapsed strip on the board and as a full dashboard.

## What I'm NOT doing

- Replacing `gt dashboard`. Parallel tool.
- Becoming a Gas City in-tree feature. Sidecar.
- Mobile native app. Responsive web is enough.
- Confluence-like docs. Scope creep.
- Direct Dolt access. Ever.
- Embedding decision logic. ZFC for the UI.
- Hardcoding pack vocabularies. Pack-agnostic.

## Work package

Decomposed into Beads:

- 1 root epic (twelve locked decisions)
- 8 phase epics (foundation → adapters → auth → beads/agents UI → boards/mutations → graph/insights/mail → molecules → release)
- 39 tasks/features + 3 pre-identified bugs
- 5 molecule formulas for multi-step checkpoint-recoverable work
- Label taxonomy includes `provider:*` so agent-view work can be correctly routed to people who understand a given provider

Phase 1 scaffold is built and verified: Go binary builds clean, tests pass with `-race`, bind policy verifiably rejects 0.0.0.0 without auth, SPA fallback doesn't shadow API 404s, yolo flag produces a WARN log. CI matrix covers macOS/Linux/Windows × Go 1.23/1.24. The `gemba doctor` command checks for either Gas Town (`gt` CLI, `~/gt`, `.gt/` or `rigs/`) or Gas City (`gc` CLI, `~/my-city`, `.gc/` or `city.toml`) so the binary is useful today against Gas Town v1 and becomes useful against Gas City the moment it's installable.

## What I'm asking for

1. **Gas City team: is this the right direction, and is the timing right?** Gemba is designed around Gas City's primitives but shipped against Gas Town v1.0 because that's what's stable today. If you want this to happen differently — a plugin into the SDK, an official reference implementation, a wholly different shape, or "wait until Gas City GA and then build" — that's the most valuable signal you can give. Julian, Chris: DMs open.

2. **Sequencing.** Would you rather I: (a) ship a Gas Town v1 UI now and swap in the Gas City adapter when it goes GA, which is the plan; (b) wait for Gas City GA and ship only against that; or (c) stop now because a reference UI is already planned on your side? Option (c) is the cheapest thing to find out early.

3. **Pack-agnostic UI sanity.** The decision that no UI layer may hardcode role names — even though Gas Town v1 has fixed role names — is strong. Does anyone see failure modes? Cases where a specific pack needs a specific UI affordance that a generic approach can't give?

4. **Desired-vs-actual view.** Is there prior art inside Gas City for this already (a `gc config explain --drift` flow, say)? If so I'd rather consume it than reinvent.

5. **Architectural red flags.** Sidecar vs plugin, Go+React vs alternatives, full mutation vs read-only v1, localhost-default. The decisions feel right but group epistemics beat mine.

6. **Prior art I missed.** Especially anything designed for the Gas Town → Gas City transition specifically. I'd rather contribute than fork.

7. **Name pushback.** "Gemba" fits the Gas City theming (Bullet Farmer → Bullet Farm was the original, but Gemba plays better with the declarative-city architecture Gas City is heading toward). If this collides with something planned upstream, tell me now.

8. **Auth sanity check.** The bind-policy startup-error is opinionated. If anyone has done a security review of a similar local tool, I'd love to hear what you'd add or remove.

9. **Anyone building something similar?** Happy to join forces.

Not asking for maintainer time or upstream integration. Just want to know if the approach is sound before I commit to Phase 2.

Thanks for reading.
