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

## The expertise layer — Personas in two varieties

**Coaches** are conversational and advisory — they suggest, the operator applies or dismisses:

- Architect, Code Reviewer, UX Expert, Technical Writer, Documentarian, Onboarder.

**Managers** are agentic and can be gate-blocking — they execute scoped tasks directly:

- Project Manager, QA, Deployment Engineer, DevOps/SRE, Security.

Managers can:

- File beads (PM's `add_to_backlog` skill, with mid-task consultation of Architect + QA as needed)
- Modify in-flight work (PM's `change_this` skill, with reverse-actions recorded)
- Block state transitions (QA's gate can block a release; override requires persona consensus or nonce-confirmed justification)

Every persona has **separately configurable prompt, context providers, and output validation**. Each lives as a TOML file; users add / modify / disable freely.

**Jam Sessions** formalize the interactive multi-topic decisioning conversation. The PM aggregates escalations from every worker (polecat HITL, Manager persona suspension, gate failures, budget crossings, adaptor-degraded events) into one agenda and walks the operator through ratification — resumable across days, auditable, the native mode for working a busy backlog at scale.

## The workspace

**Epic-granular Kanban** as the home screen. Cards are Epics — not individual stories — showing:

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

Three surfaces. All three support OSS or proprietary distribution, signed or unsigned, public or private.

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

## Business model

- **Core** is open-source under a permissive license.
- **Specialty packs** — paid, curated domain expertise (compliance, industry-specific strategy, regulatory-domain prompt libraries).
- **Training + change-management consulting** — for teams adopting agentic workflows at scale.

---

*The factory floor, the walk, and the specialists — all in one pane of glass, at the right grain, with nothing else to switch between.*
