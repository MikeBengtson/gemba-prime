# Gemba

> Large-scale **side-of-the-desk** projects: big impact, minimal cognitive load.

## The name

In lean manufacturing, *gemba* (現場) is Japanese for "the actual place" — the factory floor, where real work happens. A **gemba walk** is when leadership steps onto the floor to observe the work directly, not through reports, and leaves actionable feedback as they go.

Gemba the product is built around that metaphor. The agents are on the floor, doing the work. The operator — one person, wearing many hats — walks the floor, watches, nudges, and redirects. The UI is the walk.

## Problem statement

Operators running agentic software projects today hit a consistent failure pattern:

- **Planning is disconnected from execution.** Issues live in Jira or Beads; agents run in another terminal; output lives in git. Nobody sees all three at once.
- **Priority is invisible.** The dep graph says what *can* run; nothing says what *should* run next. The operator holds that in their head, which is fine for one project and unworkable for side-of-the-desk projects.
- **Expertise is siloed.** A side-of-the-desk project needs product judgment, architecture, UX review, QA gating, release mechanics, security — and the operator doesn't have time to don all those hats, one after the other, before shipping each increment.
- **State is fragile.** An unfruitful development line can't be cleanly reversed because git, Beads, LLM sessions, and sidecar artifacts each move on their own timeline. "Undo back to yesterday" doesn't exist.
- **Orchestration tooling is tied to one runtime.** Tools that play nicely with one agent framework or one issue tracker force a rewrite when either moves. An abstraction has never shipped.

Gemba addresses all five.

## What Gemba is

A **single-binary Go service with an embedded React SPA** that sits alongside an agentic software project and acts as its Gemba walk UI + management layer. It pairs a **Work Coordination Plane** adaptor (issue tracker — Beads, Jira, Linear, GitHub Projects, …) with an **Agent Orchestration Plane** adaptor (agent runtime — Gas Town, Gas City, LangGraph, OpenHands, …) under one interface. It ships with an opinionated **Persona layer** — configurable LLM-backed Coaches and Managers that supply the expertise the operator doesn't have time to personally deliver for every decision.

Beads and Gas Town ship as reference **pack-ins**. Jira and LangGraph are the forcing-function adaptors that prove the two-plane abstraction isn't Beads- or Gas-Town-shaped. XRay and standard linters integrate as QA's organization-surface tools. Extensibility is via adaptor plugins, persona curation, and role packs.

## How it works

### The two planes

Every workspace pairs exactly one Work Coordination Plane adaptor with exactly one Agent Orchestration Plane adaptor. The planes are typed contracts; adaptors declare their capabilities in a manifest; the UI renders only what the active manifests advertise. No backend-specific vocabulary leaks into the core SPA.

```
┌──────────────────────────────────────────────────────────┐
│  Gemba SPA — adaptor-agnostic, capability-driven          │
└──────────────────────────────────────────────────────────┘
                          ▲
                     HTTP · SSE
                          ▼
┌──────────────────────────────────────────────────────────┐
│  Gemba core (Go) — WorkItem, Agent, Epic, Evidence,       │
│  Sprint+TokenBudget, Escalation, Session, Persona, ...    │
└──────────────────────────────────────────────────────────┘
       ▲                                             ▲
 WorkPlaneAdaptor                     OrchestrationPlaneAdaptor
       ▼                                             ▼
 Beads · Jira · Linear · ...               Gas Town · LangGraph · ...
```

### The Gemba — the main view

The home screen is **the Gemba** itself — the factory-floor rendering of your project. Its primary layout is an Epic-granular Kanban where **cards are Epics**, not individual stories. Each Epic card surfaces: readiness counts (how many members are ready, blocked, in-progress), critical-path length, parallel-group membership, escalation state, and token-budget posture. Double-click drills into the member WorkItems in stage order.

The operator's main decision — *what to stage next, and what can run in parallel* — happens at this level. Stories exist; they're not the default unit.

### The Plan view — staging UX

A dedicated surface (`/plan`) lists actionable Epics in recommended order, grouped by `ParallelGroup`. The operator drags to reorder, toggles Epics in or out of scope, and clicks **Execute all in-scope** to launch the batch. Parallel safety is verified before launch.

### Gemba walks — the interactive decisioning surface

