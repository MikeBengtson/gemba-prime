# Domain Model

**Author:** Principal architect
**Date:** 2026-04-18
**Status:** Design proposal (implementable)
**Depends on:** `landscape.md` (evidence survey), `RFC.md` (product vision)

## Preamble

This document specifies the abstraction layer that lets Gemba render any supported Work Coordination Plane (Beads, Jira, Linear, GitHub Projects, Azure DevOps, Shortcut, Plane, …) over any supported Agent Orchestration Plane (Gas Town, Gas City, LangGraph, CrewAI, OpenHands, Devin, Factory, …) without changing the UI layer.

Every design choice is grounded in landscape.md evidence. References take the form `C#` (convergent pattern), `D#` (divergent pattern), `DD-N` (this document's design decision), and RFC-§N (RFC locked decision N).

Pseudo-code is **TypeScript-style** throughout (matches the SPA layer and documents types more legibly than Go for this audience). Adaptor *implementations* are free to be written in Go — only the interface shape is prescriptive.

Two inviolable principles from RFC.md propagate everywhere:

- **Zero Framework Cognition in the UI** (RFC §Architectural alignment). Adaptors encode judgment, the UI does not.
- **Pack-agnostic rendering** (RFC locked decision #2). No role/pack name ever appears in a core type; all vocabulary arrives through capability declarations.

---

## 1.0 Category preconditions — the agentic data plane

Gemba's WorkPlane abstraction generalizes from Beads, but the generalization does **not** make Beads "one of many work trackers." It targets a narrow category — the **agentic data plane** — whose members are designed (or adapted) for multi-agent AI software-engineering work tied to a Git repository.

Scope: software-engineering agents tied to Git repos. General business workflow (Jira Service Management for IT tickets, Asana for marketing, Basecamp for client delivery, enterprise control planes like Kore.ai or Glean) is out of scope. Such systems remain supportable as adaptors — they will simply fail some of the capability bars below, which is an acceptable outcome (per RFC §What I'm NOT doing).

Reference implementations in the category (detail in `landscape.md` §2 and §7): **Beads** (reference WorkPlane), **AgentHub**, **Ralph**, **Symphony**, **Raindrop (Liquid Metal)**, **Gastown** (orchestrator on Beads), **Metaswarm** (multi-agent platform on Beads).

The category is defined by **eight canonical foundational requirements** (R1–R8). They are **category-level preconditions** — not adaptor-optional quirks. The WorkPlane contract MUST honour them at the baseline bar defined below; adaptors advertise their level of compliance via the `CapabilityManifest` (§2.5) so orchestrators can reject adaptors that fall below the bar. **Do not renumber R1–R8 without user sign-off** — cross-document numbering is canonical across `domain.md`, `landscape.md`, `RFC.md`, `dataplane-requirements.md`, and the conformance harness.

| # | Requirement | Where in this doc | Contract-level | Manifest field |
|---|---|---|---|---|
| R1 | Structured, schemaful agent memory — tasks/artifacts in a relational/SQL store; writes through schema enforcement | §2.1, §2.5 | MUST | `schema_enforcement: "native" \| "synthesized"` |
| R2 | Queryable rather than parse-only — machine-friendly JSON queries, no HTML/UI on the agent path | §2.5 | MUST | `query_languages: Set<"filter-only" \| "jsonpath" \| "sql-subset" \| "graphql">` |
| R3 | Dependency-aware task graph — edges first-class; `ready-set` and `blocked` queries; graph evolves mid-execution (discovered work) | §2.4, DD-9, §2.5 | MUST (edges); adaptor-optional for native `ready-set` | `dependency_graph_native: boolean`; `ready_set_query: boolean` |
| R4 | Git-native / versioned transport — state distributable and versioned alongside code; no hard SaaS dependency | DD-8, DD-15, §2.5 | Category-defining (not strictly MUST; bar-gated) | `versioning_transport: Set<"git" \| "dolt" \| "jsonl" \| "native-sqlite-export" \| "none">` |
| R5 | Multi-agent concurrency and transaction semantics — many writers at scale (N≥16 default stress bar) with predictable read-after-write | §2.5 concurrency, §2.6 Group B, DD-12 | MUST | `concurrency_model: "optimistic" \| "mvcc" \| "git-merge" \| "dolt-merge"` |
| R6 | Decoupling of work from any single agent — work items outlive sessions/context windows; any agent or human can pick up later | DD-2, C10 (landscape.md), §2.1 | MUST | `agent_session_decoupling: boolean` (must be `true`) |
| R7 | Agent-native interfaces and ergonomics — CLI/JSON/API primary; operations vocabulary tuned for agent callers | DD-8, DD-15, §2.5 | Category-defining | `agent_native_api: "cli" \| "json-api" \| "mcp" \| "rest-only"` |
| R8 | Tight integration with orchestrators and workflows — plane is source-of-truth for "what to do next"; pluggable into Gastown / Metaswarm / Gemba | DD-2, §2.5 `subscribe`, §3 | MUST (baseline); hooks advertised per-kind | `orchestrator_hooks: Set<HookKind>` |

**Minimum bar for agentic-data-plane-class registration:** `schema_enforcement` set; `query_languages` non-empty; `dependency_graph_native == true`; `versioning_transport` contains at least one non-`"none"` value; `concurrency_model` set; `agent_session_decoupling == true`; `agent_native_api ∈ {"cli", "json-api", "mcp"}`; `orchestrator_hooks` non-empty. Adaptors below the bar may still register but the UI surfaces a "reduced-capability" indicator and orchestrators that require the full bar (Gastown, Metaswarm) refuse to bind.

Full gap analysis — per-requirement evidence of where each requirement currently appears (explicit vs implicit), which level it operates at (WorkPlane-contract vs adaptor-optional), and the per-requirement conformance test group — is in `dataplane-requirements.md`.

The design decisions that follow (DD-1 … DD-15) address design-level questions *within* a category that already takes R1–R8 as given. They refine, rather than re-open, the category preconditions.

---

## 1. Design decisions — resolving the open questions

landscape.md §6 listed 11 known-unknowns. Each is resolved below. Numbering is stable; later sections refer back by `DD-N`.

### DD-1: Agent identity model — first-class, federated to tracker assignee

**Landscape reference:** D4, D10, Gap "No standard for agent as first-class work-tracker citizen".

**Decision:** Gemba models `Agent` as a first-class entity with its own identity, role, parent, and capabilities (per C10 — identity vs session is near-universal). Each `WorkPlane` adaptor is responsible for the bidirectional mapping between a Gemba `AgentRef` and the backend's assignee primitive (bot user, `claim` string, user id, etc.). The mapping is typed and lossy-by-design: core carries only `{agent_id, display_name, role, agent_kind: "agent"|"human"}`; the adaptor preserves backend extras via the extension channel.

**Rationale:** Forcing agents into the bot-user shape (Jira/Linear/GitHub) would amputate the dimensions that make Gemba's UI useful (role, parent-agent, rig affinity). Keeping agents first-class inside the core and federating at the adaptor edge preserves the UI while still honouring trackers that only know "who is assigned."

**Tradeoffs:** Adaptors for shallow trackers (Jira, Linear, GitHub) must synthesize the extra dimensions (role, parent) from labels/custom fields. Round-tripping through such a tracker is lossy: a Jira assignee change made outside Gemba may lose role/parent metadata until the next Gemba reconciliation write.

**Out of scope for v1:** Cross-workspace agent identity federation (e.g., an agent in Gas Town-A visible in Gas Town-B) — see RFC locked decision #9.

### DD-2: Source of truth — Work Coordination Plane is primary, Orchestration Plane is derivable

**Landscape reference:** D7.

**Decision:** The WorkPlane is the source of truth for work-item state, lifecycle, assignment, and evidence. The OrchestrationPlane is the source of truth for session-level runtime state (current prompt, cost burn, sandbox fingerprint). When they disagree on anything in the WorkPlane's jurisdiction, **the WorkPlane wins** and the OrchestrationPlane reconciles. Adaptors MAY expose a read-through cache but MUST NOT silently override WorkPlane state.

**Rationale:** This matches Gas Town's operative pattern (Beads is primary, agent state is derived) and RFC locked decision #7 ("never write Dolt/JSONL/.gc/ internals directly"). It also aligns with every mainstream tracker's self-conception. Gemba's Kanban is a view over the WorkPlane — making the WorkPlane authoritative keeps the UI coherent.

**Tradeoffs:** Products where the agent session is "really" primary (Devin's VM, LangGraph's StateGraph) need an adaptor that lifts their session state into WorkPlane writes. This is work the adaptor author does once, not work the UI does every render.

**Out of scope for v1:** Bidirectional eventual-consistency models (Factory, Continue). Adaptors for such products declare a merge policy on registration (`last_writer_wins` | `workplane_wins` | `orchestrator_wins_for_state`); v1 ships with `workplane_wins` as the only supported policy and treats others as future capability.

### DD-3: Definition of Done — informational-only free-text, enforcement deferred

**Landscape reference:** D8, Gap "No cross-system DoD primitive".

**Decision:** Gemba's `DefinitionOfDone` is **informational-only** for v1. It is displayed metadata — never a gate, never machine-evaluated, never a precondition for state transitions. The schema collapses to two optional free-text strings: `acceptance_criteria` and `notes`, tagged with `version: "1.0"`. Adaptors pass this through to whichever native free-text field the backend already exposes (Jira: description or an `Acceptance Criteria` custom field; Linear: the ad-hoc acceptance-criteria custom field; GitHub Issues: a clearly-delimited section in the issue body; Beads: a new `acceptance_criteria` field on the bead; Gas Town / Gas City: the same Beads-side field). No new storage primitives, no predicate kinds, no evaluator dispatch, no `ProofOfDoD` object, no predicate registry, no scheduling.

**Rationale:** landscape.md D8 correctly observed that no industry consensus exists on completion semantics. an earlier hybrid design (a predicate schema with evaluators) would have required Gemba to *create* that consensus — a credible but expensive political bet with a wide blast radius across every adaptor. Rather than make that bet in v1, Gemba ships the *display* affordance (every Kanban card can show acceptance criteria) without making any claim that the text is machine-checkable or authoritative. When industry consensus on completion semantics emerges — or when Gemba's deployed base demands enforcement — DD-3 re-opens at `schema_version: "2.0"` as an opt-in capability. Not before.

**Tradeoffs:** v1 users who want CI-gated completion must arrange it outside Gemba (e.g., in their tracker's native workflow validators, or in CI). The Kanban cannot badge "all DoD predicates pass" because there are no predicates. This is the price of keeping adaptors cheap and avoiding a political bet.

**Out of scope for v1:** Predicate kinds, AI-check execution, evaluator dispatch, machine evaluation of any kind, gating transitions on DoD state. All deferred until industry consensus on completion semantics emerges.

### DD-4: Cost and budget — Gemba meters, adaptors contribute

**Landscape reference:** D9.

**Decision:** Gemba owns a canonical `CostMeter` schema with three axes: `{tokens_total, wallclock_seconds, dollars_est}`. The OrchestrationPlane adaptor MUST emit samples against at least one axis (typically tokens or wallclock). Gemba aggregates. Adaptors that natively meter in proprietary units (Devin's ACUs) expose the native unit as an extension while also down-converting into `dollars_est` using a configured rate card.

**Rationale:** landscape.md D9 established that tokens, ACUs, and wall-clock are not convertible; no industry standard exists. Gemba's Kanban needs *some* comparable number per card, so Gemba defines it. The rate card is config, not code, so the adaptor can be updated without a release.

**Tradeoffs:** `dollars_est` is estimated, not billed — actual invoices from Anthropic/OpenAI/Cognition will disagree. Gemba's number is for flow-management, not finance. This distinction is surfaced in the UI (the field is labelled `≈$` everywhere).

**Out of scope for v1:** ~~Budget enforcement (hard-stop an agent at $X). v1 has display + soft warnings.~~ Superseded by DD-14 — v1 now ships simple inform/warn/stop enforcement at epic + sprint scope, denominated in tokens, with the stop threshold gated behind an `X-GEMBA-Confirm` nonce override. Retail-priced enforcement (hard-stop at $X) remains a v2 concern.

### DD-5: Isolation contract — "scoped working directory" is the only MUST; everything else is capability-negotiated

**Landscape reference:** D5, C7.

**Decision:** Every OrchestrationPlane adaptor MUST declare that it can provide a *scoped working directory* for an assignment — meaning a filesystem namespace where writes by one assignment do not corrupt another in-flight assignment. The *mechanism* (worktree, Docker container, k8s pod, cloud VM, exec'd chroot) is a declared capability, negotiated at registration, and surfaced in the UI (`Workspace.isolation_kind`). Anything stronger than "scoped working directory" (network isolation, resource limits, snapshot/restore) is optional capability.

**Rationale:** C7 established that "per-agent working directory" is the universally honoured primitive. Any stronger requirement would reject legitimate adaptors (Gas Town's worktrees have no network isolation; Cursor sometimes runs local worktrees with full network access). The RFC's provider-aware agent detail view (RFC §New surfaces) already anticipates rendering the isolation kind heterogeneously.

**Tradeoffs:** "Scoped working directory" is a weak promise. An adaptor that only sets `$PWD` and trusts the agent to respect it technically conforms. The conformance suite (§3.8) exercises concurrency to filter the worst offenders, but trust is ultimately adaptor-declared.

**Out of scope for v1:** Formal isolation levels (something like Linux namespaces' hierarchy). A future capability taxonomy could codify `fs | fs+net | fs+net+cpu | vm`.

### DD-6: Escalation — unified `EscalationRequest` entity, dedicated UI inbox + card badge

**Landscape reference:** D11.

**Decision:** Gemba defines `EscalationRequest` as a cross-cutting entity (§3.1) with a single schema. MCP elicitation, A2A `input-required` task state, Claude Code permission prompts, CrewAI `flow_finished`-after-HITL, and Microsoft Agent Framework HITL approvals all map to `EscalationRequest`. The UI treats them as (a) a badge on the owning WorkItem card, (b) a first-class inbox surface (`/escalations`), and (c) an overlay on the Convoy Kanban when any card in view has an open escalation.

**Rationale:** The RFC's Convoy Kanban is the home screen (RFC §New surfaces); humans drive standups from it; they must see escalations without leaving it. An inbox alone is insufficient (escalations have work-item context); a card-only surface is insufficient (escalations across the whole city need a dashboard). Both.

**Tradeoffs:** Dual surface means dual invalidation. Mitigated by a single event stream (§4.4) driving both.

**Out of scope for v1:** Auto-routing escalations to specific humans by role. v1 routes everything to "city owner" (the operator who launched `gemba serve`).

### DD-7: Agent grouping — `AgentGroup` primitive, static+dynamic, multi-repo-ready

**Landscape reference:** D6, Gap "Agent-group membership model is immature".

**Decision:** `AgentGroup` is a first-class entity with three grouping modes declared by the orchestrator adaptor: `static` (enumerated member list, e.g., Gas Town convoy, CrewAI crew), `pool` (elastic via a `check` command returning live membership, e.g., Gas Town worker pool, Gas City `[agents.pool]`), or `graph` (LangGraph subgraph, ADK hierarchy). Gemba stores the declaration; the adaptor resolves membership on read.

**Rationale:** All four observed patterns (Gas Town convoy, CrewAI crew, LangGraph subgraph, Claude Code Agent Teams) decompose into "declared membership | live-computed membership | topology-derived membership." Naming them `static | pool | graph` covers the observed surface without inventing a grouping semantics Gemba would then have to defend.

**Tradeoffs:** `graph` mode forces the UI to render topology it doesn't own (it can't re-layout a LangGraph StateGraph). v1 treats `graph` groups as opaque — the Kanban shows the group name and member agents but not the internal edges. A future `/groups/:id/topology` view can render graph shape when the adaptor exposes it.

**Out of scope for v1:** Nested groups (group-of-groups). Technically storable but renders poorly in Kanban; deferred.

### DD-8: Adaptor transport — plurality with MCP recommended, not required

**Landscape reference:** C8, Bitter Lesson (RFC §Architectural alignment).

**Decision:** Each adaptor declares its transport on registration from the set `{api, jsonl, mcp}`. Any one satisfies the contract; multiple are supported.
- **`api`** — HTTP + JSON over a documented endpoint set (REST or JSON-RPC 2.0). Gas Town's `gt --json` + `bd --json` CLI surfaces are wrapped as an `api`-transport adaptor.
- **`jsonl`** — filesystem-scoped bulk import/export of newline-delimited JSON objects (matching the existing `issues.jsonl` shape). Useful for disconnected round-trips, air-gapped deployments, and migration bootstrapping.
- **`mcp`** — JSON-RPC 2.0 over the MCP client/server profile (C8's industry default).

MCP is the **recommended** transport for new OrchestrationPlane adaptors because it composes well with MCP-native agent ecosystems, but it is explicitly **not required**. Gemba itself does not need to speak MCP; agents running under an orchestrator can still depend on MCP — that is the agent's concern, not the adaptor's.

**Rationale:** The earlier "MCP required of adaptor" stance conflated two things: (1) agents needing a capability protocol (still true; C8 unchanged), and (2) Gemba's adaptor wire format (no reason to mandate). Gas Town talks JSON over CLI, not MCP, and works well. Mandating MCP would have forced a bridge layer into every existing adaptor for no UI benefit. Transport plurality lets existing backends plug in via the transport that already exists, while leaving MCP as the forward-looking recommendation.

**Tradeoffs:** Three transports means three sets of conformance tests. Mitigated because the conformance test schema is transport-agnostic — each transport is just an encoding of the same operation set; we test the operations, not the wires.

**Out of scope for v1:** MCP sampling delegation (MCP server asking Gemba's model to complete). Not relevant — the UI has no model. Transport auto-negotiation (adaptor declares multiple transports; Gemba picks the best). v1 adaptors declare exactly one transport.

### DD-9: Edge taxonomy — 3-core `{parent_of, blocks, relates_to}`, all other edges via extension channel

**Landscape reference:** D1, C2, C3.

**Decision:** Core edges are `{parent_of, blocks, relates_to}` (aligned to C2 + C3). All other edges — including Beads' `discovered-from`, `waits-for`, `replies-to`, `conditional-blocks`, Azure's `predecessor/successor` and `tests/tested-by`, Jira's `duplicates`, `clones`, `causes`, and any tracker-specific custom link type — are first-class inside the adaptor but surfaced to the core via the `Relationship.extension` typed map. Gemba's core graph rendering shows only the 3 canonical types by default; the dep-graph view exposes extension edges when the adaptor declares them.

**Rationale:** D1 noted no hope of a canonical superset; political reality is that even Beads (whose author is shipping Gemba) uses 7 edges that Jira, Linear, GitHub couldn't honour. Narrowing the core to the universally-agreed 3 lets every tracker round-trip losslessly. The RFC's dep-graph view (RFC §New surfaces) explicitly lists "all seven Beads edge types" — that keeps working because the Beads adaptor declares those 4 extensions.

**Tradeoffs:** Default views drop edge richness. Beads users who loaded Gemba expecting a `discovered-from` filter need to enable it via capability declaration. Acceptable — the filter UI reads from the adaptor-declared extension list, so it appears automatically when connected to Beads.

**Out of scope for v1:** Cross-adaptor edge type normalization (declaring that Jira's `duplicates` is the same edge as Linear's `duplicate`). Both sit in extension; both render; renaming is a v2 concern.

### DD-10: Multi-repo work items — **v1 is single-repo-per-WorkItem**; multi-repo is a v2 capability

**Landscape reference:** Gap "Cross-repo coordination is barely solved", RFC locked decision #9.

**Decision:** A v1 `WorkItem` is scoped to exactly one `RepositoryRef`. Evidence across repos is supported (an evidence link can point to another repo) but parent-of edges cannot cross repos. Adaptors that *want* to expose cross-repo work items (GitHub sub-issues explicitly support this; see §3 of the landscape) MUST flatten them: the core sees a single-repo parent and extension metadata notes "has cross-repo children the adaptor chose not to surface."

**Rationale:** The RFC commits to "multi-rig, single workspace for v1" (locked decision #9). Cross-repo WorkItems are strictly harder and no product has solved it well. Committing early narrows the abstraction and unblocks v1 ship.

**Tradeoffs:** GitHub Projects users with Projects-v2 multi-repo hierarchies see their work collapsed. Acceptable for v1 (explicit deferral).

**Out of scope for v1:** Multi-repo. Explicit.

### DD-11: ~~No-DoD close semantics — close permitted but flagged, audit-trail entry required~~ **WITHDRAWN**

**WITHDRAWN — see DD-3 update.** With DD-3 reduced to informational-only metadata, there is no "DoD-enforcement" for a close to bypass. "Unverified close" is no longer a meaningful distinct state — every close is simply a close, and the audit trail already records actor/timestamp via the standard event stream (§4.4). The `unverified_close` evidence type is removed. There is no special close path; all closes are treated identically.

When industry consensus on completion semantics emerges and DD-3 re-opens with enforcement, this DD will also re-open to define the no-DoD close policy. Not before.

*(Landscape reference preserved for history: known-unknown #11, D8.)*

### DD-12 (emergent): Capability-negotiation over hardcoded feature flags

**Landscape reference:** RFC §Architectural alignment (Bitter Lesson exclusions — no capability flags in the UI); C4, D2, D3 (tracker-by-tracker variance demands a protocol).

**Decision:** Every adaptor (both planes) declares its capabilities on registration via a typed `CapabilityManifest` (§4.6). The UI queries capabilities at render time to decide whether to show a control (e.g., "transition to In Review" only appears if the tracker declares `can_transition_to: ["InReview"]`). The UI never hardcodes "Jira does X, Linear does Y."

**Rationale:** The RFC's Bitter Lesson exclusion forbids hardcoded role names. By the same logic, it must forbid hardcoded tracker-capability switches. Capability negotiation is the generalization that keeps the UI honest as new adaptors ship.

**Tradeoffs:** More adaptor-author surface area. Acceptable; the conformance suite makes it testable.

**Out of scope for v1:** Capability-level permission scoping (this user can only use capabilities X, Y, Z). v1 is all-or-nothing per authenticated identity.

### DD-13 (emergent): Evidence is append-only and adaptor-synthesizable

**Landscape reference:** C5, Gap "Evidence-backed DoD verification is bespoke everywhere".

**Decision:** `Evidence` records are append-only (never mutated, only superseded). For trackers that don't natively store evidence (most), the adaptor MAY synthesize evidence from adjacent data (Git log for commits, PR API for PRs, Beads work-history for sessions). Synthesized evidence is tagged `synthesized: true` so the UI can distinguish "the tracker asserted this" from "the adaptor inferred this."

**Rationale:** Without append-only, the audit-log promise (RFC §Retro, "truthful audit log") collapses. Without synthesis, GitHub adaptors get rich evidence and Jira adaptors get nothing, ruining parity.

**Tradeoffs:** Synthesized evidence can be wrong (commit SHA mapped to wrong WorkItem via heuristic). Flagging lets retros distinguish signal from inference.

### DD-14 (emergent): Sprint — token-budgeted (not duration-bounded), with epic-level inform/warn/stop rollup

**Landscape reference:** Gap "No cross-system cost/budget accounting" (D9); domain self-critique (missing sprint primitive from the Agile-ceremony gap).

**Decision:** Gemba introduces **`Sprint`** as a first-class entity, reusing the familiar Agile term but **redefining its hard constraint**: a Sprint is bounded by a **token budget**, not a calendar duration. Calendar duration (e.g., "two weeks") is *optional planning metadata* surfaced in the UI for team cadence; it is not enforced. When the token budget is exhausted, the Sprint ends — on day 4 or day 40, irrespective of the planned calendar.

Epics reference a Sprint (`epic.sprint_ref`); WorkItems inherit the reference transitively through their parent epic. Epics carry their own `epic.token_budget` whose sum must not exceed the parent Sprint's budget (enforced at Sprint `Active` transition, not at Epic creation).

Each budget (epic-level and sprint-level) carries three thresholds with configurable percentages — defaults `inform: 50%`, `warn: 80%`, `stop: 100%` — and yields a named policy event when crossed:

- **`inform`** — UI surfaces a badge on the epic/sprint card; an event lands in the insights panel. No operator action required.
- **`warn`** — badge escalates colour; an entry appears in the `/escalations` inbox (via DD-6's `EscalationRequest` with `kind: "budget_warn"`); the event stream emits `budget.warn`.
- **`stop`** — mutations that would cause *new* token spend against that scope (claim, transition to `Started`, assignment to a new agent) are rejected unless the request carries a Gemba confirm override (`X-GEMBA-Confirm` nonce with `budget_override: true`, per RFC §Locked 7). Existing in-flight work is not terminated — `stop` is mutation-gating, not process-killing.

Sprint has its own state: `Planned → Active → Closed` or `Planned → Abandoned` / `Active → Abandoned`. Closed = scope ended intentionally; Abandoned = ended before scope complete. Token budgets are frozen at `Active` transition.

**Epic ↔ Sprint cardinality (v1):** One Sprint contains many Epics (1:N). An Epic belongs to at most one Sprint. Cross-sprint carry-over (scope moving from one Sprint to the next) is handled by closing the Epic and opening a successor Epic (linked via `relates_to`) in the next Sprint. Carry-over-as-a-first-class-operation is a v2 concern.

**Rationale:** Phase 2's self-critique (grade B− on Agile semantics) called out the missing sprint primitive. Rather than inventing new vocabulary, Gemba reuses `Sprint` — the term Agile/Scrum/Jira-fluent humans already know — but redefines its bounding constraint from calendar time to token budget. Reuse preserves mental load; redefinition earns its keep because (a) tokens are the meaningful cost axis in agent-driven deployments (DD-4), (b) calendar time is an imperfect proxy for spend when agents can spike 10x on any given day, and (c) the analogy to sprint planning (pick a scope, allocate a budget, work until it's gone) survives the swap of time→tokens cleanly.

**Tradeoffs:** A human fluent in Scrum may initially expect `sprint.duration` to be the enforced field and be surprised when a Sprint closes early because tokens ran out. Mitigated by surfacing both axes in the UI — budget remaining is the primary gauge; planned duration is a secondary gauge showing "on pace / ahead / behind" relative to the calendar. Token-denominated budgets can mislead across model tiers — a 50M-token budget that spawns expensive Opus calls hits `stop` sooner than one using Haiku. Mitigated by `dollars_est` rollup rendered alongside tokens (DD-4).

**Out of scope for v1:**
- Carry-over as a first-class operation (use `relates_to` + new Epic instead).
- Multi-Sprint WorkItems (a WorkItem is tied to its parent Epic's Sprint, transitively).
- Budget rebalancing mid-Sprint (thresholds are frozen at `Active`). A v2 feature could rebalance remaining budget across unfinished epics.
- Nested Sprints (Sprint of Sprints).
- Dollar-denominated or wallclock-denominated primary budget (tokens only in v1; other axes are rendered, not enforced).
- Duration-based auto-close (Sprint runs until budget exhausted or explicitly closed; the planned-duration field never triggers a close in v1).

### DD-15 (emergent): Adaptor transport plurality — `api | jsonl | mcp` declared at registration

*(Nested inside DD-8 rationale; promoted to its own DD for discoverability.)*

**Landscape reference:** C8 (MCP convergence), observed heterogeneity across adaptor implementation costs.

**Decision:** Each adaptor (both planes) declares exactly one transport at registration from `{api, jsonl, mcp}`. The transport declaration lives in the `CapabilityManifest` (DD-12). Gemba's adaptor-registration protocol negotiates the transport and uses that transport exclusively for all subsequent operations against the adaptor.

- **`api`** — the adaptor exposes HTTP + JSON endpoints. Gemba issues requests over HTTP. This is the pragmatic wrapper for CLI-based systems (Gas Town's `gt --json` + `bd --json` surfaces wrapped by a small HTTP shim).
- **`jsonl`** — the adaptor operates on newline-delimited JSON files (import + export). Gemba writes to an outbox file and tails an inbox file. This is the transport for air-gapped, disconnected, or migration-bootstrap scenarios; it also happens to match the existing `issues.jsonl` format.
- **`mcp`** — the adaptor speaks the MCP client/server profile (JSON-RPC 2.0 over the MCP transports). Recommended for new adaptors composing with MCP-native agent ecosystems.

**Rationale:** Locking the wire to MCP would have blocked Gas Town (which speaks CLI-JSON) without benefit. The conformance test suite is transport-agnostic; adding transports adds line coverage, not architectural complexity.

**Tradeoffs:** Gemba carries three small transport modules. Acceptable; each is a few hundred lines of glue.

**Out of scope for v1:** Multi-transport adaptors (declare `mcp` and `jsonl` and let Gemba pick). Transport capability upgrade (adaptor starts on `jsonl`, switches to `api` when online). Both are v2.

---

## 2. Work Coordination Plane

### 2.1 Entities

#### 2.1.1 `WorkItem`

**Purpose:** A unit of work of any type (epic, story, task, bug, …) that agents or humans complete.

**Fields:**

| Field | Type | Req | Tag |
|---|---|---|---|
| `id` | `WorkItemId` (opaque string, adaptor-assigned) | yes | core |
| `hierarchical_title` | `string` (e.g., `"Epic 3 / Story 7 / Task 2 — Parse YAML"`) | yes | core |
| `local_title` | `string` (leaf title only; e.g., `"Parse YAML"`) | yes | core |
| `type` | `WorkItemType` enum (§2.2) | yes | core |
| `description` | `WorkDescription` (§2.1.6) | yes | core |
| `state` | `string` (adaptor-defined name, e.g., `"In Review"`) | yes | core |
| `state_category` | `StateCategory` enum (§2.3) | yes | core |
| `assignee` | `AgentRef \| HumanRef \| null` (§2.1.3) | no | core |
| `parent_id` | `WorkItemId \| null` | no | core |
| `repository` | `RepositoryRef` (DD-10: exactly one) | yes | core |
| `relationships` | `Relationship[]` (§2.1.2) | yes | core (may be empty) |
| `evidence` | `Evidence[]` (§2.1.4, append-only) | yes | core (may be empty) |
| `dod` | `DefinitionOfDone \| null` (§2.1.5, §4.1) | no | core |
| `cost_meter` | `CostMeter \| null` (§4.2) | no | core |
| `sprint_ref` | `SprintId \| null` (DD-14; inherited from parent epic when null on a non-epic WorkItem) | no | core |
| `token_budget` | `TokenBudget \| null` (DD-14; populated on epics; inherited read-only on descendants) | no | core |
| `created_at` / `updated_at` / `closed_at` | ISO-8601 strings | yes / yes / opt | core |
| `adaptor_extensions` | `Record<string, unknown>` (typed per capability) | yes | ext (may be empty) |

**Invariants:**

- `hierarchical_title` is a derived read-only; any parent retitle propagates (§2.2).
- `state_category` MUST match `state` per the adaptor's declared `state_map` (DD-12).
- `dod`, when present, is informational only (DD-3). It never gates state transitions.
- `parent_id.repository == this.repository` (DD-10).
- No cycles in `relationships[type="parent_of"]`.
- `token_budget` MAY be set only when `type == "epic"` (v1 restriction; DD-14). Descendant WorkItems inherit `sprint_ref` from their nearest epic ancestor (resolved at read time).

**Lifecycle:** Created via `WorkPlane.create`. Moves through `state_category` values (§2.3). Closed when `state_category` reaches `Completed` or `Canceled`. Never deleted; adaptors MAY hide but MUST preserve.

**Example (JSON):**

```json
{
  "id": "gt-abc12",
  "hierarchical_title": "Epic: Adaptor layer / Story: WorkPlane iface / Task: Beads adaptor CRUD",
  "local_title": "Beads adaptor CRUD",
  "type": "task",
  "description": {
    "work_to_complete": "Implement WorkPlane.create/read/update/delete against `bd --json`.",
    "definition_of_done_ref": "dod://gt-abc12",
    "skill_persona_context": "Go engineer familiar with bd CLI. See docs/BEADS-ADAPTOR.md."
  },
  "state": "in_progress",
  "state_category": "Started",
  "assignee": { "kind": "agent", "agent_id": "mike", "display_name": "Mike (agent)" },
  "parent_id": "gt-abc10",
  "repository": { "uri": "gh:steveyegge/gemba", "branch": "main" },
  "relationships": [
    { "type": "blocks", "target_id": "gt-abc15" },
    { "type": "parent_of", "target_id": "gt-abc13" }
  ],
  "evidence": [
    { "type": "commit", "ref": "sha:d3f92a1", "producer": "agent:mike", "verified": true, "at": "2026-04-18T14:02:00Z", "synthesized": false }
  ],
  "dod": { "version": "1.0", "acceptance_criteria": "All `WorkPlane.*` CRUD methods round-trip against `bd --json` with byte-equivalent extension fields." },
  "cost_meter": { "tokens_total": 28_400, "wallclock_seconds": 430, "dollars_est": 0.21 },
  "sprint_ref": "spr-17",
  "token_budget": null,
  "created_at": "2026-04-18T10:00:00Z",
  "updated_at": "2026-04-18T14:02:30Z",
  "adaptor_extensions": {
    "beads.priority": "P1",
    "beads.edge_discovered_from": "gt-abc03"
  }
}
```

#### 2.1.2 `Relationship`

**Purpose:** A typed directed edge between two WorkItems.

**Fields:**

| Field | Type | Req | Tag |
|---|---|---|---|
| `type` | `"parent_of" \| "blocks" \| "relates_to"` (core, per DD-9) | yes | core |
| `extension_type` | `string \| null` (e.g., `"beads.discovered_from"`, `"jira.duplicates"`) | no | ext |
| `target_id` | `WorkItemId` | yes | core |
| `created_at` | ISO-8601 | yes | core |
| `created_by` | `AgentRef \| HumanRef` | no | core |

**Invariants:**

- Exactly one of `type` or `extension_type` is present.
- `parent_of` edges form a DAG (no cycles; enforced by adaptor).
- `blocks` edges form a DAG (cycle detection is the UI's job — show a cycle warning — but adaptors MAY enforce).
- `extension_type` MUST be declared in the adaptor's `CapabilityManifest.relationship_extensions`.

#### 2.1.3 `AgentRef` / `HumanRef` (discriminated union)

```typescript
type Assignee =
  | { kind: "agent"; agent_id: string; display_name: string; role?: string; parent_agent?: string }
  | { kind: "human"; user_id: string; display_name: string; email?: string }
  | null;
```

Per DD-1, `AgentRef` is the richer shape. Adaptors for trackers without the agent concept synthesize `role` and `parent_agent` from labels/custom fields at read time; they persist via label/custom field at write time.

**Invariants:**

- `agent_id` is stable across sessions (C10). The orchestrator provides an ephemeral `session_id` separately (§3.1).

#### 2.1.4 `Evidence`

**Purpose:** A typed, verifiable link that proves a claim about a WorkItem.

**Fields:**

| Field | Type | Req | Tag |
|---|---|---|---|
| `id` | `EvidenceId` | yes | core |
| `type` | `"commit" \| "pr" \| "ci_run" \| "test_report" \| "human_attestation" \| "ai_check" \| string` | yes | core |
| `ref` | `string` (URI or opaque ref, e.g., `"sha:d3f9…"`, `"gh:pr:1423"`) | yes | core |
| `producer` | `AgentRef \| HumanRef` | yes | core |
| `verified` | `boolean` | yes | core |
| `verification_method` | `string \| null` (e.g., `"github-api-check-suite"`, `"adaptor-heuristic"`) | no | core |
| `synthesized` | `boolean` (DD-13 — true if adaptor inferred this) | yes | core |
| `at` | ISO-8601 | yes | core |
| `extension` | `Record<string, unknown>` | no | ext |

**Invariants:** Append-only (DD-13). `id` is assigned on write and never reused.

#### 2.1.5 `DefinitionOfDone`

Per DD-3, v1 DoD is **informational-only**. Full (minimal) schema in §4.1:

```typescript
interface DefinitionOfDone {
  version: "1.0";
  acceptance_criteria?: string;   // Free-text, Markdown-allowed; the "what counts as done" prose
  notes?: string;                 // Optional additional context
}
```

No predicates, no evaluators, no machine checks. The UI displays these fields on the WorkItem detail view; adaptors round-trip them to whichever native free-text field the backend exposes.

#### 2.1.6 `WorkDescription`

**Purpose:** Structured description replacing the free-text `description` field most trackers use.

**Serialization:** JSON (not Markdown-wrapped). Rationale: the UI must render fields selectively (e.g., show `work_to_complete` on the card, `skill_persona_context` only on the detail page). Markdown-in-a-single-field makes that impossible without re-parsing. Raw Markdown survives *inside* each field.

```typescript
interface WorkDescription {
  work_to_complete: string;           // Markdown, required
  definition_of_done_ref?: string;    // URI pointing to the DoD (`dod://<workitem-id>`)
  skill_persona_context?: string;     // Markdown; who should pick this up and what they need to know
  links?: Array<{ label: string; url: string }>;
  extension?: Record<string, unknown>;
}
```

**Justification for not inlining DoD into the description:** Separation of concerns — the DoD (even as informational free-text per DD-3) is displayed separately on the WorkItem detail view and may be edited independently of `work_to_complete`. Reference-by-URI lets the description survive any future DoD schema evolution (a `2.0` enforcement schema would not force WorkDescription changes).

#### 2.1.7 `Sprint` (per DD-14)

**Purpose:** A token-budgeted container grouping multiple epics toward a defined scope. Reuses the Agile term; **bounded by token budget, not calendar duration.**

**Fields:**

| Field | Type | Req | Tag |
|---|---|---|---|
| `id` | `SprintId` | yes | core |
| `title` | `string` (e.g., `"Sprint 17 — WorkPlane conformance"`) | yes | core |
| `goal` | `string` (Markdown; the "what we're trying to achieve this sprint" statement) | no | core |
| `state` | `"Planned" \| "Active" \| "Closed" \| "Abandoned"` | yes | core |
| `token_budget` | `TokenBudget` (§2.1.8) | yes | core |
| `planned_start` / `planned_end` | ISO-8601 dates (*informational only* — never trigger close) | no | core |
| `actual_start` | ISO-8601 timestamp (set on Planned→Active) | no | core |
| `actual_end` | ISO-8601 timestamp (set on →Closed or →Abandoned) | no | core |
| `epic_ids` | `WorkItemId[]` (the epics in this sprint; MUST all be `type == "epic"`) | yes | core (may be empty) |
| `extension` | `Record<string, unknown>` | no | ext |

**Invariants:**
- When `state == "Active"`, `token_budget` is frozen (no mutations).
- `Σ(epic.token_budget.total for epic in epic_ids) ≤ token_budget.total` — enforced on Planned→Active transition.
- An Epic has at most one `sprint_ref` (1:N cardinality, DD-14).
- `planned_end` is advisory; exhausting `token_budget` triggers close, not `planned_end`.

**Lifecycle:** Created in `Planned`. Transition to `Active` freezes the budget and starts rollup. Transition to `Closed` on explicit operator action or when `token_budget.consumed >= token_budget.total` AND all child epics are `Completed` or `Canceled`. Transition to `Abandoned` on explicit operator action when scope is incomplete.

**Example:**

```json
{
  "id": "spr-17",
  "title": "Sprint 17 — WorkPlane conformance",
  "goal": "Ship Beads + Gas Town adaptors passing the full conformance suite.",
  "state": "Active",
  "token_budget": {
    "total": 50_000_000,
    "consumed": 22_400_000,
    "thresholds": { "inform": 0.50, "warn": 0.80, "stop": 1.00 },
    "crossed": ["inform"]
  },
  "planned_start": "2026-04-20",
  "planned_end": "2026-05-04",
  "actual_start": "2026-04-20T09:00:00Z",
  "epic_ids": ["gm-e3", "gm-e6", "gm-e7"],
  "extension": {}
}
```

#### 2.1.8 `TokenBudget` (per DD-14)

**Purpose:** The inform/warn/stop budget primitive applied at epic and sprint scope.

**Fields:**

| Field | Type | Req | Tag |
|---|---|---|---|
| `total` | `integer` (token count) | yes | core |
| `consumed` | `integer` (running total from `CostMeter` samples, §4.2) | yes | core |
| `thresholds` | `{ inform: number; warn: number; stop: number }` (fractions in [0.0, 1.0], non-decreasing) | yes | core |
| `crossed` | `Array<"inform" \| "warn" \| "stop">` (thresholds crossed at least once; append-only within this budget's lifetime) | yes | core |

**Invariants:**
- `0 ≤ thresholds.inform ≤ thresholds.warn ≤ thresholds.stop`.
- `crossed` is append-only within a single budget lifetime (even if `consumed` drops due to evidence correction, a crossed threshold remains crossed — this is an audit property, not a live state).
- When `consumed >= total * thresholds.stop` AND `"stop" ∈ crossed`, new-spend mutations against the owning scope are rejected unless the request carries a `budget_override` confirmation nonce (§4.5).

**Enforcement scope (what counts as "new spend"):**
- Claiming an unassigned WorkItem (state transition Unstarted → Started via `WorkPlane.claim`).
- Assigning a new agent to an in-progress WorkItem.
- Creating a new WorkItem whose parent epic is in this budget's scope.
- *Not* enforced: reading, querying, UI navigation, closing, attaching evidence, existing in-flight agent work (DD-14 is mutation-gating, not process-killing).

**Rollup:** An epic's budget consumption is the sum of its descendant WorkItems' `CostMeter.tokens_total`. A sprint's budget consumption is the sum of its epics' consumption. Rollup is computed at read time; adaptors supply the leaf samples.

### 2.2 Hierarchy and naming

**Canonical `WorkItemType` set:**

```typescript
type WorkItemType =
  | "epic"      // Top of backlog hierarchy, aggregates stories
  | "story"     // Feature-level unit, agent- or human-completable in hours-to-days
  | "task"      // Concrete engineering unit, agent-completable in minutes-to-hours
  | "sub_task"  // A task's atomic part
  | "bug"       // Defect (orthogonal to the epic/story/task axis — a bug can be any size)
  | "spike"     // Research / timeboxed investigation with no deliverable code
  | "chore";    // Necessary work with no product-visible outcome (dependency bumps, etc.)
```

Validated against Phase 1: Jira uses Epic/Story/Task/Bug/Sub-task; Linear has Issues + custom types; Shortcut uses Story with type=bug; Beads has task/bug/message. The canonical set is the union of commonly-observed types, adjusted for terminology (Beads' `message` is not work; it's communication — handled by a separate `Conversation` entity out of scope here).

**Parenting rules:**

| Parent \ Child | epic | story | task | sub_task | bug | spike | chore |
|---|---|---|---|---|---|---|---|
| epic | no | **yes** | yes | no | yes | yes | yes |
| story | no | no | **yes** | yes | yes | no | no |
| task | no | no | no | **yes** | no | no | no |
| sub_task | no | no | no | no | no | no | no |
| bug | no | no | yes | yes | no | no | no |
| spike | no | no | yes | yes | no | no | no |
| chore | no | no | yes | yes | no | no | no |

Bold = canonical hierarchy. Non-bold `yes` entries permit pragmatic flex (e.g., an epic that directly contains a bug).

**Hierarchical title convention:**

`{ancestor_1_local_title} / {ancestor_2_local_title} / … / {local_title}`

Example: an epic `"Adaptor layer"` contains story `"WorkPlane interface"` which contains task `"Beads CRUD"`:

- Epic hierarchical title: `"Adaptor layer"`
- Story hierarchical title: `"Adaptor layer / WorkPlane interface"`
- Task hierarchical title: `"Adaptor layer / WorkPlane interface / Beads CRUD"`

**Title stability when items re-parent:** `local_title` is immutable on re-parent; `hierarchical_title` is recomputed. UI components that cache `hierarchical_title` invalidate on `parent_id` change (§4.4 events).

**Depth limits:** Soft limit 6 levels, hard limit 10. Rationale: D2 — GitHub sub-issues go 8 deep, Jira Premium goes 5+, Beads parent-child is unlimited; past 6 the UI becomes unreadable, past 10 we refuse. Adaptors declare their native depth in `CapabilityManifest.max_hierarchy_depth`; Gemba clamps to `min(declared, 10)`.

### 2.3 State model

Per C4, 5 canonical `StateCategory` values, each with adaptor-defined `state` names.

```typescript
type StateCategory = "Backlog" | "Unstarted" | "Started" | "Completed" | "Canceled";
```

Chosen to align with Linear's 5 state types (C4 primary evidence) and Azure DevOps' 5 state categories (same count, similar semantics with renaming).

**Category definitions:**

- **Backlog** — Ingested into the tracker; not yet triaged/ready.
- **Unstarted** — Triaged, prioritized, ready for an agent/human to claim.
- **Started** — Claimed and actively being worked.
- **Completed** — Finished successfully. Close is a single path; DoD, if present, is informational only (DD-3).
- **Canceled** — Closed without completion (won't-fix, duplicate, abandoned).

**Default transitions:**

```
  Backlog ──▶ Unstarted ──▶ Started ──▶ Completed
     │            │             │             ▲
     └────┬───────┴─────────────┴───────────┬─┘
          ▼                                 │
        Canceled ◀───── (from any state) ───┘
```

Every state category (except `Completed` and `Canceled` as terminals) can transition to `Canceled`. `Completed` ↔ `Canceled` is adaptor-declared (Jira allows reopen; Beads supports it; Linear allows both). `Completed` → `Started` (reopen) is a named capability (`can_reopen_from_completed`).

**Sprint state model (per DD-14, distinct from WorkItem states):**

Sprints have their own four-state lifecycle, orthogonal to the WorkItem state categories above:

```
  Planned ──▶ Active ──▶ Closed
     │           │
     └───────────┴──▶ Abandoned
```

- **Planned** — created, epics added, token budget set, not yet started. Budget is mutable.
- **Active** — sprint is running; token budget is frozen; rollup is live; threshold crossings emit events. WorkItems claim normally; new-spend mutations are rejected at `stop` unless override-nonced.
- **Closed** — scope ended intentionally (all child epics reached `Completed`/`Canceled`, or operator explicitly closed). Terminal.
- **Abandoned** — sprint ended before scope was complete. Terminal. Remaining open epics retain their `sprint_ref` for historical audit; future WorkItems on those epics would need to be re-assigned to a different Sprint to re-activate budget accounting.

**Adaptor state-name mapping:** Each adaptor declares a `StateMap`:

```typescript
interface StateMap {
  // Adaptor state name -> Gemba category
  to_category: Record<string, StateCategory>;
  // Category -> preferred adaptor state name (for Gemba-initiated transitions)
  preferred_state: Record<StateCategory, string>;
  // Declared valid transitions in the adaptor's state name space
  valid_transitions: Array<{ from: string; to: string }>;
}
```

Example (Beads): `{ open: "Unstarted", in_progress: "Started", closed: "Completed" }`. Example (Jira): `{ "To Do": "Unstarted", "In Progress": "Started", "In Review": "Started", "Done": "Completed", "Won't Do": "Canceled" }`.

**Workflow engines (Jira, Azure):** adaptor declares `valid_transitions`; UI disables invalid transition targets in drag-drop.

**Free transitions (Linear, GitHub Projects, Beads):** adaptor declares `valid_transitions` as the full cross-product; UI enables all.

**Stalled/blocked as derivable, not stored:** A WorkItem is *blocked* when it has an unsatisfied `blocks` edge (the inverse — other WorkItems whose `blocks` edges point at this one and are not Completed/Canceled). Beads has always modeled this as derived (C4 evidence row). Gemba follows. `state_category` stays "Started" or "Unstarted"; a separate computed flag `is_blocked: boolean` drives UI badging.

**State diagram (table form):**

| From \ To | Backlog | Unstarted | Started | Completed | Canceled |
|---|---|---|---|---|---|
| Backlog | — | default | rare (skip-triage) | forbidden | allowed |
| Unstarted | allowed (reject) | — | default (claim) | forbidden | allowed |
| Started | forbidden | allowed (unclaim) | — | default | allowed |
| Completed | forbidden | capability `can_reopen_from_completed` | capability | — | capability |
| Canceled | forbidden | capability `can_reopen_from_canceled` | forbidden | forbidden | — |

### 2.4 Relationships and edge taxonomy

Per DD-9: 3 core types `{parent_of, blocks, relates_to}`; all else is extension.

**Beads 7-edge mapping:**

| Beads edge | Core type | Extension type | Notes |
|---|---|---|---|
| `parent-child` | `parent_of` | — | Direct |
| `blocks` | `blocks` | — | Direct |
| `related` | `relates_to` | — | Direct |
| `discovered-from` | — | `beads.discovered_from` | Extension (novel; no cross-tracker analogue) |
| `waits-for` | `blocks` (semantically) | `beads.waits_for` | Surface dual: the blocks edge gives cross-tracker semantics; the extension preserves the Beads-native flavor |
| `replies-to` | — | `beads.replies_to` | Extension (Beads communication is out of core scope) |
| `conditional-blocks` | — | `beads.conditional_blocks` | Extension |

**Jira/Linear/Azure extras:** `duplicates`, `clones`, `causes`, `predecessor/successor`, `tests/tested-by` → all extension, named `jira.duplicates`, `azure.predecessor`, etc. The dep-graph view reads `CapabilityManifest.relationship_extensions` to know which extensions exist and offer them as filter chips.

**Edge invariants:**

- `parent_of`: forms a DAG, max depth per §2.2, target must be same repository.
- `blocks`: SHOULD form a DAG; cycles render with a warning.
- `relates_to`: symmetric suggestion (UI creates both directions on user action; adaptor stores both or emulates symmetry at read time).
- Extension edges: adaptor-declared invariants; core enforces only type presence.

### 2.5 Adaptor interface (`WorkPlane`)

**Pseudo-TypeScript. Implementations in Go/Rust/Python all valid.**

```typescript
interface WorkPlaneAdaptor {
  // ─── Registration ───
  describe(): CapabilityManifest;

  // ─── CRUD ───
  create(input: WorkItemCreate, ctx: CallCtx): Promise<WorkItem>;
  read(id: WorkItemId, ctx: CallCtx): Promise<WorkItem | null>;
  update(id: WorkItemId, patch: WorkItemPatch, precondition: Precondition, ctx: CallCtx): Promise<WorkItem>;
  // `delete` is absent by policy — WorkItems are closed, not deleted (§2.1)

  // ─── Query ───
  query(filter: WorkItemFilter, page: PageCursor, ctx: CallCtx): Promise<Page<WorkItem>>;
  // Canonical filters: by state, state_category, assignee, parent_id, repository, type,
  // relationship (inbound/outbound of a given type), label, extension fields.

  // ─── Ready-set (R3) ───
  ready_set(filter: WorkItemFilter, page: PageCursor, ctx: CallCtx): Promise<Page<WorkItem>>;
  // Returns WorkItems whose `blocks` in-edges are all resolved (parents/blockers closed)
  // and state_category ∈ {Backlog, Unstarted}. Adaptors with `ready_set_query: true` answer
  // server-side; adaptors with `ready_set_query: false` MAY synthesize from `query` + edge
  // traversal client-side. The contract is identical either way — orchestrators use this
  // as their primary dispatch query (Gastown's `bd ready` is the Beads-adaptor fast path).

  // ─── State transitions (idempotent, nonce-gated) ───
  transition(id: WorkItemId, to_state: string, nonce: ConfirmNonce, ctx: CallCtx): Promise<WorkItem>;
  claim(id: WorkItemId, claimant: AgentRef | HumanRef, nonce: ConfirmNonce, ctx: CallCtx): Promise<WorkItem>;
  unclaim(id: WorkItemId, nonce: ConfirmNonce, ctx: CallCtx): Promise<WorkItem>;
  close(id: WorkItemId, mode: "completed" | "canceled", nonce: ConfirmNonce, ctx: CallCtx): Promise<WorkItem>;

  // ─── Relationships ───
  link(from: WorkItemId, edge: RelationshipInput, nonce: ConfirmNonce, ctx: CallCtx): Promise<Relationship>;
  unlink(from: WorkItemId, edge: RelationshipKey, nonce: ConfirmNonce, ctx: CallCtx): Promise<void>;

  // ─── Evidence (append-only) ───
  attach_evidence(id: WorkItemId, ev: EvidenceInput, ctx: CallCtx): Promise<Evidence>;

  // ─── DoD ───
  // Per DD-3, DoD is informational-only and rides as a field on WorkItem.
  // Mutations go through the standard `update` method with a `dod` patch.
  // There is no dedicated DoD method, no evaluator, no ProofOfDoD.

  // ─── Sprint (DD-14) ───
  create_sprint(input: SprintCreate, ctx: CallCtx): Promise<Sprint>;
  read_sprint(id: SprintId, ctx: CallCtx): Promise<Sprint | null>;
  update_sprint(id: SprintId, patch: SprintPatch, precondition: Precondition, ctx: CallCtx): Promise<Sprint>;
  transition_sprint(id: SprintId, to_state: "Active" | "Closed" | "Abandoned", nonce: ConfirmNonce, ctx: CallCtx): Promise<Sprint>;
  assign_epic_to_sprint(epic_id: WorkItemId, sprint_id: SprintId | null, nonce: ConfirmNonce, ctx: CallCtx): Promise<WorkItem>;
  query_sprints(filter: SprintFilter, page: PageCursor, ctx: CallCtx): Promise<Page<Sprint>>;
  // Adaptors that do NOT declare `sprint_native` (see CapabilityManifest) MAY implement
  // these by storing Sprint state in their extension channel or in a Gemba sidecar table.

  // ─── Budget query (DD-14) ───
  read_budget_rollup(scope: { kind: "epic" | "sprint"; id: string }, ctx: CallCtx): Promise<BudgetRollup>;
  // Returns current consumed + thresholds crossed. Computed by adaptor on demand
  // from underlying CostMeter samples; UI calls this when rendering budget gauges.

  // ─── Events (SSE / push / poll — adaptor-declared) ───
  subscribe(filter: SubscribeFilter, ctx: CallCtx): AsyncIterable<WorkPlaneEvent>;
  // Event stream includes `budget.inform | budget.warn | budget.stop` events
  // emitted when thresholds are first crossed for any epic or sprint in scope.

  // ─── Identity mapping ───
  resolve_assignee(ref: AgentRef | HumanRef, ctx: CallCtx): Promise<BackendIdentity>;
  identity_from_backend(backend_id: string, ctx: CallCtx): Promise<AgentRef | HumanRef | null>;
}

interface CallCtx {
  caller: AgentRef | HumanRef;       // Who is asking (for auth + audit)
  request_id: string;                // UUID for tracing
  confirm_nonce?: ConfirmNonce;      // For mutations (RFC §Locked 6)
}

type ConfirmNonce = string;          // 256-bit random; server-enforced once-only (RFC §Locked 6)

interface Precondition {
  if_match_updated_at?: string;      // Optimistic concurrency
}
```

**Idempotency (DD-12 + RFC's NDI principle):**

- `transition`, `claim`, `close`: idempotent on (id, target, nonce). Same nonce re-submitted = the same successful result (or conflict error if another transition happened in between).
- `create`: idempotent on (idempotency_key in input). Retries return the existing WorkItem.
- `attach_evidence`: idempotent on (id, ev.ref, ev.type) — re-attaching the same evidence twice yields the same record.

**Concurrency (two agents racing to claim):**

- `claim(id, A)` and `claim(id, B)` simultaneously: adaptor MUST use backend's primitive (Beads' `bd update --claim` is atomic; Linear has no native claim but simulates via optimistic `if_match_updated_at`). One call succeeds; the other receives `ConflictError` with the current `assignee` in the body. UI offers "force steal" as a nonce-gated action.

**Identity and auth:**

- `caller` in `CallCtx` is authenticated by Gemba (token, OIDC). The adaptor MUST NOT re-authenticate the caller; it MUST re-authorize (the caller may not have permission on the backend).
- Write operations pass `caller` to the backend (e.g., Jira API called with the caller's OAuth token, or — for shared-service mode — with a service principal that records `caller` in the audit trail).
- Per DD-1, `resolve_assignee` maps a Gemba `AgentRef` to a backend id; `identity_from_backend` is the reverse lookup used when reading data.

**Capability declaration:**

```typescript
interface CapabilityManifest {
  adaptor_id: string;
  adaptor_version: string;
  workplane_api_version: "1.0";   // Gemba contract version
  // Transport (DD-8 / DD-15): exactly one declared in v1
  transport: AdaptorTransport;   // "api" | "jsonl" | "mcp"
  // Core capabilities
  capabilities: Set<WorkPlaneCapability>;
  // State
  state_map: StateMap;
  // Hierarchy
  max_hierarchy_depth: number;
  // Relationship extensions
  relationship_extensions: Array<{ key: string; display_name: string; directed: boolean }>;
  // Field extensions (for adaptor_extensions)
  field_extensions: Array<{ key: string; type: "string" | "number" | "enum" | "date" | "json"; enum_values?: string[] }>;
  // Event delivery
  event_delivery: "sse" | "push" | "poll";
  poll_interval_seconds?: number;
  // Auth
  auth_model: "delegated_oauth" | "service_principal" | "local_cli";

  // ─── Agentic data plane category (R1–R8 per §1.0, dataplane-requirements.md) ───
  // Orchestrators (Gastown, Metaswarm, Gemba itself) inspect these to decide whether
  // an adaptor clears the agentic-data-plane minimum bar. Below-bar adaptors may load
  // but run in reduced-capability mode.
  schema_enforcement: "native" | "synthesized";                         // R1
  query_languages: Set<"filter-only" | "jsonpath" | "sql-subset" | "graphql">;  // R2
  dependency_graph_native: boolean;                                     // R3 (edges)
  ready_set_query: boolean;                                             // R3 (native ready-set)
  versioning_transport: Set<"none" | "git" | "dolt" | "jsonl" | "native-sqlite-export">; // R4
  concurrency_model: "optimistic" | "mvcc" | "git-merge" | "dolt-merge"; // R5
  agent_session_decoupling: boolean;                                    // R6 — must be `true` for category
  agent_native_api: "cli" | "json-api" | "mcp" | "rest-only";           // R7
  orchestrator_hooks: Set<
    | "ready-set-subscribe"
    | "claim-atomic"
    | "escalation-ingest"
    | "work-complete-ack"
    | "pool-bulk-dispatch"
  >;                                                                    // R8
}

type WorkPlaneCapability =
  | "custom_fields"
  | "workflow_fsm"                    // Backend enforces valid_transitions
  | "can_reopen_from_completed"
  | "can_reopen_from_canceled"
  | "evidence_native"                  // Backend natively stores evidence (synthesizers otherwise)
  | "cross_repo_hierarchy"             // v2; declared but ignored by v1 UI
  | "multi_assignee"                   // GitHub's up-to-10
  | "query_by_extension"               // Can filter on extension fields server-side
  | "sprint_native"                    // Backend has a native sprint/cycle/iteration; adaptor maps DD-14 Sprint onto it
  | "token_budget_enforced"            // Adaptor honors DD-14 inform/warn/stop at the WorkPlane boundary
  ;

type AdaptorTransport = "api" | "jsonl" | "mcp";   // DD-8 / DD-15 — declared in CapabilityManifest.transport
```

**Extension access:** `WorkItem.adaptor_extensions` is a flat `Record<string, unknown>`. Keys MUST be namespaced (`beads.priority`, `jira.components`, `linear.cycle_id`). The UI renders any extension field declared in `field_extensions` with a default widget per declared `type`. Writes to unknown keys are rejected with `SchemaError` by the adaptor.

### 2.6 Conformance test suite (`WorkPlane`)

Every `WorkPlane` adaptor MUST pass the following. The suite is a Gemba project; adaptor authors run it in their own CI.

**Group A — Core CRUD + query**

1. `create_round_trip`: Create a WorkItem with minimal fields; `read` returns an equivalent record (ids assigned by the adaptor match).
2. `create_with_extensions`: Create with populated `adaptor_extensions` matching the declared `field_extensions`; readback preserves them byte-equivalent for JSON types.
3. `patch_preserves_unmodified_fields`: `update` with a patch touching only `local_title`; all other fields unchanged including extensions.
4. `query_by_state_category`: Create 3 items in different categories; query `state_category=Started` returns exactly one.
5. `query_by_assignee`: Assignee filter returns only matching items; `null` assignee filter returns unassigned.
6. `query_pagination_stability`: Insert 100, paginate with cursor, verify no duplicates/gaps across pages.

**Group B — State transitions & race conditions**

1. `transition_valid`: Transition from declared-valid starting state to declared-valid target; succeeds.
2. `transition_invalid_rejected`: Invalid transition rejected with `InvalidTransitionError`; WorkItem unchanged.
3. `claim_race`: Two concurrent `claim` calls with different agents; exactly one succeeds, loser receives `ConflictError` including current assignee.
4. `transition_idempotent`: Same `transition(id, target, nonce)` submitted twice; second returns same result, state unchanged on second call.
5. `nonce_replay_rejected`: Same `nonce` used for a different mutation; rejected with `NonceReplayError` (RFC §Locked 6).
6. `close_with_reopen`: If `can_reopen_from_completed` declared, close then reopen succeeds; else reopen rejected.

**Group C — Edge taxonomy round-trip**

1. `core_edges_preserved`: Create items A, B; `link(A, {type: "blocks", target_id: B})`; read A, verify relationship present.
2. `extension_edge_preserved`: For each declared `relationship_extensions` entry, create, readback, confirm `extension_type` survives.
3. `parent_cycle_rejected`: Attempt to create a `parent_of` cycle; adaptor rejects with `CycleError`.
4. `unlink_idempotent`: Unlink a non-existent edge; no error (idempotent).
5. `cross_repo_parent_rejected` (if not declaring `cross_repo_hierarchy`): Parent in different repo rejected with `CrossRepoError`.

**Group D — Event delivery**

1. `event_fires_on_state_change`: Subscribe; mutate state; event received within declared latency budget (default 5s for poll, 1s for SSE/push).
2. `event_payload_includes_prev_and_next`: Events carry `{before, after}` for state-changing mutations.
3. `event_ordering`: Two mutations A then B; subscribers see A's event before B's event.
4. `subscribe_resume`: Kill subscription mid-stream; resume with last-seen cursor; no gaps.

**Group E — Identity mapping**

1. `resolve_assignee_roundtrip`: Create WorkItem with `AgentRef{agent_id: "mike"}`; read back; `assignee.agent_id == "mike"`.
2. `backend_identity_reverse`: Change assignee in backend directly (bypass adaptor); subscribe event reports the new assignee with `AgentRef` reconstructed via `identity_from_backend`.
3. `unknown_backend_identity`: Backend returns an assignee not in the adaptor's mapping; adaptor returns `HumanRef` with `user_id == backend_id, display_name == backend_id` (graceful fallback).

**Group F — Extension preservation**

1. `unknown_field_rejected`: Write `adaptor_extensions` with a key not in `field_extensions`; rejected.
2. `typed_field_type_enforced`: Enum extension rejects non-enum values; date extension rejects invalid ISO-8601.
3. `extension_query` (only if `query_by_extension` declared): Filter by extension field value returns correct subset.

**Group G — Dep graph evolution (R3)**

1. `ready_set_graph_evolution`: Insert A (state=Unstarted); insert B with `blocks→A`; `ready_set` returns A but not B. Close A; within the subscribe-event latency budget, `ready_set` returns B.
2. `discovered_from_mid_execution`: Agent working on A creates B via `create` with `discovered_from→A` extension (if `beads.discovered_from` declared). B appears in subsequent `ready_set` / `query` with the edge intact.

**Group H — Versioned transport (R4)** — capability-gated by `versioning_transport`

1. `versioned_state_round_trip`: Mutate state; export to declared versioning transport (`git` / `dolt` / `jsonl` / `native-sqlite-export`); import into a fresh instance; state matches byte-equivalent on typed fields.
2. `branch_merge_round_trip` (only if `versioning_transport` contains `dolt` or `git`): Create a second branch of the state; mutate each branch divergently; merge; result contains both mutations. Cell-level merge conflicts on the same record surface as a declared conflict, not silent overwrite.
3. `jsonl_export_import_round_trip` (only if `versioning_transport` contains `jsonl`): Full bulk export → bulk import → equivalence; partial-re-import idempotent on (id, updated_at).

**Group I — Concurrency stress (R5)**

1. `concurrent_writer_stress_N16`: Spawn 16 concurrent workers, each attempting `claim` on the same WorkItem; exactly one succeeds, 15 receive `ConflictError` with consistent `assignee` in the body. Total latency budget for the winning-write-to-visible-read cycle: adaptor-declared (default 2s).
2. `read_after_write_cross_writer`: Writer A completes `transition(id, "InProgress")`; writer B (different session) issues `read(id)` within the event-latency budget; sees `InProgress`. No stale-read larger than the declared budget.

**Group J — Session decoupling (R6)**

1. `session_death_recovery`: Session S1 claims X, persists notes via `update`, crashes (no `unclaim`). Session S2 opens; `query` shows X claimed-by-S1 with notes intact. S2 `unclaim(X)` + `claim(X)` succeeds; all prior notes/state survive.
2. `work_pickup_by_second_agent`: Agent A claims X; A exits cleanly (session end, no close). Agent B reads X, sees claim + state; B force-steals via `claim(X, B, override_nonce)`; X becomes B's claim; A's prior work artifacts (evidence, notes) remain attached.

**Group K — Orchestrator hooks (R8)** — each test capability-gated by `orchestrator_hooks` set membership

1. `ready_set_subscribe_latency` (if `ready-set-subscribe` declared): Subscribe to ready-set events; mutation that newly-qualifies an item delivers `ready_set.enter` within adaptor-declared latency budget.
2. `claim_atomic` (if `claim-atomic` declared): Same as Group B `claim_race` but stressed at N=16 — one winner, 15 well-formed conflicts.
3. `escalation_ingest_round_trip` (if `escalation-ingest` declared): Orchestrator pushes an `EscalationRequest` via the adaptor; readback from `subscribe(kind="escalation")` receives an equivalent event.
4. `work_complete_ack` (if `work-complete-ack` declared): `close` emits a `work.completed` event with the closing agent's identity preserved.
5. `pool_bulk_dispatch` (if `pool-bulk-dispatch` declared): Bulk-claim N items in one call; atomicity matches adaptor declaration (all-or-nothing vs best-effort).

Groups A–F remain baseline; G–K are category-level (R3 / R4 / R5 / R6 / R8) and capability-gated where listed.

---

## 3. Agent Orchestration Plane

### 3.1 Entities

#### 3.1.1 `Agent`

```typescript
interface Agent {
  id: string;                         // Stable identity (C10)
  display_name: string;
  role: string;                       // Adaptor-declared; no UI-hardcoded role names (RFC §Locked 2)
  parent_agent_id?: string;           // For hierarchies (Gas Town Mayor→Deacon; ADK hierarchy)
  capabilities: AgentCapability[];    // Declared by orchestrator, not inferred
  default_workspace_kind?: WorkspaceKind; // Preferred isolation (DD-5)
  extension?: Record<string, unknown>;
}

type AgentCapability =
  | "can_claim"                       // This agent can be assigned WorkItems
  | "can_escalate"                    // Emits EscalationRequests
  | "can_spawn_child"                 // Can create sub-agents
  | "mcp_client"
  | string;                           // Namespaced adaptor extensions
```

#### 3.1.2 `Workspace` (generic "rig")

Per DD-5.

```typescript
interface Workspace {
  id: string;
  kind: WorkspaceKind;
  scope: { repository: RepositoryRef; branch?: string; base_sha?: string };
  status: "provisioning" | "ready" | "in_use" | "released" | "error";
  isolation: IsolationCapabilities;   // Declared on acquire (§3.3)
  provider_metadata: Record<string, unknown>; // tmux session name, container id, k8s pod, VM id
  created_at: string;
  released_at?: string;
}

type WorkspaceKind = "worktree" | "container" | "k8s_pod" | "vm" | "exec" | "subprocess";

interface IsolationCapabilities {
  fs_scoped: true;                    // MUST (DD-5)
  net_isolated: boolean;
  cpu_limited: boolean;
  mem_limited: boolean;
  snapshot_restore: boolean;
}
```

#### 3.1.3 `AgentGroup` (per DD-7)

```typescript
interface AgentGroup {
  id: string;
  display_name: string;
  mode: "static" | "pool" | "graph";
  members: GroupMembers;
  scope: { workspace_ids?: string[]; repository_refs: RepositoryRef[] };  // Often single-repo (DD-10) but stored as array for v2
  extension?: Record<string, unknown>;
}

type GroupMembers =
  | { kind: "static"; agent_ids: string[] }
  | { kind: "pool"; check_endpoint: string; min_size?: number; max_size?: number }
  | { kind: "graph"; topology_ref: string; resolved_agents: string[] };
```

#### 3.1.4 `Assignment`

Binds an agent to a work item via a workspace.

```typescript
interface Assignment {
  id: string;
  workitem_id: WorkItemId;
  agent_id: string;
  workspace_id?: string;              // Optional for agents that don't need isolation (spike/chore)
  session_id?: string;                // Set when a session starts
  status: "pending" | "active" | "paused" | "finished" | "failed" | "canceled";
  started_at?: string;
  ended_at?: string;
  cost_meter?: CostMeter;
  escalations: EscalationRequest[];   // Open escalations produced by this assignment
}
```

#### 3.1.5 `Session`

Ephemeral instance of an agent running against an assignment (C10 — sessions are ephemeral, identities persist).

```typescript
interface Session {
  id: string;
  assignment_id: string;
  agent_id: string;
  status: "running" | "input_required" | "suspended" | "completed" | "failed";
  started_at: string;
  ended_at?: string;
  last_heartbeat?: string;
  transcript_ref?: string;            // Opaque URI; adaptor-resolvable
  cost_samples: CostSample[];         // Appended by adaptor
  provider_metadata: Record<string, unknown>;
}
```

#### 3.1.6 `Telemetry`

Event stream + cost meter (§4.2, §4.4).

#### 3.1.7 `EscalationRequest` (per DD-6)

```typescript
interface EscalationRequest {
  id: string;
  source: "mcp_elicitation" | "a2a_input_required" | "permission_prompt" | "hitl_approval" | "orchestrator_pause" | string;
  assignment_id?: string;
  workitem_id?: WorkItemId;
  agent_id?: string;
  urgency: "blocking" | "advisory";   // blocking = agent is suspended until answered
  title: string;
  prompt: string;                      // Markdown
  schema?: JsonSchema;                 // For structured input (MCP elicitation)
  options?: Array<{ value: string; label: string }>; // For choice prompts
  deadline?: string;                   // ISO-8601; after which request auto-cancels
  state: "open" | "resolved" | "canceled" | "expired";
  resolution?: {
    kind: "approve" | "deny" | "modify" | "defer";
    value?: unknown;                   // Matches `schema` if provided
    resolved_by: HumanRef;
    resolved_at: string;
  };
  created_at: string;
}
```

### 3.2 Grouping model

Per DD-7. Declaration vs computation per mode:

- **`static`** (Gas Town convoy, CrewAI crew): adaptor provides the member list at registration; updates via adaptor API. UI: list view with add/remove (if mutation declared).
- **`pool`** (Gas Town worker pool, Gas City `[agents.pool]`): adaptor provides a `check_endpoint` (opaque to Gemba — adaptor calls it). UI polls on a schedule and displays live count vs. min/max. RFC's elastic-pool visualization (RFC §New surfaces) reads this.
- **`graph`** (LangGraph subgraph, ADK hierarchy): adaptor resolves current members on request; the internal topology is opaque to v1 (§DD-7 tradeoff).

**Multi-group-per-repo:** A repository can participate in arbitrarily many groups simultaneously (RFC: "convoys per RFC" — one repo may have multiple convoys active). Stored as `AgentGroup[]` keyed by `scope.repository_refs`.

**Multi-repo groups:** Permitted in the type, deferred in the UI for v1 (DD-10). `scope.repository_refs` can carry >1 entry; v1 UI filters to the primary.

**Nested groups, ephemeral vs persistent:** Out of scope for v1 (DD-7).

**Backend mapping:**

| Backend | `mode` | Notes |
|---|---|---|
| Gas Town convoy | `static` | Members enumerated in convoy config |
| Gas Town worker pool | `pool` | `check_endpoint` wraps the shell `check` command |
| Gas City `[agents.pool]` | `pool` | Native |
| CrewAI Crew | `static` | Agents enumerated in Crew |
| CrewAI Flow | `graph` | Topology = Flow graph |
| LangGraph StateGraph subgraph | `graph` | Topology = subgraph |
| Claude Code Agent Teams | `static` | Team membership dynamic but adaptor snapshots it |
| ADK agent hierarchy | `graph` | Parent-child tree |

### 3.3 Workspace/isolation contract

Per DD-5.

**Minimum viable isolation guarantee:** Every workspace MUST provide `fs_scoped: true` — writes within the workspace's scope do not escape to corrupt other concurrent assignments' workspaces. Implementation varies (worktree, container, VM).

**Capability declaration (on registration):**

```typescript
interface OrchestrationCapabilityManifest {
  workspace_kinds_supported: WorkspaceKind[];
  default_workspace_kind: WorkspaceKind;
  per_kind_isolation: Record<WorkspaceKind, IsolationCapabilities>;
  // ... (other fields §3.7)
}
```

**Negotiation:** Gemba's assignment request carries a *preferred* `workspace_kind` and a set of *required* isolation flags. Adaptor picks the weakest supported kind that satisfies requirements; errors if none.

```typescript
interface WorkspaceRequest {
  assignment_id: string;
  repository: RepositoryRef;
  preferred_kind?: WorkspaceKind;
  required_isolation: Partial<IsolationCapabilities>;  // all-true subset of fields that MUST be honored
}

// Adaptor methods
acquire_workspace(req: WorkspaceRequest, ctx: CallCtx): Promise<Workspace>;
release_workspace(id: string, ctx: CallCtx): Promise<void>;
inspect_workspace(id: string, ctx: CallCtx): Promise<WorkspaceStatus>;
```

### 3.4 Assignment protocol

**Three assignment strategies observed (D6):**

- **Push** (human/Mayor pushes work to agent): explicit `assign(workitem_id, agent_id)` call.
- **Pull** (agent fetches from shared queue): agent calls `claim_next_ready(filter)`; Gemba issues a reservation.
- **Hook** (event-driven): on state transition (e.g., `Unstarted → Started`), adaptor invokes configured side-effect (Gas Town's hook model, GitHub issue-assigned webhook).

**Canonical:** **pull**, with push and hook as adaptor-supported alternatives. Rationale: C6 (shared state over P2P) + RFC's ZFC principle — the UI should expose "here are N ready items, N agents with free capacity" and let the operator (or Mayor agent) drive. Push is available for workflows that need it; hook is available because Gas Town depends on it.

**Interaction with WorkPlane state transitions:**

1. OrchestrationPlane's `claim_next_ready` returns a candidate WorkItem and opens a reservation.
2. Gemba calls `WorkPlane.claim(workitem_id, agent_id, nonce)` — atomic.
3. On success: Gemba calls `WorkPlane.transition(workitem_id, preferred_state_for(Started), nonce)`.
4. Gemba creates `Assignment` (`status: active`), acquires `Workspace`, starts `Session`.
5. On failure at step 2: OrchestrationPlane releases reservation (adaptor API); try the next candidate.

**Gas Town hook pattern as one strategy:** The Gas Town adaptor implements step 1 by tailing Beads via `bd ready`; steps 2–5 run through the generic pipeline. Gas Town's tmux-session spawning is step 4's workspace acquire.

### 3.5 Merge and conflict coordination

**Branch-per-agent defaults:** Every `Workspace` with a git-based scope gets a branch `bc/{agent_id}/{workitem_id}` by default. Agents commit there. On DoD-complete, Gemba surfaces "integrate" as an action which opens a PR via the WorkPlane's evidence linkage.

**Merge queue semantics:** Gemba does not ship a merge queue in v1 (that's the CI provider's job — GitHub Merge Queue, Graphite, etc.). Gemba surfaces *queue status* via evidence (`Evidence{type: "ci_run"}` plus adaptor-declared status).

**Cross-item conflict signalling:** When two active assignments touch overlapping files, the OrchestrationPlane adaptor MAY emit an `OrchestrationEvent{kind: "potential_conflict", a: assignment_id, b: assignment_id, reason: string}`. Gemba renders as an escalation (DD-6). Detection is best-effort; Gas Town doesn't do it today (Phase 1 observation) so the Gas Town adaptor declares this capability off.

**Human escalation on auto-resolution failure:** Creates an `EscalationRequest{source: "orchestrator_pause", urgency: "blocking"}`.

### 3.6 Traceability (linkage pair)

Work item ↔ commit/PR. Evidence is the join. Human confirmation of close is a standard event (§4.4), not a distinct record type.

**Orchestrator emits Evidence to WorkPlane:** On session events (commit, PR open, test run), the OrchestrationPlane adaptor SHOULD call `WorkPlane.attach_evidence(workitem_id, evidence)`. The adaptor is the integration author; it knows which events map to which evidence types.

**Adaptor gap-filling:** Per C5, most trackers don't store evidence natively. Per DD-13, the WorkPlane adaptor synthesizes (from git log, GitHub PR API, CI providers) when the OrchestrationPlane doesn't push. Both sources tag `producer`; consumers disambiguate.

Per DD-3, there is no `ProofOfDoD` record. DoD is informational free-text; close is a single path; traceability terminates at the human or agent who performed the close transition (captured in the standard event stream).

### 3.7 Adaptor interface (`OrchestrationPlane`)

```typescript
interface OrchestrationPlaneAdaptor {
  describe(): OrchestrationCapabilityManifest;

  // Agents
  list_agents(filter: AgentFilter, ctx: CallCtx): Promise<Agent[]>;
  read_agent(id: string, ctx: CallCtx): Promise<Agent | null>;

  // Groups
  list_groups(ctx: CallCtx): Promise<AgentGroup[]>;
  resolve_group_members(group_id: string, ctx: CallCtx): Promise<Agent[]>;

  // Assignment lifecycle
  claim_next_ready(filter: ReadyFilter, claimant: AgentRef, ctx: CallCtx): Promise<Reservation | null>;
  release_reservation(reservation_id: string, ctx: CallCtx): Promise<void>;
  start_session(assignment_id: string, prompt: SessionPrompt, ctx: CallCtx): Promise<Session>;
  pause_session(session_id: string, nonce: ConfirmNonce, ctx: CallCtx): Promise<Session>;
  resume_session(session_id: string, nonce: ConfirmNonce, ctx: CallCtx): Promise<Session>;
  end_session(session_id: string, mode: "completed" | "failed" | "canceled", nonce: ConfirmNonce, ctx: CallCtx): Promise<Session>;
  peek_session(session_id: string, ctx: CallCtx): Promise<SessionPeek>;

  // Workspaces (§3.3)
  acquire_workspace(req: WorkspaceRequest, ctx: CallCtx): Promise<Workspace>;
  release_workspace(id: string, ctx: CallCtx): Promise<void>;
  inspect_workspace(id: string, ctx: CallCtx): Promise<WorkspaceStatus>;

  // Escalations
  list_open_escalations(filter: EscalationFilter, ctx: CallCtx): Promise<EscalationRequest[]>;
  resolve_escalation(id: string, resolution: EscalationResolution, nonce: ConfirmNonce, ctx: CallCtx): Promise<EscalationRequest>;

  // Events
  subscribe(filter: OrchestrationSubscribeFilter, ctx: CallCtx): AsyncIterable<OrchestrationEvent>;
}
```

`OrchestrationCapabilityManifest` (superset of the workspace parts already shown):

```typescript
interface OrchestrationCapabilityManifest {
  adaptor_id: string;
  adaptor_version: string;
  orchestration_api_version: "1.0";
  workspace_kinds_supported: WorkspaceKind[];
  default_workspace_kind: WorkspaceKind;
  per_kind_isolation: Record<WorkspaceKind, IsolationCapabilities>;
  grouping_modes_supported: Array<"static" | "pool" | "graph">;
  assignment_strategies_supported: Array<"push" | "pull" | "hook">;
  escalation_sources_emitted: string[];       // e.g., ["mcp_elicitation", "permission_prompt"]
  cost_axes_emitted: Array<"tokens" | "wallclock" | "dollars_native">;
  native_cost_unit?: string;                  // e.g., "ACU" (Devin)
  native_cost_to_dollars_rate?: number;       // Configurable; see DD-4
  mcp_endpoint?: string;                      // DD-8
  event_delivery: "sse" | "push" | "poll";
  auth_model: "delegated_oauth" | "service_principal" | "local_cli";
}
```

### 3.8 Conformance test suite (`OrchestrationPlane`)

**Group A — Agents & groups**

1. `list_agents_returns_declared_capabilities`: Each agent's `capabilities[]` matches manifest's declarations.
2. `group_member_resolution`: For each declared group, `resolve_group_members` returns `Agent[]` whose `id`s are present in `list_agents`.
3. `pool_group_honors_check_endpoint`: For a `pool` group, calling `resolve_group_members` twice across a simulated scale event returns different counts.
4. `graph_group_opaque_but_stable`: A `graph` group's member set is stable across calls when the underlying topology is unchanged.

**Group B — Assignment lifecycle**

1. `claim_next_ready_reserves`: Two concurrent `claim_next_ready` calls return two different reservations or one + `null`.
2. `reservation_expires`: Reservation not converted to assignment within TTL auto-releases.
3. `start_session_requires_assignment`: Starting a session without a valid assignment id errors.
4. `end_session_idempotent`: Ending a session twice with same nonce: second is a no-op.
5. `session_peek_during_running`: `peek_session` during `running` returns non-empty transcript / state.

**Group C — Workspace isolation**

1. `acquire_fs_scoped_honored`: Write in one acquired workspace does not appear in another concurrently acquired workspace against the same repo.
2. `release_is_idempotent`: Releasing twice is a no-op; inspect after release returns `status: released`.
3. `required_isolation_honored`: Request with `required_isolation.net_isolated=true` is rejected if no supported kind satisfies it.
4. `default_workspace_kind_used_when_unspecified`: Request without `preferred_kind` acquires the declared default.

**Group D — Escalations**

1. `escalation_emits_on_declared_source`: For each source in `escalation_sources_emitted`, simulate; `list_open_escalations` returns the request.
2. `resolve_escalation_unblocks_session`: `blocking` escalation resolved with `approve`; associated session transitions from `input_required` → `running`.
3. `escalation_deadline_expires`: Request with past deadline auto-transitions to `expired` state; resolution attempts fail.

**Group E — Events**

1. `event_on_session_transition`: Session state transitions fire an event with `{before, after}`.
2. `event_on_cost_sample`: Cost samples emit as events (even if batched) — consumer can reconstruct the sample stream.
3. `event_ordering_across_assignment`: For one assignment, events arrive in causal order.

**Group F — MCP contract (if declared)**

1. `mcp_endpoint_reachable`: The declared `mcp_endpoint` responds to `initialize`.
2. `mcp_tools_include_escalation_ack`: Tools include one for acknowledging an escalation.

---

## 4. Cross-cutting design

### 4.1 Definition-of-Done schema (per DD-3)

**Informational-only.** v1 defers DoD enforcement until industry consensus on completion semantics emerges. The schema here is the display contract; it carries no machine-check semantics and never gates state transitions.

**Minimal schema:**

```json
{
  "$schema": "https://gemba.dev/schemas/dod/1.0.json",
  "version": "1.0",
  "acceptance_criteria": "Users can click 'Export CSV' on the Work Grid and receive a file containing all currently-filtered rows.",
  "notes": "Edge case: empty result set should still download a header-only CSV."
}
```

Both `acceptance_criteria` and `notes` are optional free-text (Markdown permitted). `version` is required so that a future enforcement schema (`2.0`) can be introduced as an opt-in capability without breaking existing deployments.

**Adaptor pass-through (where the text lives in each backend):**

| Backend | Native field used for `acceptance_criteria` |
|---|---|
| Beads | New `acceptance_criteria` field on the bead (adaptor writes via `bd` CLI) |
| Jira | `Acceptance Criteria` custom field if present; else a delimited section in `description` |
| Linear | The `Acceptance Criteria` custom field (commonly configured) |
| GitHub Issues | A delimited `## Acceptance Criteria` section in the issue body |
| Gas Town / Gas City | Same as Beads (Beads is the WorkPlane) |

Adaptors MUST preserve text round-trip byte-for-byte when read back in the same session; they MAY normalize line endings on cross-session reads.

**No evaluation, no predicate registry, no scheduling.** There is nothing to run.

**When DD-3 re-opens:** A future `schema_version: "2.0"` will be introduced as an opt-in capability if and when industry consensus on completion semantics emerges. Existing deployments carrying `version: "1.0"` continue to function unchanged; the informational schema is forward-compatible by design (any 2.0 fields are additive).

### 4.2 Cost and budget accounting (per DD-4)

**Unit model (canonical):**

```typescript
interface CostMeter {
  tokens_total: number;       // input + output across all providers
  tokens_input?: number;      // optional breakdown
  tokens_output?: number;
  wallclock_seconds: number;
  dollars_est: number;        // Per DD-4: "≈$" in the UI
  native_units?: { unit: string; amount: number };  // e.g., {unit: "ACU", amount: 1.5}
  samples?: CostSample[];     // Optional raw stream
}

interface CostSample {
  at: string;
  dtokens?: number;
  dwallclock?: number;
  ddollars_est?: number;
  source: "session" | "evidence_attach" | "orchestrator_cron";
}
```

**Collection:** OrchestrationPlane adaptor emits `CostSample` on `Session` events (start, periodic, end) and optionally after each tool call. Gemba aggregates.

**Aggregation rollup:**

- Per `Assignment`: sum of samples for that assignment's session(s).
- Per `WorkItem`: sum of all `Assignment.cost_meter` values across the item's history.
- Per `Agent`: sum across all assignments for that agent over a time window.
- Per `AgentGroup`: sum of members' costs in scope.
- Per `Epic`: sum of all descendants via `parent_of` walk. **This sum is what `TokenBudget.consumed` reflects for the epic's budget (DD-14).**
- Per `Sprint`: sum of member epics' consumption. **This sum is what `TokenBudget.consumed` reflects for the sprint's budget (DD-14).**

**Display and enforcement primitives (per DD-14):**

- **`TokenBudget`** (§2.1.8) is the v1 enforced primitive, attached to **epics** and **sprints** only. It carries inform/warn/stop thresholds and is denominated in tokens.
- **Three-tier enforcement:**
  - `inform` crossing → card badge (colour A) + insights-panel event; no operator action.
  - `warn` crossing → card badge (colour B) + `EscalationRequest{kind: "budget_warn"}` landing in `/escalations` (DD-6); event stream emits `budget.warn`.
  - `stop` crossing → new-spend mutations rejected unless request carries `X-GEMBA-Confirm` nonce with `budget_override: true` (RFC §Locked 7). Existing in-flight agents are *not* killed; `stop` is mutation-gating.
- **Rollup direction:** leaf `CostSample` → `WorkItem.cost_meter` → epic's `TokenBudget.consumed` → sprint's `TokenBudget.consumed`. All rollups computed at read time.
- **Cross-axis display:** Even though only tokens are enforced, the UI renders `wallclock_seconds` and `dollars_est` alongside for context. `dollars_est` rollup specifically helps operators spot when a token budget is being consumed by expensive-tier models (Opus vs. Haiku — see DD-14 tradeoff).
- **Non-token budgets** (`dollars_est` budgets, wallclock budgets): not enforced in v1; the RFC's insights panel renders them but they do not gate mutations.
- RFC's insights panel (RFC §New surfaces) reads per-rig / per-convoy rollups from this infrastructure.

### 4.3 Human escalation (per DD-6)

**Unified schema:** §3.1.7 above.

**Surface mappings:**

| Source | Mapping |
|---|---|
| MCP `elicitation/create` (rev 2025-06-18) | `EscalationRequest{source: "mcp_elicitation", schema: from message}` |
| A2A `task.state = input-required` | `EscalationRequest{source: "a2a_input_required", urgency: "blocking"}` |
| Claude Code permission prompt | `EscalationRequest{source: "permission_prompt", options: ["approve", "deny"]}` |
| Microsoft Agent Framework HITL approval | `EscalationRequest{source: "hitl_approval"}` |
| CrewAI flow pause | `EscalationRequest{source: "orchestrator_pause"}` |
| Devin waiting in VM (ad-hoc) | `EscalationRequest{source: "orchestrator_pause", urgency: "advisory"}` |

**UI treatment (recommendation):**

- **Card badge**: every WorkItem with an open escalation shows a badge on its Kanban card with the escalation count.
- **Inbox surface at `/escalations`**: dedicated page with filter chips (urgency, source, agent, repo). Replaces the concept of a "human TODO list" that several products ship ad hoc.
- **Convoy Kanban overlay**: when any card in the current view has an open `blocking` escalation, the board top-bar shows a persistent dismissible banner with "N blocking escalations" linking to the inbox.
- **Keyboard-first**: `cmdk` palette action "go to oldest open escalation."

**Resolution flow:**

```
open --(approve|deny|modify|defer)--> resolved
open --(deadline passes)--> expired
open --(workitem_id closed)--> canceled
```

Each resolution writes a nonce-gated mutation (RFC §Locked 6). `modify` requires a value matching the request's `schema`; `defer` reschedules with a later `deadline`.

### 4.4 Observability and telemetry

**Event schema (adaptor-agnostic):**

```typescript
interface GembaEvent {
  event_id: string;
  at: string;
  kind: string;                // "workitem.state_changed" | "session.started" | ...
  source: "workplane" | "orchestration" | "gemba";
  actor?: AgentRef | HumanRef;
  workitem_id?: WorkItemId;
  assignment_id?: string;
  session_id?: string;
  escalation_id?: string;
  before?: unknown;
  after?: unknown;
  trace_id?: string;           // W3C trace context (OTEL)
  span_id?: string;
  extension?: Record<string, unknown>;
}
```

**Trace correlation (OTEL):** Every adaptor call inherits/creates a `trace_id`. The Gemba server exposes an OTEL exporter endpoint (configurable); adaptors SHOULD forward traces.

**Metrics that matter (RFC §Retro):**

- `workitem.state_duration_seconds{from_category, to_category}` — time in each category
- `assignment.total_cost_dollars` — ties RFC insights panel
- `escalation.open_count{urgency, source}` — tracks unresolved HITL load
- `session.spawn_rate` / `session.completion_rate`
- `workspace.acquire_latency_seconds{kind}`
- `bd_stats`-compatible export for Gas Town users

### 4.5 Identity, auth, and tenancy

**Gemba identity model:** An authenticated caller has a `BCIdentity`:

```typescript
type BCIdentity =
  | { kind: "human"; user_id: string; display_name: string; email?: string; oidc_sub?: string }
  | { kind: "agent"; agent_id: string; display_name: string; role: string };  // for MCP/A2A calls from agents

interface Session_BC {
  identity: BCIdentity;
  token_id: string;
  expires_at: string;
  scopes: string[];              // capability-level scoping (DD-12 out-of-scope for v1 — v1 = "all")
}
```

**Federation to adaptors (per DD-1):** On each adaptor call, Gemba includes the caller's `BCIdentity`. The adaptor's `resolve_assignee` (for WorkPlane) or parallel method maps to the backend's identity. Auth modes: `delegated_oauth` (caller's token forwarded), `service_principal` (Gemba's token, audit-stamped with caller), `local_cli` (Gemba invokes `bd`/`gt` CLI on behalf; caller recorded in commit/author).

**Permission model (RFC §Locked 6):** Every mutation requires `X-GEMBA-Confirm` nonce header. Server mints nonce per-mutation-request (expiring), confirms exactly-once, rejects replay. `--dangerously-skip-permissions` session flag disables for interactive power use.

### 4.6 Capability negotiation and versioning

**Registration flow:**

1. Adaptor binary/process starts.
2. Gemba calls `describe()` on each adaptor.
3. Gemba validates the manifest against its expected API version (`workplane_api_version` / `orchestration_api_version`).
4. UI reads manifest on render; unsupported capabilities hidden (no errors — graceful degradation per DD-12).

**Version negotiation:**

- API versions are semver-like but add-only (`1.0`, `1.1`, `2.0`).
- Minor version bumps introduce optional capabilities; unchanged contract holds.
- Major version bumps (`2.0`) are breaking; adaptors declare the versions they support; Gemba negotiates the highest mutually-supported.

**Graceful degradation:**

- Missing capability → UI control hidden (e.g., no "reopen" button if `can_reopen_from_completed` not declared).
- Adaptor returns `UnsupportedCapabilityError` for any call that *would* require an undeclared capability (defense in depth).
- Insights panel auto-removes metrics that require missing capabilities.

---

## 5. Reference adaptor sketches

### 5.1 WorkPlane adaptors

#### 5.1.1 Beads adaptor (current system)

**Term-for-term mapping:**

| Gemba core | Beads |
|---|---|
| `WorkItem.id` | bead id (`gt-abc12`) |
| `WorkItem.local_title` | bead title |
| `WorkItem.type` | bead type (task, bug → direct; epic/story synthesized from parent/type) |
| `WorkItem.state_category` | derived from bead status (`open → Unstarted`, `in_progress → Started`, `closed → Completed`) |
| `WorkItem.state` | bead status (`open`, `in_progress`, `closed`) |
| `WorkItem.assignee` | bead `claim` field (single; `AgentRef`) |
| `WorkItem.parent_id` | `parent-child` edge |
| `Relationship{type: "blocks"}` | `blocks` edge |
| `Relationship{type: "relates_to"}` | `related` edge |
| `Relationship{extension_type: "beads.discovered_from"}` | `discovered-from` |
| `Relationship{extension_type: "beads.waits_for"}` + dual `blocks` | `waits-for` |
| `Relationship{extension_type: "beads.replies_to"}` | `replies-to` |
| `Relationship{extension_type: "beads.conditional_blocks"}` | `conditional-blocks` |
| `Evidence` | agent work history rows + Dolt commit SHAs + `bd remember` notes |

**Extension fields the adaptor needs:** `beads.priority` (P0-P3), `beads.labels` (`surface:*`, `tier:*`, `risk:*`, `fed:*`, `provider:*`), `beads.dolt_ref` (commit hash), `beads.bd_remember_ids`.

**Gaps the adaptor must synthesize:**

- **DoD** (per DD-3): adaptor maps `dod.acceptance_criteria` and `dod.notes` to a new `acceptance_criteria` free-text field on the bead. Written/read via `bd` CLI; no Dolt schema changes beyond the single new field; RFC §Locked 7 honored.
- **Epic type**: Beads lacks a native epic type; adaptor infers from `parent-child` depth (root of tree = epic) or from a `beads.type_hint = "epic"` label.
- **Evidence linkage**: Beads has work-history tables; adaptor reads and emits `Evidence`. Synthesizes `Evidence{type: "commit"}` from Dolt refs tagged `synthesized: true` per DD-13.

**Known impedance mismatches:**

- Beads uses `bd` CLI (not HTTP). Adaptor shells out. Per RFC §Locked 7, never writes Dolt directly.
- Beads has 7 edges; core has 3. Dep-graph view shows all 7 via relationship_extensions (RFC §New surfaces).
- Dolt "fragility" (per `/Users/mikebengtson/gt/CLAUDE.md`): adaptor must detect Dolt hangs and surface as `OrchestrationEvent{kind: "adaptor_degraded"}`.

#### 5.1.2 Jira adaptor (the hardest tracker)

**Term-for-term mapping:**

| Gemba core | Jira |
|---|---|
| `WorkItem.id` | Issue key (`PROJ-123`) |
| `WorkItem.local_title` | Summary |
| `WorkItem.type` | Issue Type (epic → `epic`, story → `story`, task → `task`, bug → `bug`, sub_task → `sub-task`, spike → declared extension type, chore → declared extension type) |
| `WorkItem.state_category` | mapped from workflow status category (`To Do` → Unstarted, `In Progress` → Started, `Done` → Completed; `Canceled/Won't Do` → Canceled; others declared) |
| `WorkItem.state` | workflow status name |
| `WorkItem.assignee` | Assignee user (single) |
| `WorkItem.parent_id` | Parent field (unified, post-Oct 2023) |
| `Relationship{type: "blocks"}` | `blocks` / `is blocked by` issue links |
| `Relationship{type: "relates_to"}` | `relates to` |
| `Relationship{extension_type: "jira.duplicates"}` | `duplicates` / `is duplicated by` |
| `Relationship{extension_type: "jira.clones"}` | `clones` / `is cloned by` |
| `Relationship{extension_type: "jira.causes"}` | `causes` / `is caused by` |
| `Evidence` | Development panel + Smart Commits |

**Extension fields needed:** `jira.project_key`, `jira.components`, `jira.labels`, `jira.fix_versions`, `jira.affects_versions`, `jira.priority`, `jira.epic_name`, `jira.sprint`, `jira.rank`, plus every configured custom field (schema-discovered at registration).

**Gaps the adaptor must synthesize:**

- **Agent concept (D4)**: Jira has only bot users. Adaptor uses a custom field `bc.agent_role`, `bc.parent_agent` populated on write; reconstructs `AgentRef` on read. If the field is missing, returns `HumanRef`.
- **DoD (DD-3)**: Adaptor maps `dod.acceptance_criteria` to whichever free-text field the Jira instance uses for acceptance criteria (a common `Acceptance Criteria` custom field if present; otherwise a delimited section in `description`). No structured custom field, no predicate evaluation — DoD is informational-only per DD-3.

**Known impedance mismatches:**

- **Workflow FSM (D3)**: Jira allows/denies transitions via its workflow. Adaptor populates `state_map.valid_transitions` from the Jira workflow API on registration and on periodic refresh. Gemba UI disables invalid targets.
- **Hierarchy depth (D2)**: Jira standard hierarchy is Epic > Story > Sub-task (3 levels); Premium Plans add higher. Adaptor declares `max_hierarchy_depth = 3` by default; higher tier bumps.
- **API rate limits**: Jira has strict limits; adaptor implements request coalescing + event-driven subscribe via webhooks (the only sensible pattern).
- **Multi-assignee (none)**: Jira is single-assignee; core matches.
- **Sprint/Cycle concept**: Jira has Sprints; not in core. Surfaced via extension `jira.sprint`.

### 5.2 OrchestrationPlane adaptors

#### 5.2.1 Gas Town adaptor

**Term-for-term:**

| BC core | Gas Town |
|---|---|
| `Agent` | Gas Town agent identity (persistent) |
| `Session` | Gas Town session (tmux process, ephemeral) |
| `Workspace{kind: "worktree"}` | Rig (worktree + tmux session) |
| `AgentGroup{mode: "static"}` | Convoy |
| `AgentGroup{mode: "pool"}` | Worker pool (e.g., polecat pool via `check` command) |
| `EscalationRequest{source: "orchestrator_pause"}` | Gas Town escalation (`gt escalate`) |
| `Assignment` | Bead claim + rig assignment |

**Extension fields:** `gastown.role` (Mayor, Deacon, Witness, worker roles), `gastown.rig_path`, `gastown.tmux_session_name`, `gastown.mail_thread_id`, `gastown.formula_id`, `gastown.molecule_step`.

**Gaps to synthesize:**

- **Cost meter (DD-4)**: Gas Town does not meter by default. Adaptor reads tmux + process telemetry; wraps Claude Code / Codex / Gemini invocations with a token counter. Falls back to `wallclock_seconds`-only when token data unavailable. Adaptor declares `cost_axes_emitted: ["wallclock", "tokens"]` (tokens best-effort).
- **Session peek**: Implemented via tmux capture-pane. Adaptor converts to `SessionPeek.transcript`.
- **MCP endpoint (DD-8)**: Gas Town is not natively MCP. Adaptor *itself* exposes an MCP server fronting Gas Town's shell command interface.

**Known impedance mismatches:**

- **Dolt fragility** (`/Users/mikebengtson/gt/CLAUDE.md`): adaptor must detect and signal via `OrchestrationEvent{kind: "adaptor_degraded"}`.
- **No cross-worktree conflict detection** (C7-limitation Phase 1): adaptor declares the corresponding capability off; Gemba hides conflict escalations for Gas Town.
- **Hook-based assignment**: Gas Town uses hooks; adaptor implements pull by tailing `bd ready` output and wrapping Gas Town hook invocations.

#### 5.2.2 Gas City adaptor (RFC.md anchor)

**Term-for-term (per RFC.md):**

| BC core | Gas City |
|---|---|
| `Agent` | `[[agents]]` entry |
| `Workspace.kind` | provider kind (tmux / subprocess / k8s / exec) |
| `AgentGroup{mode: "pool"}` | `[agents.pool]` with `check` command |
| `EscalationRequest` | TBD; probably via `gc escalate` analogue |
| Declared vs observed state | `city.toml` vs `.gc/agents/` (RFC §Why another UI) |

**Extension fields:** `gascity.pack_name`, `gascity.provider`, `gascity.level` (progressive capability level), `gascity.city_id`.

**Gaps / unknowns:**

- **`city.toml` spec**: not public as of Phase 1 (§6). Adaptor interface stubbed to read `city.toml`; field schema resolved when spec lands.
- **Escalation mechanism in Gas City**: unknown (landscape.md §6 explicitly asks this of the Gas City team in RFC §What I'm asking for).
- **Reconciliation API**: unknown — does `gc` have a reconcile verb? Adaptor declares the capability as unknown and falls back to drift-display-only until confirmed.

**Impedance mismatches:**

- **Declarative-vs-imperative**: Gas Town is imperative, Gas City is declarative. The adaptor speaks both idioms; the UI (per RFC §Stability posture) renders "desired-vs-actual" against Gas City and "implicit-desired" against Gas Town. This is invisible to the core abstraction.
- **Pack-agnostic UI (RFC §Locked 2)**: agent `role` is free-form string; no core enum.

#### 5.2.3 LangGraph adaptor

**Term-for-term:**

| BC core | LangGraph |
|---|---|
| `Agent` | Node (function, agent, or subgraph) |
| `AgentGroup{mode: "graph"}` | StateGraph subgraph |
| `Session` | Graph execution thread (`thread_id`) |
| `Workspace.kind` | Whatever the user's tool calls require (LangGraph is fs-agnostic; adaptor declares `exec` as default) |
| Checkpoints | Adaptor maps LangGraph checkpoint → `Session.status == "suspended"` + resume via `resume_session` |
| HITL (interrupt) | `EscalationRequest{source: "orchestrator_pause", urgency: "blocking"}` |

**Extension fields:** `langgraph.checkpoint_id`, `langgraph.state_schema_ref`, `langgraph.thread_id`, `langgraph.node_name`.

**Gaps to synthesize:**

- **Work-item concept**: LangGraph has no work-item. Gemba WorkItems come from the paired WorkPlane adaptor; LangGraph sessions are bound to them via `Assignment`.
- **Cost meter (DD-4)**: LangSmith traces carry token counts; adaptor pulls these for `cost_samples`.
- **Isolation**: LangGraph itself isolates nothing. Adaptor declares `workspace_kinds_supported: ["exec"]` and documents that user-provided tools are responsible for fs scoping. Aggressive users can wrap LangGraph with Docker and declare `container`.

**Impedance mismatches:**

- **Graph topology opaque in v1 (DD-7)**: the UI won't render LangGraph's internal graph. A follow-on feature in a future milestone could fetch the StateGraph definition and render it, gated on adaptor declaring `can_expose_topology`.
- **Persistent identity per node**: LangGraph nodes are functions, not persistent identities. Adaptor synthesizes `Agent.id` from node path; sessions become ephemeral thread-scoped.

---

## 6. Risks, open questions, what Phase 3 must address

### 6.1 Unresolved design questions

- **When DD-3 re-opens**: DD-3 is intentionally deferred until industry consensus on completion semantics emerges. The question is not *whether* to re-open but *when* the signal to re-open arrives (a widely-adopted tracker-neutral standard, deployed-user demand, or a clear Anthropic/industry RFC). Phase 3 does not need to answer this; it needs to not close the door on it (version field carried in the `1.0` schema is the door).
- **Gas City API surface**: Adaptor sketch (§5.2.2) is speculative. Phase 3 must engage the Gas City team (RFC §What I'm asking for #1) to finalize.
- **MCP elicitation schema stability**: Phase 1 notes MCP elicitation is still "marked draft" (D11). The `EscalationRequest.schema` field may need schema migrations as the MCP spec stabilizes.
- **A2A AP2 (Agent Payments Protocol) integration**: Out of scope for v1 but touches DD-4 (cost). If agents transact in AP2, the cost meter needs a fourth axis.
- **Rate-limit behavior for paged adaptors**: The WorkPlane adaptor interface has no explicit backpressure. Jira + Linear both rate-limit aggressively; conformance group D (events) needs a companion test for "adaptor can survive a rate-limit storm without dropping events."

### 6.2 Places the abstraction may leak

- **`graph` AgentGroup mode (DD-7)**: Opaque in v1, but users *will* want to see LangGraph topology. If they work around by pinning to `static`, we lose the capability-negotiation benefit.
- **Extension channel unboundedness**: `adaptor_extensions` is `Record<string, unknown>`. Adaptors can dump arbitrary JSON in there and leak schema back to the UI. Conformance group F (extension preservation) catches egregious cases but doesn't prevent growth.
- **`workplane_wins` reconciliation (DD-2)**: Factory, Continue, and future products with bidirectional sync will chafe. Our answer is "write an adaptor that hides that fact" — which is exactly where the abstraction could leak performance or correctness.
- **Single-repo WorkItem (DD-10)**: GitHub Projects users with rich multi-repo hierarchies will feel cramped. v1 ships aware of this.
- **Future DoD enforcement schema (DD-3)**: The `1.0` informational schema is opt-out-safe, but when a `2.0` enforcement schema lands it may retroactively pressure `1.0` deployments to migrate. Mitigation: `2.0` is opt-in (capability-gated) and never auto-applied; `1.0` remains a supported schema version indefinitely.

### 6.3 Design calls that would benefit from prototyping before committing

- **`EscalationRequest` UX on the Convoy Kanban (DD-6)**: The "banner + card badge + inbox" triad is a recommendation, not a tested pattern. Prototype on real Gas Town escalation traffic before commit.
- **Cost unit conversion (DD-4)**: The rate-card approach for down-converting ACUs to `dollars_est` might mislead users into thinking the numbers are billing-grade. Prototype the UI treatment of `≈$` to confirm the disclaimer sticks.
- **Adaptor transport choice (DD-8 / DD-15)**: With transport plurality (`api | jsonl | mcp`), each new adaptor chooses the transport it implements. Prototype with Gas Town (`api` wrapping CLI), Beads (`api` or `jsonl`), and a greenfield MCP-native adaptor before the conformance suite is frozen, to ensure the operation set is transport-agnostic in practice.
- **Token-budget rollup cost (DD-14)**: Rollup from leaf `CostSample` → epic → sprint is computed at read time. For large deployments (10K+ WorkItems, 50+ active epics), naive recomputation could be expensive. Prototype an incremental rollup cache before committing to read-time-only.
- **Sprint semantics redefinition risk (DD-14)**: Agile-fluent users expect `sprint.duration` to be the enforced bound. Prototype the Kanban UI treatment ("budget remaining" as primary gauge, "planned duration" as secondary) on real users before commit — if the mental-model friction is higher than expected, we may need a UI-level term other than the word "Sprint" even though the entity retains the name in the data model.

### 6.4 Hand-offs to Phase 3

1. **Pick a reference implementation language/runtime** for the adaptor spec. The pseudo-TypeScript here is for legibility; the actual adaptor library could be Go (matches the `gemba` binary) or a thin Protobuf/JSON schema both sides share.
2. **Finalize `CapabilityManifest` version negotiation protocol** (semver, discovery, registration endpoint).
3. **Implement the Beads adaptor** as the first reference — its 7-to-3 edge fold, DoD as a single new free-text `acceptance_criteria` bead field, and `bd`-CLI-only mutation path will validate the shape.
4. **Draft an RFC to the Gas City team** with the adaptor sketch in §5.2.2 and the specific questions in §6.1.
5. **Write the conformance harness** (groups A–F each) as a runnable CLI so adaptor authors can `gemba adaptor test --workplane ./my-adaptor` and see pass/fail per test.
6. **Specify the `X-GEMBA-Confirm` nonce implementation** (TTL, storage, replay detection) — RFC locked decision #6 is clear on intent but not on mechanism.
7. **Biggest risks** (explicitly, now that DD-3 is deferred): **DD-1 (agent identity federation)**, **DD-12 (capability negotiation over hardcoded feature flags)**, and **DD-14 (Sprint as token-budgeted, mental-model redefinition)**. DD-1 carries the highest cross-adaptor correctness risk — every tracker with a "bot user" primitive (Jira, Linear, GitHub) must losslessly round-trip the richer `AgentRef` shape, and a mis-synthesis silently corrupts agent identity across sessions. DD-12 is the widest blast radius: every UI surface reads capabilities at render time, so a manifest schema mistake in v1 propagates to every adaptor ever written afterward. DD-14 carries user-perception risk — reusing the word "Sprint" while changing its bounding axis from calendar to tokens is an intentional friction that must be validated with real Scrum-fluent operators before the UI surface is frozen. Phase 3 must prototype all three against at least two adaptors/personas each before the contract freezes.

---

## Appendix A: Novel contributions

This design introduces primitives and framings that no surveyed system provides. Each is anchored to the Phase 1 gap it addresses and the design decision that defines it.

### A.1 Genuinely novel to the industry

No surveyed work tracker or agent orchestration system has these. Each fills an explicit Phase 1 gap.

1. **Sprint redefined as token-budget-bounded (not calendar-bounded)** — DD-14. Every surveyed tracker's Sprint/Cycle/Iteration is calendar-bound; no agentic framework has a sprint container at all. Gemba reuses the Agile term but swaps the bounding axis. Calendar duration becomes advisory. Fills the dual gap of "trackers have sprints without cost axis" × "agent frameworks have tokens without sprint container."

2. **`TokenBudget` with three-tier inform/warn/stop enforcement at epic + sprint scope** — DD-14. Threshold crossings emit `budget.inform` / `.warn` / `.stop` events; `stop` gates *mutations* (claim, new assignment, new WorkItem in scope) without killing in-flight agent processes. No surveyed system combines rollup + threshold enforcement + mutation-gating. Addresses Phase 1 gap D9 ("no cross-system cost/budget accounting").

3. **Unified `EscalationRequest` entity** — DD-6. Normalizes MCP elicitation, A2A `input-required`, Claude Code permission prompts, CrewAI HITL, and Microsoft Agent Framework HITL into one schema with a triple UI surface (card badge + `/escalations` inbox + Kanban banner). Phase 1 D11 explicitly noted no unified UX exists.

4. **Agent as a first-class tracker citizen** — DD-1. `AgentRef` carries `{agent_id, role, parent_agent, display_name}`. Every surveyed tracker collapses agents to bot-users; Gas Town invented the richer shape but it hasn't crossed over. Adaptors round-trip through custom fields / labels with a lossy-but-typed mapping. Phase 1 D4 identified this as the biggest impedance mismatch in the domain.

5. **Synthesized-evidence flag** (`Evidence.synthesized: true`) — DD-13. Append-only evidence records may be adaptor-*inferred* from adjacent data (git log, PR APIs, CI status) with an explicit tag so retros distinguish signal from inference. Phase 1: "evidence-backed DoD verification is bespoke everywhere."

6. **Transport-agnostic adaptor conformance across `api | jsonl | mcp`** — DD-15. Industry gravity is MCP-only for new adaptor contracts; Gemba tests the *operations*, not the wire, and runs identical conformance across three transports. No surveyed framework does this.

7. **`AgentGroup` with three declared modes: `static | pool | graph`** — DD-7. Normalizes Gas Town convoys, CrewAI crews, LangGraph subgraphs, and Claude Code Agent Teams into one primitive. Phase 1 gap: "agent-group membership model is immature."

8. **Desired-vs-actual for agent orchestration.** Generalizes Gas City's `city.toml` (declared) vs `.gc/agents/` (observed) pattern into `OrchestrationPlaneAdaptor.declared_state()` vs `observed_state()` for *any* orchestrator. Kubernetes has this for infrastructure; nothing in the agentic landscape before Gemba.

9. **Two-plane formalized contract** (`WorkPlane` + `OrchestrationPlane`) with separate capability manifests, conformance suites, and adaptor registries. Several products pair a tracker with an orchestrator in practice; no one has formalized the two-plane split as a reusable contract.

### A.2 Novel framings of components that exist piecewise elsewhere

10. **`CapabilityManifest` uniformly driving UI rendering** — DD-12. Capability negotiation exists in isolated contexts (MCP capability advertising, Jira API features endpoint); nowhere is the UI layer fully capability-driven with zero hardcoded backend-specific branches. Enforced via a `no-adaptor-name-strings-in-components` snapshot test.

11. **DoD informational-only with versioned forward door** — DD-3. Free-text acceptance criteria are common; what's novel is the explicit *deferral stance* (`version: "1.0"` reserved for non-enforcement; any future `2.0` is opt-in capability-gated). A design pattern for "we're not standardizing this yet, but we're leaving the door open."

12. **Evidence as typed-link collection with adaptor-synthesizable gap-fill.** Phase 1 C5: most trackers link evidence out-of-band via integrations. Gemba makes it a first-class collection AND mandates a shared synthesis library that multiple adaptors use.

13. **`X-GEMBA-Confirm` nonce with typed intent channel** (`budget_override: true`, `force_steal: true`, etc.). The confirmation-nonce pattern is borrowed from Claude Code's `--dangerously-skip-permissions`, but Gemba extends it into a typed intent channel — a single nonce authorizes one specific kind of bypass.

14. **Read-time budget rollup** (leaf `CostSample` → `WorkItem.cost_meter` → `Epic.TokenBudget.consumed` → `Sprint.TokenBudget.consumed`) with memoization. No surveyed system computes a comparable scope rollup; Devin's ACU accounting is per-session, not per-scope.

15. **Reuse-with-redefinition as a design choice.** The decision to keep the word "Sprint" while changing its bounding axis is itself a novel design pattern — preserves human mental load while earning the redefinition through the token-vs-calendar distinction. Most systems either adopt vocabulary verbatim or invent new terms; Gemba does neither.

### A.3 Inherited from the RFC, preserved/generalized by this design

16. **Pack-agnostic UI** — no hardcoded role names, column headers, or panel vocabulary (RFC locked #4). Generalized from pack-specific to adaptor-agnostic.

17. **Confirmation-gated mutation surface** — every state-changing action requires a server-enforced nonce (RFC locked #7). Extended by DD-14's `budget_override` channel.

18. **Data-integrity principle** — never write backend private storage directly; all mutations through adaptor public API (RFC locked #9). Generalized from "never write Dolt/JSONL/`.gt/`/`.gc/`" to "never write any backend's private storage."

### A.4 Count summary

- **9** genuinely novel contributions (no industry precedent)
- **6** novel framings of existing components
- **3** RFC-inherited principles extended by this design

The three most industry-consequential are **A.1.1 (Sprint-as-token-budget)**, **A.1.2 (TokenBudget enforcement scope)**, and **A.1.3 (unified EscalationRequest)** — each fills an explicit Phase 1 gap with a primitive no surveyed system provides.

---

*End of Phase 2 design document.*
