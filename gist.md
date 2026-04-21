# Gemba

*Large-scale side-of-the-desk projects: big impact, minimal cognitive load.*

## The factory floor

In lean manufacturing, gemba (現場) is "the actual place" — the factory floor, where real work happens. A *gemba walk* is when leadership observes the work directly, not through reports, and leaves actionable feedback as they go. Gemba the product is built around that metaphor. Operators running agentic software projects today hit a consistent failure pattern:

- Planning is disconnected from execution — issues in Jira or Beads, agents in a terminal, output in git.
- Priority is invisible. The dep graph says what *can* run; nothing says what *should* run next.
- Expertise is siloed — a side-of-the-desk project needs product judgment, architecture, UX review, QA gating, release mechanics, security, and the operator doesn't have time to personally don each hat.
- State is fragile — git, Beads, LLM sessions, and sidecar artifacts each move on their own timeline; "undo back to yesterday" doesn't exist.
- Orchestration tooling is tied to one runtime — playing nicely with one tracker or one agent framework means a rewrite when either moves.

Gemba addresses all five: a browser-based UI for walking the floor of an agentic project, seeing the work at the right grain, directing it, with a roster of configurable LLM specialists a click away for the expertise the operator doesn't have time to personally deliver for every decision.

## The shape

A **single Go binary with an embedded React SPA**. It pairs *exactly one* **Work Coordination Plane** adaptor — the issue tracker (Beads, Jira, Linear, GitHub Projects, Azure DevOps, …) — with *exactly one* **Agent Orchestration Plane** adaptor — the agent runtime (Gas Town, Gas City, LangGraph, OpenHands, Devin, …) — under a typed contract. The UI is adaptor-agnostic: no backend vocabulary leaks in; what renders is what the active capability manifests declare.

- **Reference pack-ins (v1):** Beads as the WorkPlane, Gas Town as the OrchestrationPlane.
- **Forcing-function adaptors (v1):** Jira and LangGraph — quirks are supersets of their categories' easier members, so the contract is proven against them. If it handles Jira's workflow FSM, Linear is easy. If it handles LangGraph's checkpoint-and-graph topology, OpenHands is easy.

## The expertise layer — Coaches, the Project Manager, and Gemba walks

### Two persona varieties

**Coaches** are conversational and advisory — they observe and suggest; the operator applies or dismisses. Output is structured: markdown coaching narratives for broad questions (*what remains on the board right now?*), JSONL-ranked recommendations for specific decisions (*which epics should I stage next, in what order?*), typed reports for reviews. Each invocation is cheap, auditable, and rejectable. The seed roster:

- **Architect** — design review, dep-graph hygiene, refactor guidance, type-system advice.
- **Code Reviewer** — diff review, PR feedback, API-shape critique, test-coverage concerns.
- **UX Expert** — UI spec consistency, vocabulary ratification, user-flow critique, accessibility.
- **Technical Writer** — bead-description clarity, commit-message quality, docs copy, release notes.
- **Documentarian** — curates human-readable artifacts; maintains the project summary and decisions log that every other persona reads from.
- **Onboarder** — first-run tour, new-adaptor setup, context bootstrap for new users.

**Managers** are agentic and can be gate-blocking — they execute scoped tasks directly, consult other personas mid-task, and pause for human-in-the-loop input when they need a judgment call:

- **Project Manager** — staging, ordering, scoping, escalation triage, sprint retros, and the coordinator persona most operators talk to most. Files beads via `add_to_backlog`; modifies in-flight work via `change_this` (with reverse-actions recorded for rollback).
- **QA** — regression-suite catalog owner; can block state transitions (an Epic cannot move to Completed until its gate passes); overrides require persona consensus or nonce-confirmed justification. Integrates with XRay for test management and configurable linters as regression-suite members.
- **Deployment Engineer** — release-engineering mechanics: goreleaser, CI matrices, artifact signing, Homebrew tap + npm wrapper alignment, semver compatibility, release notes.
- **DevOps/SRE** — runtime operations, incident response, capacity planning, on-call.
- **Security** — auth-surface review, secret hunting, CVE triage, policy compliance (Manager authority activates for auth-labeled work; advisory otherwise).

Every persona has **separately configurable prompt, context providers, and output validation**. Each lives as a TOML file; users add / modify / disable freely. Model choice is per-persona — Claude Opus for deep reasoning, Sonnet for iteration, Haiku for high-volume copy, or plug a different vendor altogether.

