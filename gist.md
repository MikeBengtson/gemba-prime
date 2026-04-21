# Gemba

**Large-scale side-of-the-desk projects: big impact, minimal cognitive load.**

In lean manufacturing, *gemba* (現場) is "the actual place" — the factory floor. A *gemba walk* is when leadership observes the work directly, not through reports, and leaves actionable feedback as they go. Gemba the product is a browser-based UI for exactly that: walking the floor of an agentic software project, seeing the work at the right grain, and directing it — with a roster of configurable LLM-backed specialists a click away when the expertise isn't already in the operator's head.

**The shape.** A single Go binary with an embedded React SPA. It pairs one **Work Coordination Plane** adaptor (the issue tracker — Beads, Jira, Linear, GitHub Projects, …) with one **Agent Orchestration Plane** adaptor (the agent runtime — Gas Town, Gas City, LangGraph, OpenHands, …) under a typed contract. The UI is adaptor-agnostic: no backend vocabulary leaks in; what renders is what the active capability manifests declare. Beads and Gas Town ship as reference pack-ins. Jira and LangGraph are the forcing-function adaptors that prove the abstraction isn't Beads- or Gas-Town-shaped.

**The home screen is an Epic-granular Kanban.** Cards are Epics, not stories — with readiness counts, parallel-group membership, escalation state, token-budget posture, and drill-down to member work items. The operator's real decision (what to stage next, what can run in parallel) happens at this level. A dedicated Plan view lets them drag to reorder, toggle in or out of scope, and launch the whole batch in one click after parallel-safety is verified.

**Personas are first-class: Coaches and Managers.** Coaches are conversational and advisory — Architect, Code Reviewer, UX Expert, Technical Writer, Documentarian, Onboarder. Managers are agentic — Project Manager, QA, Deployment Engineer, DevOps/SRE, Security. Managers execute scoped tasks (*add this to backlog*, *change this*, *check release readiness*), consult other personas mid-task, pause for human-in-the-loop input when they need a judgment call, and can block state transitions (QA gating a release). Each persona has separately configurable prompt, context providers, and output validation. Add a persona by dropping a TOML file. Ship curated **role packs** — CTO today; CEO, COO, CRO/LRC later.

**Project values and guardrails are injected at the highest prompt layer.** Innovation, transparency, execution, empathy ship as defaults; projects add their own. Guardrails are values with explicit blockers that Managers refuse to cross. Project and Epic goals are PM-generated, user-editable, and flow into every relevant persona invocation. Workspace modes (unsupervised / supervised / managed) govern interaction style — managed mode requires approval at every coarse-grained step; unsupervised widens auto-approve budgets.

**Jam Sessions** are the first-class interactive decisioning surface — multi-topic conversations with the PM that aggregate escalations from every worker (polecat / persona / gate / budget / adaptor-degraded) and produce a stream of ratified / modified / rejected / deferred decisions. Resumable, auditable, and the native mode for walking the floor at scale.

**Whole-project versioning.** Checkpoints atomically snapshot every git repo, the Beads database, live session context, sidecar state, and artifacts. v1 triggers are intentionally minimal (manual + epic-start + epic-stop); each checkpoint emits a Beads record so snapshots are as discoverable as any other workspace event. Operators can "undo back to yesterday" and roll every dimension back together.

**Bootstrap** pulls from one of four sources: Jira (doc-import), Beads (local seed), **an existing source-code repo** (agentic code analysis walks module structure + call graph + entry points to propose candidate Epic decomposition), or fresh (Onboarder-driven interview). Agentic code analysis — GitNexus-class knowledge graphs — is itself a first-class Gemba capability: pluggable backends feed four context providers that every persona opts into as needed. Workspace repos (the `gemba_prime` / `gemba` pattern) are supported first-class.

**Organization surface.** Jira, XRay (test management + evidence), and configurable linters plug in as team-level concerns — QA reads and writes XRay, runs linters as regression suites, and gates state transitions on combined results. **Execution surface.** Beads and Gas Town ship as reference pack-ins; alternatives arrive via the pack browser.

**Extensibility: adaptors, personas, packs.** Write a WorkPlane or OrchestrationPlane adaptor against the typed contract and run the importable conformance harness. Curate a persona, or a pack bundling personas + skills + default values — **packs are arbitrary in name and intent** (role packs like CTO today / CEO / COO / CRO-LRC tomorrow; domain packs; task packs; framework packs; customer-specific private packs). Signed for provenance, public or private.

**Business model.** Gemba core is OSS. Commercial value is in adaptor + persona pack curation, and in training and change-management consulting for teams adopting agentic workflows at scale.

*The place where work happens, and the operator can see all of it at the right grain, with the right expertise a click away.*
