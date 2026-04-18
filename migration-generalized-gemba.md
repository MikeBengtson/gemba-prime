# Migration Plan: Generalizing Gemba

**Author:** Principal architect, Phase 3
**Date:** 2026-04-18
**Status:** Actionable migration plan (importable)
**Depends on:** `landscape-generalized-gemba.md` (Phase 1), `domain-generalized-gemba.md` (Phase 2), `RFC.md` (product vision), `issues.jsonl` (existing planned work)

This document is the bridge between Phase 2 design and execution. It is opinionated, orderable, and directly importable as Beads issues. Every Design Decision (DD-1..DD-13) in the Phase 2 domain model is traced to at least one work item. Every existing bead in `issues.jsonl` has an explicit disposition. The final section contains a copy-pasteable JSONL block and the shell commands to import it.

---

## 1. Executive summary

### Scope

**In scope:**

- Generalizing the Gemba adaptor layer from Gas Town + Beads-only (`internal/adapter/gt/`, `internal/adapter/bd/`) to a pluggable two-plane contract (`WorkPlane`, `OrchestrationPlane`) per Phase 2 §2.5 and §3.7.
- Defining and validating the cross-cutting primitives (DoD, CostMeter, **Sprint + TokenBudget**, EscalationRequest, CapabilityManifest, Evidence) introduced in Phase 2 §4 and DD-14.
- Making Beads the first reference `WorkPlane` adaptor and Gas Town the first reference `OrchestrationPlane` adaptor — without regressing the existing v1 functionality that Phase 1 scaffolded.
- Forcing-function second adaptors (Jira WorkPlane, LangGraph OrchestrationPlane) to prove the abstraction.
- **Transport plurality** (per DD-8 / DD-15): adaptors declare one of `{api, jsonl, mcp}`. Gas Town ships as `api`-transport; second-adaptor `mcp` transport validates the recommended-not-required stance.
- **Sprint + TokenBudget** implementation: entity, rollup, three-tier inform/warn/stop enforcement at epic and sprint scope (per DD-14).
- UI generalization: removing Gas Town/Beads-specific vocabulary from the SPA (convoy → AgentGroup, rig → Workspace, etc.), driven by capability negotiation.
- Documentation + migration guide for existing Beads+Gas Town users of Gemba v1.

**Out of scope (deferred to v2 or later):**

- Cross-repo WorkItems (per DD-10 — explicit v1 deferral).
- Dollar-denominated or wallclock-denominated *enforced* budgets (per DD-14 — tokens are the only enforced axis in v1; other axes are rendered but not gating).
- Cross-sprint carry-over as a first-class operation (per DD-14 — use `relates_to` + successor epic instead).
- DoD enforcement of any kind (per DD-3 — informational-only in v1; re-opens when industry consensus on completion semantics emerges).
- Graph-mode topology rendering for LangGraph/ADK (per DD-7 — opaque in v1).
- Capability-level permission scoping (per DD-12 — all-or-nothing in v1).
- Multi-transport adaptors (per DD-15 — exactly one transport per adaptor in v1).
- Migrating every existing Gemba user onto generalized adaptors in lockstep — we will ship generalization behind a feature flag and allow Beads+Gas Town users to opt in.

### Sequencing rationale

**Validation gates precede build gates.** Phase 2 flags DD-1 (agent identity federation) and DD-12 (capability negotiation) as the highest-risk decisions now that DD-3 is deferred to informational-only, and DD-8 and DD-9 as needing external sign-off. Building adaptors against contracts that the Beads or Gas City maintainers later reject is a sunk cost we can avoid by front-loading the conversation. The plan therefore spends a dedicated phase (`gm-gen-v`) on validation before any adaptor work opens.

**Reference adaptors precede forcing-function adaptors.** Beads and Gas Town are the existing runtime; the contract must encode *their* quirks losslessly before we prove portability. Jira (WorkPlane) and LangGraph (OrchestrationPlane) are the forcing functions — if the contract handles them, it handles most of what the landscape survey identified.

**Cross-cutting features ride second-adaptor work.** DoD, CostMeter, Escalation, Capability negotiation all need at least two adaptors before their abstractions are meaningful. Building them once against Beads+Gas Town risks baking in Beads-isms we won't see until Jira arrives.

**UI generalization is last, not first.** The UI already assumes Gas Town vocabulary. Regenerating its types from capability manifests is a mechanical pass best done after the contract is stable.

### Key risks

1. **DD-1 agent identity federation (HIGHEST).** Every tracker with a "bot user" primitive (Jira, Linear, GitHub) must losslessly round-trip the richer `AgentRef` shape through custom fields or labels. A mis-synthesis silently corrupts agent identity across sessions and propagates through evidence, assignments, and audit trails. Mitigation: mandatory conformance group E tests (identity mapping round-trip); lossy-round-trip warnings surfaced in adaptor capability manifests.
2. **DD-12 capability negotiation blast radius.** Every UI surface reads capabilities at render time. A manifest schema mistake in v1 propagates to every adaptor ever written afterward, and manifest reads on every cell render can regress Kanban performance. Mitigation: capability schemas are add-only within a minor version; manifest memoization in the SPA; conformance group F (extension preservation) treated as a ship-blocker.
3. **DD-14 Sprint semantics redefinition.** Reusing the word "Sprint" while redefining its bounding constraint from calendar to tokens is an intentional friction that risks confusing Scrum-fluent operators. Mitigation: Kanban UI renders token-budget as the primary gauge and planned-duration as a secondary "on pace / ahead / behind" indicator; migration guide devotes a section to the semantic redefinition; prototype with real users before the UI surface freezes.
4. **DD-9 edge-taxonomy narrowing.** Beads has 7 edges; the core has 3. Beads users may resist the "default view hides 4 of your edges" ergonomics even with the extension-channel compromise. Mitigation: make the dep-graph view auto-surface all declared extension edges; ship with Beads extensions on by default.
5. **Gas City API churn.** `city.toml` spec and `gc escalate` semantics are not public as of 2026-04-18. Any adaptor work for Gas City must assume the spec will shift; we explicitly defer full Gas City adaptor wire-up to after the Gas City team's response to the RFC question.
6. **Abstraction leakage through `adaptor_extensions`.** An unbounded `Record<string, unknown>` channel is load-bearing in the Phase 2 design. Without strong conformance pressure, adaptors will dump arbitrary JSON through it and the UI will end up reading extensions the way it used to read Gas Town-specific fields. Conformance group F must be treated as a gate, not an afterthought.
7. **Token-budget rollup performance (DD-14).** Leaf → epic → sprint rollup computed at read time may not scale past ~10K WorkItems + ~50 active epics without a cache. Mitigation: benchmark before freezing; add incremental rollup cache as a stretch goal in `gm-gen-x`.

### Exit criteria for migration-complete

- All 13 DDs have landed tasks, and those tasks are closed.
- Beads + Gas Town function end-to-end through the generalized `WorkPlane` + `OrchestrationPlane` adaptors with **zero UI regressions** versus Gemba v1 (measured by a regression suite defined in §7).
- Jira + LangGraph adaptors pass the full conformance suite (§2.6, §3.8 of the domain doc).
- No Gas Town or Beads vocabulary appears in the React SPA outside adaptor-namespaced extension widgets.
- Migration guide published for existing Gemba users; feature flag `GEMBA_GENERALIZED=1` flips to default-on.
- DD-3 informational-only DoD schema is documented at `/schemas/dod/1.0.json` (minimal: `acceptance_criteria` + `notes`) and referenced from a public SPEC document noting the deferral-until-industry-consensus stance.

---

## 2. Validation gates (before any adaptor work begins)

Per Phase 2 §6.4 hand-off #7, validation must precede build. Each gate below has an owner, a decision space, a fallback, and a success signal. **No `gm-gen-a*` (adaptor implementation) task may start until every gate below is either GREEN (signed off) or FALLBACK (documented decision to ship the fallback design).**

> **Note on DD-3:** DD-3 (Definition of Done) is now informational-only until industry consensus on completion semantics emerges (see domain doc). No external sign-off gate is needed for DoD in v1; adaptors simply pass the free-text field through to the backend's existing free-text storage. The former Gate V1 is therefore dropped; remaining gates are renumbered V1–V5.

### Gate V1 — DD-9: Core edge taxonomy

- **Question:** Is narrowing the core edge set to `{parent_of, blocks, relates_to}` with a declared extension channel acceptable to Beads (whose 7 edges are load-bearing today), to the RFC's dep-graph view commitment, and to Gemba users who actively use `discovered-from` + `conditional-blocks`?
- **Sign-off needed from:** Steve Yegge (Beads), Mike Bengtson.
- **Decision options:**
  1. **GREEN:** Ship as designed; Beads adaptor declares the 4 extra extensions.
  2. **FALLBACK:** Expand core to `{parent_of, blocks, relates_to, discovered_from, waits_for}` (the subset Jira/Linear can still represent via custom fields); push `replies_to`, `conditional_blocks` to extension only.
- **Downstream impact if not GREEN:** Relationship types grow in `gm-gen-c2` (core types); Jira adaptor (`gm-gen-a3`) must synthesize more edges.
- **Success signal:** Beads maintainer's written OK on the 7→3 narrowing *or* on the expansion fallback.
- **Timebox:** 5 business days.

### Gate V2 — DD-1: Agent as first-class WorkItem citizen

- **Question:** Does Gas Town (current primary OrchestrationPlane) accept the `AgentRef` shape in Phase 2 §2.1.3 (role + parent_agent + agent_kind fields federated to its bot-user assignee model)? Does Gas City's pack-agnostic design conflict with our carrying `role` as a string?
- **Sign-off needed from:** Gas Town maintainers, Gas City maintainers.
- **Decision options:**
  1. **GREEN:** Ship as designed.
  2. **FALLBACK:** Drop `role` and `parent_agent` from core; they become namespaced extensions (`gastown.role`, `gascity.role`). Core `AgentRef` collapses to `{agent_id, display_name, agent_kind}`.
- **Downstream impact if not GREEN:** UI loses hierarchical agent views without the extension being present; agent-group surfaces thin out.
- **Timebox:** 7 business days.

### Gate V3 — DD-4 + DD-14: CostMeter axes and Sprint/TokenBudget enforcement semantics

- **Question:** (a) Are `{tokens_total, wallclock_seconds, dollars_est}` plus a `native_units` extension a defensible universal model? (b) Is redefining "Sprint" from calendar-bounded to token-budget-bounded (DD-14) an acceptable reuse of Agile vocabulary, and are the inform/warn/stop defaults (50% / 80% / 100%) reasonable for typical agent deployments?
- **Sign-off needed from:** At least one non-Gas-Town adaptor-implementer candidate (LangGraph, OpenHands, or a Devin integrator) for CostMeter axes; at least two Scrum-fluent Gemba prospective users for DD-14 sprint redefinition; Mike Bengtson.
- **Decision options (CostMeter):**
  1. **GREEN:** Ship as designed.
  2. **FALLBACK:** Core carries only `wallclock_seconds` (universally meaningful) + `native_units`. `dollars_est` moves to an optional UI-computed field.
- **Decision options (Sprint redefinition):**
  1. **GREEN:** Keep the name `Sprint`; ship with budget-primary / duration-secondary UI gauges.
  2. **FALLBACK:** Keep the entity and semantics; rename the UI surface (not the data model) to something less sticky (candidates: `Run`, `Budget Window`, `Iteration`). Data model remains `Sprint` so future UIs can revert.
- **Downstream impact if either not GREEN:** `gm-gen-x2` (CostMeter) and `gm-gen-x5` (Sprint + TokenBudget) retarget to their fallback shapes; insights panel may lose dollar rollups or UI copy changes throughout.
- **Timebox:** 10 business days.

### Gate V4 — DD-13: Evidence synthesis requirement

- **Question:** Is it acceptable that a WorkPlane adaptor for a tracker without native evidence (Jira, Linear, most) synthesizes evidence from adjacent data (git log, PR APIs) and tags `synthesized: true`?
- **Sign-off needed from:** Mike Bengtson + the first two adaptor authors.
- **Decision options:**
  1. **GREEN:** Ship as designed.
  2. **FALLBACK:** Synthesis becomes opt-in per adaptor; adaptors without synthesis simply declare `evidence_native: false` and ship an empty evidence array. UI gracefully degrades.
- **Timebox:** 5 business days. Lower risk than V1–V3.

> **Note on DD-8 / DD-15 transport plurality:** DD-8 has been loosened to recommend-not-require MCP; adaptors declare one of `{api, jsonl, mcp}` as their transport (DD-15). **No external sign-off gate is needed** — Gas Town's existing CLI-JSON surface wraps as `api`-transport, and MCP remains the forward-looking recommendation. The former DD-8 gate is dropped; transport plurality is validated through the reference adaptors (`gm-gen-a1`, `gm-gen-a2`) and second-adaptor forcing functions (`gm-gen-a3`, `gm-gen-a4`).

### Gate summary

| Gate | Risk | Timebox | Blocks |
|---|---|---|---|
| V1 — DD-9 edges | MEDIUM | 5 days | WorkPlane contract + Beads adaptor |
| V2 — DD-1 agents | HIGH | 7 days | OrchestrationPlane contract (agent identity is the new highest risk) |
| V3 — DD-4 cost + DD-14 Sprint | MEDIUM-HIGH | 10 days | CostMeter, Sprint/TokenBudget, insights panel, UI copy |
| V4 — DD-13 evidence | LOW | 5 days | Evidence pipeline |

---

## 3. Existing beads — disposition analysis

Every existing bead in `issues.jsonl` and in the live Beads rig is categorized below. The live Beads rig (`bd list` on 2026-04-18) currently shows only `gmp-rig-gemba_prime`, `gmp-eju`, `gmp-gj8`, `gmp-oh6` — these are rig-patrol beads, operational, **Unchanged** by this migration. All substantive product beads live in `issues.jsonl` and are addressed below.

### 3.1 Root epic

| Bead | Disposition | Notes |
|---|---|---|
| `gm-root` | **Updated** | The twelve locked decisions need surgical edits (details §3.5). The epic itself remains the root; the migration does not replace it. New generalization epic `gm-gen-root` becomes a sibling child of `gm-root` so the existing phase work stays in one tree. |

### 3.2 Phase 1 (Foundation) epic + tasks — scaffolding, CI, embed pipeline

| Bead | Disposition | Notes |
|---|---|---|
| `gm-e1` | **Unchanged** | Phase 1 scaffold is runtime-agnostic. |
| `gm-e1.1` → `gm-e1.6` | **Unchanged** | Foundation tasks stand. |

### 3.3 Phase 2 (Adapters + Core API) epic + tasks — the reshaped tree

| Bead | Disposition | Notes |
|---|---|---|
| `gm-e2` | **Re-scoped** | Still the "adapters + core API" epic, but its children now split: `gm-e2.1` (domain model) is re-scoped to build the generalized domain types; `gm-e2.2` / `gm-e2.3` / `gm-e2.3b` / `gm-e2.4` are re-scoped under new adaptor contracts. Epic description updated to reference `WorkPlane` and `OrchestrationPlane` (see §3.5 for edit text). |
| `gm-e2.1` (Domain model) | **Re-scoped** | Now "build the generalized `WorkItem`, `AgentRef`, `Relationship`, `Evidence`, `DefinitionOfDone` types from Phase 2 §2.1" rather than Beads-specific `Bead`. `Bead`-adaptor-specific types move to `internal/adapter/beads/types.go`. Labels add `migration:generalization`. Blocks `gm-gen-c1`. |
| `gm-e2.2` (bd adapter) | **Superseded** | Replaced by `gm-gen-a1` (Beads `WorkPlane` adaptor). Keep bead open for cross-referencing but mark status `blocked` with a `blocked-by: gm-gen-a1` relationship until `gm-gen-a1` closes, at which point close with a `superseded-by` note. |
| `gm-e2.3` (gt adapter) | **Superseded** | Replaced by `gm-gen-a2` (Gas Town `OrchestrationPlane` adaptor). Same treatment as `gm-e2.2`. |
| `gm-e2.3b` (gc adapter stub) | **Superseded** | Replaced by `gm-gen-a4` (Gas City `OrchestrationPlane` adaptor — still a stub in v1, see DD and Gas City API churn risk). |
| `gm-e2.4` (fs adapter) | **Re-scoped** | Still needed — the WorkPlane/OrchestrationPlane adaptors are built on top of the fs adapter's tailing primitives. Description updated to name the adaptors using it rather than "the gt handler." Stays. |
| `gm-e2.5` (SSE hub) | **Unchanged** | Transport layer; unaffected. |
| `gm-e2.6` (HTTP API + OpenAPI + TS codegen) | **Updated** | OpenAPI spec + TypeScript types must regenerate from the generalized domain (`WorkItem`, etc.). Description patched to reference the new types. Blocked by `gm-gen-c1`. |
| `gm-e2.7` (Mutation confirmation gating / nonce) | **Unchanged** | RFC-locked and transport-level. |

### 3.4 Phase 3–8 (Auth, UI, Boards, Graph, Molecules, Release) — mostly untouched, with UI generalization work slotted in