### The Project Manager as coordinator

The PM is the central persona — the one the operator talks to most, and the one that coordinates every other persona. PM skills span four categories:

- **Planning** — `epic_order`, `parallel_safety`, `scope_trim`, `epic_decompose`, `epic_merge`, `workspace_priority`, `budget_replan`.
- **Operational coaching** — `what_remains` (structured-markdown "next actionable chunk" narrative), `escalation_triage`, `stale_session`, `find_checkpoint`.
- **Agentic actions** — `add_to_backlog` (files beads with Architect + QA + Tech Writer consultation), `change_this` (modifies in-flight work with HITL for affected polecat sessions), `dispatch_readiness` (pre-sling DoD check).
- **Retro + insights** — `velocity_calibration`, `evidence_summary` integration, sprint + token-budget reporting.

The PM panel lives in the SPA chrome, always one click away. Plan view buttons ("Recommend order", "What remains", "Trim to budget") call PM skills directly. Every invocation produces a `PersonaConsultRecord` — permanent audit trail, reviewable in `/insights/personas` with per-persona aggregates (hit rate, cost, applied-vs-dismissed ratio). Retros use this to calibrate which personas are earning their keep.

### Gemba walks — the interactive decisioning surface

A Gemba walk is an interactive multi-topic conversation between the operator and the PM — the same pattern an operator-and-assistant fall into naturally when working through a busy backlog, made first-class. On start, the PM auto-populates the agenda from every escalation source in the workspace:

- **Open EscalationRequests** — polecat / crew escalations, Manager persona suspensions, Witness findings, Refinery merge rejections, budget-stop events, adaptor-degraded notifications, gate failures.
- **HITL questions** — Manager persona sessions that paused mid-task awaiting a judgment call.
- **Recently-filed beads** — awaiting ratification (created in the last 24h, configurable).
- **Recently-closed work** — needing retro or summary (Documentarian-flagged).
- **User-added topics** — anything the operator wants on the agenda.

The operator and PM walk the agenda one item at a time. For each: the PM frames the context, summarizes what's happened, proposes actions; the operator ratifies / modifies / rejects / defers; ratified actions apply as nonce-gated mutations through the same API any client uses. The PM may consult other personas mid-session — Architect for design impact, QA for test coverage, Security for auth-surface concerns — with brief consultations running inline and their responses feeding the current decision.

Gemba walks are **resumable** across days (pause and pick up later; serialized state survives process restarts), **auditable** (every turn, every decision, every consulted persona captured), and produce a **Documentarian-written summary artifact** on end. The always-available PM panel doubles as the active Gemba walk's chat surface — no context switch between "asking the PM" and "working the list."

Gemba walks are the native mode for walking the floor at scale — the operator's running conversation with the project's brain.

## The workspace

**The Gemba** is the home screen — the factory-floor view of your project: an Epic-granular Kanban rendering. Cards are Epics — not individual stories — showing:

- Readiness counts (how many members ready / blocked / in progress)
- Parallel-group membership
- Escalation state + token-budget posture
- Critical-path length

Drill-down reveals member work items in stage order. The **Plan view** lets the operator drag to reorder, toggle Epics in or out of scope, and launch the whole batch after parallel-safety is verified.

**Values + guardrails + goals** inject at the top prompt layer for every persona invocation:

- Four seed values: innovation, transparency, execution, empathy (user-extensible)
- Guardrails: values with Manager-enforced blockers
- Project-level and Epic-level goals flow into relevant prompts

**Workspace modes** govern how much friction is in the way of execution:

- **Unsupervised** — no interruptions, auto-approve 10x default
- **Supervised** (default) — largely automatic, checks in on ambiguous decisions
- **Managed** — every coarse-grained step summarized and user-approved

**Checkpoints** atomically snapshot everything that matters — every git repo involved, the Beads database, live session context summaries, sidecar state, generated artifacts. Operators can "undo back to yesterday" and roll every dimension back together.

**Agentic code analysis** — GitNexus-class knowledge graphs, pluggable backends — is a first-class capability. It feeds personas' context (module inventory, call graph, impact analysis, health report) and powers richer source-code-repo bootstrap.

## Extensibility

Three surfaces. All three support signed or unsigned distribution, public or private.

