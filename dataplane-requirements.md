# Agentic Data Plane — Foundational Requirements Gap Analysis

**Author:** Polecat rust (gemba_prime)
**Date:** 2026-04-20
**Status:** Design integration — companion to `domain.md`, `landscape.md`, `RFC.md`
**Bead:** gmp-phc

## Purpose

Reconcile Gemba's generalized WorkPlane abstraction against the eight foundational requirements that distinguish an **agentic data plane** — the category of work-coordination system designed (or adapted) for multi-agent AI software-engineering work tied to a Git repository.

The WorkPlane contract was generalized from Beads (the reference implementation). The risk with any generalization is that category-level preconditions silently become treated as "Beads-specific quirks" and are not enforced at the abstraction boundary. This document:

1. Names the category explicitly and fixes its scope (software-engineering agents tied to Git repos).
2. Captures the eight foundational requirements as a **canonical taxonomy** used across `domain.md`, `landscape.md`, `RFC.md`, and the conformance harness.
3. For each requirement, records where it currently appears in our design, whether it's explicit or implicit, and whether it's **WorkPlane-contract-level** (every adaptor MUST meet it) or **adaptor-optional** (advertised via the capability manifest, UI degrades gracefully if absent).
4. Specifies the concrete `WorkPlaneCapabilityManifest` fields and conformance test groups that operationalize the taxonomy.

## Scope

**In scope:** Work-coordination planes designed for or adapted to multi-agent AI software engineering tied to a Git repository.

**Out of scope:** General business workflow (Jira Service Management for IT tickets, Asana for marketing teams, Basecamp for client delivery, enterprise control planes like Kore.ai or Glean). These may satisfy some requirements but not all; they are not the category Gemba optimizes for. They remain supportable as WorkPlane adaptors — they simply fail certain capability bars, and that's a valid outcome (per RFC §What I'm NOT doing).

## Reference systems in the category

| System | Role | Status |
|---|---|---|
| **Beads** | Reference WorkPlane (Dolt-backed, Git-synced JSONL, explicit task graph, multi-agent safe) | Active; current Gemba reference adaptor |
| **AgentHub** | Git DAG + message board; less schemaful, weaker dependency semantics | Active (OpenHands ecosystem) |
| **Ralph** | Git + per-iteration progress files; linear, single-agent | Active |
| **Symphony** | `WORKFLOW.md` + per-issue workspace; markdown-centric, weak querying | Active |
| **Raindrop (Liquid Metal)** | Agent-native hosting with unified state; weak on task-graph and Git sync | Emerging |
| **Gastown** | Orchestrator using Beads as data plane | Active |
| **Metaswarm** | Multi-agent platform using Beads memory | Active |

Broader "agentic platforms" (Kore.ai, Glean, enterprise control planes) are SaaS/UI-centric, not VCS-native, and are explicitly **out of scope**.

## The eight foundational requirements

Each requirement is numbered R1–R8. Numbering is **canonical** — do not renumber without user sign-off. The taxonomy is preserved verbatim in `landscape.md` §7, `domain.md` §1.0, and the conformance harness groups.

### R1 — Structured, schemaful agent memory

Tasks/artifacts live in a relational/SQL store (not markdown blobs). Schema encodes status, priority, dependencies, acceptance criteria, discovered-from relationships. Writes go through schema enforcement.

- **Current coverage:** Explicit. `domain.md` §2.1.1 defines `WorkItem` as a typed, schemaful entity; §2.5 mandates that writes go through `WorkPlaneAdaptor.create/update` with typed patches and schema-enforced `field_extensions`.
- **Level:** **WorkPlane-contract.** Every adaptor MUST present a schemaful interface; markdown-only systems (Symphony) can be adapted by synthesizing schema at the adaptor edge, but the contract between Gemba core and the adaptor is always typed.
- **Manifest field:** `schema_enforcement: "native" | "synthesized" | "none"` — `"native"` = backend enforces schema (Beads, Jira, Linear); `"synthesized"` = adaptor enforces schema over an unstructured backend (Symphony, Ralph); `"none"` fails registration.
- **Gap:** None — this is already the implicit core assumption. The manifest field makes it explicit and queryable.

