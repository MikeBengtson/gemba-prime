# Discord post (short-form RFC)

## Message 1 — the pitch

Hey 👋 posting this for community feedback before I commit further build cycles. TL;DR below; full RFC + product description attached.

**Gemba** (`gemba`) — the Gemba walk UI for agentic software projects. **Large-scale side-of-the-desk projects: big impact, minimal cognitive load.**

In lean manufacturing, *gemba* (現場) is "the actual place" — the factory floor. A *gemba walk* is when leadership observes the work directly, not through reports, and leaves actionable feedback as they go. Gemba the product is a browser-based UI for exactly that: walking the floor of an agentic software project — with configurable LLM specialists a click away for the expertise the operator doesn't have time to personally deliver.

Single-binary Go service with an embedded React SPA. Pairs *exactly one* **WorkPlane adaptor** (work tracker — Beads, Jira, Linear, GitHub Projects, Azure DevOps, Shortcut, Plane, …) with *exactly one* **OrchestrationPlane adaptor** (agent runtime — Gas Town, Gas City, LangGraph, CrewAI, OpenHands, Devin, Factory, …) and renders whatever the two declare.

The product is the abstraction plus the Persona layer on top. Beads + Gas Town ship as v1 *reference* pack-ins. Jira (WorkPlane) and LangGraph (OrchestrationPlane) are v1 *forcing-function* adaptors — if the contract handles Jira's workflow FSM, Linear is easy; if it handles LangGraph's checkpoint-and-graph topology, OpenHands is easy.

**Two Persona varieties:** **Coaches** (conversational, advisory — Architect, Code Reviewer, UX Expert, Technical Writer, Documentarian, Onboarder) and **Managers** (agentic, can be gate-blocking — Project Manager, QA, Deployment Engineer, DevOps/SRE, Security). PM's `add_to_backlog` skill files beads; QA's gate can block a release; every persona has separately configurable prompt + context providers + output validation. **Gemba walks** make the interactive multi-topic decisioning conversation first-class — the PM pulls escalations from every worker (polecat / persona / gate / budget / adaptor-degraded) into one agenda and walks the operator through ratification. **Agentic code analysis** (GitNexus-class) is a first-class pluggable capability — the knowledge graph feeds personas' context and powers richer source-code-repo bootstrap. Ship curated packs with arbitrary names and intents (CTO today; CEO / COO / CRO/LRC later; domain / task / framework packs open to anyone).

**No backend-specific vocabulary in the core SPA** — all backend-flavor lives in capability-gated extension widgets.

**What it's for — three concrete workflows:**
1. **Walk the floor.** Epic-granular Kanban is the home screen — cards are Epics (not individual stories) with readiness counts, parallel-group membership, escalation state, token-budget posture. Drill-down to member work items is double-click. The Plan view lets you drag-to-reorder, toggle in/out of scope, and launch the batch after parallel-safety is verified.
2. **Ask a specialist.** PM panel always available. `/plan` "Recommend order" → PM persona returns JSONL-ranked Epics with rationale. Managers can take scoped agentic action (`add_to_backlog`, `change_this`, `check release readiness`), consult other personas mid-task, and HITL-pause when they need a judgment call. QA gates can block a release; override requires persona consensus or nonce-confirmed justification.
3. **Undo back to yesterday.** Checkpoints atomically snapshot every git repo involved, the Beads database, live session context summaries, sidecar state, and artifacts. Restore rolls every dimension back together.

**Values + guardrails + modes.** Projects inject values (innovation / transparency / execution / empathy ship as defaults) into the highest prompt layer. Guardrails are values with explicit blockers. Workspace modes (unsupervised / supervised / managed) govern interaction style. Bootstrap pulls from Jira or Beads and generates the project description, initial goals, candidate values, and starting plan for the operator to ratify.

**The four hardest open questions I most want answered:**
- **DD-1 (Agent as first-class core type).** Is `{agent_id, display_name, role, parent_id?, agent_kind}` enough to render usefully without amputating dimensions orchestrator maintainers care about?
- **DD-9 (3 core edge types + adaptor extensions).** Beads has 7 edges; Jira has many; LangGraph has graph-edges. Is `blocks`/`parent_child`/`relates_to` core + the rest as namespaced extensions a contract trackers can write against?
- **DD-13 (synthesize Evidence at the adaptor edge).** Tag `synthesized: true` on git/CI-derived evidence so the UI renders provenance honestly. Trackers with native PR-link evidence: is the contract clear?
- **DD-14 (Sprint-as-token-budget).** Three-tier enforcement at epic and sprint scope. Tokens the only enforced axis in v1. Scrum-fluent users: does this redefinition break your mental model?

(thread 👇)

---

## Message 2 — the answer to "why a sidecar"

A few people will ask why this is a sidecar instead of a backend-native dashboard or a tracker plugin. Three reasons:

1. **Cross-plane is the value.** Backend-native dashboards (gt dashboard, Linear UI, Jira native) all have the same shape: tightly coupled to one backend, one work model, one set of vocabulary. Gemba's value is the cross-plane view — work tracker × agent orchestrator — without picking sides.
2. **No backend's plugin surface is for HTTP servers.** Sidecar is the idiomatic path everywhere.
3. **Adaptor work is decoupled from backend release cycles.** A new Linear adaptor doesn't require a Linear release. A LangGraph upgrade doesn't require a Gemba release.

---

## Message 3 — the work package

~80 beads across 14 phase epics:

1. Foundation — repo, Cobra, embed, Vite/React/TS, Makefile, CI
2. Validation — four sociopolitical gates (DD-1, DD-9, DD-13, DD-14)
3. Core contracts — domain types, two adaptor interfaces, registration, conformance harness, events, noop adaptors
4. Transport — HTTP API, OpenAPI/TS codegen, SSE, mutation nonce
5. Auth — bind policy, token, TLS, OIDC stub
6. Reference WorkPlane: Beads
7. Reference OrchestrationPlane: Gas Town
8. Forcing-function WorkPlane: Jira
9. Forcing-function OrchestrationPlane: LangGraph (transport: mcp — proves transport plurality)
10. Stub OrchestrationPlane: Gas City
11. Cross-cutting (DoD, CostMeter, Escalation, Capability, Sprint+Budget, Evidence, Transport)
12. UI — adaptor-agnostic SPA (every component capability-gated)
13. Molecules — capability-gated workflow DAGs (Gas Town today)
14. Release — goreleaser, brew, npm, docs, guide, announcement

Phase 1 scaffold is built and verified locally.

---

## Message 4 — the asks

If you maintain a work tracker (Beads, Jira, Linear, GitHub Projects, Azure DevOps, Shortcut, Plane) or an agent orchestrator (Gas Town, Gas City, LangGraph, CrewAI, OpenHands, Devin, Factory) — or operate either at scale — I'd love a sanity check on the four hardest decisions above.

If you're building something similar — happy to join forces.

If you think this is the wrong shape entirely — that's the cheapest thing to find out now.

Full RFC attached. Thanks for reading.