- **Adaptors** — implement the typed two-plane contract; run the importable conformance harness (`gemba/testing`) in your own CI.
- **Personas** — author a TOML file in `.gemba/personas/`. Tune system prompt, select model, opt context providers on or off, declare Skills, set budget caps.
- **Packs** — bundle personas + skills + default values + guardrails + adaptor preferences. **Arbitrary in name and intent**, not constrained to executive roles:
  - Role packs: CTO today; CEO, COO, CRO/LRC later
  - Domain packs: fintech-compliance, healthcare-hipaa, crypto-defi
  - Task packs: migration, launch-readiness, incident-response
  - Customer-specific or internal packs: privately distributed

## Bootstrap

New projects start from one of four first-class sources:

- **Jira** — doc-import adaptor reads existing epics, stories, specs, acceptance criteria
- **Beads** — local workspace seed
- **Source-code repo** — agentic code analysis walks module structure, call graph, entry points to propose candidate Epic decomposition
- **Fresh** — Onboarder-driven 5-to-10-question interview

An Onboarder + PM + Documentarian trio runs on whatever source is chosen to produce a project description, initial goals, candidate values, recommended guardrails, and a starting plan — validated for internal consistency before the operator ratifies.

## Organization + execution surfaces

- **Organization surface** — tools shared across a team: Jira, XRay (test management + evidence + requirement-to-test traceability), configurable linters. QA's Manager reads and writes XRay, runs linters as regression suites, and gates state transitions on combined results.
- **Execution surface** — per-workspace tools where actual work happens: Beads, Gas Town, LangGraph, per-workspace CI. Swappable via adaptors.

## Workspace repos come in pairs

Every project pairs two repos by convention, formalized as a first-class product concept:

- **`<project>_prime`** — the workspace repo: docs, digests, design artifacts, decision log, product description, RFCs, ADRs. Versioned, commit-logged, walkable as a historical record. Contains the `.gemba/` sidecar.
- **`<project>`** — the output repo: the actual shippable code or content.

Bootstrap creates both. Adaptors map to both. Checkpoints capture both atomically. The UI toggles between workspace-repo view and output-repo view. Documentarian writes to the workspace repo by default.

## System surfaces — extensibility goes deeper than the UI

- **HTTP API** at `/api/v1/*` — OpenAPI-documented, TypeScript client codegenned, stable.
- **Two-plane adaptor contracts** — typed interfaces with transport plurality: `api`, `jsonl`, or `mcp`. MCP is recommended but not required.
- **Conformance harness** — importable Go package (`gemba/testing`) plus `gemba adaptor test` CLI so third-party adaptor authors can run contract tests in their own CI.
- **SSE events** — discriminated union, capability-filtered subscriptions, W3C trace propagation, rotation + retention from day one.
- **External consumer preservation** — the API, schema, and conformance harness are designed so future UIs (VS Code extensions, npm wrappers, third-party consumers) can sit over Gemba's adaptor layer without forking.

## Security + auditability

- **Mutation safety**: every mutation requires a server-enforced `X-GEMBA-Confirm` nonce; `--dangerously-skip-permissions` (copied verbatim from Claude Code, not softened) disables for the session.
- **Auth**: localhost-bound by default; non-loopback bind without `--auth` is a startup error; token auth is 256-bit, argon2id-hashed, printed once; TLS via user certs or `--tls-self-signed`.
- **Data integrity**: never write any backend's private storage directly; every mutation round-trips through the adaptor's public CLI/API.
- **Audit log**: every persona consult + Manager action + checkpoint + mutation is recorded as an immutable record; `/insights/personas` + the Checkpoint timeline make everything retros-ready.

## What Gemba is *not*

- Not a replacement for a full-featured PM SaaS — Gemba plugs into Jira, Linear, Beads; it doesn't replace them.
- Not an agent framework — agents run in Gas Town, LangGraph, OpenHands, whatever your orchestrator is; Gemba renders and directs, not embeds.
- Not a chat product — personas surface in chat modals, but the product value is in the structured Skill outputs and Kanban-level operational UX.
- Not a mobile native app — responsive web is enough.
- Not an in-tree feature of any backend — always sidecar; always standalone binary.

---

*The factory floor, the walk, and the specialists — all in one pane of glass, at the right grain, with nothing else to switch between.*
