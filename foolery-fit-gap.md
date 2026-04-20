# Foolery ↔ Gemba Phase 12 Fit-Gap Matrix

> Spike output for **gm-mth** (2026-04-20, polecat jasper).
>
> Maps Gemba's Phase 12 (adaptor-agnostic SPA) tasks onto Foolery's shipped
> feature set. Coverage = how much of each Gemba task Foolery 0.10.0 already
> delivers if we wire a `gemba-backend.ts` `BackendPort` implementation.
>
> Legend: 🟢 green (ships today), 🟡 yellow (partial — gap described), 🔴 red
> (not shipped — must build).

## Matrix

| # | Gemba task | Title | P | Coverage | Notes |
|---|------------|-------|---|----------|-------|
| 1 | gm-e12.1 | App shell: sidebar, topbar, routing, theme | P0 | 🟢 | Next.js 16 App Router; sidebar + topbar + theme all shipped. (Already closed in Gemba's tree anyway.) |
| 2 | gm-e12.2 | react-query data layer with SSE-driven invalidation | P0 | 🟡 | TanStack Query v5 is the data layer. **Gap:** SSE exists only for terminal streams (`src/app/api/terminal/[sessionId]/route.ts`). Beat reads are polled; no SSE channel pushes beat updates. The 500ms-latency DoD is unmet today. |
| 3 | gm-e12.3 | WorkItem grid (tanstack/react-table, virtualized 10k rows) | P0 | 🟢 | Queues view uses `@tanstack/react-table` (`src/components/use-beat-table-state.ts`). Virtualization present. Keyboard-first selection + bulk editing. Maps 1:1 to WorkItem grid. |
| 4 | gm-e12.5 | WorkItem detail drawer with tabs | P0 | 🟢 | Beat inline summary + notes dialog + label dialog cover the core. "Tabs" is a UX detail; the data is there. |
| 5 | gm-e12.7 | AgentGroup board (Kanban) with @dnd-kit | P0 | 🟡 | Queues/Active/Retakes/History are lane views over Beat state, keyboard-driven. **Gap:** no drag-and-drop reordering; @dnd-kit not present. State transitions go via hotkey + API, not drag. |
| 6 | gm-e12.4 | Agents dashboard with live tiles | P1 | 🟡 | Active view shows agent, model, version per beat. **Gap:** not a cross-cutting "agents" dashboard — tiles are per-beat rows, not per-agent aggregates. |
| 7 | gm-e12.6 | Global cmdk command palette | P1 | 🟢 | `cmdk` is in dependencies; command palette shipped with navigation + bulk actions. |
| 8 | gm-e12.8 | AgentGroup board view (mode: static \| pool \| graph) | P1 | 🟡 | Foolery's Dispatch Simple / Dispatch Advanced (weighted pools) covers the pool+static cases at settings level. **Gap:** no "graph" mode, no in-board visualization. |
| 9 | gm-e12.9 | Backlog board across all workspaces | P1 | 🟡 | Queues can filter across repos; Foolery is multi-repo by design (`Shift+R` next repo). **Gap:** not a unified "backlog" abstraction — it's per-repo views stitched by keyboard shortcut. |
| 10 | gm-e12.10 | WorkItem creation flow with smart defaults | P1 | 🟢 | `Shift+N` creates a new beat; `react-hook-form` + Zod schemas + backend-provided defaults. |
| 11 | gm-e12.11 | Bulk actions in grid view | P2 | 🟢 | Spacebar multi-select + bulk-update on labels/state/priority/assignee. First-class. |
| 12 | gm-e12.12 | YOLO mode toggle in UI (gated by server flag) | P2 | 🔴 | No YOLO concept in Foolery. Would be additive. |
| 13 | gm-e12.13 | Desired-vs-actual view (drift dashboard) | P1 | 🔴 | Not present. Foolery has no "desired state" model; it views backend-of-record only. |
| 14 | gm-e12.14 | Adaptor capability browser | P1 | 🔴 | `BackendCapabilities` exists as data, but no UI browses/introspects it. Capability flags drive gating internally, not exposed. |
| 15 | gm-e12.15 | Provider-aware agent detail view (Workspace.kind switch) | P1 | 🟡 | Agent dialects (claude/codex/copilot/opencode/gemini) already drive per-dialect arg builders and normalizers. **Gap:** no "agent detail" view — dialect awareness is invisible, baked into session runtime. |
| 16 | gm-e12.16 | Dependency graph with React Flow | P1 | 🔴 | `BeatDependency` data exists (blocker-blocked pairs), but no graph view. React Flow not in deps. |
| 17 | gm-e12.17 | Insights panel with OTEL-driven charts | P1 | 🔴 | Diagnostics view exists (Runtime + Leases tabs) with perf telemetry, but not OTEL, not insights over work. Different shape. |

## Counts

- 🟢 Green: **6** (e12.1, e12.3, e12.5, e12.6, e12.10, e12.11)
- 🟡 Yellow: **6** (e12.2, e12.4, e12.7, e12.8, e12.9, e12.15)
- 🔴 Red:   **5** (e12.12, e12.13, e12.14, e12.16, e12.17)

If we include the already-closed e12.1, Foolery delivers ≈ 6/17 P0-P2 tasks
fully and ≈ 6/17 partially. The five red tasks are primarily Gemba-native
concepts (drift, capability introspection, dependency graph, OTEL insights,
YOLO) that Foolery has no reason to build.

## Where Foolery ships things Phase 12 doesn't list

- **Retakes view:** post-ship review lane. Maps to Gemba's "shipped &
  reviewable" state but isn't a P12 task. Useful for free.
- **History view:** session timeline with agent conversation logs. P11 territory
  (evidence / escalation) rather than P12.
- **Terminal panel (xterm):** session tailing. Not a Gemba roadmap item.
- **Keyboard-first UX:** extensive hotkey system (navigate / select / bulk /
  fold / notes / label / create / terminal). Gemba has no equivalent budgeted.

If Gemba adopts Foolery (Path B) or consumes it (Path D), these come free.

## Critical path readout

The three gaps that would block Path B ("Foolery is our UI") are:

1. **SSE for beat updates** (currently terminal-only). e12.2's 500ms DoD fails
   without it. Fix shape: extend the existing SSE pipeline to emit
   `beat_state_observed` / `beat_updated` events from backend mutations and
   from external-change detection in the `gemba-backend.ts` adapter.
2. **Adaptor capability browser** (e12.14). Must expose `BackendCapabilities`
   + Gemba's `CapabilityManifest` as a browseable surface. Moderate effort; the
   data model is already there.
3. **Dependency graph** (e12.16). Add React Flow, render `BeatDependency` as
   DAG. Standalone view, no cross-cutting coupling.

The two red-zone items that are fine to defer (e12.13 drift, e12.17 insights)
are P1, and both are tractable as Gemba-specific views we can layer even inside
a Foolery host via route additions.
