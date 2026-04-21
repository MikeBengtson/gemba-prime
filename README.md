# Gemba — Import Package

A browser-based, Atlassian-style UI for multi-agent orchestration. Renders any **Work Coordination Plane** (Beads, Jira, Linear, GitHub Projects, Azure DevOps, Shortcut, Plane, …) over any **Agent Orchestration Plane** (Gas Town, Gas City, LangGraph, CrewAI, OpenHands, Devin, Factory, …) without UI changes.

This directory is the work package: the design docs, the work breakdown (`issues.jsonl`), the molecule formulas, and the import tooling that drops it all into a Beads database so an orchestrator can decompose and execute the build.

## What Gemba is

A single-binary Go service with an embedded React SPA that pairs *exactly one* WorkPlane adaptor with *exactly one* OrchestrationPlane adaptor in any active configuration, and renders everything they declare. Adaptors arrive via a typed contract; the UI consumes capability manifests, never role/pack vocabulary.

```
brew install YOUR_ORG/tap/gemba
cd <a workspace whose adaptors Gemba can detect>
gemba serve
# -> http://localhost:7666
```

The product is the abstraction. Beads is the first reference WorkPlane. Gas Town is the first reference OrchestrationPlane. Both are demoted from "the runtime" to "the proof the contract works." Jira (forcing-function WorkPlane) and LangGraph (forcing-function OrchestrationPlane) are the second-mover adaptors that prove the contract isn't accidentally Beads/Gas-Town-shaped.

## Twelve locked architectural decisions

Non-negotiable. Changing one requires an escalation, not a local edit.

1. **Topology.** Standalone sidecar binary (`gemba`). Separate repo, separate process. Not a plugin for any backend. Talks to one configured `WorkPlaneAdaptor` and one configured `OrchestrationPlaneAdaptor`. Default configuration discovers the adaptors a workspace can satisfy.
2. **Backend.** Go single binary. `go:embed` ships the SPA. Cobra for CLI. chi for routing. SSE (not WebSockets) for live updates.
3. **Frontend.** React + TypeScript + Vite. shadcn/ui + Tailwind. TanStack Query/Table. @dnd-kit. React Flow. cmdk.
4. **Adaptor-agnostic UI.** No role name, column header, panel, or string literal in the SPA hardcodes vocabulary from a specific WorkPlane or OrchestrationPlane. All vocabulary arrives through `CapabilityManifest`. Any backend-specific rendering lives in `web/src/extensions/<adaptor-id>/` behind a capability gate.
5. **Pluggable workspaces from day one.** `Workspace.kind` is declared by the active OrchestrationPlane adaptor (`worktree | container | k8s_pod | vm | exec | subprocess`). The agent detail view is built pluggable; no adaptor's workspace shape is assumed by core.
6. **Multi-workspace, not-yet-federated.** Gemba can attach to multiple workspaces in v1. Wasteland-style federation is out of scope. Every identity carries `WorkspaceID`; labels mark `fed:safe` / `fed:bridge` / `fed:blocked`.
7. **Mutation model.** Full mutation surface, server-enforced confirmation via `X-GEMBA-Confirm` nonce. `--dangerously-skip-permissions` (name copied verbatim from Claude Code, not softened) disables for the session.
8. **Auth.** Localhost-bound by default. Non-loopback bind without `--auth` is a startup error. Token auth: 256-bit, argon2id, printed once. TLS via user certs or `--tls-self-signed`. OIDC stubbed for v1.1.
9. **Data integrity.** Never write any backend's private storage directly (Dolt files, Jira databases, Linear internal APIs, controller sockets, JSONL on disk, `.gt/` / `.gc/` directories, …). Every mutation round-trips through the adaptor, which uses the backend's public CLI/API.
10. **Declarative UX.** The UI shows `OrchestrationPlaneAdaptor.declared_state()` (desired) vs `observed_state()` (actual) with drift highlighted. Adaptors that lack a declarative source render the implicit-desired derived from their capability manifest.
11. **ZFC for the UI.** Gemba presents data and offers actions. It does not embed decision logic about what agents should do. Same principle Gas City applies to Go, applied to TypeScript.
12. **Distribution.** Homebrew tap, npm wrapper, GitHub Releases for macOS / Linux / Windows / FreeBSD.

## The two planes

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
        │   (CRUD, query, transition,                  │   (agents, groups, workspaces,
        │    edges, evidence, sprints, budgets)        │    sessions, cost, escalations)
        ▼                                              ▼
  ┌───────────────────────┐                   ┌───────────────────────────┐
  │  v1 reference: Beads  │                   │  v1 reference: Gas Town   │
  │  forcing fn:   Jira   │                   │  forcing fn:  LangGraph   │
  │  (Linear, GH, …)      │                   │  (Gas City, OpenHands, …) │
  └───────────────────────┘                   └───────────────────────────┘
