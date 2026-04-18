# Discord post (short-form RFC)

## Message 1 — the pitch

Hey 👋 posting this for community feedback before I commit further build cycles. TL;DR below; full RFC attached.

**Gemba** (`gemba`) — a single-binary Go service with an embedded React SPA that pairs *exactly one* **WorkPlane adaptor** (work tracker — Beads, Jira, Linear, GitHub Projects, Azure DevOps, Shortcut, Plane, …) with *exactly one* **OrchestrationPlane adaptor** (agent runtime — Gas Town, Gas City, LangGraph, CrewAI, OpenHands, Devin, Factory, …) and renders whatever the two declare.

The product is the abstraction. Beads + Gas Town are the v1 *reference* adaptors. Jira (WorkPlane) and LangGraph (OrchestrationPlane) are v1 *forcing-function* adaptors — picked because their quirks are supersets of the easier members of their categories. If the contract handles Jira's workflow FSM, Linear is easy. If it handles LangGraph's checkpoint-and-graph topology, OpenHands is easy.

**No backend-specific vocabulary in the core SPA** — all backend-flavor lives in capability-gated extension widgets under `web/src/extensions/<adaptor-id>/`.

**What it's for — three concrete workflows:**
1. **Plan & refine.** 10k-WorkItem virtualized grid across every workspace; saved filters; bulk JSONL import; Jira-style detail drawer.
2. **Day-of ops.** AgentGroup Kanban (the home screen) — drag-drop round-trips through `WorkPlaneAdaptor.transition`; multi-select to dispatch via `OrchestrationPlaneAdaptor.acquire_workspace + start_session`. Desired-vs-actual drift tints column headers; provider-aware agent peek; every mutation `X-GEMBA-Confirm` nonce-gated.
3. **Retro & release.** Landed-AgentGroup review, molecule replay, insights from OTEL + adaptor-supplied `CostMeter`; sprint-as-token-budget with three-tier inform/warn/stop enforcement.

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