### R2 — Queryable rather than parse-only

Agents issue focused queries ("next ready task", "open bugs in file Y") returning machine-friendly JSON. No HTML/UI payloads on the agent path.

- **Current coverage:** Explicit. `domain.md` §2.5 defines `query(filter, page, ctx): Page<WorkItem>` as a first-class adaptor operation with canonical filter axes (state, state_category, assignee, parent_id, repository, type, relationship, label, extension fields). RFC §TL;DR and §New surfaces reference the "cross-workspace work grid, 10k WorkItems, virtualized" rendering — which requires queryable backends.
- **Level:** **WorkPlane-contract.** An adaptor that can only dump all records and expects Gemba to filter in-process fails at realistic scale.
- **Manifest field:** `query_languages: Set<QueryLanguage>` where `QueryLanguage = "filter-only" | "jsonpath" | "sql-subset" | "graphql"`. Minimum bar: `"filter-only"` (adaptor supports the canonical filter set server-side). Stronger: `"sql-subset"` means the adaptor can answer arbitrary joins (Beads via Dolt).
- **Gap:** None — already implicit. Expose it in the manifest so the UI can offer richer query affordances (advanced filter builder, saved queries) only when supported.

### R3 — Dependency-aware task graph

Dependencies are first-class objects. System must answer `ready-set` and `blocked` queries. Graph must evolve as agents discover new work mid-execution.

- **Current coverage:** Explicit for edges (`domain.md` §2.1.2, §2.4, DD-9). Implicit for `ready-set`/`blocked` queries — the canonical filter set in §2.5 includes "relationship (inbound/outbound of a given type)" but does not name a dedicated `ready` query. `landscape.md` C2/C3 establish parent-child and blocks as near-universal, but the *graph-evolution-mid-execution* property is only called out obliquely in `domain.md` DD-9's "discovered-from" extension mapping.
- **Level:** **WorkPlane-contract** for edge CRUD; **adaptor-optional** for native `ready-set` (adaptor MAY synthesize the query client-side from the edge graph, but "native" support indicates server-side efficiency).
- **Manifest fields:** `dependency_graph_native: boolean` (the backend has first-class dependency edges, not just metadata fields — Beads yes, GitHub approximately, Jira yes, Linear partial, Basecamp no); `ready_set_query: boolean` (stronger — the backend answers "what's ready" as a single query, not a client-side graph walk).
- **Gap to close:** `domain.md` §2.5 should list a `ready_set(filter, ctx)` operation in the WorkPlane interface; adaptors without native support synthesize it from `query` + edge traversal. Conformance group C gains a `ready_set_graph_evolution` test: insert A, insert B with `blocks → A`, verify B is not in ready set; close A, verify B becomes ready within the subscribe-event latency budget.

### R4 — Git-native / versioned transport

State is distributable and versioned alongside code. Branch/merge/history apply to data and code together. No hard SaaS dependency; local + VCS sync.

- **Current coverage:** Partial. DD-15 / DD-8 name `jsonl` as a transport for "disconnected round-trips, air-gapped deployments, and migration bootstrapping" — which covers the *distribute-over-Git* axis. Beads' Dolt remote + `bd dolt push/pull` (called out in `/Users/mikebengtson/gt/CLAUDE.md`) is the reference implementation. But the **category-level assumption that an agentic data plane should version state alongside code** is not named as a design principle in `domain.md` or `RFC.md`.
- **Level:** **Adaptor-optional, but category-defining.** A SaaS-only tracker (Jira Cloud without Data Center, Linear without export) does not satisfy R4. That's an acceptable outcome — such adaptors will fail the `versioning_transport` capability bar, and the UI will surface that to the operator, but they remain loadable for teams that accept the tradeoff.
- **Manifest field:** `versioning_transport: Set<Transport>` where `Transport = "none" | "git" | "dolt" | "jsonl" | "native-sqlite-export"`. Agentic-data-plane-class adaptors MUST declare at least one non-`"none"` value.
- **Gap to close:** `domain.md` §1 gains a category-level preamble ("Agentic data plane: foundational assumptions") that names R4 explicitly. Orchestrators that require R4 (e.g., Gastown, Metaswarm) can reject adaptors whose manifest declares only `"none"`.