| Bead | Disposition | Notes |
|---|---|---|
| `gm-e3` / `gm-e3.1-4` (Auth) | **Unchanged** | Auth layer is transport. No Beads or Gas Town coupling. |
| `gm-e4` (Beads & Agents UI) | **Re-scoped** | Title remains recognizable but the description now says "renders `WorkItem`s and `Agent`s from any declared adaptor." Add dependency on `gm-gen-c1` (core types) so UI components consume the generalized shapes from day one. |
| `gm-e4.1` (App shell) | **Unchanged** | |
| `gm-e4.2` (react-query + SSE invalidation) | **Updated** | Event-subscription filters now consume capability manifests (DD-12). Description patched. |
| `gm-e4.3` (Work grid) | **Updated** | Grid columns derive from the `CapabilityManifest.field_extensions`, not hardcoded Beads columns. |
| `gm-e4.4` (Agents dashboard) | **Updated** | Reads `Agent` (§3.1.1) not Gas Town-specific agent shape; group rendering reads `AgentGroup.mode`. |
| `gm-e4.5` (Bead detail drawer) | **Updated** | Retitle to "WorkItem detail drawer"; shows canonical core fields + declared extensions. |
| `gm-e4.6` (cmdk palette) | **Unchanged** | |
| `gm-e5` (Boards & Mutations) | **Re-scoped** | Same shift: columns derive from `state_category`, not Beads statuses. Drag-drop uses `WorkPlane.transition`. |
| `gm-e5.1` (Kanban) | **Updated** | Description patched (see §3.5 edit texts). |
| `gm-e5.2` (Convoy board) | **Re-scoped + renamed** | Renamed to "AgentGroup board view" in description (`AgentGroup` replaces `Convoy`). Original "convoy" language remains in Gas Town-specific extension UI. |
| `gm-e5.3` (Backlog board) | **Unchanged** | Cross-rig → cross-workspace, but concept is stable. |
| `gm-e5.4` (Bead creation) | **Updated** | Creates a `WorkItem` via the active WorkPlane adaptor. |
| `gm-e5.5` (Bulk actions) | **Unchanged** | |
| `gm-e5.6` (YOLO mode) | **Unchanged** | |
| `gm-e5.7` (Desired-vs-actual) | **Updated** | Reads from `OrchestrationPlaneAdaptor` capability declarations; for Gas Town renders implicit-desired, for Gas City renders `city.toml`. No longer Gas-City-specific in the UI layer. |
| `gm-e5.8` (Pack browser) | **Re-scoped** | Retitle description to "Adaptor capability browser" — enumerates installed adaptors and their manifests. Gas City packs are one specific manifestation. |
| `gm-e5.9` (Provider-aware agent detail) | **Updated** | Reads `Workspace.kind` (§3.1.2) rather than Gas Town-specific `session.Provider` name. |
| `gm-e6` (Graph, Insights, Mail) | **Updated** | Graph consumes `CapabilityManifest.relationship_extensions`; insights consumes `CostMeter`. |
| `gm-e6.1` (Dep graph) | **Updated** | Renders the 3 core edge types + declared extension edges (DD-9). |
| `gm-e6.2` (Insights panel) | **Updated** | Reads `CostMeter` from core rather than `bd stats`-specific schema. |
| `gm-e6.3` (Mail view) | **Unchanged** | Gas Town-specific today; gated behind Gas Town adaptor capability declaration. |
| `gm-e6.4` (Escalations drawer) | **Updated** | Replaced by `gm-gen-x3` (Escalation inbox + card badge). Marked superseded once `gm-gen-x3` closes. |
| `gm-e7` (Molecules) | **Unchanged** | Molecule formulas are Gas Town native; rendered via extension. Post-migration, may become a capability pattern but v1 keeps the existing work. |
| `gm-e7.1` / `gm-e7.2` | **Unchanged** | |
| `gm-e8` (Release) | **Updated** | Release criteria expand to include "adaptor conformance suite green," "Jira adaptor working against public sandbox," "migration guide published." See §3.5 for edit text. |
| `gm-e8.1–4` | **Unchanged** | Mechanics unchanged. |

### 3.5 Bugs

| Bead | Disposition | Notes |
|---|---|---|
| `gm-b1` (bd daemon offline handling) | **Re-scoped** | Surface is now "adaptor-degraded signaling" (DD-13 in §5.1.1). Applies to any adaptor, not just bd. Retitle description to generalize. |
| `gm-b2` (SPA fallback vs API 404) | **Unchanged** | Transport. |
| `gm-b3` (token auth on loopback) | **Unchanged** | Auth. |

### 3.6 Specific text edits for Updated beads

The following `bd update` operations (exact command list in §10) patch existing beads. Critical edits shown inline.

**`gm-root`** — Twelve locked decisions need the following surgical edits:

- **Locked decision 1 (TOPOLOGY):** Replace "talks to `gt --json` and `bd --json`" with "talks to one configured `OrchestrationPlane` adaptor and one configured `WorkPlane` adaptor. Default configuration pairs the Gas Town `OrchestrationPlane` adaptor with the Beads `WorkPlane` adaptor for Gas Town v1 workspaces."
- **Locked decision 4 (PACK-AGNOSTIC UI):** Keep, expand with: "This principle now generalizes to any adaptor: no role name, column header, or panel may hardcode vocabulary from a specific WorkPlane or OrchestrationPlane. All vocabulary arrives via `CapabilityManifest` (Phase 2 §4.6)."
- **Locked decision 5 (PROVIDER-AWARE):** Generalize "tmux/k8s/subprocess/exec" to "the `WorkspaceKind` values declared by the active OrchestrationPlane adaptor."
- **Locked decision 9 (DATA INTEGRITY):** Expand to: "Never write to any backend's private storage directly (Dolt, JSONL, `.gt/`, `.gc/`, controller sockets, Jira databases, Linear internal APIs). Every mutation round-trips through the adaptor, which in turn uses the backend's public CLI/API."
- **Locked decision 10 (DECLARATIVE UX):** Generalize "city.toml vs .gc/agents/" to "the `OrchestrationPlaneAdaptor.declared_state()` vs `observed_state()` returned via capability declaration. Gas City's `city.toml` is one instance."

Full edit text is in the `bd update` commands in §10.

---

## 4. New work structure

### 4.1 Naming convention

**Prefix:** `gm-gen-*`

**Justification:**

- The existing tree uses `gm-root` → `gm-e<N>` (phase epics) → `gm-e<N>.<M>` (tasks). The generalization work is an orthogonal concern that overlays multiple phases.
- Using `gm-gen-*` makes it immediately filterable in `bd list`, distinguishes generalization beads from phase beads in search, and leaves room for phased sub-IDs within generalization (`gm-gen-v1`, `gm-gen-c2`, `gm-gen-a3`).
- The alternative `gm-e9`, `gm-e10`, ... would imply "post-Phase-8" sequentiality when generalization actually interleaves with existing phases.

**Sub-prefixes within `gm-gen-*`:**

- `gm-gen-root` — the root epic for the entire generalization initiative (child of `gm-root`).
- `gm-gen-v<N>` — validation-phase epics (V1 through V6).
- `gm-gen-c<N>` — core contracts phase (interface definitions, conformance test suites, type generation).
- `gm-gen-a<N>` — adaptor phase (reference + forcing-function adaptors).
- `gm-gen-x<N>` — cross-cutting features (DoD, cost meter, escalation, capability negotiation).
- `gm-gen-u<N>` — UI generalization phase (SPA language + component generalization).
- `gm-gen-d<N>` — documentation & release phase.

**New label:** `migration:generalization` applied to every `gm-gen-*` bead and to every existing bead touched by the migration.

**New field convention:** `resolves_dd: string[]` added to task descriptions (in the `# Definition of Done` section as a trailing "**Resolves DDs:**" line). This is a description-level convention, not a schema change to `issues.jsonl`; beads do not require a new field in Beads storage.

### 4.2 Phase epics

#### [gm-gen-root] — Generalization root

- **Goal:** Parent container for the full generalization initiative, sibling to `gm-root`'s phase epics under `gm-root`.
- **Resolves DDs:** all (as container).
- **Depends on:** `gm-root` (parent-child).
- **Blocks:** nothing upstream; children are the work.
- **Exit criteria:** All `gm-gen-*` epics closed; migration guide published; `GEMBA_GENERALIZED=1` default-on.
- **Estimated risk:** HIGH (as sum of children).

#### [gm-gen-v] — Validation phase

- **Goal:** Socialize DD-9, DD-1, DD-4, DD-13, and DD-14 with external maintainers and prospective users; freeze the fallback design for each. (DD-3 removed: informational-only per domain doc. DD-8 removed as a gate: transport plurality per DD-15 means MCP is recommended-not-required, no external sign-off needed.)
- **Resolves DDs:** DD-9, DD-1, DD-4, DD-13, DD-14.
- **Depends on:** `gm-gen-root`.
- **Blocks:** `gm-gen-c` (core contracts cannot finalize until gates close).
- **Exit criteria:** Every gate either GREEN or FALLBACK-documented; Gemba publishes a short "Design Decisions" document referencing each outcome.
- **Tasks:** 4 (one per gate: V1 DD-9, V2 DD-1, V3 DD-4+DD-14, V4 DD-13).
- **Estimated risk:** MEDIUM-HIGH (political, not technical; DD-1 is top of this list).

#### [gm-gen-c] — Core contracts phase

- **Goal:** Define `WorkPlane` and `OrchestrationPlane` interfaces in code, conformance test suite skeletons, capability-manifest types, adaptor-registration protocol.
- **Resolves DDs:** DD-2, DD-5, DD-7, DD-10, DD-12.
- **Depends on:** `gm-gen-v` (all gates closed).
- **Blocks:** `gm-gen-a*`, `gm-gen-x*`.
- **Exit criteria:** Interfaces compile in Go + TS; conformance test suite skeleton runs green on a noop adaptor; capability manifest types codegenned into TS from Go; OpenAPI spec at `/api/openapi.json` renders adaptor endpoints.
- **Tasks:** 7.
- **Estimated risk:** MEDIUM (design-heavy, but now unblocked by gates).

#### [gm-gen-a1] — Reference Beads `WorkPlane` adaptor

- **Goal:** Make the existing Beads integration the first conformance-passing `WorkPlane` adaptor; retire `gm-e2.2` (bd adapter) into the new structure.
- **Resolves DDs:** DD-1, DD-2, DD-3 (pass-through of free-text), DD-9, DD-10, DD-13.
- **Depends on:** `gm-gen-c`.
- **Blocks:** `gm-gen-x*` (cross-cutting features need a real adaptor to test against).
- **Exit criteria:** Conformance suite groups A–F all green against Beads; `gm-e2.2` marked superseded; no regression in existing Gemba functionality (regression suite §7).
- **Tasks:** 7.
- **Estimated risk:** MEDIUM (pipeline is clear; the work is schema synthesis + CLI wrapping).

#### [gm-gen-a2] — Reference Gas Town `OrchestrationPlane` adaptor

- **Goal:** Make Gas Town the first conformance-passing `OrchestrationPlane` adaptor; retire `gm-e2.3` (gt adapter).
- **Resolves DDs:** DD-1, DD-4, DD-5, DD-6, DD-7, DD-8, DD-12.
- **Depends on:** `gm-gen-c`, `gm-gen-a1` (Beads adaptor — because end-to-end conformance needs both planes).
- **Blocks:** `gm-gen-x*`.
- **Exit criteria:** Conformance suite groups A–F pass; all existing Gemba Gas Town functionality preserved.
- **Tasks:** 7.
- **Estimated risk:** MEDIUM.

#### [gm-gen-a3] — Forcing-function Jira `WorkPlane` adaptor