A **Gemba walk** is an interactive multi-topic conversation between the operator and the PM persona — the same pattern an operator-and-assistant fall into naturally when working through a busy backlog, made first-class. On start, the PM auto-populates the agenda from every escalation source in the workspace: open EscalationRequests (polecat / crew / Manager persona / Witness / Refinery / Gate failures), pending HITL questions from suspended Manager sessions, recently-filed beads needing ratification, recently-closed work needing retro. The operator and PM walk the agenda: for each item, PM frames, proposes actions; operator ratifies / modifies / rejects / defers; decisions apply as nonce-gated mutations; remaining items park for later or defer to backlog.

Gemba walks are resumable (pause and pick up days later; serialized state survives process restarts), auditable (every decision plus the full transcript lands in the audit log), and produce a Documentarian-written summary artifact on end. The always-available PM panel doubles as the active Gemba walk's chat surface — no context switch between "asking the PM" and "working the list."

### Agentic code analysis — first-class knowledge-graph context

Every persona — Architect, PM, Code Reviewer, QA, Documentarian, Security — reasons better when it has the actual call graph, flow graph, and module structure of the codebase, not just the README and git log. Gemba makes **agentic code analysis** a first-class pluggable capability: GitNexus is the reference backend; Sourcegraph, CodeQL, or custom tree-sitter-driven indexers plug in via a typed `CodeAnalysisProvider` interface. The knowledge graph surfaces as four context providers personas can opt into (summary, symbol-context, impact-analysis, health-report), feeds the bootstrap flow's source-code-import path for richer first-draft epic decomposition, and is reindexed automatically on merge (configurable per repo).

### Coaches and Managers

Personas are first-class configurable LLM assistants. Two varieties:

- **Coaches** — conversational, advisory. Offer suggestions the operator applies or dismisses. Non-blocking. *Architect, Code Reviewer, UX Expert, Technical Writer, Documentarian, Onboarder.*
- **Managers** — agentic. Given a scoped task (*"add this to backlog"*, *"change this"*, *"check release readiness"*) they perform the work themselves, consulting other personas mid-task, pausing for human-in-the-loop input when they need a judgment call, and applying changes through the same nonce-gated API any client uses. Can be configured to block state transitions (QA gating a release, for instance). *Project Manager, QA, Deployment Engineer, DevOps/SRE, Security (Manager for auth-labeled work).*

Each persona has **separately configurable prompt, context providers, and output validation/sharing**. Context providers include: project summary, project state, decisions log, issues log, and per-repo bead databases. The operator swaps models, tunes prompts, opts context on or off — no code changes.

Personas are **extensible and composable**. Add a persona by writing a TOML file in `.gemba/personas/`. Compose by declaring which Skills a persona opts into and which other personas it may consult. Ship curated role **Packs** — bundles of personas + skills + default values (*CTO pack* today; *CEO*, *COO*, *CRO/LRC* later) — as the install/swap unit.

The **always-available PM panel** lives in the SPA chrome. Any decision point — "what's next", "is this release ready", "add this to backlog" — is one click away, on every screen.

### Values, guardrails, goals

Every project injects four seed **values** at the highest prompt layer:

- **Innovation** — validate against prior art; don't reinvent
- **Transparency** — always surface what you're unsure of, left incomplete, or couldn't decide
- **Execution** — every project converges toward release
- **Empathy** — users span a wide range of skill and experience

**Guardrails** are values with explicit blockers — conditions where a Manager persona refuses to proceed. Projects can add their own.

**Project goals** and **Epic goals** are PM-generated and user-editable. They flow into the relevant prompt layers: a PM consulting the Architect on a new feature gets both sets of goals in context.

### Workspace modes

Three operator-visible modes govern interaction style:

- **Unsupervised** — no interruptions; take your best guess; call the AI to solve if needed
- **Supervised** (default) — largely automatic; may check in on ambiguous decisions
- **Managed** — all coarse-grained steps summarized and presented for approval before execution

Modes compose with workspace mutation policy: managed mode narrows auto-approve budgets; unsupervised widens them. Mode is first-class workspace config.

### Checkpoints — whole-project versioning