### R5 — Multi-agent concurrency and transaction semantics

Many agents writing concurrently, with transactional semantics or VCS primitives to avoid conflicts. Predictable read-after-write at scale (dozens of parallel workers).

- **Current coverage:** Partial. `domain.md` §2.5 specifies idempotency for `transition`, `claim`, `close`, `create`, `attach_evidence` via nonces and idempotency keys; §2.5 "Concurrency" section describes the `claim_race` behavior (one wins, other gets `ConflictError`). Conformance Group B includes `claim_race`, `transition_idempotent`, `nonce_replay_rejected`. But the **scale assumption** (dozens of concurrent writers) is not quantified anywhere.
- **Level:** **WorkPlane-contract.** The idempotency and conflict surface is already contract-level.
- **Manifest field:** `concurrency_model: "none" | "optimistic" | "mvcc" | "git-merge" | "dolt-merge"` — names the primitive the adaptor relies on. `"none"` fails the category bar. Gemba's core mutation protocol works over any non-`"none"` model; the manifest field exists so the conformance harness can tune its race tests (optimistic needs `if_match_updated_at`; git-merge needs simulated concurrent branches).
- **Gap to close:** `domain.md` §2.6 Group B should add a `concurrent_writer_stress` test parameterized by worker count (default 16) — run the `claim_race` pattern at N=16, verify all-but-one get a well-formed `ConflictError` and the winner's state is visible to subsequent reads within the declared event-latency budget. Adaptors whose concurrency model can't survive N=16 fail the stress test (not the baseline conformance).

### R6 — Decoupling of work from any single agent

Work items outlive agent sessions/context windows. Any agent or human can pick up later based on persisted state.