- **Goal:** Prove the abstraction by implementing Jira (hardest common-case tracker: workflow FSM, custom fields, rate limits, no native agent concept, no native evidence). Defended against Linear on the grounds that Jira's quirks are a superset of Linear's — if the contract handles Jira, Linear is easy.
- **Resolves DDs:** DD-1, DD-3 (pass-through), DD-9, DD-12, DD-13 (all under the hardest constraint).
- **Depends on:** `gm-gen-a1`.
- **Blocks:** `gm-gen-u*` (UI generalization needs a non-Beads adaptor to test against).
- **Exit criteria:** Conformance suite green; read+write smoke test against an Atlassian Jira Cloud sandbox.
- **Tasks:** 6.
- **Estimated risk:** HIGH (Jira's quirks are the forcing function; rate limits and workflow FSM are real).

#### [gm-gen-a4] — Forcing-function LangGraph `OrchestrationPlane` adaptor

- **Goal:** Prove the abstraction by implementing LangGraph (hardest common-case orchestrator: no native agent identity, no native work item, graph-mode grouping, checkpoint-based session). Defended against OpenHands on the grounds that OpenHands is already server-product-shaped and has clearer work-item primitives; LangGraph exposes the largest impedance mismatch.
- **Resolves DDs:** DD-1, DD-4, DD-5, DD-7, DD-8, DD-12.
- **Depends on:** `gm-gen-a2`.
- **Blocks:** `gm-gen-u*`.
- **Exit criteria:** Conformance suite green; end-to-end demo with LangGraph thread checkpointed and resumed from the Gemba UI.
- **Tasks:** 6.
- **Estimated risk:** HIGH (graph-mode opacity and checkpoint semantics are novel).

#### [gm-gen-a4b] — Gas City `OrchestrationPlane` adaptor (stub → wire-up)

- **Goal:** Keep the Gas City adaptor designed-for and stubbed; wire it up fully when the Gas City spec stabilizes. Consumes `gm-e2.3b`.
- **Resolves DDs:** DD-1, DD-5, DD-7, DD-12.
- **Depends on:** `gm-gen-a2`, Gas City team's reply to the RFC (external dependency).
- **Blocks:** none for v1 migration-complete (Gas City is post-GA); explicit v1 exit-criteria exemption.
- **Exit criteria (v1):** Stub compiles, workspace detection routes to it, capability manifest declares "alpha/stub."
- **Tasks:** 3.
- **Estimated risk:** LOW-MEDIUM (stub-sized).

#### [gm-gen-x] — Cross-cutting features

- **Goal:** Build the cross-cutting primitives (informational-only DoD, CostMeter, **Sprint + TokenBudget**, EscalationRequest, Capability manifest, Evidence synthesis, **transport plurality**) against two real adaptors.
- **Resolves DDs:** DD-3 (informational), DD-4, DD-6, DD-12, DD-13, **DD-14, DD-15**.
- **Depends on:** `gm-gen-a1`, `gm-gen-a2`.
- **Blocks:** `gm-gen-u*`.
- **Exit criteria:** DoD minimal schema + 1-page spec published; cost rollups render in insights panel; **Sprint + TokenBudget entity live with three-tier inform/warn/stop enforcement at epic and sprint scope**; escalation inbox + card badge live (with `budget_warn` kind); capability-manifest driven UI adjustments working; **at least two transports (`api` + one other) proven end-to-end**.
- **Tasks:** 7 (adds Sprint/TokenBudget implementation + transport plurality beyond original 5).
- **Estimated risk:** MEDIUM (sprint semantics redefinition is a user-perception risk — prototype with Scrum-fluent users per V3 gate before committing UI copy).

#### [gm-gen-u] — UI generalization phase

- **Goal:** Remove Gas Town/Beads vocabulary from the SPA. Drive field visibility, labels, and terminology from capability manifests.
- **Resolves DDs:** DD-12 primarily; all DDs' UI surfaces.
- **Depends on:** `gm-gen-a3` + `gm-gen-a4` + `gm-gen-x` (need two adaptors on both planes and the cross-cutting types).
- **Blocks:** `gm-gen-d`.
- **Exit criteria:** No Gas Town/Beads string appears outside adaptor-namespaced extension widgets; snapshot test catches regressions; Jira + LangGraph render correctly in the Kanban and graph views.
- **Tasks:** 5.
- **Estimated risk:** MEDIUM (mechanical but wide).

#### [gm-gen-d] — Documentation & release phase

- **Goal:** Migration guide, public adaptor authoring docs, cut a release with `GEMBA_GENERALIZED=1` default-on.
- **Resolves DDs:** DD-12, DD-3 (informational-only spec publication), all (as release gate).
- **Depends on:** `gm-gen-u`.
- **Blocks:** migration-complete.
- **Exit criteria:** Docs site has "Writing an adaptor" guide; migration guide for v1 Beads+Gas Town users published; release cut.
- **Tasks:** 4.
- **Estimated risk:** LOW.

### 4.3 Tasks per epic

Every task below carries (in its description):

- `# Goal`, `# Inputs`, `# Outputs`, `# Definition of Done` (matching the existing issues.jsonl format exactly)
- A trailing `**Resolves DDs:** DD-N, DD-M` line in the DoD section
- `labels` include `migration:generalization` + the existing taxonomy (`surface:*`, `tier:*`, `risk:*`, `fed:*`, `area:*`)
- `dependencies` list both `parent-child` (to the epic) and `blocks` (to precursor tasks)

The full task-by-task details are in the JSONL block in §10. A compact summary follows:

**`gm-gen-v` children (4):**

- `gm-gen-v1` — Socialize DD-9 edge narrowing with Beads author. Resolves DD-9.
- `gm-gen-v2` — Socialize DD-1 AgentRef shape with Gas Town/Gas City maintainers. Resolves DD-1.
- `gm-gen-v3` — Socialize DD-4 cost-meter axes + DD-14 Sprint/TokenBudget semantics (Sprint-as-token-budget redefinition) with at least one non-Gas-Town adaptor-implementer candidate AND two Scrum-fluent prospective users. Resolves DD-4, DD-14.
- `gm-gen-v4` — Socialize DD-13 evidence-synthesis stance. Resolves DD-13.

**`gm-gen-c` children (7):**

- `gm-gen-c1` — Define `WorkItem`, `AgentRef`, `Relationship`, `Evidence`, `DefinitionOfDone` (informational-only: `acceptance_criteria` + `notes` + `version`), `Sprint`, `TokenBudget` core types in Go; codegen TS. Resolves DD-2, DD-10, DD-14.
- `gm-gen-c2` — Define `WorkPlaneAdaptor` interface (including Sprint ops + `read_budget_rollup`) + `CapabilityManifest` (including `transport: "api"|"jsonl"|"mcp"` and `sprint_native`, `token_budget_enforced` capabilities) in Go. Resolves DD-9, DD-12, DD-14, DD-15.
- `gm-gen-c3` — Define `OrchestrationPlaneAdaptor` interface + `OrchestrationCapabilityManifest` in Go. Resolves DD-5, DD-7.
- `gm-gen-c4` — Adaptor registration + version-negotiation protocol over all three transports (`api`, `jsonl`, `mcp`); describe/register RPC. Resolves DD-8, DD-12, DD-15.
- `gm-gen-c5` — Conformance test suite harness (CLI runs A–F groups against any adaptor); transport-agnostic — same tests run against `api`, `jsonl`, and `mcp` transports. Resolves DD-12, DD-15.
- `gm-gen-c6` — Event schema (including `budget.inform`, `budget.warn`, `budget.stop` events per DD-14) + OTEL trace propagation in adaptor boundary. Resolves DD-12, DD-14.
- `gm-gen-c7` — Noop/reference adaptors (in-memory) passing conformance, used for testing UI without a backend; ships as `jsonl` transport to exercise that path. Resolves DD-12, DD-15.

**`gm-gen-a1` children (7):**

- `gm-gen-a1.1` — Beads `WorkPlane` adaptor CRUD over `bd --json` (supersedes `gm-e2.2`). Resolves DD-2.
- `gm-gen-a1.2` — Beads edge mapping (7→3 + 4 extensions per §2.4). Resolves DD-9.
- `gm-gen-a1.3` — Beads `AgentRef` ↔ claim federation. Resolves DD-1.
- `gm-gen-a1.4` — Beads DoD pass-through: map `dod.acceptance_criteria` + `dod.notes` to a single new free-text `acceptance_criteria` field on the bead (via `bd` CLI). Resolves DD-3.
- `gm-gen-a1.5` — Beads evidence synthesis from work-history + Dolt refs (`synthesized: true` tagging). Resolves DD-13.
- `gm-gen-a1.6` — Beads subscribe/event delivery via fsnotify + `bd events` (Beads event bus). Resolves DD-12.
- `gm-gen-a1.7` — Beads adaptor passes conformance suite groups A–F. Resolves DD-2, DD-9, DD-13.

**`gm-gen-a2` children (7):**

- `gm-gen-a2.1` — Gas Town agent + group enumeration (`list_agents`, `list_groups`), convoy → AgentGroup static, pool → AgentGroup pool. Resolves DD-7.
- `gm-gen-a2.2` — Gas Town Workspace adaptor (tmux rig → `WorkspaceKind=worktree`, `fs_scoped:true` declared). Resolves DD-5.
- `gm-gen-a2.3` — Gas Town session lifecycle (start/pause/resume/end/peek) + tmux capture-pane peek. Resolves DD-12.
- `gm-gen-a2.4` — Gas Town cost meter synthesis (tokens + wallclock from session telemetry; fallback per V5 outcome). Resolves DD-4.
- `gm-gen-a2.5` — Gas Town escalation mapping (`gt escalate` → `EscalationRequest{source:"orchestrator_pause"}`). Resolves DD-6.
- `gm-gen-a2.6` — Gas Town adaptor declares `transport: "api"` and ships the thin HTTP+JSON shim wrapping `gt --json` + `bd --json` CLIs (no MCP bridge required per DD-8/DD-15 loosening). Resolves DD-8, DD-15.
- `gm-gen-a2.7` — Gas Town adaptor passes conformance suite. Resolves DD-5, DD-6, DD-7, DD-8, DD-15.

**`gm-gen-a3` children (6):**

- `gm-gen-a3.1` — Jira `WorkPlane` adaptor CRUD via Atlassian REST v3. Resolves DD-2.
- `gm-gen-a3.2` — Jira workflow FSM → `state_map.valid_transitions` on registration + refresh. Resolves DD-12.
- `gm-gen-a3.3` — Jira agent synthesis via custom field `bc.agent_role` / `bc.parent_agent`. Resolves DD-1.
- `gm-gen-a3.4` — Jira DoD pass-through: map `dod.acceptance_criteria` to the `Acceptance Criteria` custom field if present, else a delimited section in `description`. Resolves DD-3.
- `gm-gen-a3.5` — Jira rate-limit-aware subscribe (webhooks + coalescing). Resolves DD-12.
- `gm-gen-a3.6` — Jira adaptor passes conformance suite. Resolves DD-1, DD-3, DD-9.

**`gm-gen-a4` children (6):**

- `gm-gen-a4.1` — LangGraph adaptor: `Agent` synthesis from node paths; thread_id as session. Resolves DD-1.
- `gm-gen-a4.2` — LangGraph `AgentGroup{mode:"graph"}` surfacing; members resolved on read. Resolves DD-7.
- `gm-gen-a4.3` — LangGraph checkpoint → session suspend/resume; HITL interrupt → EscalationRequest. Resolves DD-6.
- `gm-gen-a4.4` — LangGraph cost: LangSmith token pull → `CostMeter.tokens_total`. Resolves DD-4.
- `gm-gen-a4.5` — LangGraph workspace: declared `exec`, fs_scoped:true with caveat (documented). Resolves DD-5.
- `gm-gen-a4.6` — LangGraph adaptor passes conformance suite (graph-opaque group tests). Resolves DD-5, DD-6, DD-7.

**`gm-gen-a4b` children (3):**

- `gm-gen-a4b.1` — Gas City adaptor skeleton matching Gas Town shape; capability manifest declares `alpha/stub`.
- `gm-gen-a4b.2` — Gas City workspace detection (`city.toml` presence) routes to this adaptor.
- `gm-gen-a4b.3` — Gas City RFC follow-up: publish Gemba's spec questions, collect answers.

**`gm-gen-x` children (7):**

- `gm-gen-x1` — Document informational-only DoD stance + ship minimal schema (1-page SPEC): `acceptance_criteria` + `notes` + `version: "1.0"`; Go + TS types; deferral rationale prominent. Resolves DD-3.
- `gm-gen-x2` — CostMeter rollups: per-assignment, per-workitem, per-agent, per-group, per-epic, per-sprint. Insights panel rendering. Resolves DD-4.
- `gm-gen-x3` — EscalationRequest pipeline: card badge on Kanban, `/escalations` inbox, banner overlay, cmdk action; includes `budget_warn` kind per DD-14. Supersedes `gm-e6.4`. Resolves DD-6.
- `gm-gen-x4` — Capability-negotiation UI layer: hide controls by manifest; field extensions rendered by declared type; transport chosen per `CapabilityManifest.transport`. Resolves DD-12, DD-15.
- `gm-gen-x5` — **Sprint + TokenBudget implementation**: entity CRUD, epic↔sprint binding, rollup engine (leaf→epic→sprint computed at read time with memoization), three-tier inform/warn/stop enforcement, `budget_override` nonce integration, UI gauges (budget primary, planned-duration secondary "on pace / ahead / behind"). Sprint picker on Kanban top bar. Resolves DD-14.
- `gm-gen-x6` — Evidence synthesis library shared across adaptors (git log, PR APIs, CI status); adaptor opt-in. Resolves DD-13.
- `gm-gen-x7` — Transport plurality harness: proof of at least two transports end-to-end (`api` via Gas Town adaptor + one other — `jsonl` via noop adaptor OR `mcp` via second-adaptor experiment). Transport switch is a CapabilityManifest field; conformance tests run identically across transports. Resolves DD-8, DD-15.

**`gm-gen-u` children (5):**

- `gm-gen-u1` — Rename SPA types: `Bead` → `WorkItem`, `Convoy` → `AgentGroup`, `Rig` → `Workspace`. Mechanical sweep + codemod.
- `gm-gen-u2` — Column/field derivation from capability manifests (work grid, Kanban).
- `gm-gen-u3` — Pack browser → adaptor capability browser (`gm-e5.8` superseded in content).
- `gm-gen-u4` — Snapshot test: no adaptor-specific vocabulary in rendered UI outside extension components.
- `gm-gen-u5` — Gas Town / Beads-specific extension widgets isolated into `web/src/extensions/{beads,gastown}/`.

**`gm-gen-d` children (4):**

- `gm-gen-d1` — Public "Writing a Gemba adaptor" guide; includes conformance harness usage.
- `gm-gen-d2` — Migration guide for existing Gemba v1 users (Beads + Gas Town); covers flag flip.
- `gm-gen-d3` — Release cut with `GEMBA_GENERALIZED=1` default-on; gated on conformance green on both reference adaptors.
- `gm-gen-d4` — Announcement: gastown discussions + HN + Reddit + blog post update for generalization (supplements `gm-e8.4`).

Total new beads: **1 (gen-root) + 10 phase epics + 56 tasks = 67 new beads**. Breakdown: 1 root; v: 1 epic + 4 tasks; c: 1 epic + 7 tasks; a1: 1 epic + 7 tasks; a2: 1 epic + 7 tasks; a3: 1 epic + 6 tasks; a4: 1 epic + 6 tasks; a4b: 1 epic + 3 tasks; x: 1 epic + 7 tasks; u: 1 epic + 5 tasks; d: 1 epic + 4 tasks.

---

## 5. Dependency graph

```
            gm-root
               │
               ▼
          gm-gen-root
               │
       ┌───────┴──────┐
       ▼              ▼
   gm-gen-v      (existing gm-e1..gm-e8 continue in parallel where independent)
       │
  [V1 V2 V3 V4 V5 all GREEN or FALLBACK — DD-3 no longer a gate]
       │
       ▼
   gm-gen-c  ──────────┐
       │               │
       ▼               ▼
   gm-gen-a1      gm-gen-a2
       │          (Gas Town)
   (Beads)           │
       │               │
       └──────┬────────┘
              │
              ▼
        ┌──── gm-gen-x ───┐
        │    (cross-cut)  │
        ▼                 ▼
   gm-gen-a3         gm-gen-a4
   (Jira)           (LangGraph)
        │                 │
        └────────┬────────┘
                 ▼
             gm-gen-u
           (UI generalize)
                 │
                 ▼
             gm-gen-d
          (docs + release)
                 │
                 ▼
       migration-complete

         (gm-gen-a4b — Gas City stub — slot between a2 and u
          but exit criteria are lower; not a v1 blocker)
```

Critical-path tasks (the sequence that defines ship date):

`gm-gen-v2` (DD-1 validation) → `gm-gen-c1` (core types) → `gm-gen-c2` + `gm-gen-c3` (interfaces) → `gm-gen-c5` (conformance harness) → `gm-gen-a1.1` (Beads CRUD) → `gm-gen-a1.7` (Beads conformance) → `gm-gen-a2.1` (Gas Town groups) → `gm-gen-a2.7` (Gas Town conformance) → `gm-gen-x1` (informational DoD spec) → `gm-gen-a3.6` (Jira conformance) → `gm-gen-u1` (SPA rename) → `gm-gen-u4` (snapshot test) → `gm-gen-d2` (migration guide) → `gm-gen-d3` (release).

---

## 6. Cross-cutting concerns

### 6.1 DoD schema rollout

Per DD-3, DoD is informational-only in v1 — there are no alternative paths. Single path:

- `gm-gen-x1` ships a 1-page SPEC and the minimal schema (`acceptance_criteria?` + `notes?` + `version: "1.0"`); no predicate kinds, no evaluator, no registry.
- Adaptor tasks `gm-gen-a1.4` (Beads) and `gm-gen-a3.4` (Jira) pass the text through to a single free-text field on the backend (new `acceptance_criteria` field on the bead; `Acceptance Criteria` custom field or delimited `description` section on Jira).
- Other adaptors (Linear, GitHub Issues, Gas Town/Gas City) follow the same pass-through pattern when they land.
- DD-3 re-opens as `schema_version: "2.0"` (opt-in capability) if and when industry consensus on completion semantics emerges. `1.0` deployments remain supported indefinitely.

### 6.2 Cost meter + Sprint budget implementation (per DD-4, DD-14)

- Protocol (`CostSample`, `CostMeter`) defined in `gm-gen-c1` / `gm-gen-c3`.
- `Sprint` + `TokenBudget` entities + rollup engine defined in `gm-gen-c1` and implemented in `gm-gen-x5`.
- Adaptor contract: every OrchestrationPlane adaptor MUST declare `cost_axes_emitted` in its manifest (per V3 outcome this may reduce to `["wallclock"]` only). WorkPlane adaptors MAY declare `sprint_native: true` (if the backend has a native sprint/cycle/iteration) and `token_budget_enforced: true` (if the adaptor polices mutations at the backend boundary).
- Three-tier enforcement (`inform` / `warn` / `stop`): rollup computed at read time; `stop` crossing gates new-spend mutations unless the request carries `X-GEMBA-Confirm` nonce with `budget_override: true`. See `gm-gen-x5` and `gm-gen-x4`.
- UI surface: `gm-gen-x2` builds insights panel rollups (per-sprint lane); `gm-gen-x5` adds Sprint picker on the Kanban top bar and budget gauges on epic/sprint cards; `gm-e6.2` description updated to reference this.

### 6.3 Escalation inbox (per DD-6, extended by DD-14)

- `gm-gen-x3` is the single tracking bead; it supersedes `gm-e6.4`.
- Surfaces: Kanban card badge (reads open-escalation count via event subscription), `/escalations` page (dedicated filter UI), Kanban banner (dismissible when any card in view has `urgency:"blocking"`), cmdk action.
- Source mapping table (§4.3 of domain doc) is implemented as a strategy registry in `gm-gen-x3`.
- Per DD-14: `EscalationRequest{kind: "budget_warn"}` is produced by the rollup engine when an epic or sprint first crosses its `warn` threshold; lands in the same inbox with a distinct visual treatment.

### 6.4 Capability negotiation mechanism (per DD-12, extended by DD-15)

- Used by every adaptor: core → `gm-gen-c4` (registration protocol supports all three transports) + `gm-gen-x4` (UI-layer capability consumption).
- Adaptor → manifest returned from `describe()`; includes `transport: "api" | "jsonl" | "mcp"` and the new `sprint_native` / `token_budget_enforced` capabilities.
- UI → `gm-gen-x4` replaces hardcoded feature checks with manifest reads; transport-specific adaptor calls are routed by `gm-gen-c4`'s registration layer.

### 6.5 Evidence synthesis for gap-filling adaptors (per DD-13)

- Shared library in `gm-gen-x6` (git log walker, GitHub PR fetcher, CI-status poller) used by Jira, GitHub Issues, Linear, Azure DevOps adaptors.
- `synthesized: true` flag enforced by core schema validator.
- Beads adaptor (`gm-gen-a1.5`) consumes `gm-gen-x6` for git/PR synthesis; Beads' native work-history is NOT synthesized.

### 6.6 Transport plurality (per DD-8, DD-15)

- Three transports supported: `api` (HTTP+JSON), `jsonl` (file-based import/export), `mcp` (MCP client/server profile).
- Each adaptor declares exactly one transport in its `CapabilityManifest.transport` field; `gm-gen-c4` routes calls accordingly.
- `gm-gen-x7` proves transport plurality by running conformance tests against at least two transports end-to-end.
- Gas Town adaptor (`gm-gen-a2`) ships `api`; noop reference adaptor (`gm-gen-c7`) ships `jsonl`; a forcing-function adaptor may ship `mcp` to validate that path.
- Gemba itself is agnostic about transport; agents (under whatever orchestrator) remain free to depend on MCP without Gemba needing to speak it.

---

## 7. Rollback and safety

### 7.1 Per-epic rollback

| Epic | Rollback mechanism |
|---|---|
| `gm-gen-v` | Pure documentation work; revert notes. No user impact. |
| `gm-gen-c` | Core types land behind build tag `bc_generalized`; default build still uses `gm-e2.1` types. Revert = delete build tag. |
| `gm-gen-a1` | Beads adaptor sits behind `GEMBA_GENERALIZED=1` env var at runtime; default path uses existing `gm-e2.2` client. Revert = unset flag. |
| `gm-gen-a2` | Same runtime flag gates Gas Town adaptor vs `gm-e2.3` client. |
| `gm-gen-a3` / `gm-gen-a4` | New adaptors; no rollback needed (they add capability). |
| `gm-gen-x*` | Each cross-cutting feature has its own kill switch (e.g., `BC_DOD_ENABLED`, `BC_ESCALATION_V2`). Removing the flag bypasses. |
| `gm-gen-u*` | SPA rename is mechanical; revert is a `git revert` of the codemod commit. |
| `gm-gen-d*` | Docs are additive. |

### 7.2 Feature flags and gradual cutover

- Master flag: `GEMBA_GENERALIZED=1` (env var + command-line `--generalized`). Default off through `gm-gen-a2` completion; default on at `gm-gen-d3`.
- Per-feature flags: `BC_DOD_ENABLED`, `BC_ESCALATION_V2`, `BC_COST_METER_V2`. Each defaults in lockstep with master but can be independently toggled for debugging.
- Capability-manifest version: `1.0` (v1 target). `1.x` additions are safe; `2.0` breaks.

### 7.3 Regression test suite

Must pass at every phase boundary:

- **`gm-e*` snapshot suite:** existing Phase 1–8 functional tests run green against the non-generalized path.
- **Generalized path parity:** identical UI snapshot with `GEMBA_GENERALIZED=1` for Gas Town + Beads (Kanban, grid, graph, insights all pixel-equivalent modulo vocabulary changes documented in `gm-gen-u4`).
- **Conformance suite:** groups A–F green on both reference adaptors (Beads, Gas Town) and both forcing-function adaptors (Jira, LangGraph).
- **Performance budget:** Kanban render time for 10k beads regresses ≤ 10% vs. Phase 1–8 path. If worse, block `gm-gen-d3`.
- **Auth + nonce suite:** `gm-e3.*` and `gm-e2.7` suites green unchanged.

---

## 8. Success metrics

### 8.1 Per-epic exit criteria (rollup from §4.2)

| Epic | Exit signal |
|---|---|
| `gm-gen-v` | All 5 gates closed (GREEN or FALLBACK documented). |
| `gm-gen-c` | Interfaces compile; conformance harness runs; noop adaptor passes. |
| `gm-gen-a1` | Beads adaptor passes groups A–F. |
| `gm-gen-a2` | Gas Town adaptor passes groups A–F. |
| `gm-gen-a3` | Jira adaptor passes A–F + sandbox smoke. |
| `gm-gen-a4` | LangGraph adaptor passes A–F + checkpoint demo. |
| `gm-gen-a4b` | Stub compiles, capability manifest advertises alpha. |
| `gm-gen-x` | DoD/cost/escalation/capability/evidence all rendering in UI. |
| `gm-gen-u` | SPA snapshot test green; no Beads/Gas Town string outside extensions. |
| `gm-gen-d` | Docs published; release cut; flag default-on. |

### 8.2 Overall migration-complete

(Repeat from §1 executive summary, above.)

### 8.3 Observability signals

- `adaptor.conformance_pass_rate{adaptor_id}` — must be 1.0 in production.
- `workitem.state_change.duration_seconds{adaptor}` — no adaptor regresses > 2× Beads baseline.
- `capability_manifest.version{adaptor}` — alerts if any adaptor drops below agreed minor version.
- `ui.extension_render.count` — sanity check that the extension channel is used (else the UI is too generic) but doesn't dominate (else extensions are leaking).

---

## 9. Risks, open questions, and what we might get wrong

### 9.1 Political risks

- **DD-1 agent-shape rejection.** Gas Town and Gas City maintainers may push back on carrying `role` and `parent_agent` as core fields. Mitigation = fallback collapses these to namespaced extensions; specced in Gate V2's fallback branch; adaptor work doesn't wait.
- **DD-9 edge narrowing friction.** Beads users loudly want all 7 edges always visible. Mitigation = default the dep-graph view to show all declared extensions; the "hide" is an opt-in filter, not a loss.
- **Gas City team silence.** Still the biggest unknown per Phase 1 §6. Mitigation = ship `gm-gen-a4b` as a formal stub with a public questions list; don't block v1 on Gas City wire-up.
- **Future DD-3 re-opening pressure.** Re-opening DD-3 when industry consensus on completion semantics emerges could retroactively force schema changes in deployed Gemba installations. Mitigation: the informational-only schema is versioned (`1.0`) from day one; any future enforcement schema is `schema_version: "2.0"` with opt-in capability-gating, never auto-applied. `1.0` remains a supported schema version indefinitely.

### 9.2 Technical risks

- **Adaptor impedance mismatches in Jira rate-limit handling.** Jira rate limits + webhook delivery delays + our SSE freshness guarantees may not all be mutually satisfiable. Mitigation: `gm-gen-a3.5` has an explicit "prototype first" task; escalate to a rethink if the SLA can't be met.
- **Capability negotiation churn.** As adaptors land, new capabilities will be proposed and the manifest schema will grow. Mitigation = capabilities are add-only within a minor version; we bump `1.0 → 1.1 → 1.2` liberally but never remove in 1.x.
- **LangGraph graph opacity.** v1 commits to opaque `graph` groups; if real LangGraph users immediately ask for topology rendering, that's a v1.1 feature we should scope but not ship in v1.
- **Performance at 10k beads with capability-manifest-driven rendering.** Manifest lookups on every cell render can regress. Mitigation = manifest memoization in the SPA; perf budget test at phase boundaries (§7.3).

### 9.3 Things that will likely change mid-migration and how to absorb them

- **Gas City spec stabilizes mid-flight.** Our `gm-gen-a4b` is explicitly designed to track this. We do NOT freeze against today's Gas City surface.
- **MCP elicitation schema revs.** `EscalationRequest.schema` field may need migration. Mitigation = schema-version the field; adaptors declare supported MCP revs.
- **A2A 1.0 + AP2 payments.** Out of scope for v1 but touches CostMeter. Reserve `CostMeter.native_units` for AP2 amounts if they land before release.
- **New forcing-function adaptor demand.** Users will ask for GitHub Projects or Plane.so before we ship. Mitigation = after `gm-gen-a3` + `gm-gen-a4` land, the conformance harness is the entry point for community adaptors; we do not need to ship those in-tree.
- **Gemba's own UX on escalations untested.** `gm-gen-x3` should prototype against real Gas Town escalation traffic before committing.

---

## 10. Importable JSONL block

### Shell commands

Save the JSONL block below to a file and import. The current `issues.jsonl` is the source of truth for the existing beads; the new-beads block below is purely additive. Apply updates to existing beads via the `bd update` commands that follow.

```bash
# 1. Save the new-beads block to a file
cat > /tmp/migration-issues.jsonl <<'JSONL_END'
# (paste the JSONL lines from the fenced block below between these sentinels)
JSONL_END

# 2. Import new beads (replace with the repo's actual bulk-import path;
#    the existing issues.jsonl convention suggests `bd create` per line
#    or `bd import` if available):
while IFS= read -r line; do
  echo "$line" | bd import --from-stdin
done < /tmp/migration-issues.jsonl

# Fallback if `bd import` is not available, use `bd create --json`:
# while IFS= read -r line; do
#   bd create --json "$line"
# done < /tmp/migration-issues.jsonl

# 3. Apply updates to existing beads
bash /tmp/migration-updates.sh
```

### `bd update` commands for existing beads (§3.5)

Save as `/tmp/migration-updates.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail

# gm-root — patch locked decisions 1, 4, 5, 9, 10 and add generalization label
bd update gm-root --label-add migration:generalization
bd update gm-root --append-description "

# Addendum (Phase 3 migration)

Locked decisions 1, 4, 5, 9, 10 are generalized by the migration initiative tracked under gm-gen-root:
- LD-1: 'talks to gt --json and bd --json' → 'talks to one OrchestrationPlane adaptor and one WorkPlane adaptor; default pairs Gas Town + Beads adaptors'.
- LD-4: pack-agnostic principle now applies to any adaptor (WorkPlane or OrchestrationPlane), driven by CapabilityManifest (Phase 2 §4.6).
- LD-5: 'tmux/k8s/subprocess/exec' → 'WorkspaceKind values declared by the active OrchestrationPlane adaptor'.
- LD-9: 'never write Dolt/JSONL/.gt/.gc/controller.sock directly' generalizes to 'never write any backend's private storage directly; all mutations through adaptor public CLI/API'.
- LD-10: 'city.toml vs .gc/agents/' generalizes to 'declared_state() vs observed_state() from the OrchestrationPlaneAdaptor capability declaration'.

Migration does NOT replace gm-root — the twelve locked decisions remain governing, with these generalizations overlaid."

# gm-e2 — reshape epic
bd update gm-e2 --label-add migration:generalization
bd update gm-e2 --append-description "

# Migration update (Phase 3)

This epic is re-scoped by the generalization initiative:
- gm-e2.1 (domain model) now builds the generalized WorkItem/AgentRef/Relationship/Evidence/DefinitionOfDone types per Phase 2 §2.1 (see gm-gen-c1).
- gm-e2.2 (bd adapter), gm-e2.3 (gt adapter), gm-e2.3b (gc adapter) are superseded by gm-gen-a1 (Beads WorkPlane), gm-gen-a2 (Gas Town OrchestrationPlane), gm-gen-a4b (Gas City OrchestrationPlane stub) respectively.
- gm-e2.4 (fs adapter), gm-e2.5 (SSE hub), gm-e2.7 (nonce gating) are unchanged.
- gm-e2.6 (HTTP + OpenAPI + TS codegen) is updated to regenerate from the generalized types."

# gm-e2.1 — re-scope to generalized types
bd update gm-e2.1 --label-add migration:generalization
bd update gm-e2.1 --append-description "

# Migration update (Phase 3)

Re-scoped: build the GENERALIZED domain types (WorkItem, AgentRef, Relationship, Evidence, DefinitionOfDone, CostMeter, EscalationRequest, Workspace, Agent, AgentGroup, Assignment, Session) per Phase 2 §2.1 and §3.1. Beads-adaptor-specific types move to internal/adapter/beads/types.go. See gm-gen-c1."

# gm-e2.2 — superseded by gm-gen-a1
bd update gm-e2.2 --label-add migration:generalization
bd update gm-e2.2 --append-description "

# Migration update (Phase 3): SUPERSEDED
This work is continued under gm-gen-a1 (Beads WorkPlane adaptor). Leaving open with a blocks dependency until gm-gen-a1 closes."

# gm-e2.3 — superseded by gm-gen-a2
bd update gm-e2.3 --label-add migration:generalization
bd update gm-e2.3 --append-description "

# Migration update (Phase 3): SUPERSEDED
Continued under gm-gen-a2 (Gas Town OrchestrationPlane adaptor)."

# gm-e2.3b — superseded by gm-gen-a4b
bd update gm-e2.3b --label-add migration:generalization
bd update gm-e2.3b --append-description "

# Migration update (Phase 3): SUPERSEDED
Continued under gm-gen-a4b (Gas City OrchestrationPlane stub)."

# gm-e2.4 — updated, names adaptors generically
bd update gm-e2.4 --label-add migration:generalization
bd update gm-e2.4 --append-description "

# Migration update (Phase 3)
Filesystem adapter stays as a shared primitive below the WorkPlane/OrchestrationPlane adaptors. Users: Beads adaptor (gm-gen-a1) tails bd events; Gas Town adaptor (gm-gen-a2) tails .events.jsonl + .gt/daemon.json; Gas City adaptor (gm-gen-a4b) tails city.toml + .gc/agents/*.json."

# gm-e2.6 — regenerate from generalized types
bd update gm-e2.6 --label-add migration:generalization
bd update gm-e2.6 --append-description "

# Migration update (Phase 3)
OpenAPI spec and TS codegen must target the generalized domain types (WorkItem etc. from gm-gen-c1). Blocked by gm-gen-c1."

# gm-e4 through gm-e6: UI epics — update labels + descriptions
for bead in gm-e4 gm-e4.2 gm-e4.3 gm-e4.4 gm-e4.5 gm-e5 gm-e5.1 gm-e5.2 gm-e5.4 gm-e5.7 gm-e5.8 gm-e5.9 gm-e6 gm-e6.1 gm-e6.2 gm-e6.4 gm-e8; do
  bd update "$bead" --label-add migration:generalization
done

bd update gm-e5.2 --append-description "

# Migration update (Phase 3)
Re-scoped: this is now an 'AgentGroup board view' in description; Gas Town 'convoy' is the specific instance the Gas Town adaptor exposes via AgentGroup.mode='static'. UI consumes generic AgentGroup; Beads+Gas Town renders as 'convoy' via the Gas Town adaptor's extension vocabulary."

bd update gm-e5.8 --append-description "

# Migration update (Phase 3)
Re-scoped: becomes 'Adaptor capability browser' — enumerates installed adaptors and their CapabilityManifests. Gas City 'packs' are one specific manifestation the Gas City adaptor exposes."

bd update gm-e6.4 --append-description "

# Migration update (Phase 3): SUPERSEDED by gm-gen-x3 (EscalationRequest pipeline).
Close once gm-gen-x3 delivers the full card-badge + inbox + banner pattern."

bd update gm-e8 --append-description "

# Migration update (Phase 3)
Release criteria expand to: conformance suite green on Beads + Gas Town + Jira + LangGraph adaptors; migration guide (gm-gen-d2) published; GEMBA_GENERALIZED=1 default-on; CapabilityManifest v1.0 declared stable."

# gm-b1 — generalize to 'adaptor-degraded signaling'
bd update gm-b1 --label-add migration:generalization
bd update gm-b1 --append-description "

# Migration update (Phase 3)
Generalized from 'bd daemon offline' to 'OrchestrationEvent{kind:\"adaptor_degraded\"}' signaling for ANY adaptor. Pattern applies to bd (Beads), gt (Gas Town), and future adaptors."
```

### New beads JSONL (67 new beads)

```jsonl
{"id": "gm-gen-root", "title": "Generalization initiative root epic", "description": "Root epic for generalizing Gemba from Beads+Gas Town-only to a pluggable WorkPlane + OrchestrationPlane model per the Phase 2 domain design.\n\n# Goal\nReshape Gemba's adaptor layer so any supported WorkPlane (Beads, Jira, Linear, GitHub Projects, ...) pairs with any supported OrchestrationPlane (Gas Town, Gas City, LangGraph, OpenHands, ...) without UI changes. Introduce Sprint + TokenBudget (DD-14) as a token-budgeted sprint analogue with inform/warn/stop enforcement at epic and sprint scope. Support transport plurality (DD-15: api | jsonl | mcp) so MCP is recommended but not required.\n\n# Scope\nSee migration-generalized-gemba.md §1 for full scope and out-of-scope list.\n\n# Phases\n- gm-gen-v — Validation gates (DD-9, DD-1, DD-4+DD-14, DD-13)\n- gm-gen-c — Core contracts (interfaces, types, conformance harness)\n- gm-gen-a1 — Reference Beads WorkPlane adaptor\n- gm-gen-a2 — Reference Gas Town OrchestrationPlane adaptor (api transport)\n- gm-gen-a3 — Forcing-function Jira WorkPlane adaptor\n- gm-gen-a4 — Forcing-function LangGraph OrchestrationPlane adaptor\n- gm-gen-a4b — Gas City OrchestrationPlane stub\n- gm-gen-x — Cross-cutting features (DoD, CostMeter, Sprint+TokenBudget, Escalation, Capability, Evidence, transport plurality)\n- gm-gen-u — UI generalization\n- gm-gen-d — Documentation + release\n\n# Definition of Done\n- All phase epics closed\n- Conformance suite green on Beads + Gas Town + Jira + LangGraph adaptors\n- At least two adaptor transports proven end-to-end (api + one of jsonl/mcp)\n- Sprint + TokenBudget live with three-tier enforcement; token rollups render in UI\n- GEMBA_GENERALIZED=1 default-on in release binary\n- Migration guide published; existing v1 users have a clean upgrade path\n- No Gas Town/Beads vocabulary appears in SPA outside adaptor-namespaced extensions\n- Every active DD (DD-1..DD-10, DD-12, DD-13, DD-14, DD-15) has a closed task resolving it (DD-11 withdrawn; DD-3 resolved as informational-only)\n**Resolves DDs:** DD-1,DD-2,DD-3,DD-4,DD-5,DD-6,DD-7,DD-8,DD-9,DD-10,DD-12,DD-13,DD-14,DD-15", "issue_type": "epic", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:docs", "tier:opus", "risk:high", "fed:safe"], "dependencies": [{"depends_on_id": "gm-root", "type": "parent-child"}]}
{"id": "gm-gen-v", "title": "Phase V: Validation gates — socialize DD-9, DD-1, DD-4+DD-14, DD-13", "description": "Validation phase — socialize the four gated design decisions with external maintainers and prospective users; freeze fallback designs before any build work starts.\n\n# Goal\nNo gm-gen-a* task begins before every gate is GREEN or FALLBACK-documented.\n\n# Gates\n- V1 — DD-9: 3-core edge taxonomy (parent_of/blocks/relates_to + extension channel)\n- V2 — DD-1: Agent as first-class WorkItem citizen (AgentRef shape)\n- V3 — DD-4 + DD-14: CostMeter axes AND Sprint-as-token-budget redefinition\n- V4 — DD-13: Evidence synthesis requirement\n\n# Not gated (design already resolved)\n- DD-3 (DoD informational-only, no external sign-off needed)\n- DD-8 / DD-15 (transport plurality — MCP is recommended, not required; validated via reference adaptors)\n\n# Definition of Done\n- Every gate outcome (GREEN or FALLBACK) documented at /docs/design/decisions/\n- No GREEN gate has dissenting stakeholder comment unresolved\n**Resolves DDs:** DD-1, DD-9, DD-4, DD-13, DD-14", "issue_type": "epic", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:docs", "tier:opus", "risk:high", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-root", "type": "parent-child"}]}
{"id": "gm-gen-v1", "title": "Gate V1: Socialize DD-9 (3-core edge taxonomy) with Beads author", "description": "# Goal\nSecure sign-off from Steve Yegge on narrowing the core edge set from Beads' 7 to {parent_of, blocks, relates_to} with the 4 Beads-specific edges in the extension channel.\n\n# Inputs\n- Phase 2 §2.4 (edge taxonomy) + DD-9\n- migration-generalized-gemba.md §2 Gate V1\n\n# Outputs\n- Written reply from Beads maintainer or Gemba lead with decision\n- If FALLBACK: core expands to 5 edges; Phase 2 §2.4 patched\n\n# Definition of Done\n- Decision recorded\n- Phase 2 §2.4 patched\n- Timebox: 5 business days\n**Resolves DDs:** DD-9", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:docs", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-v", "type": "parent-child"}]}
{"id": "gm-gen-v2", "title": "Gate V2: Socialize DD-1 (Agent as first-class WorkItem citizen) with Gas Town + Gas City", "description": "# Goal\nConfirm with Gas Town + Gas City maintainers that the AgentRef shape (role + parent_agent + agent_kind) is acceptable as a core type, or land fallback where those become extensions. DD-1 is now the highest-risk political decision now that DD-3 has been deferred to informational-only.\n\n# Inputs\n- Phase 2 §2.1.3 + DD-1\n- migration-generalized-gemba.md §2 Gate V2\n\n# Outputs\n- Written reply with decision\n- If FALLBACK: Phase 2 §2.1.3 patched; AgentRef collapses to {agent_id, display_name, agent_kind}\n\n# Definition of Done\n- Decision recorded\n- Timebox: 7 business days\n**Resolves DDs:** DD-1", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:docs", "tier:opus", "risk:high", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-v", "type": "parent-child"}]}
{"id": "gm-gen-v3", "title": "Gate V3: Socialize DD-4 (CostMeter axes) + DD-14 (Sprint as token-budget)", "description": "Socialize two intertwined decisions: (a) the CostMeter axes `{tokens_total, wallclock_seconds, dollars_est}` + `native_units` extension, and (b) Sprint redefined as token-budget-bounded rather than duration-bounded, with inform/warn/stop defaults 50%/80%/100%.\n\n# Goal\nSecure sign-off (GREEN or FALLBACK) from at least one non-Gas-Town adaptor-implementer candidate for CostMeter axes, AND two Scrum-fluent prospective users for the Sprint redefinition.\n\n# Inputs\n- Phase 2 §4.2 CostMeter schema\n- Phase 2 DD-14 (Sprint + TokenBudget)\n- Phase 2 DD-4\n\n# Outputs\n- Gate V3 outcome documented at /docs/design/decisions/v3.md\n- CostMeter final axis set frozen\n- Sprint UI-copy decision: keep name 'Sprint' (GREEN) or alternate (FALLBACK)\n\n# Definition of Done\n- GREEN or FALLBACK documented; no unresolved objections\n- gm-gen-x2 (CostMeter) and gm-gen-x5 (Sprint+TokenBudget) retargetable to either path\n**Resolves DDs:** DD-4, DD-14", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:docs", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-v", "type": "parent-child"}]}
{"id": "gm-gen-v4", "title": "Gate V4: Socialize DD-13 (evidence synthesis) with first two adaptor authors", "description": "# Goal\nConfirm that adaptor-synthesized evidence (tagged synthesized:true) is acceptable, or land fallback where synthesis is opt-in per adaptor.\n\n# Inputs\n- Phase 2 §2.1.4 + DD-13\n- migration-generalized-gemba.md §2 Gate V5\n\n# Outputs\n- Written reply from the first two prospective adaptor authors\n- If FALLBACK: synthesis becomes opt-in; adaptors without synthesis declare evidence_native:false\n\n# Definition of Done\n- Decision recorded\n- Timebox: 5 business days\n**Resolves DDs:** DD-13", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:docs", "tier:sonnet", "risk:low", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-v", "type": "parent-child"}]}
{"id": "gm-gen-c", "title": "Phase C: Core contracts — WorkPlane + OrchestrationPlane interfaces, types, conformance harness", "description": "# Goal\nDefine the adaptor contracts in code so every downstream adaptor has a stable target. Ship conformance test suite skeletons so adaptor authors can self-validate.\n\n# Inputs\n- gm-gen-v closed (all gates resolved)\n- Phase 2 §2, §3, §4\n\n# Outputs\n- Go + TS type definitions for WorkItem, Relationship, Evidence, DefinitionOfDone, CostMeter, EscalationRequest, Agent, AgentGroup, Assignment, Session, Workspace, CapabilityManifest\n- WorkPlaneAdaptor and OrchestrationPlaneAdaptor Go interfaces\n- Adaptor-registration + version-negotiation RPC\n- Conformance test harness (CLI: `gemba adaptor test --workplane ./my-adaptor`)\n- OTEL-aware event schema\n- Noop reference adaptors passing conformance\n\n# Definition of Done\n- All 7 child tasks closed\n- `gemba adaptor test` runs groups A–F against the noop adaptor and reports pass\n- OpenAPI spec at /api/openapi.json renders adaptor endpoints\n- TypeScript types codegenned into the SPA\n**Resolves DDs:** DD-2,DD-5,DD-7,DD-10,DD-12", "issue_type": "epic", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "surface:protocol", "tier:opus", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-root", "type": "parent-child"}, {"depends_on_id": "gm-gen-v", "type": "blocks"}]}
{"id": "gm-gen-c1", "title": "Define core types: WorkItem, AgentRef, Relationship, Evidence, DefinitionOfDone (informational), Sprint, TokenBudget", "description": "Go source-of-truth types for all WorkPlane core entities, with codegen to TypeScript for the SPA.\n\n# Goal\nOne set of structs in Go that the adaptor library, conformance harness, and codegenned TS types all share. Single source of truth.\n\n# Inputs\n- Phase 2 §2.1 entities\n- DD-14 (Sprint + TokenBudget)\n- DD-3 (DoD informational-only schema)\n\n# Outputs\n- `internal/model/workitem.go` — WorkItem, AgentRef, Relationship, Evidence, DefinitionOfDone (acceptance_criteria + notes + version='1.0'), Sprint, TokenBudget\n- `internal/model/state.go` — StateCategory enum, Sprint state enum, StateMap\n- `web/src/types/generated/` — TS codegen output\n- Round-trip test: Go struct → JSON → TS type → JSON → Go struct yields byte-equivalent output\n\n# Definition of Done\n- `go test ./internal/model/...` green\n- `pnpm --filter web typecheck` green\n- Schema JSON at `/schemas/workitem/1.0.json`, `/schemas/sprint/1.0.json`, `/schemas/dod/1.0.json`\n**Resolves DDs:** DD-2, DD-10, DD-14", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "surface:protocol", "tier:opus", "risk:high", "fed:safe", "area:budget"], "dependencies": [{"depends_on_id": "gm-gen-c", "type": "parent-child"}]}
{"id": "gm-gen-c2", "title": "Define WorkPlaneAdaptor interface (including Sprint ops + budget rollup) + CapabilityManifest (with transport + sprint_native + token_budget_enforced)", "description": "Go interface for any WorkPlane adaptor, plus the CapabilityManifest that every adaptor returns from `describe()`.\n\n# Goal\nFreeze the adaptor contract. Any adaptor author reads this file and knows exactly which methods to implement.\n\n# Inputs\n- Phase 2 §2.5 WorkPlaneAdaptor interface\n- DD-12 (capability negotiation)\n- DD-14 (Sprint ops: create_sprint, read_sprint, update_sprint, transition_sprint, assign_epic_to_sprint, query_sprints, read_budget_rollup)\n- DD-15 (transport field: \"api\" | \"jsonl\" | \"mcp\")\n\n# Outputs\n- `internal/workplane/adaptor.go` — `WorkPlaneAdaptor` interface\n- `internal/workplane/capability.go` — `CapabilityManifest` struct with `Transport` field + `SprintNative` + `TokenBudgetEnforced` capability flags\n- Codegenned TS types\n\n# Definition of Done\n- Noop adaptor compiles against the interface\n- CapabilityManifest JSON schema published\n**Resolves DDs:** DD-9, DD-12, DD-14, DD-15", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "surface:protocol", "tier:opus", "risk:medium", "fed:safe", "area:budget", "area:transport"], "dependencies": [{"depends_on_id": "gm-gen-c1", "type": "blocks"}, {"depends_on_id": "gm-gen-c", "type": "parent-child"}]}
{"id": "gm-gen-c3", "title": "Define OrchestrationPlaneAdaptor interface + OrchestrationCapabilityManifest", "description": "# Goal\nEncode Phase 2 §3.7 interface in Go. Every OrchestrationPlane adaptor implements this.\n\n# Inputs\n- gm-gen-c1 closed\n- Phase 2 §3.1, §3.3–3.7, §3.8\n- Gate V3 outcome (MCP required or fallback)\n\n# Outputs\n- internal/adaptor/orchestration/iface.go with OrchestrationPlaneAdaptor interface\n- OrchestrationCapabilityManifest with workspace_kinds_supported, per_kind_isolation, grouping_modes_supported, assignment_strategies_supported, escalation_sources_emitted, cost_axes_emitted, mcp_endpoint (or not per V3), event_delivery, auth_model\n- Reservation, SessionPrompt, SessionPeek, WorkspaceRequest, WorkspaceStatus types\n- AgentGroup / GroupMembers per §3.1.3\n\n# Definition of Done\n- Interface compiles\n- Per Gate V4 outcome, MCP endpoint is required or optional\n**Resolves DDs:** DD-5,DD-7", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "surface:protocol", "tier:opus", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-c1", "type": "blocks"}, {"depends_on_id": "gm-gen-c", "type": "parent-child"}]}
{"id": "gm-gen-c4", "title": "Adaptor registration + version negotiation protocol across api / jsonl / mcp transports", "description": "Implement the registration flow: adaptor binary (or file + schema) introduces itself to Gemba via its declared transport; Gemba validates the CapabilityManifest; calls are routed per transport for the duration of the session.\n\n# Goal\nGemba can accept adaptors that speak any one of `api`, `jsonl`, or `mcp` with identical downstream behaviour.\n\n# Inputs\n- gm-gen-c2 (WorkPlaneAdaptor interface)\n- DD-8 (MCP recommended not required)\n- DD-15 (transport plurality)\n\n# Outputs\n- `internal/adapter/registry/` — transport-agnostic router\n- `internal/adapter/transport/api.go` — HTTP+JSON transport\n- `internal/adapter/transport/jsonl.go` — file-based import/export\n- `internal/adapter/transport/mcp.go` — MCP client/server profile\n- Semver negotiation (rejects adaptors declaring api_version incompatible with Gemba's)\n\n# Definition of Done\n- Noop adaptor registers over all three transports in integration tests\n- `gemba adaptor register --transport=jsonl ./noop.jsonl` completes round-trip\n- `gemba adaptor register --transport=api http://localhost:9999/` completes round-trip\n**Resolves DDs:** DD-8, DD-12, DD-15", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "surface:protocol", "tier:opus", "risk:medium", "fed:safe", "area:transport"], "dependencies": [{"depends_on_id": "gm-gen-c2", "type": "blocks"}, {"depends_on_id": "gm-gen-c3", "type": "blocks"}, {"depends_on_id": "gm-gen-c", "type": "parent-child"}]}
{"id": "gm-gen-c5", "title": "Conformance test harness: `gemba adaptor test` CLI runs groups A–F", "description": "# Goal\nShip a CLI that adaptor authors can run locally (`gemba adaptor test --workplane ./my-adaptor` or `--orchestration ./my-adaptor`) to self-validate against Phase 2 §2.6 and §3.8 test suites.\n\n# Inputs\n- gm-gen-c2, gm-gen-c3 closed\n- Phase 2 §2.6 groups A–F, §3.8 groups A–F\n\n# Outputs\n- internal/conformance/workplane/ with group A–F tests\n- internal/conformance/orchestration/ with group A–F tests\n- cmd/gemba/adaptor_test.go subcommand\n- JSON + human-readable output with per-test pass/fail + reason\n- Golden fixtures for round-trip testing\n\n# Definition of Done\n- `gemba adaptor test --workplane ./noop-workplane` reports all pass\n- `gemba adaptor test --orchestration ./noop-orchestration` reports all pass\n- Test output machine-readable for CI usage\n**Resolves DDs:** DD-12\n\n# Updated for DD-15\nThe conformance harness MUST run identically against any declared transport. Tests live in `internal/conformance/`; transport is a configuration, not a test axis. CI runs the suite against the noop reference adaptor over all three transports.\n\n**Resolves DDs (updated):** DD-12, DD-15", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "tier:opus", "risk:medium", "fed:safe", "area:transport"], "dependencies": [{"depends_on_id": "gm-gen-c4", "type": "blocks"}, {"depends_on_id": "gm-gen-c", "type": "parent-child"}]}
{"id": "gm-gen-c6", "title": "Event schema + OTEL trace propagation across adaptor boundary", "description": "# Goal\nImplement Phase 2 §4.4 BulletCityEvent + W3C trace context propagation so adaptor-emitted events retain cross-component correlation.\n\n# Inputs\n- gm-gen-c2, gm-gen-c3 closed\n- Phase 2 §4.4\n\n# Outputs\n- internal/events/schema.go (BulletCityEvent unified)\n- OTEL exporter wrapper; adaptors inherit CallCtx.trace_id\n- Integration with gm-e2.5 SSE hub\n- Metric emitters: workitem.state_duration_seconds, assignment.total_cost_dollars, escalation.open_count, session.spawn_rate, workspace.acquire_latency_seconds, bd_stats-compatible export\n\n# Definition of Done\n- Events flow adaptor→hub→SPA with trace_id intact (verified via OTEL collector stub)\n- Prometheus-style metrics endpoint exposes named metrics\n**Resolves DDs:** DD-12\n\n# Updated for DD-14\nEvent schema MUST include `budget.inform`, `budget.warn`, `budget.stop` events emitted on the first threshold crossing for any epic or sprint in scope. These events carry `{scope_kind, scope_id, threshold, consumed, total}`.\n\n**Resolves DDs (updated):** DD-12, DD-14", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:events", "tier:sonnet", "risk:medium", "fed:safe", "area:budget"], "dependencies": [{"depends_on_id": "gm-gen-c2", "type": "blocks"}, {"depends_on_id": "gm-gen-c3", "type": "blocks"}, {"depends_on_id": "gm-gen-c", "type": "parent-child"}]}
{"id": "gm-gen-c7", "title": "Noop in-memory reference adaptors (WorkPlane + OrchestrationPlane) passing conformance", "description": "# Goal\nBuild in-memory reference adaptors that pass the full conformance suite. Used for SPA development without a real backend and as the gold-standard 'does the contract even compose' integration test.\n\n# Inputs\n- gm-gen-c5 closed\n\n# Outputs\n- internal/adaptor/noop/workplane/ in-memory WorkPlane adaptor\n- internal/adaptor/noop/orchestration/ in-memory OrchestrationPlane adaptor\n- Seeded fixtures: 100 WorkItems, 5 Agents, 2 AgentGroups, 10 Sessions, ~20 Events, a few EscalationRequests\n- `gemba serve --noop` starts with both noop adaptors\n\n# Definition of Done\n- `gemba adaptor test` green on both noop adaptors, all groups\n- SPA renders against `gemba serve --noop` with full feature set\n- Tests for the noop adaptors themselves exist (recursive sanity)\n**Resolves DDs:** DD-12\n\n# Updated for DD-15\nThe noop reference adaptor ships as a `jsonl`-transport adaptor so CI exercises the file-based transport path. A secondary noop variant exposes the same state over `api` for cross-transport conformance comparison.\n\n**Resolves DDs (updated):** DD-12, DD-15", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "tier:sonnet", "risk:low", "fed:safe", "area:transport"], "dependencies": [{"depends_on_id": "gm-gen-c5", "type": "blocks"}, {"depends_on_id": "gm-gen-c", "type": "parent-child"}]}
{"id": "gm-gen-a1", "title": "Phase A1: Beads WorkPlane reference adaptor", "description": "# Goal\nImplement the Beads WorkPlane adaptor as the first conformance-passing reference. Supersedes gm-e2.2.\n\n# Inputs\n- gm-gen-c closed (contracts + harness ready)\n- Phase 2 §5.1.1 (Beads adaptor sketch)\n\n# Outputs\n- internal/adaptor/beads/ full implementation\n- Conformance suite groups A–F green\n- Integration with real bd CLI in tmpdir test harness\n- Beads-specific extensions registered: beads.priority, beads.labels, beads.dolt_ref, beads.bd_remember_ids, beads.discovered_from, beads.waits_for, beads.replies_to, beads.conditional_blocks\n\n# Definition of Done\n- All 7 child tasks closed\n- `gemba adaptor test --workplane gemba-beads-adaptor` green on all groups\n- No regressions in existing Gemba Beads functionality (regression suite from §7 passes)\n- gm-e2.2 marked superseded-close\n**Resolves DDs:** DD-1,DD-2,DD-3,DD-9,DD-10,DD-13", "issue_type": "epic", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-bd", "tier:opus", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-root", "type": "parent-child"}, {"depends_on_id": "gm-gen-c", "type": "blocks"}]}
{"id": "gm-gen-a1.1", "title": "Beads WorkPlane adaptor: CRUD + query via `bd --json`", "description": "# Goal\nImplement WorkPlaneAdaptor.create/read/update/query for Beads via `bd --json` subprocess invocation. Supersedes gm-e2.2 CRUD surface.\n\n# Inputs\n- gm-gen-c2 closed\n- bd >= 0.60.0\n\n# Outputs\n- internal/adaptor/beads/crud.go with create/read/update/query\n- Process pool to avoid forking per-call\n- Error classification: NotFoundError, ConflictError, SchemaError, adaptor-degraded (gm-b1)\n- Query filter translation: state_category→bd status filter, assignee→claim, parent_id→parent edge, repository→prefix\n\n# Definition of Done\n- Conformance group A (CRUD + query) green\n- Existing gm-e2.2 integration tests pass through the new adaptor\n**Resolves DDs:** DD-2", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-bd", "tier:sonnet", "risk:high", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a1", "type": "parent-child"}]}
{"id": "gm-gen-a1.2", "title": "Beads edge mapping: 7 native edges → 3 core + 4 extensions", "description": "# Goal\nImplement the Phase 2 §2.4 Beads 7→3 edge mapping. parent-child→parent_of, blocks→blocks, related→relates_to; discovered-from, waits-for (with dual blocks), replies-to, conditional-blocks→extensions.\n\n# Inputs\n- gm-gen-a1.1 closed\n- Gate V2 outcome (3 vs 5 core edges)\n\n# Outputs\n- internal/adaptor/beads/edges.go\n- Bidirectional mapping with round-trip tests\n- CapabilityManifest.relationship_extensions declares the 4 Beads extensions with display names\n- waits-for written as both a blocks core edge AND beads.waits_for extension; read prefers extension if present, falls back to blocks\n\n# Definition of Done\n- Conformance group C green\n- For each of 7 Beads edge types, create+read round-trip preserves semantics\n- Dep-graph view automatically surfaces all 7 when connected to Beads (via CapabilityManifest read)\n**Resolves DDs:** DD-9", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-bd", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a1.1", "type": "blocks"}, {"depends_on_id": "gm-gen-a1", "type": "parent-child"}]}
{"id": "gm-gen-a1.3", "title": "Beads AgentRef ↔ bd claim federation (DD-1)", "description": "# Goal\nImplement DD-1 federation for Beads: AgentRef.agent_id ↔ bd's claim string, with synthesis of role + parent_agent from labels.\n\n# Inputs\n- gm-gen-a1.1 closed\n- Gate V2 outcome (AgentRef shape)\n\n# Outputs\n- internal/adaptor/beads/identity.go\n- resolve_assignee: AgentRef → claim string; role/parent_agent serialized via `agent-role:*` and `agent-parent:*` labels on the bead\n- identity_from_backend: claim string → AgentRef; labels parsed to reconstruct\n- Tests for lossy round-trip (Jira-style change bypassing adaptor)\n\n# Definition of Done\n- Conformance group E green\n- Per Gate V2 outcome, AgentRef shape matches final decision\n**Resolves DDs:** DD-1", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-bd", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a1.1", "type": "blocks"}, {"depends_on_id": "gm-gen-v2", "type": "blocks"}, {"depends_on_id": "gm-gen-a1", "type": "parent-child"}]}
{"id": "gm-gen-a1.4", "title": "Beads DoD pass-through: free-text acceptance_criteria field on the bead", "description": "# Goal\nImplement informational-only DoD for Beads per DD-3. Map `dod.acceptance_criteria` and `dod.notes` to a single new free-text `acceptance_criteria` field on the bead, written/read via `bd` CLI. No schema evaluation, no predicate dispatch, no `bc_dod` table.\n\n# Inputs\n- gm-gen-c1 (DoD type) closed\n- gm-gen-a1.1 closed\n\n# Outputs\n- internal/adaptor/beads/dod.go with read/write pass-through only\n- `bd` CLI surface for setting/reading the new field (contribute to bd if needed)\n- DoD mutations ride as a standard WorkItem update patch (no dedicated set_dod method)\n\n# Definition of Done\n- DoD round-trip (write free-text, read back) preserves bytes\n- Conformance test for DoD preservation passes\n- No evaluation pipeline invoked\n**Resolves DDs:** DD-3", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-bd", "tier:sonnet", "risk:low", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a1.1", "type": "blocks"}, {"depends_on_id": "gm-gen-a1", "type": "parent-child"}]}
{"id": "gm-gen-a1.5", "title": "Beads evidence synthesis from work-history + Dolt refs", "description": "# Goal\nSynthesize Evidence records from Beads work-history rows and Dolt commit SHAs. Tag synthesized:true per DD-13.\n\n# Inputs\n- gm-gen-c1 closed\n- gm-gen-a1.1 closed\n- gm-gen-x5 shared synthesis library (optional — can ship standalone here first)\n- Gate V5 outcome\n\n# Outputs\n- internal/adaptor/beads/evidence.go\n- On read, synthesize Evidence{type:'commit', ref:'sha:...', synthesized:true} from agent work-history + Dolt\n- attach_evidence writes to Beads work-history table via bd CLI\n- Native evidence (from bd work-history) tagged synthesized:false\n\n# Definition of Done\n- Evidence round-trip: attach then read returns same record\n- Synthesized evidence clearly flagged; UI can filter\n- Conformance test for evidence preservation passes\n**Resolves DDs:** DD-13", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-bd", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a1.1", "type": "blocks"}, {"depends_on_id": "gm-gen-a1", "type": "parent-child"}]}
{"id": "gm-gen-a1.6", "title": "Beads subscribe/event delivery via fsnotify + `bd events`", "description": "# Goal\nImplement WorkPlaneAdaptor.subscribe for Beads using the existing fsnotify tailer (gm-e2.4) plus `bd events` for structured events.\n\n# Inputs\n- gm-gen-a1.1 closed\n- gm-e2.4 (fs adapter) complete\n- gm-gen-c6 (event schema) closed\n\n# Outputs\n- internal/adaptor/beads/events.go\n- CapabilityManifest declares event_delivery: 'sse' (via server-side translation) or 'poll' with poll_interval_seconds\n- subscribe returns an async iterable of WorkPlaneEvent with before/after for state changes\n- Integration with gm-e2.5 SSE hub\n\n# Definition of Done\n- Conformance group D (event delivery) green\n- Existing gm-e2.5 SSE integration tests continue to pass via the new adaptor\n**Resolves DDs:** DD-12", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-bd", "layer:events", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a1.1", "type": "blocks"}, {"depends_on_id": "gm-gen-c6", "type": "blocks"}, {"depends_on_id": "gm-gen-a1", "type": "parent-child"}]}
{"id": "gm-gen-a1.7", "title": "Beads adaptor passes conformance suite groups A–F", "description": "# Goal\nBring the Beads adaptor to full conformance. This is the exit gate for gm-gen-a1.\n\n# Inputs\n- gm-gen-a1.1..a1.6 closed\n- gm-gen-c5 (conformance harness) closed\n\n# Outputs\n- CI job running `gemba adaptor test --workplane gemba-beads-adaptor` green\n- Any remaining group-F extension-preservation issues resolved\n- Regression suite (§7) green\n\n# Definition of Done\n- 100% of A–F tests green\n- CI job is now a required check on PRs that touch the Beads adaptor\n- gm-e2.2 marked superseded and closed\n**Resolves DDs:** DD-2,DD-9,DD-13", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-bd", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a1.2", "type": "blocks"}, {"depends_on_id": "gm-gen-a1.3", "type": "blocks"}, {"depends_on_id": "gm-gen-a1.4", "type": "blocks"}, {"depends_on_id": "gm-gen-a1.5", "type": "blocks"}, {"depends_on_id": "gm-gen-a1.6", "type": "blocks"}, {"depends_on_id": "gm-gen-a1", "type": "parent-child"}]}
{"id": "gm-gen-a2", "title": "Phase A2: Gas Town OrchestrationPlane reference adaptor", "description": "# Goal\nImplement Gas Town as the first conformance-passing OrchestrationPlane adaptor. Supersedes gm-e2.3.\n\n# Inputs\n- gm-gen-c closed\n- gm-gen-a1 closed (end-to-end needs both planes)\n- Phase 2 §5.2.1 (Gas Town adaptor sketch)\n\n# Outputs\n- internal/adaptor/gastown/ full implementation\n- Conformance suite groups A–F green\n- All existing Gas Town functionality preserved\n\n# Definition of Done\n- All 7 child tasks closed\n- `gemba adaptor test --orchestration gemba-gastown-adaptor` green\n- Regression suite (§7) green for Gas Town + Beads pair\n- gm-e2.3 superseded and closed\n**Resolves DDs:** DD-1,DD-4,DD-5,DD-6,DD-7,DD-8,DD-12", "issue_type": "epic", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-gt", "tier:opus", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-root", "type": "parent-child"}, {"depends_on_id": "gm-gen-c", "type": "blocks"}, {"depends_on_id": "gm-gen-a1", "type": "blocks"}]}
{"id": "gm-gen-a2.1", "title": "Gas Town: list_agents, list_groups (convoy→static, pool→pool)", "description": "# Goal\nImplement Agent and AgentGroup enumeration for Gas Town. Convoys map to AgentGroup{mode:'static'}; worker pools map to AgentGroup{mode:'pool'} with the `check` command wrapped.\n\n# Inputs\n- gm-gen-c3 closed, gm-gen-a2 parent open\n\n# Outputs\n- internal/adaptor/gastown/agents.go, groups.go\n- `gt agents --json` → []Agent with gastown.role, gastown.rig_path extensions\n- `gt convoy list --json` → []AgentGroup{static}\n- Worker pool (e.g., polecat) → AgentGroup{pool, check_endpoint: wraps shell check}\n- CapabilityManifest declares grouping_modes_supported: ['static','pool']\n\n# Definition of Done\n- Conformance group A green\n- Existing Gas Town agent + convoy UI works via the new adaptor\n**Resolves DDs:** DD-7", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-gt", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a2", "type": "parent-child"}]}
{"id": "gm-gen-a2.2", "title": "Gas Town: acquire_workspace / release_workspace (tmux rig → WorkspaceKind=worktree)", "description": "# Goal\nImplement workspace primitives for Gas Town. Rigs (worktree + tmux session) → Workspace{kind:'worktree', isolation.fs_scoped:true, net_isolated:false, cpu_limited:false, mem_limited:false, snapshot_restore:false}.\n\n# Inputs\n- gm-gen-c3 closed\n\n# Outputs\n- internal/adaptor/gastown/workspace.go\n- `gt rig add` / `gt rig remove` wrapped\n- CapabilityManifest declares per_kind_isolation['worktree'] fully\n- WorkspaceRequest negotiation: rejects required_isolation.net_isolated=true\n\n# Definition of Done\n- Conformance group C (workspace) green\n- RFC provider-aware agent detail (gm-e5.9) renders worktree kind correctly\n**Resolves DDs:** DD-5", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-gt", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a2", "type": "parent-child"}]}
{"id": "gm-gen-a2.3", "title": "Gas Town: session lifecycle + tmux capture-pane peek", "description": "# Goal\nImplement start_session, pause_session, resume_session, end_session, peek_session. Peek uses `tmux capture-pane`; pause/resume map to tmux send-keys C-z / fg or process SIGSTOP/SIGCONT as Gas Town docs dictate.\n\n# Inputs\n- gm-gen-a2.2 closed\n\n# Outputs\n- internal/adaptor/gastown/session.go\n- SessionPeek populated with last-N lines of tmux pane\n- Idempotent end_session via nonce gating\n\n# Definition of Done\n- Conformance group B green (incl. claim_race, reservation_expires, session_peek_during_running)\n- SPA provider-aware detail view renders session state\n**Resolves DDs:** DD-12", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-gt", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a2.1", "type": "blocks"}, {"depends_on_id": "gm-gen-a2.2", "type": "blocks"}, {"depends_on_id": "gm-gen-a2", "type": "parent-child"}]}
{"id": "gm-gen-a2.4", "title": "Gas Town: cost meter synthesis (tokens + wallclock from session telemetry)", "description": "# Goal\nSynthesize CostMeter samples for Gas Town sessions. tokens_total from wrapped Claude Code/Codex/Gemini stderr parsing; wallclock_seconds from session duration.\n\n# Inputs\n- gm-gen-a2.3 closed\n- Gate V4 outcome (cost axes)\n\n# Outputs\n- internal/adaptor/gastown/cost.go\n- Per-session sampler emits CostSample on session events (start, periodic, end)\n- CapabilityManifest.cost_axes_emitted reflects V4 outcome (GREEN: ['tokens','wallclock','dollars_est'], FALLBACK: ['wallclock','native'])\n- Aggregator feeds gm-gen-x2 rollups\n\n# Definition of Done\n- CostMeter samples appear in events for a live Gas Town session\n- Insights panel (gm-e6.2) shows Gas Town costs via the new path\n**Resolves DDs:** DD-4", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-gt", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a2.3", "type": "blocks"}, {"depends_on_id": "gm-gen-v3", "type": "blocks"}, {"depends_on_id": "gm-gen-a2", "type": "parent-child"}]}
{"id": "gm-gen-a2.5", "title": "Gas Town: escalation mapping (`gt escalate` → EscalationRequest)", "description": "# Goal\nMap Gas Town escalations to EscalationRequest{source:'orchestrator_pause'}. Tail gt escalate events; expose list_open_escalations + resolve_escalation.\n\n# Inputs\n- gm-gen-a2.3 closed\n- gm-gen-c1 EscalationRequest type closed\n\n# Outputs\n- internal/adaptor/gastown/escalation.go\n- Gas Town escalation events → EscalationRequest with severity mapped to urgency\n- CapabilityManifest.escalation_sources_emitted: ['orchestrator_pause']\n- resolve_escalation round-trips to `gt ack` or equivalent\n\n# Definition of Done\n- Conformance group D green\n- gm-gen-x3 (UI inbox) renders Gas Town escalations\n**Resolves DDs:** DD-6", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-gt", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a2.3", "type": "blocks"}, {"depends_on_id": "gm-gen-a2", "type": "parent-child"}]}
{"id": "gm-gen-a2.6", "title": "Gas Town adaptor declares transport: \"api\"; ships HTTP+JSON shim over gt --json + bd --json CLIs", "description": "Per DD-8 + DD-15, the Gas Town adaptor declares `transport: \"api\"` in its CapabilityManifest. Gemba talks to it over HTTP+JSON; the adaptor shells out to `gt --json` and `bd --json` internally. No MCP bridge is required.\n\n# Goal\nGas Town adaptor is a native `api`-transport adaptor, proving the loosened DD-8 stance.\n\n# Inputs\n- gm-gen-c4 (transport router)\n- DD-15 (transport plurality)\n- DD-8 (MCP not required)\n\n# Outputs\n- `internal/adapter/gastown/server.go` — HTTP+JSON handler\n- Adaptor binary `gm-adaptor-gastown` registering via `transport: \"api\"`\n- No MCP dependencies in this adaptor's go.mod\n\n# Definition of Done\n- `gemba adaptor register --transport=api` succeeds against a running Gas Town v1 install\n- Conformance groups A–F run green over the api transport\n**Resolves DDs:** DD-8, DD-15", "issue_type": "task", "priority": 2, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-gt", "surface:protocol", "tier:sonnet", "risk:medium", "fed:safe", "area:transport"], "dependencies": [{"depends_on_id": "gm-gen-a2.5", "type": "blocks"}, {"depends_on_id": "gm-gen-a2", "type": "parent-child"}]}
{"id": "gm-gen-a2.7", "title": "Gas Town adaptor passes conformance suite A–F", "description": "# Goal\nBring the Gas Town adaptor to full conformance. Exit gate for gm-gen-a2.\n\n# Inputs\n- gm-gen-a2.1..a2.6 closed\n\n# Outputs\n- CI job running `gemba adaptor test --orchestration gemba-gastown-adaptor` green\n- Regression suite green\n- gm-e2.3 superseded and closed\n\n# Definition of Done\n- 100% of A–F green\n- No regressions in existing Gas Town functionality\n**Resolves DDs:** DD-5,DD-6,DD-7,DD-8", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-gt", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a2.1", "type": "blocks"}, {"depends_on_id": "gm-gen-a2.2", "type": "blocks"}, {"depends_on_id": "gm-gen-a2.3", "type": "blocks"}, {"depends_on_id": "gm-gen-a2.4", "type": "blocks"}, {"depends_on_id": "gm-gen-a2.5", "type": "blocks"}, {"depends_on_id": "gm-gen-a2.6", "type": "blocks"}, {"depends_on_id": "gm-gen-a2", "type": "parent-child"}]}
{"id": "gm-gen-a3", "title": "Phase A3: Jira WorkPlane forcing-function adaptor", "description": "# Goal\nImplement Jira as the hardest-case WorkPlane adaptor to prove the abstraction. Jira's workflow FSM, custom fields, rate limits, absence of agent + DoD + evidence primitives are the superset of Linear / GitHub Issues / Shortcut concerns.\n\n# Inputs\n- gm-gen-a1 closed (contract proven with one reference)\n- Phase 2 §5.1.2 (Jira sketch)\n\n# Outputs\n- internal/adaptor/jira/ implementation\n- Conformance suite A–F green\n- Read+write smoke test against an Atlassian Jira Cloud sandbox\n\n# Definition of Done\n- All 6 children closed\n- `gemba adaptor test --workplane gemba-jira-adaptor` green\n- Sandbox smoke test CI job passes (with secrets)\n**Resolves DDs:** DD-1,DD-3,DD-9,DD-12,DD-13", "issue_type": "epic", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "area:jira", "tier:opus", "risk:high", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-root", "type": "parent-child"}, {"depends_on_id": "gm-gen-a1", "type": "blocks"}]}
{"id": "gm-gen-a3.1", "title": "Jira WorkPlane adaptor: CRUD + query via Atlassian REST v3", "description": "# Goal\nImplement CRUD for Jira issues via the Cloud REST v3 API.\n\n# Inputs\n- gm-gen-c2 closed\n- Atlassian REST v3 docs\n\n# Outputs\n- internal/adaptor/jira/crud.go\n- JQL translation from WorkItemFilter\n- Extension field schema discovery via /rest/api/3/field\n- Error mapping: Jira 403→ConflictError, 404→NotFoundError, 429→backpressure\n\n# Definition of Done\n- Conformance group A green against sandbox\n**Resolves DDs:** DD-2", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "area:jira", "tier:sonnet", "risk:high", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a3", "type": "parent-child"}]}
{"id": "gm-gen-a3.2", "title": "Jira: workflow FSM → state_map.valid_transitions with refresh", "description": "# Goal\nPopulate CapabilityManifest.state_map.valid_transitions from the Jira workflow API. Refresh on schedule. SPA disables invalid transitions in drag-drop.\n\n# Inputs\n- gm-gen-a3.1 closed\n\n# Outputs\n- internal/adaptor/jira/workflow.go\n- CapabilityManifest declares workflow_fsm capability\n- Transition validation on write; invalid targets return InvalidTransitionError\n\n# Definition of Done\n- Conformance group B: transition_invalid_rejected, transition_valid green\n**Resolves DDs:** DD-12", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "area:jira", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a3.1", "type": "blocks"}, {"depends_on_id": "gm-gen-a3", "type": "parent-child"}]}
{"id": "gm-gen-a3.3", "title": "Jira: synthesize Agent concept via `bc.agent_role` + `bc.parent_agent` custom fields", "description": "# Goal\nJira has no native agent primitive. Adaptor uses two custom fields (`bc.agent_role`, `bc.parent_agent`) on issues; reads reconstruct AgentRef; writes populate both.\n\n# Inputs\n- gm-gen-a3.1 closed\n- Gate V2 outcome\n\n# Outputs\n- internal/adaptor/jira/identity.go\n- resolve_assignee writes both native assignee + the two custom fields\n- identity_from_backend reads custom fields; graceful fallback to HumanRef when missing\n- Bootstrap documentation for admins on custom field setup\n\n# Definition of Done\n- Conformance group E green in sandbox (with custom fields configured)\n- Graceful degradation if fields absent\n**Resolves DDs:** DD-1", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "area:jira", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a3.1", "type": "blocks"}, {"depends_on_id": "gm-gen-a3", "type": "parent-child"}]}
{"id": "gm-gen-a3.4", "title": "Jira: DoD pass-through to native free-text (acceptance criteria field or description section)", "description": "# Goal\nPer DD-3, DoD is informational-only. Adaptor passes `dod.acceptance_criteria` through to whichever native free-text field the Jira instance uses. Preference order: the `Acceptance Criteria` custom field if configured; else a clearly-delimited `## Acceptance Criteria` section appended to `description`. No JSON custom field, no evaluator, no `bc.dod`.\n\n# Inputs\n- gm-gen-a3.1 closed\n- Domain doc DD-3 (informational-only stance)\n\n# Outputs\n- internal/adaptor/jira/dod.go with read/write pass-through only\n- Custom-field discovery at registration picks the right target field\n- Description-section fallback is byte-stable (no reformatting)\n\n# Definition of Done\n- DoD round-trip preserves prose byte-for-byte within a session\n- Conformance test for DoD preservation passes\n**Resolves DDs:** DD-3", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "area:jira", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a3.1", "type": "blocks"}, {"depends_on_id": "gm-gen-a3", "type": "parent-child"}]}
{"id": "gm-gen-a3.5", "title": "Jira: rate-limit-aware subscribe via webhooks + coalescing", "description": "# Goal\nImplement subscribe for Jira using its webhook facility + coalesced polling for gap-filling. Jira rate limits are aggressive; naive polling will not meet SLAs.\n\n# Inputs\n- gm-gen-a3.1 closed\n- gm-gen-c6 event schema\n\n# Outputs\n- internal/adaptor/jira/events.go with webhook receiver + poll coalescer\n- Backpressure: 429 → exponential backoff, surfaced as adaptor_degraded events\n- CapabilityManifest declares event_delivery: 'push' with fallback poll_interval_seconds\n\n# Definition of Done\n- Conformance group D green (event latency < 30s in sandbox)\n- Synthetic rate-limit storm test does not drop events\n**Resolves DDs:** DD-12", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "area:jira", "layer:events", "tier:sonnet", "risk:high", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a3.1", "type": "blocks"}, {"depends_on_id": "gm-gen-a3", "type": "parent-child"}]}
{"id": "gm-gen-a3.6", "title": "Jira adaptor passes conformance suite A–F", "description": "# Goal\nBring Jira adaptor to full conformance.\n\n# Inputs\n- gm-gen-a3.1..a3.5 closed\n\n# Outputs\n- CI job running conformance against sandbox\n- Published 'Jira adaptor setup guide' linked from gm-gen-d1\n\n# Definition of Done\n- 100% A–F green\n- Documented quirks (rate-limit handling, custom field setup)\n**Resolves DDs:** DD-1,DD-3,DD-9", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "area:jira", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a3.1", "type": "blocks"}, {"depends_on_id": "gm-gen-a3.2", "type": "blocks"}, {"depends_on_id": "gm-gen-a3.3", "type": "blocks"}, {"depends_on_id": "gm-gen-a3.4", "type": "blocks"}, {"depends_on_id": "gm-gen-a3.5", "type": "blocks"}, {"depends_on_id": "gm-gen-a3", "type": "parent-child"}]}
{"id": "gm-gen-a4", "title": "Phase A4: LangGraph OrchestrationPlane forcing-function adaptor", "description": "# Goal\nProve the OrchestrationPlane abstraction against LangGraph — no native agent identity, no native work item, graph-mode grouping, checkpoint-based session. Expose the largest impedance mismatch in the ecosystem.\n\n# Inputs\n- gm-gen-a2 closed\n- Phase 2 §5.2.3 (LangGraph sketch)\n\n# Outputs\n- internal/adaptor/langgraph/ implementation\n- End-to-end demo: LangGraph thread checkpointed and resumed from the Gemba UI\n- Conformance suite A–F green\n\n# Definition of Done\n- All 6 children closed\n- Demo video or recorded session attached\n**Resolves DDs:** DD-1,DD-4,DD-5,DD-7,DD-8,DD-12", "issue_type": "epic", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "area:langgraph", "tier:opus", "risk:high", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-root", "type": "parent-child"}, {"depends_on_id": "gm-gen-a2", "type": "blocks"}]}
{"id": "gm-gen-a4.1", "title": "LangGraph: Agent synthesis from node paths, thread_id as session", "description": "# Goal\nSynthesize AgentRef per LangGraph node; thread_id → Session.id; StateGraph checkpoint → Session.status='suspended'.\n\n# Inputs\n- gm-gen-c3 closed\n- Gate V2 outcome\n\n# Outputs\n- internal/adaptor/langgraph/agents.go\n- Agent.id derived from node path; role from node type (agent / function / subgraph)\n- thread_id → session.id mapping\n\n# Definition of Done\n- Conformance group A green on a sample graph\n**Resolves DDs:** DD-1", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "area:langgraph", "tier:sonnet", "risk:high", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a4", "type": "parent-child"}]}
{"id": "gm-gen-a4.2", "title": "LangGraph: AgentGroup{mode:'graph'} surfacing", "description": "# Goal\nExpose StateGraph subgraphs as AgentGroup{mode:'graph'}. v1 treats internal topology as opaque; resolve_group_members returns current members, not edges.\n\n# Inputs\n- gm-gen-a4.1 closed\n- DD-7 opacity commitment\n\n# Outputs\n- internal/adaptor/langgraph/groups.go\n- CapabilityManifest declares grouping_modes_supported: ['graph']\n\n# Definition of Done\n- Conformance group A: graph_group_opaque_but_stable green\n**Resolves DDs:** DD-7", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "area:langgraph", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a4.1", "type": "blocks"}, {"depends_on_id": "gm-gen-a4", "type": "parent-child"}]}
{"id": "gm-gen-a4.3", "title": "LangGraph: checkpoint → suspend/resume; HITL interrupt → EscalationRequest", "description": "# Goal\nMap LangGraph checkpoint/resume to Session.status transitions; map LangGraph's interrupt() to EscalationRequest{source:'orchestrator_pause', urgency:'blocking'}.\n\n# Inputs\n- gm-gen-a4.1 closed\n\n# Outputs\n- internal/adaptor/langgraph/session.go\n- pause_session → persist checkpoint; resume_session → resume from last checkpoint\n- Interrupt detection → EscalationRequest emission\n\n# Definition of Done\n- Conformance group B + D green on interrupt demo\n- resolve_escalation unblocks the session (approve → graph resumes)\n**Resolves DDs:** DD-6", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "area:langgraph", "tier:sonnet", "risk:high", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a4.1", "type": "blocks"}, {"depends_on_id": "gm-gen-a4", "type": "parent-child"}]}
{"id": "gm-gen-a4.4", "title": "LangGraph: cost meter from LangSmith token pull", "description": "# Goal\nPull token counts from LangSmith traces into CostMeter.tokens_total. wallclock_seconds from thread execution time.\n\n# Inputs\n- gm-gen-a4.1 closed\n- Gate V4 outcome\n\n# Outputs\n- internal/adaptor/langgraph/cost.go\n- LangSmith API client; sampling cadence configurable\n\n# Definition of Done\n- CostSample events flow to insights panel\n**Resolves DDs:** DD-4", "issue_type": "task", "priority": 2, "status": "open", "labels": ["migration:generalization", "surface:backend", "area:langgraph", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a4.1", "type": "blocks"}, {"depends_on_id": "gm-gen-v3", "type": "blocks"}, {"depends_on_id": "gm-gen-a4", "type": "parent-child"}]}
{"id": "gm-gen-a4.5", "title": "LangGraph: workspace — declared `exec`, fs_scoped with documented caveat", "description": "# Goal\nLangGraph itself isolates nothing. Adaptor declares WorkspaceKind='exec' with fs_scoped:true relying on user-provided tools to honor cwd scoping. Documents the caveat prominently.\n\n# Inputs\n- gm-gen-c3 closed\n\n# Outputs\n- internal/adaptor/langgraph/workspace.go\n- CapabilityManifest.per_kind_isolation['exec']: {fs_scoped:true, net_isolated:false, cpu_limited:false, mem_limited:false, snapshot_restore:false}\n- Docs warning in adaptor README\n\n# Definition of Done\n- Conformance group C honors required_isolation rejection\n**Resolves DDs:** DD-5", "issue_type": "task", "priority": 2, "status": "open", "labels": ["migration:generalization", "surface:backend", "area:langgraph", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a4", "type": "parent-child"}]}
{"id": "gm-gen-a4.6", "title": "LangGraph adaptor passes conformance A–F", "description": "# Goal\nFull conformance + demo.\n\n# Inputs\n- gm-gen-a4.1..a4.5 closed\n\n# Outputs\n- CI job green\n- Demo recording: create LangGraph thread, pause via Gemba UI, edit state, resume\n\n# Definition of Done\n- 100% A–F green\n- Demo linked from gm-gen-d1 adaptor authoring guide\n**Resolves DDs:** DD-5,DD-6,DD-7", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "area:langgraph", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a4.1", "type": "blocks"}, {"depends_on_id": "gm-gen-a4.2", "type": "blocks"}, {"depends_on_id": "gm-gen-a4.3", "type": "blocks"}, {"depends_on_id": "gm-gen-a4.4", "type": "blocks"}, {"depends_on_id": "gm-gen-a4.5", "type": "blocks"}, {"depends_on_id": "gm-gen-a4", "type": "parent-child"}]}
{"id": "gm-gen-a4b", "title": "Phase A4b: Gas City OrchestrationPlane stub (designed-for, primary at GC GA)", "description": "# Goal\nKeep the Gas City adaptor actively developed alongside Gas Town so the transition at GC GA is a configuration change, not a rewrite. v1 exit criterion is 'stub compiles, workspace detection dispatches to it.' Full wire-up follows Gas City's public spec release.\n\n# Inputs\n- gm-gen-a2 closed (matching shape)\n- Gas City team response to the RFC's questions (gm-gen-a4b.3)\n- Phase 2 §5.2.2 (Gas City sketch)\n\n# Outputs\n- internal/adaptor/gascity/ skeleton\n- Workspace detection: city.toml → route to this adaptor\n- Capability manifest declares alpha/stub status\n\n# Definition of Done\n- Stub compiles\n- Workspace detection routes correctly\n- Public questions list published for the Gas City team\n- Ready to wire up incrementally as Gas City GA nears\n**Resolves DDs:** DD-1,DD-5,DD-7,DD-12", "issue_type": "epic", "priority": 2, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-gc", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-root", "type": "parent-child"}, {"depends_on_id": "gm-gen-a2", "type": "blocks"}]}
{"id": "gm-gen-a4b.1", "title": "Gas City adaptor skeleton mirroring Gas Town shape", "description": "# Goal\nBuild the Gas City adaptor skeleton with the same interface surface as the Gas Town adaptor. Most methods return UnsupportedCapabilityError until Gas City's spec stabilizes.\n\n# Inputs\n- gm-gen-c3 closed\n- gm-gen-a2 closed (reference shape)\n\n# Outputs\n- internal/adaptor/gascity/ with all methods stubbed\n- CapabilityManifest declares alpha version, list of supported vs pending methods\n\n# Definition of Done\n- go build ./... clean\n- `gemba adaptor list` shows gascity adaptor with alpha/stub tag\n**Resolves DDs:** DD-12", "issue_type": "task", "priority": 2, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-gc", "tier:sonnet", "risk:low", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a4b", "type": "parent-child"}]}
{"id": "gm-gen-a4b.2", "title": "Gas City workspace detection (city.toml → gascity adaptor)", "description": "# Goal\nBoot-time workspace detection correctly picks the gascity adaptor for workspaces with city.toml, otherwise gastown.\n\n# Inputs\n- gm-gen-a4b.1 closed\n- gm-e2.4 fs adapter\n\n# Outputs\n- internal/adaptor/registry/detect.go\n- Smoke test in a synthetic tmpdir with city.toml vs .gt\n\n# Definition of Done\n- Detection unambiguous and tested\n**Resolves DDs:** DD-12", "issue_type": "task", "priority": 2, "status": "open", "labels": ["migration:generalization", "surface:backend", "layer:adapter-gc", "tier:sonnet", "risk:low", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a4b.1", "type": "blocks"}, {"depends_on_id": "gm-gen-a4b", "type": "parent-child"}]}
{"id": "gm-gen-a4b.3", "title": "Gas City RFC follow-up: publish spec questions, collect answers", "description": "# Goal\nPublish the Gemba questions for the Gas City team (city.toml spec stability, escalation mechanism, reconciliation verb). Collect + archive responses. Feeds future wire-up work.\n\n# Inputs\n- Phase 2 §6.1 open questions\n- RFC §What I'm asking for (1, 4)\n\n# Outputs\n- A public RFC reply or discussion thread\n- Collected answers written back to internal/adaptor/gascity/QUESTIONS.md\n\n# Definition of Done\n- Questions sent, responses (or silence) recorded\n- Any answered items feed into follow-up gm-gen-a4b.* tasks (to be filed as needed)\n**Resolves DDs:** (meta — enables all DDs to fully resolve for Gas City)", "issue_type": "task", "priority": 2, "status": "open", "labels": ["migration:generalization", "surface:docs", "layer:adapter-gc", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-a4b", "type": "parent-child"}]}
{"id": "gm-gen-x", "title": "Phase X: Cross-cutting features (DoD informational, CostMeter, Escalation, Capability+transport, Sprint+TokenBudget, Evidence, transport plurality)", "description": "Build the cross-cutting primitives once against two real reference adaptors (Beads + Gas Town) so the abstractions are real, not theoretical.\n\n# Goal\nDoD minimal schema, CostMeter rollups, EscalationRequest pipeline, Capability-driven UI, Sprint + TokenBudget enforcement, Evidence synthesis, and transport plurality all live by end of phase.\n\n# Definition of Done\n- DoD minimal schema + 1-page SPEC published\n- Cost rollups render in insights panel; Sprint/epic budgets render on Kanban\n- Three-tier inform/warn/stop enforcement live; mutations gated at stop\n- Escalation inbox + card badge live (including budget_warn kind)\n- Capability-manifest driven UI adjustments working\n- At least two transports proven end-to-end\n**Resolves DDs:** DD-3, DD-4, DD-6, DD-12, DD-13, DD-14, DD-15", "issue_type": "epic", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "surface:frontend", "tier:opus", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-root", "type": "parent-child"}, {"depends_on_id": "gm-gen-a1", "type": "blocks"}, {"depends_on_id": "gm-gen-a2", "type": "blocks"}]}
{"id": "gm-gen-x1", "title": "Document informational-only DoD stance + ship minimal schema", "description": "Per DD-3, DoD is informational-only in v1. This task publishes the minimal schema and the deferral-until-industry-consensus SPEC.\n\n# Goal\nOne page of SPEC + a JSON schema file define the entire v1 DoD surface.\n\n# Inputs\n- DD-3 (informational-only)\n- Phase 2 §4.1 minimal schema\n\n# Outputs\n- `/schemas/dod/1.0.json` — `{acceptance_criteria?, notes?, version: '1.0'}`\n- Go + TS types\n- `/docs/specs/dod.md` — 1-page SPEC explaining the informational stance\n\n# Definition of Done\n- Schema resolves to valid JSON Schema 2020-12\n- Types compile into Go and TS\n- SPEC linked from README and architecture docs\n**Resolves DDs:** DD-3", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:backend", "surface:protocol", "tier:opus", "risk:high", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-x", "type": "parent-child"}]}
{"id": "gm-gen-x2", "title": "CostMeter rollups (assignment/workitem/agent/group/epic/sprint) + insights panel", "description": "Implement the rollup engine and insights panel rendering for CostMeter data.\n\n# Goal\nEvery card (WorkItem, epic, sprint, agent, group) shows its cost rollup; insights panel aggregates per rig/convoy/sprint.\n\n# Inputs\n- DD-4 (CostMeter axes)\n- DD-14 (sprint scope)\n- gm-gen-c1 types\n\n# Outputs\n- `internal/rollup/cost.go` — leaf → workitem → epic → sprint rollup\n- Memoization/cache for sprint-level aggregates (watch perf on 10K+ workitems)\n- SPA insights panel with per-rig, per-sprint, per-convoy lanes\n- Per-card cost badge (tokens + ≈$)\n\n# Definition of Done\n- Rollup benchmark < 100ms on 10K workitems, 50 epics, 5 active sprints\n- Insights panel renders live data from at least one OrchestrationPlane adaptor\n**Resolves DDs:** DD-4, DD-14", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "surface:frontend", "tier:sonnet", "risk:medium", "fed:safe", "area:budget"], "dependencies": [{"depends_on_id": "gm-gen-a2", "type": "blocks"}, {"depends_on_id": "gm-gen-x", "type": "parent-child"}]}
{"id": "gm-gen-x3", "title": "EscalationRequest pipeline: card badge, `/escalations` inbox, Kanban banner", "description": "# Goal\nImplement the DD-6 triad: per-card badge, dedicated `/escalations` inbox, dismissible banner when any visible card has a blocking escalation. cmdk action to jump to oldest open. Supersedes gm-e6.4.\n\n# Inputs\n- gm-gen-c1 EscalationRequest type closed\n- gm-gen-a2.5 Gas Town escalation emission closed\n- RFC §New surfaces treatment in §4.3\n\n# Outputs\n- web/src/escalations/ — card badge, inbox view, banner overlay\n- SPA event subscription keyed on escalation state\n- Keyboard shortcut in cmdk\n\n# Definition of Done\n- Gas Town escalations render in all three surfaces\n- Resolving an escalation (approve/deny/modify/defer) round-trips back through the adaptor\n- gm-e6.4 superseded and closed\n**Resolves DDs:** DD-6\n\n# Updated for DD-14\nEscalationRequest pipeline adds the `budget_warn` kind produced by the rollup engine when an epic or sprint first crosses its `warn` threshold. Inbox visually distinguishes `budget_warn` from session-produced escalations.\n\n**Resolves DDs (updated):** DD-6, DD-14", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:frontend", "tier:sonnet", "risk:medium", "fed:safe", "area:budget"], "dependencies": [{"depends_on_id": "gm-gen-a2.5", "type": "blocks"}, {"depends_on_id": "gm-gen-x", "type": "parent-child"}]}
{"id": "gm-gen-x4", "title": "Capability-negotiation UI layer (hide controls by manifest; field extensions; transport-aware routing)", "description": "Remove all hardcoded feature checks in the SPA. Every UI control's visibility and behaviour comes from the active adaptor's CapabilityManifest. Transport is chosen per registration and routed through gm-gen-c4.\n\n# Goal\nNo `if (backend === 'beads')` anywhere in `web/src/`. Controls render from manifest data.\n\n# Inputs\n- gm-gen-c4 (registration + transport routing)\n- DD-12\n- DD-15 (transport field)\n\n# Outputs\n- `web/src/capabilities/` hook that reads manifest\n- Field-extension renderer keyed by declared type (string/number/enum/date/json)\n- Transport chosen at registration; UI doesn't need to know which one\n- `web/src/stores/capabilities.ts` — capability memoization\n\n# Definition of Done\n- Snapshot test: no adaptor-name strings in UI components\n- Capabilities reload on manifest change without full SPA reload\n**Resolves DDs:** DD-12, DD-15", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:frontend", "tier:opus", "risk:medium", "fed:safe", "area:transport"], "dependencies": [{"depends_on_id": "gm-gen-c4", "type": "blocks"}, {"depends_on_id": "gm-gen-x", "type": "parent-child"}]}
{"id": "gm-gen-x5", "title": "Sprint + TokenBudget implementation: entity, rollup engine, three-tier inform/warn/stop enforcement, UI gauges", "description": "Per DD-14, Sprint is a first-class entity bounded by a token budget (not calendar duration). This task implements the entity, rollup engine, threshold enforcement, and UI surfaces.\n\n# Goal\nOperators can create a Sprint with a token budget, assign epics to it, watch the inform/warn/stop gauge, and have mutations gated at stop without agents being killed mid-flight.\n\n# Inputs\n- DD-14 (Sprint + TokenBudget)\n- gm-gen-c1 types (Sprint, TokenBudget)\n- gm-gen-x2 (CostMeter rollup engine)\n\n# Outputs\n- Sprint CRUD via WorkPlane adaptor methods (gm-gen-c2 scope)\n- Rollup engine: leaf → epic → sprint, computed at read time with memoization\n- Threshold detection + event emission (`budget.inform`, `budget.warn`, `budget.stop`)\n- `stop` threshold gates new-spend mutations unless `X-GEMBA-Confirm` nonce carries `budget_override: true`\n- Kanban top-bar Sprint picker (filter by sprint)\n- Epic/Sprint budget gauges: primary = tokens remaining; secondary = `on pace / ahead / behind` relative to planned duration\n- EscalationRequest emission for `warn` (via gm-gen-x3)\n\n# Definition of Done\n- Integration test: create Sprint, burn 49% → no event; burn 50% → `budget.inform` emitted; burn 80% → `budget.warn` + escalation; burn 100% → mutation gated until override\n- Rollup benchmark ≤ 100ms for 10K workitems / 50 epics / 5 sprints\n- Planned-duration gauge renders without ever triggering close (duration is advisory)\n- Scrum-fluent user test: 3/3 users correctly identify token-budget as primary bound within 30s\n**Resolves DDs:** DD-14", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "surface:frontend", "tier:opus", "risk:medium", "fed:safe", "area:budget"], "dependencies": [{"depends_on_id": "gm-gen-x", "type": "parent-child"}, {"depends_on_id": "gm-gen-v3", "type": "blocks"}, {"depends_on_id": "gm-gen-c1", "type": "blocks"}, {"depends_on_id": "gm-gen-x2", "type": "blocks"}]}
{"id": "gm-gen-x6", "title": "Shared evidence synthesis library (git log, GitHub PR API, CI status)", "description": "# Goal\nBuild the reusable evidence-synthesis primitives shared across adaptors. Jira, Linear, GitHub adaptors all benefit; Beads adaptor opts in per gm-gen-a1.5.\n\n# Inputs\n- gm-gen-c1 Evidence type closed\n- Gate V6 outcome\n\n# Outputs\n- internal/evidence/synth/git.go (git log walker)\n- internal/evidence/synth/gh.go (PR + check-runs)\n- internal/evidence/synth/ci.go (CI status poller)\n- All output tagged synthesized:true\n\n# Definition of Done\n- Beads adaptor (gm-gen-a1.5) and Jira adaptor (future) both consume library\n- Unit tests cover each synth source\n**Resolves DDs:** DD-13", "issue_type": "task", "priority": 2, "status": "open", "labels": ["migration:generalization", "surface:backend", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-v4", "type": "blocks"}, {"depends_on_id": "gm-gen-x", "type": "parent-child"}]}
{"id": "gm-gen-x7", "title": "Transport plurality harness: prove at least two transports end-to-end (api + one of jsonl/mcp)", "description": "Per DD-8 + DD-15, Gemba supports three adaptor transports. This task proves the plurality end-to-end so the conformance suite doesn't bake in a single-transport assumption.\n\n# Goal\nShip a CI matrix that runs the WorkPlane conformance suite against the same operations over at least two distinct transports (api + jsonl, or api + mcp).\n\n# Inputs\n- gm-gen-c4 (registration over all transports)\n- gm-gen-c5 (conformance harness)\n- gm-gen-c7 (noop adaptor as jsonl)\n- gm-gen-a2.6 (Gas Town as api)\n\n# Outputs\n- CI workflow `adaptor-matrix.yml` running conformance over ≥2 transports\n- One forcing-function MCP adaptor (minimal; can be derived from the noop) validating the mcp path\n- `gemba adaptor test --transport=<X>` CLI flag\n\n# Definition of Done\n- Conformance green on api + one other transport in CI\n- MCP adaptor path validated even if not shipped as a primary adaptor\n- Contract regression test: a conformance change affects only one transport implementation\n**Resolves DDs:** DD-8, DD-15", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:backend", "surface:infra", "tier:sonnet", "risk:medium", "fed:safe", "area:transport"], "dependencies": [{"depends_on_id": "gm-gen-x", "type": "parent-child"}, {"depends_on_id": "gm-gen-c4", "type": "blocks"}, {"depends_on_id": "gm-gen-c5", "type": "blocks"}, {"depends_on_id": "gm-gen-c7", "type": "blocks"}, {"depends_on_id": "gm-gen-a2.6", "type": "blocks"}]}
{"id": "gm-gen-u", "title": "Phase U: UI generalization — remove Gas Town/Beads vocabulary", "description": "# Goal\nRemove Gas Town/Beads vocabulary from the SPA outside adaptor-namespaced extensions. Drive column, field, and label derivations from capability manifests.\n\n# Inputs\n- gm-gen-a3 closed (two WorkPlane adaptors)\n- gm-gen-a4 closed (two OrchestrationPlane adaptors)\n- gm-gen-x closed\n\n# Outputs\n- Renamed types, generic components, extension-only adaptor widgets\n- Snapshot test enforcing absence of reserved strings\n\n# Definition of Done\n- All 5 children closed\n- `grep -ri '(bead|convoy|rig|mayor|polecat|gastown|gascity)' web/src/ | grep -v /extensions/` returns empty\n**Resolves DDs:** DD-12 (UI surfaces); supports all DDs", "issue_type": "epic", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:frontend", "tier:opus", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-root", "type": "parent-child"}, {"depends_on_id": "gm-gen-a3", "type": "blocks"}, {"depends_on_id": "gm-gen-a4", "type": "blocks"}, {"depends_on_id": "gm-gen-x", "type": "blocks"}]}
{"id": "gm-gen-u1", "title": "SPA type rename: Bead→WorkItem, Convoy→AgentGroup, Rig→Workspace", "description": "# Goal\nMechanical codemod across web/src/ replacing Beads/Gas Town types with generalized types. Keep Gas Town-specific vocabulary inside web/src/extensions/gastown/ only.\n\n# Inputs\n- gm-gen-c1 TS types ready\n\n# Outputs\n- Renamed type imports across all components\n- Gas Town-specific language isolated\n- Git-blame survivable: codemod commit with a clear message\n\n# Definition of Done\n- All tests green post-codemod\n- Snapshot of key screens (grid, Kanban, detail) unchanged rendering\n**Resolves DDs:** DD-12", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:frontend", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-u", "type": "parent-child"}]}
{"id": "gm-gen-u2", "title": "Column / field derivation from capability manifests in work grid + Kanban", "description": "# Goal\nWork grid columns + Kanban card fields are not hardcoded; they read from CapabilityManifest.field_extensions and render via default widgets. Users can add/remove extension columns without code changes.\n\n# Inputs\n- gm-gen-u1 closed\n- gm-gen-x5 closed\n\n# Outputs\n- web/src/grid/columns.ts now manifest-driven\n- Kanban card footer shows top-3 declared extensions with type-appropriate widgets\n\n# Definition of Done\n- Jira extensions (project_key, components, fix_versions) render without Jira-specific grid code\n- Beads extensions (priority, labels) render without Beads-specific grid code\n**Resolves DDs:** DD-12", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:frontend", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-u1", "type": "blocks"}, {"depends_on_id": "gm-gen-u", "type": "parent-child"}]}
{"id": "gm-gen-u3", "title": "Pack browser → Adaptor capability browser (supersedes gm-e5.8 content)", "description": "# Goal\nRetitle/refocus gm-e5.8's work. Page enumerates installed adaptors, shows each CapabilityManifest, capability-by-capability status. Gas City packs are one section rendered when the gascity adaptor is installed.\n\n# Inputs\n- gm-gen-u1 closed\n- gm-gen-c4 adaptor registration closed\n\n# Outputs\n- /adaptors page listing installed adaptors\n- Per-adaptor capability detail view\n- Gas City pack list is an extension subview of the gascity adaptor card\n\n# Definition of Done\n- Gas Town + Beads + Jira + LangGraph adaptor cards render correctly\n- gm-e5.8 marked re-scoped with a pointer to this bead\n**Resolves DDs:** DD-12", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:frontend", "tier:sonnet", "risk:low", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-u1", "type": "blocks"}, {"depends_on_id": "gm-gen-u", "type": "parent-child"}]}
{"id": "gm-gen-u4", "title": "Snapshot test: no Gas Town/Beads vocabulary outside extensions", "description": "# Goal\nLock in the generalization by adding a repo-wide grep + Playwright snapshot test that fails CI if reserved vocabulary leaks into core UI code.\n\n# Inputs\n- gm-gen-u1..u3 closed\n\n# Outputs\n- scripts/check-no-adaptor-leak.sh grepping web/src/ ex extensions/\n- Playwright snapshot test rendering main screens under a generic fixture\n\n# Definition of Done\n- CI job runs the grep + snapshot; green on main\n- Failing regressions block PRs\n**Resolves DDs:** DD-12", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:frontend", "tier:sonnet", "risk:low", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-u1", "type": "blocks"}, {"depends_on_id": "gm-gen-u2", "type": "blocks"}, {"depends_on_id": "gm-gen-u3", "type": "blocks"}, {"depends_on_id": "gm-gen-u", "type": "parent-child"}]}
{"id": "gm-gen-u5", "title": "Isolate Gas Town / Beads-specific extension widgets into web/src/extensions/", "description": "# Goal\nPreserve Gas Town/Beads-specific rendering (convoy details, Mayor/Deacon/Witness role chips, Beads priority P0-P3 widgets) inside web/src/extensions/{gastown,beads}/ — composed into core views via extension slots.\n\n# Inputs\n- gm-gen-u1 closed\n\n# Outputs\n- web/src/extensions/gastown/ with existing components moved\n- web/src/extensions/beads/ similarly\n- Extension slot registry used by core views\n\n# Definition of Done\n- Snapshot test (gm-gen-u4) green with extensions mounted\n- Removing the gastown extension cleanly hides its UI without breakage\n**Resolves DDs:** DD-12", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:frontend", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-u1", "type": "blocks"}, {"depends_on_id": "gm-gen-u", "type": "parent-child"}]}
{"id": "gm-gen-d", "title": "Phase D: Documentation + release", "description": "# Goal\nPublish adaptor authoring + migration guides, cut a release with GEMBA_GENERALIZED=1 default-on.\n\n# Inputs\n- gm-gen-u closed\n- All conformance suites green on 4 adaptors\n\n# Outputs\n- 'Writing a Gemba adaptor' guide\n- 'Migrating from Gemba v1 to v1.1 (generalized)' guide\n- Release cut + announcement\n\n# Definition of Done\n- All 4 children closed\n- Release binary ships with generalized path default\n**Resolves DDs:** DD-3 (exit criterion publication); all", "issue_type": "epic", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:docs", "tier:sonnet", "risk:low", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-root", "type": "parent-child"}, {"depends_on_id": "gm-gen-u", "type": "blocks"}]}
{"id": "gm-gen-d1", "title": "Public 'Writing a Gemba adaptor' guide", "description": "# Goal\nAuthor the public-facing guide for writing new WorkPlane or OrchestrationPlane adaptors. Covers interface, capability manifest, conformance harness, testing.\n\n# Inputs\n- Conformance suites green on four adaptors\n\n# Outputs\n- docs/adaptors/writing-a-workplane.md\n- docs/adaptors/writing-an-orchestration.md\n- Links to Jira + LangGraph adaptor READMEs as worked examples\n- Conformance CLI usage examples\n\n# Definition of Done\n- Docs published on the docs site (gm-e8.3)\n- At least one external contributor has read it and attempted an adaptor (or confirmed readability)\n**Resolves DDs:** DD-12", "issue_type": "task", "priority": 1, "status": "open", "labels": ["migration:generalization", "surface:docs", "tier:sonnet", "risk:low", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-d", "type": "parent-child"}]}
{"id": "gm-gen-d2", "title": "Migration guide for existing Gemba v1 users (Beads + Gas Town)", "description": "# Goal\nDocument the migration path for users on Gemba v1 with Beads + Gas Town. Covers flag flip, any breaking changes in extension vocabulary, preserved functionality, new features.\n\n# Inputs\n- gm-gen-u closed\n- Known breaking changes cataloged\n\n# Outputs\n- docs/migration/v1-to-generalized.md\n- Changelog entry\n- Linked from release notes\n\n# Definition of Done\n- Guide reviewed by at least one Gemba v1 user (real or simulated)\n- Includes rollback instructions (unset GEMBA_GENERALIZED=1)\n**Resolves DDs:** all", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:docs", "tier:sonnet", "risk:low", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-d", "type": "parent-child"}]}
{"id": "gm-gen-d3", "title": "Release cut with GEMBA_GENERALIZED=1 default-on", "description": "# Goal\nCut the release. Flip the default so fresh installs get the generalized path; existing users see the flag flip advertised in the changelog.\n\n# Inputs\n- gm-gen-d1 and gm-gen-d2 closed\n- All conformance suites green\n- Regression suite (§7) green\n\n# Outputs\n- Tagged release; goreleaser artifacts\n- Binary with GEMBA_GENERALIZED default true\n- Release notes\n\n# Definition of Done\n- brew install gemba installs the generalized binary\n- gemba doctor reports the active adaptors and capability summary\n- Users can still roll back by setting GEMBA_GENERALIZED=0\n**Resolves DDs:** all (release gate)", "issue_type": "task", "priority": 0, "status": "open", "labels": ["migration:generalization", "surface:infra", "tier:sonnet", "risk:medium", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-d1", "type": "blocks"}, {"depends_on_id": "gm-gen-d2", "type": "blocks"}, {"depends_on_id": "gm-gen-d", "type": "parent-child"}]}
{"id": "gm-gen-d4", "title": "Announcement: gastown discussions + HN + Reddit + blog post", "description": "# Goal\nAnnounce generalized Gemba. Supplements gm-e8.4 with emphasis on the adaptor story.\n\n# Inputs\n- gm-gen-d3 closed\n\n# Outputs\n- Blog post draft + publication\n- gastown discussions thread\n- HN + Reddit posts (r/LocalLLaMA, r/devops, r/programming as appropriate)\n\n# Definition of Done\n- Posts live; engagement monitored for a week\n**Resolves DDs:** (meta — release socialization)", "issue_type": "task", "priority": 2, "status": "open", "labels": ["migration:generalization", "surface:docs", "tier:sonnet", "risk:low", "fed:safe"], "dependencies": [{"depends_on_id": "gm-gen-d3", "type": "blocks"}, {"depends_on_id": "gm-gen-d", "type": "parent-child"}]}
```

---

## 11. Reviewer checklist

Human reviewer: check these before importing any of the JSONL above.

- [ ] **DD traceability**: every active DD (DD-1..DD-10, DD-12..DD-15) appears in at least one task's `**Resolves DDs:**` line. DD-11 is withdrawn (see domain doc). Verified mapping:
  - DD-1 in v2/a1.3/a3.3/a4.1
  - DD-2 in c1/c2/a1.1/a3.1
  - DD-3 in x1/a1.4/a3.4 (informational pass-through only)
  - DD-4 in v3/x2/a2.4/a4.4
  - DD-5 in c3/a2.2/a4.5
  - DD-6 in x3/a2.5/a4.3
  - DD-7 in c3/a2.1/a4.2
  - DD-8 in a2.6/c4/x7 (no dedicated gate — loosened per DD-15)
  - DD-9 in v1/c2/a1.2
  - DD-10 in c1
  - DD-11: WITHDRAWN — see domain doc DD-3 update
  - DD-12 in c2/c4/c5/c6/a3.2/a3.5/x4/u1-u5
  - DD-13 in v4/x6/a1.5
  - DD-14 (Sprint + TokenBudget) in v3/c1/c2/c6/x2/x3/x5
  - DD-15 (transport plurality) in c2/c4/c5/c7/a2.6/a2.7/x4/x7
- [ ] **Gate ownership**: every gate has a named sign-off owner (V1: Yegge; V2: Gas Town + Gas City maintainers; V3: ≥1 non-GT adaptor candidate + ≥2 Scrum-fluent prospective users for DD-14 sprint redefinition; V4: first two adaptor authors). Confirm real people have been asked or reach out is scheduled.
- [ ] **JSONL syntactic validity**: each line is a single valid JSON object, no trailing commas, all keys present (`id`, `title`, `description`, `issue_type`, `priority`, `status`, `labels`, `dependencies`).
- [ ] **Prefix uniqueness**: no new id collides with an existing `bc-*` id. (`gm-gen-*` is reserved.)
- [ ] **Label taxonomy**: every new bead carries `migration:generalization` + existing taxonomy entries (`surface:*`, `tier:*`, `risk:*`, `fed:*`). New area labels (`area:budget`, `area:transport`) introduced for Sprint/TokenBudget and transport-plurality beads.
- [ ] **Existing bead updates**: §3.6 `bd update` commands are safe — they only `--append-description` and `--label-add`. No destructive edits.
- [ ] **Superseded vs open**: existing gm-e2.2, gm-e2.3, gm-e2.3b, gm-e6.4 remain open during migration (marked superseded) and close when their replacement closes. Verify this policy with the PM.
- [ ] **Release gate**: `gm-gen-d3` explicitly depends on the regression suite (§7) passing. Confirm §7 is a real CI job before importing or file it as a follow-up.
- [ ] **Fallback readiness**: Confirm fallback designs for V1, V3, V4 are specced (even as one-page notes) before opening the corresponding build tasks. Note V3 has two decision axes (CostMeter axes AND Sprint redefinition UI copy) — both need fallback design.
- [ ] **Gas City exemption**: confirm `gm-gen-a4b` is explicitly non-blocking for migration-complete. It should not gate `gm-gen-d3`.
- [ ] **Performance budget**: §7.3 "Kanban render time ≤10% regression" — confirm a baseline measurement exists before `gm-gen-u1` starts, else the budget is unenforceable. Add a separate budget for the `gm-gen-x5` rollup engine: ≤100ms on 10K workitems / 50 epics / 5 sprints.
- [ ] **Transport plurality proof**: confirm `gm-gen-x7` ships before `gm-gen-d3` so the loosened DD-8 stance is actually demonstrated in CI, not just documented.
- [ ] **Sprint UX prototype**: confirm V3 includes a prototype-with-real-users step *before* `gm-gen-x5` commits UI copy, per the DD-14 tradeoff in the domain doc.

---

*End of migration plan.*