```

Adaptors declare a `transport` (`api | jsonl | mcp`) and a `CapabilityManifest`. Capability manifests carry `state_map`, `edge_extensions`, `field_extensions`, `relationship_extensions`, plus boolean capabilities (`sprint_native`, `token_budget_enforced`, `evidence_synthesis_required`, …). The UI hides controls and columns the manifest does not advertise.

## Cross-cutting primitives

Every adaptor sees these core types. Adaptors with native equivalents wire them through; adaptors without synthesize them.

- **`WorkItem`** — the unit of work. Six core fields + adaptor extensions. `state_category ∈ Backlog | Unstarted | Started | Completed | Canceled` is canonical; per-state names are adaptor-declared.
- **`AgentRef`** — first-class agent identity (`agent_id`, `display_name`, `role`, `parent_id?`, `agent_kind ∈ agent | human`). Adaptors that model agents only as users/bots/claims federate at the edge.
- **`Relationship`** — three core edge types (`blocks`, `parent_child`, `relates_to`) plus adaptor-declared extensions. The dep graph renders core edges always; extensions render only if declared.
- **`Evidence`** — links to PRs, commits, runs, traces, artifacts. Adaptors without native evidence synthesize from git/CI; the UI marks synthesized evidence with `synthesized: true`.
- **`DefinitionOfDone`** — informational-only in v1. Free-text `acceptance_criteria` + `notes` + `version`. No enforcement.
- **`Sprint` + `TokenBudget`** — sprint-as-token-budget. Three-tier `inform | warn | stop` thresholds at epic and sprint scope. The first non-deferred enforced budget axis. `dollars` and `wallclock` rendered, not gating.
- **`CostMeter`** — token / dollar / wallclock rollups at assignment, work item, agent, group, epic, and sprint scope.
- **`EscalationRequest`** — orchestrator-paused sessions, budget threshold crossings, rate-limit waits, HITL interrupts. Surfaces in the `/escalations` inbox with one-click ack.
- **`CapabilityManifest`** — adaptor declares what it can do at registration; UI consumes at runtime.

See `domain.md` for the full type system and adaptor interfaces.

## Three concrete user workflows

Every architectural decision exists to make these three workflows fast.

### 1. Plan & refine — work the backlog like a PM tool, not an agent console

10k-WorkItem virtualized grid across every workspace; saved filters; column presets; bulk JSONL import; click any row for a Jira-style detail drawer with labels, edges, activity, and actions. Author molecule formulas as DAGs before any agent is dispatched.

### 2. Scrum / day-of ops — Kanban is the home screen

`AgentGroup` board (`mode: static | pool | graph`) with WIP limits, swimlanes, filter chips, cmdk keyboard nav. Drag-drop round-trips through `WorkPlaneAdaptor.transition`. Dispatch through `OrchestrationPlaneAdaptor.acquire_workspace + start_session`. Desired-vs-actual drift tints column headers. Provider-aware agent peek for the "why is this one stuck" moment. Every mutation `X-GEMBA-Confirm` nonce-gated.

### 3. Retro & release — landed-work review, replay, insights

Landed-`AgentGroup` review; molecule step-by-step replay (prompts + outputs + checkpoints); insights panel from OTEL + adaptor-supplied `CostMeter` (token spend, sprint burn-down, stuck-session minutes, merge-queue latency).

## How Gemba differs from the closest existing tools

The Beads-ecosystem UI layer (`Beads Kanban`, `Beads Project Manager`, `vscode-beads`) and the emerging web-native tool `Foolery` each cover a slice of Gemba's Phase 12 UI surface — keyboard-first grids, kanban, session monitoring — for the single-plane Beads case. They are not competitors to Gemba's core abstraction; Gemba's unique bet is **cross-plane**: any `WorkPlaneAdaptor` × any `OrchestrationPlaneAdaptor` rendered under one capability-manifest-driven SPA with typed contracts, transport plurality (`api | jsonl | mcp`), declarative drift, token-budget enforcement, and unified escalation.

Full differentiator matrices are in `landscape.md §8.5` (Gemba ↔ Foolery — WorkPlane-side lessons) and `§8.6` (Gemba ↔ t3code — OrchestrationPlane-side lessons from a separate audit of t3code's provider subsystem). Gemba's architecture explicitly preserves the option for external UI consumers (future npm packages for Foolery + t3code, VS Code extensions, CLI wrappers) to sit over Gemba's adaptor layer without forking — that invariant is tracked in the `gm-ege` bead.

## Work graph shape

- **1 root epic** (`gm-root`) — holds the twelve locked decisions
- **13 phase epics** (`gm-e1` … `gm-e13`) — foundation, validation, core contracts, transport, auth, reference adaptors (Beads + Gas Town), forcing-function adaptors (Jira + LangGraph), Gas City stub, cross-cutting features, UI, molecules, release
- **~75 tasks** nested under phase epics with hierarchical IDs (`gm-e3.1`, `gm-e5.1.1`, …)
- **3 bugs** (`gm-b1`–`gm-b3`)

Molecule formulas (TOML, multi-step checkpoint-recoverable workflows) are introduced under Phase 13 once the cross-cutting capability surface lands; none are pre-authored in the import package.

## Tagging taxonomy

Every issue carries labels from these orthogonal dimensions.

### Surface (pick one)
- `surface:backend` — Go in `cmd/` or `internal/`
- `surface:frontend` — React/TS in `web/`
- `surface:infra` — build, CI, release, packaging
- `surface:docs` — user docs, architecture docs, READMEs
- `surface:protocol` — wire types shared between backend & frontend

### Layer (for backend; pick one or more)
- `layer:core` — adaptor-agnostic domain types, conformance suite, registration
- `layer:adapter-workplane` — any WorkPlane adaptor implementation
- `layer:adapter-orchestration` — any OrchestrationPlane adaptor implementation
- `layer:transport` — `api` / `jsonl` / `mcp` shims
- `layer:api` — HTTP handlers
- `layer:events` — SSE fan-out, OTEL trace propagation
- `layer:auth` — authentication, authorization, TLS

### Feature area (pick one or more)
- `area:work-items` · `area:agents` · `area:groups` · `area:workspaces`
- `area:sessions` · `area:graph` · `area:budget` · `area:escalations`
- `area:evidence` · `area:capability` · `area:insights` · `area:mail`

### Adaptor (when work targets a specific adaptor)
- `adaptor:beads` · `adaptor:gastown` · `adaptor:jira` · `adaptor:langgraph` · `adaptor:gascity` · `adaptor:noop`

### Workspace kind (for agent-detail work; pick one or more)
- `workspace:worktree` · `workspace:container` · `workspace:k8s_pod` · `workspace:vm` · `workspace:exec` · `workspace:subprocess`

### Skill tier (pick one)
- `tier:haiku` — mechanical, well-specified work
- `tier:sonnet` — standard implementation
- `tier:opus` — architectural, ambiguous, security-sensitive

### Risk (pick one)
- `risk:low` — pure additive, well-tested area
- `risk:medium` — touches shared code, needs review
- `risk:high` — mutations against a live backend, auth surface, data integrity

### Federation readiness (pick one)
- `fed:safe` — does not constrain a future Wasteland-style federation
- `fed:bridge` — requires explicit multi-workspace consideration
- `fed:blocked` — would need rework to federate; avoid

## Conventions for the orchestrator

- Every parent epic uses `issue_type: "epic"`. Children use the right leaf type (`task`, `feature`, `bug`, `story`).
- Every task has a detailed `description` with: **Goal**, **Inputs**, **Outputs**, **Definition of Done**, and a trailing **Resolves DDs:** line citing the design decisions it satisfies.
- `blocks` enforces ordering. `parent_child` is epic → child. `discovered_from` is reserved for issues filed during execution. `relates_to` is for advisory cross-references.
- Honor `tier:*` when routing work. `tier:opus` should not be handed to Haiku.
- Ambiguity in any locked decision triggers an escalation, not a local call.
- When rendering adaptor-specific UI, honor `adaptor:*` — never ship Gas-Town-shaped affordances to a Jira+LangGraph workspace.

## How to import

```bash
# 1. Validate (no writes)
./validate-import.py --dry-run

# 2. Import into a target Beads-backed workspace
./validate-import.py --target ~/gt/gemba --prefix gm

# After import:
cd ~/gt/gemba
bd stats
bd list --status open --json | jq 'length'   # expect ~80
bd ready --json | jq 'length'                # Phase 1 starters
```

## Files in this package

```
.
├── README.md            # this file
├── RFC.md               # community RFC
├── domain.md            # full domain model + adaptor interfaces
├── landscape.md         # evidence-grounded landscape survey (Phase 1 input)
├── issues.jsonl         # all epics, tasks, bugs (one JSON per line)
├── validate-import.py   # prereq + schema + dry-run validator
├── merge-import.py      # merge JSONL into an existing Beads store
├── bootstrap-prompt.md  # orchestrator bootstrap prompt
└── discord-post.md      # short-form community pitch
```
