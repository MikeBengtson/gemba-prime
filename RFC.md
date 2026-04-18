# RFC: Gemba — a generalized Kanban-style web UI for any work tracker × any agent orchestrator

**Status:** Proposal / seeking feedback
**Author:** Mike Bengtson (@mikebengtson)
**Target audience:** maintainers and operators of work trackers (Beads, Jira, Linear, GitHub Projects, Azure DevOps, Shortcut, Plane, …) and agent orchestrators (Gas Town, Gas City, LangGraph, CrewAI, OpenHands, Devin, Factory, …).
**Type:** Sidecar tool (standalone, not upstream into any backend).

Posting this to gather feedback before committing further build cycles. Looking for architectural gut-checks, prior art I've missed, and "don't do that" signals from people deeper in the ecosystem than I am — particularly from work-tracker and orchestrator maintainers whose contracts I'm proposing to map onto a shared abstraction.

## TL;DR

**Gemba** (`gemba`) is a single-binary Go service with an embedded React SPA that pairs *exactly one* **Work Coordination Plane** adaptor (the work tracker — Beads, Jira, Linear, …) with *exactly one* **Agent Orchestration Plane** adaptor (the runtime — Gas Town, Gas City, LangGraph, …) and renders whatever the two planes declare. The UI is adaptor-agnostic: no role name, column header, panel, or string literal in the SPA hardcodes vocabulary from a specific backend.

Beads and Gas Town are the **reference adaptors** for v1 (the simplest path to a working release). Jira (WorkPlane) and LangGraph (OrchestrationPlane) are the **forcing-function adaptors** for v1 — picked because their quirks are supersets of the easier members of their categories. If the contract handles Jira's workflow FSM, Linear is easy. If it handles LangGraph's checkpoint-and-graph topology, OpenHands is easy.

```
brew install YOUR_ORG/tap/gemba
cd <a workspace whose adaptors Gemba can detect>
gemba serve
# -> http://localhost:7666
```

The phase-1 scaffold (foundation + CI) builds clean. Before I commit to phase 2, I want to know if the abstraction is right. Specifically: whether the four hardest open questions (DD-1, DD-9, DD-13, DD-14 below) are answered the way the people running these backends would want them answered.

## What it looks like in practice — three concrete user workflows

Every other decision in this RFC exists to make these three workflows fast.

### 1. Plan & refine — work the backlog like a PM tool, not an agent console

Review the backlog — stories, tasks, epics, bugs — across every workspace from one screen.

- **Cross-workspace work grid.** 10k WorkItems, virtualized, column presets, saved filters. Jira/Linear ergonomics sized for agent-generated volume.
- **Edit inline or bulk-import.** Update descriptions, labels, priorities, acceptance criteria; import whole epics from JSONL for RFC-driven work packages.
- **Dep graph over the three core edge types** (`blocks`, `parent_child`, `relates_to`) plus any extension edges declared by the active WorkPlane (Beads's `discovered_from`, `waits_for`, `replies_to`, `conditional_blocks`; Jira's `clones`, `causes`, `is_caused_by`; …) — each visually distinct, with cycle highlighting and critical-path mode.

### 2. Scrum / day-of ops — Kanban is the home screen

The `AgentGroup` board is what opens on `gemba serve` — drag-drop status changes round-trip through `WorkPlaneAdaptor.transition`; multi-select cards to dispatch via `OrchestrationPlaneAdaptor.acquire_workspace + start_session`.

- **AgentGroup board.** Columns derive from `state_category` (canonical, five values) with names from `CapabilityManifest.state_map`. WIP limits, swimlanes by group/assignee/label, filter chips, cmdk keyboard.
- **Desired-vs-actual.** Tints column headers when `OrchestrationPlaneAdaptor.declared_state()` and `observed_state()` diverge. Adaptors without a declarative source render the implicit-desired derived from their capability manifest.
- **Provider-aware agent peek.** `Workspace.kind` (`tmux | container | k8s_pod | vm | exec | subprocess`) drives the agent detail surface. Each kind gets a distinct affordance set (tmux → Attach; k8s → Peek + pod status; subprocess → process tree; exec → last command + exit code).
- **Mutation safety.** Every mutation `X-GEMBA-Confirm` nonce-gated. `--dangerously-skip-permissions` (name copied verbatim from Claude Code, not softened) disables for the session.

### 3. Retro & release — landed-work review, replay, insights