A **Checkpoint** is an atomic, cross-dimension snapshot: every git repo involved, the Beads database state, live LLM session context summaries, Gemba's sidecar state, and generated artifacts. Operators can "undo back to yesterday" via a Checkpoint, which rolls every dimension back atomically.

**v1 triggers** are intentionally minimal: **manual** (user clicks "Checkpoint now" with a label), **epic_start** (auto-fire when an Epic transitions to InProgress), and **epic_stop** (auto-fire on completion). Each checkpoint emits a first-class Beads record (informational bead with `kind:checkpoint`) so snapshots are discoverable via `bd list`, citable from personas, and appear in `what_remains` coaching alongside regular work.

**Restore** is nonce-gated, atomic across dimensions, surfaces external-state warnings (pushed commits can't un-push), and auto-checkpoints the current state so the restore itself is undoable. Local CAS (content-addressed storage) backs the snapshots in v1; remote backends (S3 / GCS / Git-LFS) are a v2 follow-up. Additional trigger kinds (scheduled, pre-persona-mutation, pre-sling, pre-merge, pre-release, session_start, post_restore) also defer to v2.

### Bootstrap

A new project bootstraps from one of four first-class sources: **Jira** (doc-import adaptor reads existing epics/stories/specs/acceptance-criteria), **Beads** (local workspace seed), **Source-code repo** (existing git repo — the agentic code analysis capability walks module structure, call graph, entry points, and recent git history to propose candidate Epic decomposition), or **Fresh** (Onboarder-driven 5–10-question interview). An Onboarder + PM + Documentarian trio runs on whatever source is chosen to produce: a project description, initial goals, candidate values, recommended guardrails, and a validated-for-consistency starting plan. The operator reviews + edits + ratifies via nonce; Gemba commits the new project config. Wizard UI at `/bootstrap`.

## User surfaces

- **Epic Kanban** (home) — drag-to-reorder, scope toggles, drill-down to members
- **Plan view** — staging, parallel-group grouping, execute-all
- **Gemba walk** — interactive multi-topic decisioning with PM, aggregating escalations from all workers
- **PM panel** — persistent, right-side; any question any time; doubles as active-Gemba walk chat
- **Persona roster + chat modals** — conversational access to every configured Coach and Manager
- **WorkItem grid** — Jira/Linear-style power-user view for triage
- **Dependency graph** — React Flow over the three core edge types + declared extensions
- **Insights panel** — OTEL-driven: spawn rate, sprint burn, stuck-session minutes, token cost, escalation backlog
- **`/qa/health` + `/qa/gates`** — QA dashboard with regression suites, coverage, gate status
- **Agent detail + session peek** — provider-aware (tmux attach, k8s pod status, container logs, subprocess tree, exec output)
- **Escalations inbox** — unified surface for orchestrator pauses, HITL questions, budget crossings, rate-limit waits, gate failures
- **Capability browser** — what each active adaptor can and cannot do
- **Code analysis explorer** — knowledge-graph queries, module inventory, impact analysis, health report
- **Checkpoints timeline** — snapshot history with restore UX
- **Adaptor marketplace / Pack browser** — installable adaptors and pack bundles (arbitrary names and intents)

## System surfaces

- **HTTP API** at `/api/v1/*` — OpenAPI-documented, TS client codegenned
- **SSE events** — typed discriminated union, capability-filtered subscriptions, W3C trace propagation, rotation + retention policy
- **Two-plane adaptor contracts** — `WorkPlaneAdaptor`, `OrchestrationPlaneAdaptor`; transport plurality (`api | jsonl | mcp`)
- **Conformance harness** — importable Go package (`gemba/testing`); `gemba adaptor test` CLI for third-party authors
- **Persona contract** — `Persona`, `Skill`, `SkillRequest`, `SkillResponse`, `PersonaConsultRecord` typed entities; TOML-based persona definitions
- **Checkpoint CAS** — content-addressed storage for snapshot artifacts, optional remote backend
- **Mutation safety** — server-enforced `X-GEMBA-Confirm` nonce, argon2id-hashed 256-bit tokens, TLS via user cert or self-signed, OIDC adaptor stubbed

## Organization surface

Tools shared across a team or organization — planning and audit at scale:

- **Jira** — issue tracking as a WorkPlane adaptor; doc-import adaptor for bootstrapping Gemba from existing Jira projects
- **XRay** — test management + evidence/traceability layer as the QA Manager's canonical integration: imports test-case definitions, submits run results, attaches evidence to test executions, reads requirement-to-test coverage
- **Configurable style + general linters** — QA Manager's code-quality axis; linter configs plug into the regression-suite catalog the same way test frameworks do

Gemba's QA persona reads and writes XRay, runs linters as regression suites, and gates state transitions on the combined result.

## Execution surface

Per-workspace, where the actual work happens — the reference pack-ins Gemba ships with:

- **Beads** — the reference WorkPlane. Git-native, Dolt-versioned issues. Bootstrap convention for most users.
- **Gas Town** — the reference OrchestrationPlane. Multi-agent rigs in git worktrees, tmux session lifecycle, mail-based coordination.

Both are swappable. Jira + LangGraph prove the contract; a Gas City adaptor is designed-for. Community adaptors ship in the pack browser.

## Workspace repo

Every Gemba project pairs two repos by convention:

- **`<project>_prime`** — the workspace repo: docs, digests, design artifacts, decision log, this kind of material. Versioned, commit-logged, walk-able as a historical record.
- **`<project>`** — the output repo: the actual shippable code / content.

The workspace repo is a Gemba-supported first-class concept. Bootstrapping creates both; adaptors map to both; Checkpoints capture both atomically.

## Branch strategy

Configurable, with sensible defaults:

- **Default**: one worktree per worker (polecat, crew). Each worker's branch is their workspace.
- **Optional**: named feature branches or experiment branches for major work, configurable per workspace.
- **Always**: the merge queue is the only path to main. Workers never push to main directly.

## Extensibility

Three extension surfaces:

1. **Adaptors** — write a `WorkPlaneAdaptor` or `OrchestrationPlaneAdaptor` implementing the typed contract. Ship via Go module or over the MCP transport. Run the conformance harness in your CI. Publish in the adaptor marketplace.
2. **Personas** — author a TOML file in `.gemba/personas/`. Tune system prompt, select model, opt context providers on/off, declare the Skills you fulfill, set budget caps.
3. **Packs** — bundles of personas + skills + default values + guardrails + adaptor preferences + UI emphasis. Installable unit. Ship signed for provenance (private packs for internal teams; public packs for community distribution). Packs are **arbitrary in name and intent**, not just executive-role-shaped — the v1 seed ships a CTO pack; future first-party packs will cover CEO / COO / CRO-LRC contexts; community and private packs can be organized any way that makes sense (domain packs like `fintech-compliance` or `healthcare-hipaa`; framework packs like `langchain-focused`; task packs like `migration` or `launch-readiness`; customer-specific internal packs). Default install scope is per-workspace — a team can run one pack on one project and a different pack on another.

## Multi-organization-context roadmap

Gemba v1 ships optimized for **CTO context** — technical leadership of an agentic software project, which is where the product originates and where the v1 pack ships. The adaptor + persona + pack architecture is designed to extend:

- **CEO context** — product-strategy work: market validation, positioning, customer discovery, founder narrative. Pack includes product-strategy and go-to-market personas.
- **COO context** — ongoing operations: support load, uptime, on-call rotation, capacity planning. Pack includes incident-response and capacity-planning personas.
- **CRO / LRC context** — legal, risk, compliance: contract review, license compliance, data handling policy, audit response. Pack includes policy-review and audit-prep personas.

All four contexts share the same core (two planes, Kanban, Plan view, Checkpoints, API). They differ in persona roster, default values, and the UI surfaces that emphasize.

## What Gemba is *not*

- A replacement for a full-featured project management SaaS. Gemba plugs into Jira, Linear, Beads — it doesn't replace them.
- An agent framework. Agents run via Gas Town, LangGraph, OpenHands, or whatever your orchestrator is. Gemba renders and directs them; it doesn't embed them.
- A chat product. Personas surface in chat modals, but the product value is in the structured Skill outputs and the Kanban-level operational UX, not the chat UI.
- A mobile app. Responsive web is enough.
- An in-tree feature of any backend. Always sidecar; always standalone binary.

---

*Gemba is the UI for walking the factory floor of an agentic software project. Where the work happens — and where the operator can see all of it, at the right grain, with the right expertise a click away.*