- **Current coverage:** Explicit. `domain.md` DD-2 ("WorkPlane is source of truth; OrchestrationPlane is derivable") and C10 ("identity vs session is near-universal") codify this. Beads' `bd remember` pattern and Gastown's "findings persistence" discipline (session survives code but analysis only survives in bead notes) both demonstrate the principle operationally. `landscape.md` §4's terminology crosswalk separates "Agent" (persistent) from "Session" (ephemeral) for every surveyed agentic system.
- **Level:** **WorkPlane-contract.** A WorkPlane that requires session affinity (work disappears when the session ends) fails the category bar.
- **Manifest field:** `agent_session_decoupling: boolean` — MUST be `true` for agentic-data-plane-class adaptors. Systems where work is intrinsically session-scoped (Ralph's per-iteration progress files, some notebook-based tools) declare `false` and fail registration as agentic-data-plane adaptors (they can still be loaded as read-only views).
- **Gap:** None — already load-bearing in the design. Manifest field formalizes the implicit assumption.

### R7 — Agent-native interfaces and ergonomics

CLI/JSON/API is primary; UI is secondary. Operations vocabulary (list/claim/update/discover/fetch-subgraph) is tuned for agent callers.

- **Current coverage:** Partial. DD-8 / DD-15 establish transport plurality (`api | jsonl | mcp`) which is the *wire-format* axis of R7. The *vocabulary* axis (the adaptor operation names should read like agent-callable verbs) is implicit in §2.5 where methods are named `create`, `read`, `update`, `query`, `transition`, `claim`, `link`, `attach_evidence`, `subscribe` — all agent-idiomatic — but nowhere does the design *state* that agent ergonomics is a first-class constraint.
- **Level:** **Category-defining.** A WorkPlane whose primary interface is a human web UI with an afterthought JSON export fails R7 (Jira Cloud, pre-API-v3 legacy tools). Gemba can still wrap such systems as adaptors but the capability bar surfaces the quality gap.
- **Manifest field:** `agent_native_api: "cli" | "json-api" | "mcp" | "rest-only" | "soap" | "ui-scraping"`. Agentic-data-plane-class adaptors declare `"cli"`, `"json-api"`, or `"mcp"`. `"rest-only"` passes but with a caveat (acceptable for CI-driven use; weaker for interactive agents). `"soap"` / `"ui-scraping"` fail the category bar.
- **Gap to close:** `domain.md` §1 category-level preamble explicitly names R7 as a precondition. RFC's TL;DR already says "Gemba talks to every backend through its public API" — extend that to name agent-native interface as a category assumption, not a convenience.

### R8 — Tight integration with orchestrators and workflows

Plane is the source of truth for "what to do next". Clean separation: specs → tasks in plane → multi-agent execution. Pluggable into orchestrators (Gastown, Metaswarm, Gemba itself).

- **Current coverage:** Explicit for Gemba's own orchestration role (RFC architecture diagram, DD-2). Implicit for third-party orchestrators — `domain.md` §2.5 `subscribe(filter): AsyncIterable<WorkPlaneEvent>` is the primary orchestrator hook, but the design does not enumerate the hook *kinds* needed for the common orchestrator patterns (ready-set polling, event-driven dispatch, claim/release loops, escalation ingest).
- **Level:** **Adaptor-optional at granularity; WorkPlane-contract at baseline.** Every adaptor MUST support `subscribe` (baseline). Specific orchestrator hooks (dispatch-ready-to-pool, claim-atomic, escalation-ingest) are advertised via the manifest.
- **Manifest field:** `orchestrator_hooks: Set<HookKind>` where `HookKind = "ready-set-subscribe" | "claim-atomic" | "escalation-ingest" | "work-complete-ack" | "pool-bulk-dispatch"`. Orchestrators inspect this set to decide whether they can drive the plane natively or must degrade to polling + best-effort.
- **Gap to close:** `domain.md` §3 (Orchestration Plane) gains cross-reference text naming WorkPlane as the source-of-truth for "what to do next" (already in DD-2, reinforce in §3.2 Grouping model). `domain.md` §4.6 capability negotiation section gains an "orchestrator hook kinds" subsection.

## Summary matrix — current coverage per requirement

| Req | Name | In domain.md | In landscape.md | In RFC.md | Contract-level | Manifest field | New test group |
|---|---|---|---|---|---|---|---|
| R1 | Schemaful memory | Explicit (§2.1, §2.5) | Implicit (C1) | Implicit (arch. diagram) | MUST | `schema_enforcement` | — (covered by Group A) |
| R2 | Queryable | Explicit (§2.5) | Partial (C5) | Explicit (TL;DR scale) | MUST | `query_languages` | — (covered by Group A) |
| R3 | Dep-aware graph | Edge explicit (§2.4, DD-9); ready-set implicit | Explicit (C2/C3, Gaps) | Explicit (dep graph view) | Partial | `dependency_graph_native`, `ready_set_query` | **New: `ready_set_graph_evolution`** |
| R4 | Git-native transport | Partial (DD-8/DD-15) | Implicit | Absent | Optional | `versioning_transport` | **New: `versioned_state_round_trip`** |
| R5 | Multi-agent concurrency | Explicit idempotency (§2.5, Group B); scale implicit | Implicit (C6) | Implicit | MUST | `concurrency_model` | **New: `concurrent_writer_stress`** |
| R6 | Session decoupling | Explicit (DD-2, C10) | Explicit (§4 crosswalk) | Implicit | MUST | `agent_session_decoupling` | **New: `session_death_recovery`** |
| R7 | Agent-native interface | Partial (DD-8/DD-15 wire; vocabulary implicit) | Implicit (C8) | Partial (TL;DR) | Category-defining | `agent_native_api` | — (covered by existing transport tests) |
| R8 | Orchestrator integration | Partial (§2.5 subscribe; hook kinds implicit) | Partial (C6) | Explicit (two-plane arch) | Partial | `orchestrator_hooks` | **New: `orchestrator_hook_contract`** |

## Reference implementations — conformance projection

Projection of the taxonomy onto the category's reference implementations. Cells are the **expected** manifest value once each adaptor lands in Gemba. This is projection, not empirical audit — the audit is filed as beads under gm-e6 (Beads adaptor audit) and as future work for the other systems.

| System | R1 schema | R2 query | R3 graph | R4 version-tx | R5 concurrency | R6 decoupling | R7 api | R8 hooks |
|---|---|---|---|---|---|---|---|---|
| **Beads** | native | sql-subset | native + ready | git, dolt, jsonl | dolt-merge | ✓ | cli, json-api | ready-set-subscribe, claim-atomic, escalation-ingest, work-complete-ack |
| **AgentHub** | synthesized | filter-only | partial | git | git-merge | ✓ | cli | ready-set-subscribe (weak) |
| **Ralph** | synthesized | filter-only | none | git | none (single-agent) | ✗ | cli | — |
| **Symphony** | synthesized | filter-only | none | git | none | ✓ | cli (markdown-shaped) | — |
| **Raindrop** | native | filter-only | partial | none (SaaS) | mvcc | ✓ | json-api | — |
| **Gastown** | (uses Beads as WP) | — | — | — | — | — | — | — (it's an orchestrator, not a WP) |
| **Metaswarm** | (uses Beads as WP) | — | — | — | — | — | — | — (orchestrator) |

Observations:
- **Beads** satisfies all eight requirements and is the valid reference adaptor.
- **Ralph** and **Symphony** fail R3 and most of R5 — they are not agentic-data-plane-class. Gemba may still load them as degraded adaptors for specific users (Ralph users who want Gemba's UI over a linear flow), but the capability bars document the limitation.
- **Raindrop** fails R4 (no versioned transport) — SaaS dependency is a category-level gap for it. Capability bar exposes the limitation honestly.
- **Gastown** and **Metaswarm** are orchestrators consuming Beads as their WorkPlane — they are OrchestrationPlane adaptors, not WorkPlane adaptors. Their R8 integration is evaluated at the OrchestrationPlane boundary (outside this doc's scope but linked from `domain.md` §3).

## Concrete manifest expansion (target for gm-e3.2)

Propose the following additions to `WorkPlaneCapabilityManifest` in `domain.md` §2.5:

```typescript
// Agentic data plane category capabilities (R1–R8).
// Each field is derivable from current design + R1–R8 taxonomy.
// Orchestrators can reject adaptors whose declared values don't meet the minimum bar.
interface WorkPlaneCapabilityManifest {
  // ... existing fields (adaptor_id, adaptor_version, workplane_api_version,
  // transport, capabilities, state_map, max_hierarchy_depth,
  // relationship_extensions, field_extensions, event_delivery, auth_model) ...

  // R1 — Structured, schemaful agent memory
  schema_enforcement: "native" | "synthesized";

  // R2 — Queryable interface
  query_languages: Set<"filter-only" | "jsonpath" | "sql-subset" | "graphql">;

  // R3 — Dependency-aware task graph
  dependency_graph_native: boolean;   // edges are first-class
  ready_set_query: boolean;           // stronger: native server-side ready-set

  // R4 — Git-native / versioned transport
  versioning_transport: Set<"none" | "git" | "dolt" | "jsonl" | "native-sqlite-export">;

  // R5 — Multi-agent concurrency
  concurrency_model: "optimistic" | "mvcc" | "git-merge" | "dolt-merge";
  // "none" is not representable here; adaptors with no concurrency primitive
  // fail registration as agentic-data-plane adaptors.

  // R6 — Decoupling of work from any single agent
  agent_session_decoupling: boolean;  // MUST be true for agentic-data-plane class

  // R7 — Agent-native interfaces and ergonomics
  agent_native_api: "cli" | "json-api" | "mcp" | "rest-only";
  // "soap" and "ui-scraping" are not representable — they fail the category bar.

  // R8 — Orchestrator integration hooks
  orchestrator_hooks: Set<
    | "ready-set-subscribe"
    | "claim-atomic"
    | "escalation-ingest"
    | "work-complete-ack"
    | "pool-bulk-dispatch"
  >;
}
```

**Minimum bar for agentic-data-plane class:** `schema_enforcement != null`, `query_languages` non-empty, `dependency_graph_native == true`, `versioning_transport` contains at least one non-`"none"` value, `concurrency_model` non-null, `agent_session_decoupling == true`, `agent_native_api ∈ {"cli", "json-api", "mcp"}`, `orchestrator_hooks` non-empty.

Adaptors failing this bar may still register but the UI surfaces a "reduced-capability" indicator and orchestrators that require the full bar (Gastown, Metaswarm) can refuse to bind.

## Conformance test groups (target for gm-e3.5)

`gemba adaptor test` gains one test group per requirement. Capability-gated: skipped (not failed) when the manifest doesn't advertise the capability.

| Group | Req | New tests (added to existing Groups A–F) |
|---|---|---|
| **G — Dep graph evolution** | R3 | `ready_set_graph_evolution`, `discovered_from_mid_execution` |
| **H — Versioned transport** | R4 | `versioned_state_round_trip`, `branch_merge_round_trip` (Dolt/Git adaptors only), `jsonl_export_import_round_trip` (jsonl-declared adaptors only) |
| **I — Concurrency stress** | R5 | `concurrent_writer_stress_N16`, `read_after_write_cross_writer` |
| **J — Session decoupling** | R6 | `session_death_recovery`, `work_pickup_by_second_agent` |
| **K — Orchestrator hooks** | R8 | `orchestrator_hook_contract`, `ready_set_subscribe_latency`, `escalation_ingest_round_trip` |

Groups A (CRUD), B (transitions/races), C (edges), D (events), E (identity), F (extensions) remain unchanged. R1, R2, R7 are validated implicitly by Groups A/D and by manifest-field inspection (no new test group required).

## New beads to file

All new beads link back to `gmp-phc` as their rationale anchor.

### Filed in `gemba_prime` (prefix `gmp-`)
- `gmp-phc` (this bead) — integration task, closed when DoD met.

### To file in `gemba` (prefix `gm-`)
1. **gm-e3.2.N: WorkPlaneCapabilityManifest — R1–R8 field additions.** Implement the manifest schema above. Update `domain.md` §2.5 interface block. Update registration/validation code to enforce the minimum-bar check.
2. **gm-e3.5.N: Conformance test groups G–K.** Author the five new test groups. Capability-gate each so adaptors skip groups they don't advertise.
3. **gm-e6.audit: Beads adaptor — R1–R8 conformance audit.** Run the new groups against the current Beads adaptor (`internal/adapter/bd/` when it lands). Gaps become sub-beads under gm-e6.
4. **gm-e3.N: domain.md — add §1.0 "Agentic data plane: foundational assumptions" preamble.** Codify R1–R8 as category preconditions with `software-engineering agents tied to Git repos` scope.
5. **gm-e2.N: RFC.md — name the category in the product vision.** Gemba targets agentic data planes, not general business workflow trackers.
6. **gm-e2.N: landscape.md — R1–R8 comparison matrix across reference systems.** Projection matrix above, preserved with update cadence.

## Definition of Done (tracked on gmp-phc)

- [x] `dataplane-requirements.md` committed to the gemba_prime repo.
- [ ] `domain.md` §1.0 names the category and R1–R8 as preconditions.
- [ ] `RFC.md` TL;DR and/or product-vision paragraph names the category.
- [ ] `landscape.md` gains a §7 comparison matrix for R1–R8 × reference systems.
- [ ] `gm-*` beads filed under e3.2, e3.5, e6, e3 preamble, e2 RFC/landscape.
- [ ] All new `gm-*` beads link back to `gmp-phc`.

## Non-goals (preserved from gmp-phc)

- Not redesigning Beads itself.
- Not broadening scope beyond software-engineering agents tied to Git repos.
- Not building new adaptors.
- Not forcing SaaS trackers (Jira/Linear) to retrofit; they may fail specific capability bars, and that's a valid outcome.

## Constraints

- R1–R8 are the canonical taxonomy. Do not introduce a 9th or renumber without user sign-off.
- All cross-system framing (Beads, AgentHub, Ralph, Symphony, Raindrop, Gastown, Metaswarm) is preserved in `landscape.md` §2–§3 and the matrix in §7.