- **Landed-AgentGroup review.** What shipped, with full activity log and synthesized evidence (PR links, commit SHAs, run IDs).
- **Molecule progress + replay.** Multi-step workflow DAGs with checkpoint state; step-by-step replay of prompts and outputs.
- **Insights panel.** Fed from OTEL + adaptor-supplied `CostMeter`: spawn rate, completion rate, sprint burn-down, stuck-session minutes, token spend, escalation backlog.
- **EscalationRequest inbox.** `/escalations` surfaces orchestrator-paused sessions, budget threshold crossings, rate-limit waits, HITL interrupts. One-click ack.

## Why a sidecar, why now

There's already prior art in the in-tree-dashboard lane (`gt dashboard`, `gc dashboard` planned, Jira's native UI, Linear's native UI). They each have the same shape: tightly coupled to one backend, one work model, one set of vocabulary. The gap Gemba fills is **one UI that renders the full surface across both planes** — work tracker × agent orchestrator — without picking sides.

| Existing | Strength | What's missing |
|---|---|---|
| Backend-native dashboards (gt, Linear UI, Jira native) | Zero install, canonical | Locked to one backend; no cross-plane view |
| [gvid](https://github.com/intent-solutions-io/gastown-viewer-intent) | Single binary, dep graph | Gas Town–specific in the UI layer |
| [Smorgasbord](https://smorgasbord.pm) | Polished Kanban | Next.js footprint; Gas Town–specific |
| Atlassian Marketplace tools | Mature PM ergonomics | Jira-only; no agent execution surface |

## Architecture in one diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      Gemba SPA (React/TS)                        │
│        no role names · no pack vocabulary · capability-driven    │
└─────────────────────────────────────────────────────────────────┘
                                ▲
                  HTTP / SSE — capability-negotiated
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Gemba core (Go binary)                       │
│   types: WorkItem · AgentRef · Relationship · Evidence · DoD     │
│          Sprint · TokenBudget · CostMeter · EscalationRequest    │
└─────────────────────────────────────────────────────────────────┘
        ▲                                              ▲
        │   WorkPlaneAdaptor                           │   OrchestrationPlaneAdaptor
        │   transport: api | jsonl | mcp               │   transport: api | jsonl | mcp
        ▼                                              ▼
  ┌───────────────────────┐                   ┌───────────────────────────┐
  │  v1 reference: Beads  │                   │  v1 reference: Gas Town   │
  │  forcing fn:   Jira   │                   │  forcing fn:  LangGraph   │
  │  (Linear, GH, …)      │                   │  (Gas City, OpenHands, …) │
  └───────────────────────┘                   └───────────────────────────┘
```

## The two-plane contract

Both adaptor interfaces (full TypeScript-style spec in `domain.md`) are typed, versioned, and capability-declared.

**`WorkPlaneAdaptor`** — owns work items, edges, transitions, evidence, DoD, sprints, budgets:
```ts
interface WorkPlaneAdaptor {
  describe(): CapabilityManifest;
  list(query: WorkItemQuery): Page<WorkItem>;
  get(id: WorkItemId): WorkItem;
  create(draft: WorkItemDraft, ctx: CallCtx): WorkItem;
  update(id, patch, ctx): WorkItem;
  transition(id, to: StateRef, ctx): WorkItem;
  edges(id): Relationship[];
  add_edge(edge, ctx): void;
  evidence(id): Evidence[];
  read_budget_rollup(scope_kind, scope_id): TokenBudgetRollup;
  list_sprints(query?): Sprint[];
  subscribe(filter): AsyncIterator<WorkPlaneEvent>;
}
```

**`OrchestrationPlaneAdaptor`** — owns agents, groups, workspaces, sessions, cost, escalations:
```ts
interface OrchestrationPlaneAdaptor {
  describe(): OrchestrationCapabilityManifest;
  list_agents(filter?): Agent[];
  list_groups(filter?): AgentGroup[];
  acquire_workspace(spec, ctx): Workspace;
  release_workspace(id, ctx): void;
  start_session(spec, ctx): Session;
  peek_session(id): SessionPeek;
  pause_session(id, ctx) / resume_session(id, ctx) / end_session(id, ctx): void;
  read_cost(scope): CostMeter;
  declared_state(): WorkspaceTopology;
  observed_state(): WorkspaceTopology;
  subscribe(filter): AsyncIterator<OrchestrationEvent>;
}
```

Capability manifests carry `state_map`, `edge_extensions`, `field_extensions`, `relationship_extensions`, plus boolean capabilities (`sprint_native`, `token_budget_enforced`, `evidence_synthesis_required`, …). The UI hides controls and columns the manifest does not advertise.

## Twelve locked decisions

These survive the design pass. Changing one is an escalation, not a local edit.

1. **Topology.** Standalone sidecar, separate binary. Talks to one configured WorkPlane adaptor and one configured OrchestrationPlane adaptor; default config discovers what the workspace supports.
2. **Backend.** Go single binary; `go:embed` SPA; Cobra; chi; SSE.
3. **Frontend.** React + TypeScript + Vite; shadcn/ui + Tailwind; TanStack Query/Table; @dnd-kit; React Flow; cmdk.
4. **Adaptor-agnostic UI.** No role/pack vocabulary in the SPA outside `web/src/extensions/<adaptor-id>/` capability-gated widgets.
5. **Pluggable workspaces.** `Workspace.kind ∈ worktree | container | k8s_pod | vm | exec | subprocess`, declared by the orchestration adaptor.
6. **Multi-workspace, not federated.** Multiple workspaces in a single Gemba install; no Wasteland-style cross-workspace federation in v1.
7. **Mutation model.** Server-enforced `X-GEMBA-Confirm` nonce; `--dangerously-skip-permissions` disables for the session.
8. **Auth.** Localhost by default; non-loopback without `--auth` is a startup error; token (256-bit, argon2id, printed once); TLS via certs or `--tls-self-signed`; OIDC stubbed for v1.1.
9. **Data integrity.** Never write any backend's private storage directly. Every mutation goes through the adaptor's public CLI/API.
10. **Declarative UX.** UI shows `declared_state()` vs `observed_state()` with drift highlighted. Adaptors without a declarative source render implicit-desired from the capability manifest.
11. **ZFC for the UI.** Present data, surface actions, let the operator decide. No decision logic in TypeScript.
12. **Distribution.** Homebrew tap, npm wrapper, GitHub Releases binaries for macOS/Linux/Windows/FreeBSD.

## Cross-cutting primitives

These types appear in every adaptor's surface. Adaptors with native equivalents wire them through; adaptors without synthesize them at the edge.

- **`WorkItem` + canonical `state_category`** (`Backlog | Unstarted | Started | Completed | Canceled`). Per-state names are adaptor-declared.
- **`AgentRef`** as a first-class core type. Adaptors that model agents only as user/bot/claim federate at the edge.
- **`Relationship`** with three core edge types (`blocks`, `parent_child`, `relates_to`) + adaptor-declared extensions.
- **`Evidence`**: PRs, commits, runs, traces, artifacts. Synthesized from git/CI for adaptors without native evidence; UI marks synthesized evidence with `synthesized: true`.
- **`DefinitionOfDone`** — informational-only in v1 (free-text `acceptance_criteria` + `notes` + `version`; no enforcement).
- **`Sprint` + `TokenBudget`** — sprint-as-token-budget. Three-tier `inform | warn | stop` thresholds at epic and sprint scope. Tokens are the only enforced budget axis in v1; dollars and wallclock render but do not gate.
- **`CostMeter`** — token / dollar / wallclock rollups at assignment, work item, agent, group, epic, and sprint scope.
- **`EscalationRequest`** — orchestrator pauses, budget threshold crossings, rate-limit waits, HITL interrupts.
- **`CapabilityManifest`** — adaptor declares at registration; UI consumes at runtime.

## What I'm asking for

The four highest-risk decisions, each scoped as a validation gate before contracts go to code:

1. **DD-1: Agent as a first-class core type, federated to backend assignee.** Trackers that only know "user / bot / claim" must synthesize agent role and parent-agent at the adaptor edge. Maintainers of Beads, Jira, Linear, GitHub Projects, Plane: is the federation shape (custom field + label fallback) something you'd accept as a contract Gemba writes against? Orchestrator maintainers (Gas Town, Gas City, LangGraph, OpenHands, Devin): is `{agent_id, display_name, role, parent_id?, agent_kind}` enough to render usefully without amputating dimensions you care about?

2. **DD-9: Three core edge types** (`blocks`, `parent_child`, `relates_to`) **with the rest as adaptor extensions.** Beads has seven; Jira has many; LangGraph has graph-edges. The narrowing forces every UI to render the three core types always and the rest only when declared. Beads maintainers: comfortable with `discovered_from`, `waits_for`, `replies_to`, `conditional_blocks` as Beads-namespaced extensions rather than core?

3. **DD-13: Evidence synthesis at the adaptor edge for adaptors without native evidence.** Tag synthesized evidence with `synthesized: true` so the UI can render provenance honestly. Trackers that *do* have native evidence (Linear's auto-linked PRs, GitHub's native PR↔Issue links): is the contract clear enough that you'd write the adaptor without us rewriting half of it post-hoc?

4. **DD-14: Sprint-as-token-budget** with three-tier `inform | warn | stop` enforcement at epic and sprint scope. Tokens the only enforced axis in v1; dollars and wallclock rendered, not gating. Scrum-fluent users: does redefining "sprint" as a token-budget container break your mental model in unproductive ways, or does it sharpen the UX for agent-driven work?

Lower-stakes asks:

5. **Sequencing.** Reference adaptors first (Beads + Gas Town to a working binary), then forcing-function adaptors (Jira + LangGraph), then the rest? Or do forcing-function adaptors before the reference adaptors get too crystallized to refactor?
6. **Transport plurality (DD-15).** Adaptors declare one of `{api, jsonl, mcp}`. MCP is recommended-but-not-required. Anyone building MCP-first adaptor integrations: is the recommended-not-required stance safe for you, or do you want it tighter?
7. **Capability negotiation (DD-12).** All-or-nothing capability scoping in v1 (no per-capability permission scoping). For multi-tenant deployments down the line, is that a non-starter or acceptable v1 simplification?
8. **Auth posture.** Localhost-default + bind-policy startup-error. Anyone done a security review of a similar local tool — what would you add or remove?
9. **Prior art I missed.** Especially anything generalized across work trackers and orchestrators. I'd rather contribute than fork.
10. **Anyone building something similar?** Happy to join forces.

## What I'm NOT doing

- Picking sides between work trackers or orchestrators. Adaptors are first-class.
- Writing to any backend's private storage. Every mutation through the adaptor's public CLI/API.
- Embedding decision logic in the UI. ZFC for the UI.
- Federating workspaces in v1. The labels (`fed:safe` / `fed:bridge` / `fed:blocked`) leave the door open.
- Mobile native. Responsive web is enough.
- Confluence-like docs. Scope creep.

## Work package

Decomposed into ~80 Beads issues across 13 phase epics:

1. **Foundation** — repo, Cobra, embed pipeline, Vite/React/TS, Makefile, CI
2. **Validation** — four gates on DD-1, DD-9, DD-13, DD-14
3. **Core contracts** — domain types, two adaptor interfaces, registration, conformance harness, event schema, noop reference adaptors
4. **Transport** — HTTP API + chi, OpenAPI/TS codegen, SSE hub, mutation nonce
5. **Auth** — bind policy, token, TLS, OIDC stub
6. **Reference WorkPlane: Beads** — CRUD, edge mapping, AgentRef federation, DoD pass-through, evidence synthesis, subscribe, conformance
7. **Reference OrchestrationPlane: Gas Town** — agents/groups, workspace, sessions, cost meter, escalation mapping, transport declaration, conformance
8. **Forcing-function WorkPlane: Jira** — REST v3 CRUD, workflow FSM mapping, custom-field synthesis, DoD, rate-limit subscribe, conformance
9. **Forcing-function OrchestrationPlane: LangGraph** — Agent synthesis from node paths, graph-mode AgentGroup, checkpoint suspend/resume, LangSmith cost, exec workspace, conformance
10. **Stub OrchestrationPlane: Gas City** — skeleton, workspace detection, RFC follow-up
11. **Cross-cutting** — DoD informational, CostMeter, EscalationRequest pipeline, capability negotiation UI, Sprint+TokenBudget enforcement, evidence synthesis library, transport plurality harness
12. **UI** — app shell, react-query+SSE, work grid, AgentGroup board (Kanban), backlog board, WorkItem creation, bulk actions, YOLO toggle, drawers, palette, dep graph, insights, mail (gated), escalations, capability browser, agent detail (`Workspace.kind`-driven), desired-vs-actual
13. **Molecules** — formula catalog, molecule progress
14. **Release** — goreleaser, npm wrapper, docs site, "Writing a Gemba adaptor" guide, migration guide, announcement

Phase-1 scaffold is built and verified. CI matrix covers macOS/Linux/Windows × Go 1.23/1.24. The `gemba doctor` command discovers which adaptors a workspace can satisfy.

Not asking for maintainer time or upstream integration. Just want to know if the abstraction is sound before I commit further build cycles.

Thanks for reading.
