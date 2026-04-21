# Landscape Survey

**Author:** Principal architect research pass
**Date:** 2026-04-18
**Purpose:** Evidence-backed landscape survey of agentic software-development orchestration systems and work-tracking platforms, grounding the two-plane abstraction in `domain.md`. Research only — no design decisions made here.

**Assumptions stated up front:**
- "Latest release / commit" reflects what public search surfaced on 2026-04-18; private roadmaps are unknown.
- Where this document cites a dated blog post or aggregator page, the underlying primary source was preferred when available.
- Items flagged "I could not determine X" are real gaps in the public record, not investigative failures to suppress.
- Gas Town and Gas City information comes from a mix of public repos (`github.com/steveyegge/gastown`, `github.com/gastownhall/gascity`) and the local workspace (`/Users/mikebengtson/gt/`). Local-workspace-only details are labelled as such.

---

## 1. Taxonomy

These five categories are distinct along three axes: (a) who runs the code, (b) what the contract is, (c) who the end user is. A system can span categories — Claude Code is both an IDE agent and (via the Agent SDK) a framework — but we tag by its *primary* positioning.

- **Agent orchestration protocol** — A wire-level, vendor-neutral contract specifying messages, lifecycle, and identity for agent interop. Does not prescribe runtime, language, or work model. Examples: MCP (tool/resource/prompt contract), A2A (agent-to-agent task/artifact contract), ACP (IBM's HTTP-only variant), AG-UI (agent ↔ frontend). Protocols define *shapes*; they do not schedule work.
- **Agent orchestration framework** — A library or runtime for composing multi-step, multi-agent workflows in a host program. Ships as code the user links against. Control flow is expressed in the framework's idioms (graph, crew, handoff, flow). Examples: LangGraph, CrewAI, OpenAI Agents SDK, Anthropic Claude Agent SDK, Google ADK, Microsoft Agent Framework.
- **Agent execution product** — A deployed system a user interacts with to run agents end-to-end: it owns the sandbox, the scheduler, the UI, and usually a billing meter. Not a library. Examples: Devin, OpenHands Cloud, Factory, Cursor Cloud Agents, Gas Town, Gas City.
- **Work tracker** — A system of record for *units of work* (issues, stories, epics, tasks), their relationships, their state transitions, their assignees, and their evidence (comments, links, attachments). API-first ones can be driven by agents; schema-rigid ones resist it. Examples: Jira, Linear, GitHub Issues/Projects, Azure DevOps Boards, Shortcut, Asana, Basecamp, Plane.so, Beads.
- **Coding agent / IDE agent** — Single-operator assistants that live in (or alongside) an editor/terminal and work on the user's behalf on one task at a time. They may internally spawn subagents, but the end-user mental model is *one agent on one change*. Examples: Aider, Cline, Roo Code, Continue.dev, Sourcegraph Amp, Cursor (in-editor), Goose.

Gemba is a **UI over work-tracker + execution-product pairs**. Its abstraction therefore needs to bind those two categories; protocols and frameworks are implementation details downstream of that binding.

---

## 2. Agent-side survey

### Tier 1 — deep cards

### Gas Town

**Category:** Agent execution product
**Status:** Active (v1.0, released April 2026)
**Latest release / commit:** v1.0 stable, April 2026 ([DoltHub blog: A Week in Gas Town, 2026-03-24](https://www.dolthub.com/blog/2026-03-24-a-week-in-gas-town/))
**Primary sources:**
- [github.com/steveyegge/gastown](https://github.com/steveyegge/gastown)
- [Steve Yegge — Welcome to Gas Town](https://steve-yegge.medium.com/welcome-to-gas-town-4f25ee16dd04)
- [Cloud Native Now — Kubernetes for AI Coding Agents](https://cloudnativenow.com/features/gas-town-what-kubernetes-for-ai-coding-agents-actually-looks-like/)
- Local workspace at `/Users/mikebengtson/gt/` (observed)

Gas Town is a multi-agent workspace manager that coordinates heterogeneous coding agents (Claude Code, Copilot, Codex, Gemini) on a shared codebase by giving each a dedicated *rig* (git worktree + tmux session) and routing work through Beads. Identity (the agent persona) persists while sessions (the process) are ephemeral. A Mayor agent is the human's primary interface; Deacons, Witnesses, and other fixed roles provide supervision, auditing, and escalation. Gas Town does not link against agent code — integration is configuration via shell commands.

- **Work item model:** Beads issues (Dolt-backed). Bead IDs prefixed by city (`gt-abc12`, `hq-x7k2m`).
- **Worker grouping model:** Fixed role hierarchy (Mayor, Deacon, Witness, worker roles) + elastic worker pools.
- **Repository interaction:** Git worktree per rig (persistent on disk under `~/gt/<agent>/`).
- **Assignment mechanism:** Push via Mayor + pull via `bd ready` from worker rigs.
- **Merge / conflict handling:** Worktree-level isolation; integration happens when agents commit back to main. No automatic cross-worktree conflict detection (inherited from git worktree semantics — see [Penligent analysis](https://www.penligent.ai/hackinglabs/git-worktrees-need-runtime-isolation-for-parallel-ai-agent-development/)).
- **State model:** Beads states (open → in_progress → closed; plus blocked derived from deps). No Gas-Town-native workflow states — delegated to Beads.
- **Traceability:** Each bead links to commits via agent work history stored in Dolt; `bd remember` persists context beads across sessions.
- **Extension points:** Agent provider integration is shell-command based ([agent-provider-integration.md](https://github.com/steveyegge/gastown/blob/main/docs/agent-provider-integration.md)). Mail protocol, escalation protocol, formulas (agent role templates).
- **Distinctive feature:** Persistent agent *identity* decoupled from *session* lifetime, backed by a versioned SQL database (Dolt) that can be diffed, branched, and merged like source code.
- **Observed limitations:** Dolt is explicitly called "fragile" in internal docs (per `/Users/mikebengtson/gt/CLAUDE.md`, which mandates a diagnostic-then-escalate protocol for Dolt hangs). Fixed role structure limits fluid reassignment. Tmux-only runtime pins Gas Town to local workstations/servers.

---

### Gas City

**Category:** Agent execution product (declarative, pre-release)
**Status:** Pre-release / alpha
**Latest release / commit:** Active development as of April 2026 ([github.com/gastownhall/gascity](https://github.com/gastownhall/gascity))
**Primary sources:**
- [github.com/gastownhall/gascity](https://github.com/gastownhall/gascity)
- [gascityhall.com](https://gascityhall.com/)

Gas City is the declarative successor SDK to Gas Town. It extracts Gas Town's reusable infrastructure (runtime providers, work routing, formulas, orders, health patrol) into a configurable toolkit driven by `city.toml` declared state and `.gc/agents/` running sessions. Pack-agnostic: agent behaviors are user-authored packs rather than Gas Town's fixed roles. Provider pluggable: tmux, subprocess, k8s, exec. Work provider pluggable: Beads by default, file-based with `GC_BEADS=file`, other providers via configuration. Progressive capability levels let a deployment start simple and grow.

- **Work item model:** Provider-neutral; Beads default. File store available.
- **Worker grouping model:** User-declared pools in `city.toml`; elastic via shell `check` commands that return agent count/health.
- **Repository interaction:** Worktree via provider; provider-dependent otherwise (k8s containers, exec).
- **Assignment mechanism:** Routing layer distinct from pool management; pull-first.
- **Merge / conflict handling:** Delegated to provider + work tracker.
- **State model:** Declared vs observed state reconciliation (Kubernetes-like control loop).
- **Traceability:** Inherits from work provider.
- **Extension points:** Packs (agent role+prompt bundles), providers (runtime), work providers (tracker), formulas, orders.
- **Distinctive feature:** Declared-vs-observed reconciliation model imported from infrastructure-as-code into agent orchestration.
- **Observed limitations:** Pre-GA; public docs sparse; ecosystem of packs and providers still thin as of April 2026. I could not locate a public spec for `city.toml` from web search alone.

---

### Devin (Cognition)

**Category:** Agent execution product
**Status:** Active
**Latest release / commit:** Rolling updates through April 2026; v3 API promoted out of beta ([Devin 2026 release notes](https://docs.devin.ai/release-notes/2026))
**Primary sources:**
- [docs.devin.ai/release-notes/2026](https://docs.devin.ai/release-notes/2026)
- [cognition.ai/blog/introducing-devin](https://cognition.ai/blog/introducing-devin)
- [eesel AI pricing explainer](https://www.eesel.ai/blog/cognition-ai-pricing)

Devin is a closed-source cloud execution product. Each user "hires" one Devin; a *session* is the unit of work, billed in ACUs (Agent Compute Units, Cognition's proprietary resource meter, ~15 minutes of active work = 1 ACU, $2.25/ACU on the Core plan). Devin runs in a managed VM, can create child sessions with structured output schemas and playbooks, accepts tasks from Slack/API/web, submits PRs, and now (2026) supports end-to-end desktop testing via computer use. Knowledge notes persist across sessions.

- **Work item model:** Sessions with optional playbooks + structured output schemas. External integrations ingest Jira/Linear issues.
- **Worker grouping model:** Parent session + child sessions (structured handoff).
- **Repository interaction:** Managed VM with git checkout; submits PRs.
- **Assignment mechanism:** Human push (Slack/web/API) or external webhook.
- **Merge / conflict handling:** PR review by human; Devin Review chat agent can propose edits directly in comment threads.
- **State model:** Session lifecycle (planning, executing, waiting, done) — not exposed as first-class Agile states.
- **Traceability:** Session → PR → commits; session replay with full shell/file/browser/git/MCP activity searchable.
- **Extension points:** MCP support; Knowledge (playbooks, notes); v3 API with RBAC and session attribution.
- **Distinctive feature:** ACU meter as a first-class economic primitive. Session-replay debuggability.
- **Observed limitations:** Closed source. Reported benchmark numbers have been disputed since launch; most recent independent benchmarks still place Devin mid-pack on SWE-bench Verified. Pricing is opaque for heavy users.

---

### OpenHands (All Hands AI, fka OpenDevin)

**Category:** Agent execution product + framework SDK
**Status:** Active (V0 → V1 transition; V0 removal April 1, 2026)
**Latest release / commit:** V1 Software Agent SDK ([arXiv 2511.03690, Nov 2025](https://arxiv.org/html/2511.03690v1))
**Primary sources:**
- [github.com/All-Hands-AI/OpenHands](https://github.com/OpenHands/OpenHands)
- [arxiv.org/abs/2407.16741](https://arxiv.org/abs/2407.16741) (original OpenDevin paper)
- [arxiv.org/html/2511.03690v1](https://arxiv.org/html/2511.03690v1) (V1 SDK paper)
- [docs.all-hands.dev](https://docs.all-hands.dev/)

OpenHands is both an open-source execution product and a composable Python SDK (openhands-sdk). The agent ↔ environment interface is an *event stream* of actions and observations, which serves as both the agent's memory and the audit log. V1 is PostgreSQL-backed and SDK-based; V0 (file-based AgentController) is being retired. Deployable locally, in Docker, or in Kubernetes. AgentHub registry holds agent templates (CodeActAgent, BrowserAgent, micro-agents).

- **Work item model:** Conversation/session with event-log state; external issues ingested via integrations.
- **Worker grouping model:** Single agent per session, can delegate to sub-agents from AgentHub.
- **Repository interaction:** Sandboxed container per session (Docker/k8s).
- **Assignment mechanism:** Human push; GitHub App for issue-triggered runs.
- **Merge / conflict handling:** PR-based.
- **State model:** Event-stream + session status (running, stopped, error).
- **Traceability:** Full event log per session.
- **Extension points:** SDK (openhands-sdk), tool packages, workspace packages, AgentHub templates.
- **Distinctive feature:** Event-stream-as-memory abstraction; rigorous published research foundation.
- **Observed limitations:** V0→V1 migration is a live disruption; V0 removal date April 1, 2026 means integrations built on V0 internals are now breaking or broken. Dual-path routing adds latency.

---

### SWE-agent (Princeton NLP / Stanford)

**Category:** Research-first agent framework / research prototype promoted to working tool
**Status:** Active (research)
**Latest release / commit:** SWE-agent 1.0 + mini-SWE-agent (2025-2026); SWE-agent-LM-32b open weights ([github.com/SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent))
**Primary sources:**
- [github.com/SWE-agent/SWE-agent](https://github.com/SWE-agent/SWE-agent)
- [swebench.com](https://www.swebench.com/)
- [princeton-nlp/SWE-bench_Verified dataset](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified)

SWE-agent is the original canonical research implementation of "LM-as-software-engineer" built on an Agent-Computer Interface (ACI). It takes a GitHub issue + repo and attempts to produce a patch. Mini-SWE-Agent (100 lines of Python) achieves 65% on SWE-bench Verified, demonstrating that simplicity + a good harness beats baroque orchestration. Not a production orchestrator; the value is the benchmark leaderboard, the open-weights models, and the ACI primitives.

- **Work item model:** One issue = one task = one attempted patch.
- **Worker grouping model:** Single agent; no native multi-agent.
- **Repository interaction:** Ephemeral clone in sandboxed environment.
- **Assignment mechanism:** Programmatic (benchmark harness); CLI for single tasks.
- **Merge / conflict handling:** n/a — produces patches, doesn't integrate.
- **State model:** Benchmark states (resolved / not resolved / errored).
- **Traceability:** Trajectory logs per task.
- **Extension points:** Config YAMLs define prompts, tools, and harness; models are swappable.
- **Distinctive feature:** ACI (Agent-Computer Interface) — treat the agent's interaction with a shell/editor as a designed API rather than a language prompt.
- **Observed limitations:** Not a production system. No multi-agent, no tracker integration, no workflow state. Used as a *library of ideas* more than a runtime.

---

### LangGraph (LangChain)

**Category:** Agent orchestration framework
**Status:** Active (stable, production-used)
**Latest release / commit:** Regular 2026 releases ([langchain-ai/langgraph](https://github.com/langchain-ai/langgraph))
**Primary sources:**
- [langchain.com/langgraph](https://www.langchain.com/langgraph)
- [docs.langchain.com/oss/python/langgraph/overview](https://docs.langchain.com/oss/python/langgraph/overview)
- [blog.langchain.com/langgraph-multi-agent-workflows/](https://blog.langchain.com/langgraph-multi-agent-workflows/)

LangGraph is a low-level stateful graph runtime. Nodes are functions/agents; edges are transitions (static or conditional); a central StateGraph holds shared evolving state. Design intent: durable, long-running, stateful agents with checkpoint/resume. Used in production at Klarna, Uber, J.P. Morgan (per LangChain marketing).

- **Work item model:** None native; workflows consume external state.
- **Worker grouping model:** Directed graph of agents/functions.
- **Repository interaction:** Agnostic.
- **Assignment mechanism:** Graph transitions (router edges, supervisor nodes).
- **Merge / conflict handling:** n/a — out of scope.
- **State model:** User-defined StateGraph schema; checkpoints to PostgreSQL or custom stores.
- **Traceability:** LangSmith traces per run.
- **Extension points:** Custom nodes, custom edges, custom checkpointers, custom stores.
- **Distinctive feature:** Treats agent workflow as a compilable graph with first-class state checkpoint/resume.
- **Observed limitations:** Steeper learning curve than CrewAI/Agents SDK; expressive but demands explicit state design. No work-tracker opinions.

---

### CrewAI

**Category:** Agent orchestration framework
**Status:** Active
**Latest release / commit:** Regular 2026 releases, Flows GA for production ([github.com/crewAIInc/crewAI](https://github.com/crewaiinc/crewai))
**Primary sources:**
- [crewai.com](https://crewai.com/)
- [docs.crewai.com](https://docs.crewai.com/en/concepts/agents)
- [github.com/crewAIInc/crewAI/releases](https://github.com/crewAIInc/crewAI/releases)

CrewAI models work as *Agents* (role + goal + backstory), *Tasks* (description + expected_output), and *Crews* (agent teams with a collaboration process). Recent versions add *Flows* for structured, event-driven production orchestration including HITL resume (flow_finished after human-in-the-loop).

- **Work item model:** Task object (description, expected_output, agent assignment).
- **Worker grouping model:** Crew (sequential/hierarchical process); Flow (event-driven state machine).
- **Repository interaction:** Agnostic — tool-based.
- **Assignment mechanism:** Task → Agent binding or manager-agent delegation.
- **Merge / conflict handling:** n/a.
- **State model:** Flow states; Task status (in progress/complete).
- **Traceability:** Execution logs; telemetry via observability integrations.
- **Extension points:** Tools, custom agents, Flow events, memory providers.
- **Distinctive feature:** Role-and-backstory agent definitions (closest to "agent persona" in mainstream frameworks) + explicit task deliverable contracts (expected_output acts as a DoD-lite).
- **Observed limitations:** Role/backstory framing is prompt-engineering dressed up as architecture; little guardrail against verbosity. Limited structured output schema enforcement compared to LangGraph.

---

### OpenAI Agents SDK

**Category:** Agent orchestration framework
**Status:** Active (major April 2026 update)
**Latest release / commit:** April 16, 2026 — sandboxing + model-native harness ([techcrunch](https://techcrunch.com/2026/04/15/openai-updates-its-agents-sdk-to-help-enterprises-build-safer-more-capable-agents/))
**Primary sources:**
- [openai.github.io/openai-agents-python](https://openai.github.io/openai-agents-python/)
- [openai.com/index/the-next-evolution-of-the-agents-sdk/](https://openai.com/index/the-next-evolution-of-the-agents-sdk/)
- [github.com/openai/openai-agents-python](https://github.com/openai/openai-agents-python)

The SDK formalizes *agents as objects* with tools, handoffs, and guardrails. Handoffs are modeled *as tools the LLM calls* (e.g., `transfer_to_refund_agent`) — a Python-level refactor of "which prompt runs now" into "which function do I call." April 2026 update added native sandbox execution and a Codex-style harness that bundles approvals, tracing, resume bookkeeping, and handoffs.

- **Work item model:** Conversation + handoff chain.
- **Worker grouping model:** Agent tree via handoffs (not a graph — call-stack semantics).
- **Repository interaction:** Sandbox (new in April 2026).
- **Assignment mechanism:** LLM-chosen handoff.
- **Merge / conflict handling:** n/a.
- **State model:** Conversation history; resume bookkeeping; approvals queue.
- **Traceability:** Tracing built in; MCP server tool integration.
- **Extension points:** Function tools, MCP servers, guardrails, handoffs.
- **Distinctive feature:** Handoffs-as-tools — the cleanest "agent A invokes agent B" primitive in mainstream frameworks, because it reuses the existing tool-call mechanism.
- **Observed limitations:** Model-coupled (OpenAI-flavored even though model-swappable in theory). Conversation-history-based state is bulky for long-lived sessions.

---

### Anthropic Claude Agent SDK

**Category:** Agent orchestration framework
**Status:** Active
**Latest release / commit:** Python v0.1.63 on 2026-04-18 ([releasebot/anthropic/claude-code](https://releasebot.io/updates/anthropic/claude-code))
**Primary sources:**
- [github.com/anthropics/claude-agent-sdk-python/releases](https://github.com/anthropics/claude-agent-sdk-python/releases)
- [anthropic.com/news/claude-sonnet-4-5](https://www.anthropic.com/news/claude-sonnet-4-5)
- [platform.claude.com/docs/en/release-notes/overview](https://platform.claude.com/docs/en/release-notes/overview)

Formerly "Claude Code SDK" — renamed to Claude Agent SDK in 2026. Exposes the primitives Claude Code uses internally (tool permission system, context-usage accounting, MCP client, subagent spawning) as a library. Python and TypeScript. Claude Code itself added Agent Teams (experimental shared-task-list multi-agent coordination) and Focus view.

- **Work item model:** Session with todo-list / task-list (Agent Teams share one).
- **Worker grouping model:** Main agent + subagents; Agent Teams = peer agents with shared task list.
- **Repository interaction:** Direct edit in cwd with permission system + sandbox; worktree recommended for parallel agents.
- **Assignment mechanism:** Subagent pulls from shared list (Agent Teams), claim with agent id.
- **Merge / conflict handling:** Worktree-based isolation; git is the merge mechanism.
- **State model:** Session state; todo-list items (pending/in_progress/done).
- **Traceability:** Session transcripts; context usage telemetry per category.
- **Extension points:** MCP servers, hooks, skills, permission modes, sandbox configs, custom session ids.
- **Distinctive feature:** Agent Teams model where peer agents (same model, different contexts) coordinate via a shared task list — closer to Gemba's mental model than any other major SDK.
- **Observed limitations:** Agent Teams experimental and off by default as of April 2026. Heavy coupling to Claude models (MCP helps but the ergonomics are Anthropic-shaped).

---

### Google ADK (Agent Development Kit)

**Category:** Agent orchestration framework
**Status:** Active
**Latest release / commit:** Active through 2026; Python/Go/Java/TypeScript + ADK for Web UI ([google.github.io/adk-docs](https://google.github.io/adk-docs))
**Primary sources:**
- [google.github.io/adk-docs](https://google.github.io/adk-docs)
- [developers.googleblog.com — ADK introduction](https://developers.googleblog.com/en/agent-development-kit-easy-to-build-multi-agent-applications/)
- [github.com/google/adk-python](https://github.com/google/adk-python)

ADK is Google's code-first multi-agent framework. Supports hierarchical agents, treats context like source code (structured event view, automatic summarization, lazy artifact loading, token tracking). Recommended deployment target: Vertex AI Agent Engine. Integrates with A2A for cross-agent interop and with AG-UI for frontends.

- **Work item model:** Task objects; session state.
- **Worker grouping model:** Agent hierarchy; supports sequential, parallel, and LLM-routed composition.
- **Repository interaction:** Agnostic; tooling-dependent.
- **Assignment mechanism:** Parent-agent delegation or LLM-routed.
- **Merge / conflict handling:** n/a.
- **State model:** Session memory + artifact store.
- **Traceability:** Event log; Vertex observability.
- **Extension points:** Tools, sub-agents, A2A servers, AG-UI events.
- **Distinctive feature:** "Context as source code" — structured context management with lazy loading and token accounting built into the framework.
- **Observed limitations:** Best experience is Gemini + Vertex; cross-cloud ergonomics are rougher.

---

### Anthropic MCP (Model Context Protocol)

**Category:** Agent orchestration protocol
**Status:** Active; donated to Linux Foundation's Agentic AI Foundation (AAIF) in December 2025
**Latest release / commit:** Spec 2025-11-25 ([modelcontextprotocol.io/specification/2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25))
**Primary sources:**
- [modelcontextprotocol.io/specification/2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25)
- [github.com/modelcontextprotocol](https://github.com/modelcontextprotocol)
- [WorkOS — MCP Features Guide](https://workos.com/blog/mcp-features-guide)

MCP is JSON-RPC 2.0 over stdio or Streamable HTTP, inspired by LSP. Six primitives: **Tools**, **Resources**, **Prompts** (server-side); **Roots**, **Sampling**, **Elicitation** (client-side). Elicitation (finalized in spec revision 2025-06-18) lets a server pause and request structured input from the user mid-call. 97M monthly SDK downloads, 10k+ active servers as of Dec 2025 (Anthropic's numbers).

- **Work item model:** n/a — protocol, not a tracker.
- **Worker grouping model:** n/a.
- **Repository interaction:** Via Roots capability (client-declared paths server may access).
- **Assignment mechanism:** n/a.
- **Merge / conflict handling:** n/a.
- **State model:** Stateless per call + optional long-lived HTTP session.
- **Traceability:** Call-level logging at client/server discretion.
- **Extension points:** Custom tools, resources, prompts; elicitation forms; sampling delegation.
- **Distinctive feature:** Bidirectionality via sampling (server asks the client's model) and elicitation (server asks the user). No other mainstream agent protocol has both.
- **Observed limitations:** No native task/work-item primitive — MCP is about *capabilities*, not *work*. Must be paired with a work tracker.

---

### Google A2A (Agent2Agent)

**Category:** Agent orchestration protocol
**Status:** Active; v1.0 GA early 2026; Linux Foundation–owned
**Latest release / commit:** v1.0 early 2026 ([a2a-protocol.org/latest/specification](https://a2a-protocol.org/latest/specification/))
**Primary sources:**
- [github.com/a2aproject/A2A](https://github.com/a2aproject/A2A)
- [a2a-protocol.org/latest/specification](https://a2a-protocol.org/latest/specification/)
- [a2a-protocol.org/latest/topics/life-of-a-task/](https://a2a-protocol.org/latest/topics/life-of-a-task/)

A2A is JSON-RPC 2.0 over HTTP/SSE/gRPC. Designed for agents to talk to *opaque* agents (you don't share internals — you share a contract). Core objects: **Agent Card** (signed JSON manifest: identity, skills, endpoint, auth), **Task** (stateful unit of work with defined lifecycle), **Message** (a turn), **Part** (content chunk: text/file/data), **Artifact** (output composed of parts). v1.0 added Signed Agent Cards, gRPC, and AP2 (Agent Payments Protocol) as a formal extension. 150+ orgs adopting.

- **Work item model:** Task with lifecycle states (submitted → working → input-required → completed / failed / canceled / rejected).
- **Worker grouping model:** Agents as peers; no topology prescription.
- **Repository interaction:** n/a — protocol.
- **Assignment mechanism:** One agent issues task to another.
- **Merge / conflict handling:** n/a.
- **State model:** Task lifecycle is *specified* — rare for a protocol.
- **Traceability:** Task ID + artifact chain.
- **Extension points:** Protocol extensions (AP2 is one); custom parts.
- **Distinctive feature:** The *only* mainstream protocol that specifies a task lifecycle (with input-required re-entry) — meaning A2A already contains a generic work-item model.
- **Observed limitations:** "Task" is narrow (single request-response cycle with streaming); doesn't model epics, hierarchies, or backlog. Agent Cards are JSON — no semantic standard for skill names yet (150+ orgs means 150+ naming conventions).

---

### Tier 2 — standard cards

### AutoGen / Microsoft Agent Framework

**Category:** Agent orchestration framework
**Status:** AutoGen → maintenance mode; successor Microsoft Agent Framework v1.0 GA April 3, 2026; AG2 is a community fork
**Latest release / commit:** Agent Framework v1.0, April 3, 2026 ([Microsoft devblogs](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/))
**Primary sources:**
- [learn.microsoft.com/en-us/agent-framework/overview](https://learn.microsoft.com/en-us/agent-framework/overview/)
- [github.com/microsoft/autogen](https://github.com/microsoft/autogen)
- [github.com/microsoft/autogen/discussions/7066](https://github.com/microsoft/autogen/discussions/7066)

The Microsoft Agent Framework is the convergence of AutoGen (research patterns) and Semantic Kernel (enterprise runtime). Ships graph-based workflows + five patterns (sequential, concurrent, handoff, group chat, Magentic-One). Streaming, checkpointing, HITL approvals, pause/resume.

- **Work item model:** Workflow state per pattern; no tracker.
- **Worker grouping model:** Five patterns, user-selected.
- **Repository interaction:** Agnostic.
- **Assignment mechanism:** Pattern-dependent (manager routes in group chat; handoff tool calls in handoff).
- **Merge / conflict handling:** n/a.
- **State model:** Session state + workflow checkpoints.
- **Traceability:** Built-in telemetry middleware.
- **Extension points:** Middleware, custom agents, custom workflow nodes.
- **Distinctive feature:** Named orchestration patterns as library-level citizens (Magentic-One being the interesting one — an orchestrator/planner pair).
- **Observed limitations:** AutoGen legacy users are now navigating a deprecation path. AG2 fork may fragment community.

---

### Cursor Background / Cloud Agents

**Category:** Agent execution product (IDE-adjacent)
**Status:** Active (Cursor 3 released April 2026)
**Latest release / commit:** Cursor 3 ([cursor.com/blog/cursor-3](https://cursor.com/blog/cursor-3))
**Primary sources:**
- [cursor.com/blog/cursor-3](https://cursor.com/blog/cursor-3)
- [cursor.com/changelog](https://cursor.com/changelog)
- [infoq.com/news/2026/04/cursor-3-agent-first-interface/](https://www.infoq.com/news/2026/04/cursor-3-agent-first-interface/)

Cursor 3 ditches the traditional IDE layout for an "agent-first" interface. Cloud Agents (née Background Agents) run in remote VMs; up to 8 agents in parallel per prompt using git worktrees or remote machines. Sessions are movable: local ↔ cloud. Panes let you run multiple agents simultaneously in the same window.

- **Work item model:** Session/prompt; plans optionally produced by parallel planner agents.
- **Worker grouping model:** Parallel fleet (up to 8), each a sibling.
- **Repository interaction:** Local worktree or cloud VM.
- **Assignment mechanism:** Human issues prompt; fan-out to parallel agents.
- **Merge / conflict handling:** Worktrees; human picks winning plan/PR.
- **State model:** Session states (running, paused, completed).
- **Traceability:** Agent transcript per session; PR linkage via GitHub integration.
- **Extension points:** Rules, MCP servers, hooks.
- **Distinctive feature:** "Plan with parallel agents" — fan out N planners, pick the best, then execute. Cheap variance exploration.
- **Observed limitations:** Closed-source. Cloud/local session mobility relies on Cursor's own sync. Heavy worktree use reported as disk-hungry (Cursor forum reports ~10GB in a 20-minute session).

---

### Sourcegraph Amp

**Category:** Agent execution product (CLI + editor agent)
**Status:** Active; spun out from Sourcegraph as independent company (2025)
**Latest release / commit:** 2026 iterations ([ampcode.com](https://ampcode.com/))
**Primary sources:**
- [sourcegraph.com/amp](https://sourcegraph.com/amp)
- [ampcode.com](https://ampcode.com/)
- [HackerNoon — spin-out story](https://hackernoon.com/sourcegraph-spins-out-amp-to-chase-the-ai-coding-frontier)

Amp (formerly Cody) is a "frontier coding agent" positioned around always-use-best-model economics. Pay-as-you-go with no token markup for individuals. Runs in CLI, VS Code, Cursor (as MCP), Windsurf, JetBrains, Neovim. Claims profitability at spin-out.

- **Work item model:** Chat/session.
- **Worker grouping model:** Single agent per session.
- **Repository interaction:** Local; Sourcegraph code-graph context.
- **Assignment mechanism:** Human.
- **State model:** Session.
- **Traceability:** Transcripts.
- **Distinctive feature:** Code-graph-aware context retrieval (Sourcegraph heritage).
- **Observed limitations:** No first-class multi-agent or work-tracker integration.

---

### Factory

**Category:** Agent execution product (enterprise)
**Status:** Active; GA April 2026; Series C $150M at $1.5B valuation ([Factory GA announcement](https://www.factory.ai/news/ga))
**Latest release / commit:** GA April 2026
**Primary sources:**
- [factory.ai](https://factory.ai/)
- [factory.ai/news/ga](https://www.factory.ai/news/ga)
- [latent.space/p/factory](https://www.latent.space/p/factory)

Factory builds "Droids" — autonomous software-development agents aimed at enterprise. Droids cover the full SDLC: ticket → code → review → test → deploy → incident response. Customer logos include Nvidia, Adobe, MongoDB, Zapier.

- **Work item model:** Ticket / spec / prompt.
- **Worker grouping model:** Droid fleet; specialized droids per SDLC phase.
- **Repository interaction:** PR-based.
- **Distinctive feature:** SDLC-spanning agent roles (not just coding — triage, RCA, review).
- **Observed limitations:** Closed source; pricing opaque; no public API docs surfaced in web search.

---

### Sweep AI

**Category:** Coding agent (PR bot, now IDE)
**Status:** Maintenance / pivot
**Latest release / commit:** Main repo last updated 2025-09-18; shifted focus to JetBrains plugin
**Primary sources:** [github.com/sweepai/sweep](https://github.com/sweepai/sweep)

Originally a GitHub-issue-to-PR bot. Has pivoted to a JetBrains IDE plugin. Not a current front-runner; included for completeness because it was an early canonical example of "issue in → PR out."

---

### Goose (Block → Linux Foundation AAIF)

**Category:** Agent orchestration framework + coding agent
**Status:** Active; moved to AAIF under Linux Foundation (2025)
**Latest release / commit:** 2026 continuing ([github.com/block/goose](https://github.com/block/goose))
**Primary sources:**
- [github.com/block/goose](https://github.com/block/goose)
- [block.xyz — codename goose intro](https://block.xyz/inside/block-open-source-introduces-codename-goose)

Open, extensible, Apache-2.0, MCP-native. Supports 15+ LLM providers. 29k+ GitHub stars. Moved from `block/goose` to `aaif-goose/goose`.

- **Work item model:** Session + recipes.
- **Worker grouping model:** Single primary + tool extensions.
- **Repository interaction:** Local execute-everything.
- **Distinctive feature:** MCP-native from day one; LF-governed.
- **Observed limitations:** Primarily single-agent; multi-agent coordination is user-constructed.

---

### Aider

**Category:** Coding agent (CLI)
**Status:** Active
**Latest release / commit:** Continuous ([aider.chat](https://aider.chat/))
**Primary sources:** [aider.chat](https://aider.chat/), [aider.chat/blog](https://aider.chat/blog/)

Terminal-native pair programmer. Uses git commits as the interaction primitive (every AI change is a commit). Supports 100+ languages. Claims "Aider writes 70% of new code in each release." Caching, browser UI, images/URLs in chat.

- **Distinctive feature:** Git-commit-per-exchange as the state model. Treats git as the undo/redo layer.
- **Observed limitations:** Single-agent; no work-tracker integration beyond whatever you wire via git hooks.

---

### Cline

**Category:** Coding agent (VS Code)
**Status:** Active ([cline.bot](https://cline.bot/))
**Primary sources:** [github.com/cline/cline](https://github.com/cline/cline)

Plan/Act modes, MCP integration, terminal + browser + file tools. Model-agnostic. 15k+ stars. 5M+ developers claimed.

- **Distinctive feature:** Explicit Plan vs Act separation at the UX level.
- **Observed limitations:** Per several reviews, can be "too aggressive with changes" — trust/guardrail model is weaker than Roo.

---

### Roo Code (fka Roo Cline)

**Category:** Coding agent (VS Code)
**Status:** Active; v3.50.4 on 2026-02-21 ([github.com/RooCodeInc/Roo-Code](https://github.com/RooCodeInc/Roo-Code))
**Primary sources:** [roocode.com](https://roocode.com/), [docs.roocode.com](https://docs.roocode.com/)

Fork of Cline that emphasizes mode-based personas (Architect — plan only, Code — execute, Ask — read-only). Multi-mode "whole dev team" framing.

- **Distinctive feature:** Role-based modes with *capability restrictions* (Architect literally can't write code). First IDE agent to put real guardrails on agent-role behavior.
- **Observed limitations:** Still single-session at heart; modes are templates, not concurrent agents.

---

### Continue.dev

**Category:** Coding agent + CI checks
**Status:** Active ([continue.dev](https://www.continue.dev/))
**Primary sources:** [docs.continue.dev](https://docs.continue.dev/), [blog.continue.dev](https://blog.continue.dev/)

IDE assistant (VS Code, JetBrains) + CLI + background agents that plug into GitHub Actions, Sentry, Snyk, Jira, Confluence. Novel angle: "AI checks on every PR as GitHub status checks" — red/green enforceable in CI.

- **Distinctive feature:** Source-controlled AI checks that become CI status. Evidence linkage treated as a first-class product surface.
- **Observed limitations:** Checks are a proprietary concept; no spec for other tools to implement them.

---

### Tier 3 — one-liners

- **Codex CLI / Codex Cloud (OpenAI)** — OpenAI's CLI/cloud coding agent, now benefiting from Agents SDK sandbox/harness. [developers.openai.com](https://developers.openai.com/api/docs/guides/agents)
- **Windsurf (Cascade)** — IDE with Cascade agent; Codeium rebranded. Acquired path shifted through 2025. No canonical public API for multi-agent.
- **GitHub Copilot Workspace / Copilot Spaces** — GitHub's coding agent features; closed, tightly bound to GitHub Issues/PRs.
- **Tabnine Agent** — enterprise on-prem coding agent.
- **Magentic-One (Microsoft Research)** — research orchestrator pattern absorbed into Microsoft Agent Framework.
- **BabyAGI / AutoGPT** — historical prototypes, stalled.
- **Smyth OS / Sim Studio / Flowise** — no-code agent builders; not engineering-focused.
- **Qodo / CodiumAI** — test-generation agents.
- **Jules (Google)** — Google's autonomous coding agent; closed.
- **Lovable / v0 / Bolt** — product builders, web-app generators; lateral category.
- **Replit Agent** — Replit's browser-IDE agent; single-agent, strong sandbox.
- **hermes-agent (NousResearch)** — open-source CLI agent; has open issue requesting worktree isolation (#652), evidence of live problem.
- **AG-UI** — separate protocol for agent↔frontend ([docs.ag-ui.com](https://docs.ag-ui.com/)); adjacent to Gemba's problem space — Gemba *is* an AG-UI consumer candidate.
- **ACP (IBM BeeAI)** — HTTP-conventional agent-comms protocol launched May 2025 ([github.com/i-am-bee/acp](https://github.com/i-am-bee/acp)); overlaps A2A.
- **Zed Agent** — Zed editor's agent mode; single-agent.
- **Codeium Forge / Cascade** — enterprise agent bundle.

---

## 3. Work-tracker survey

### Tier 1

### Jira (Atlassian)

**Status:** Active (market dominant)
**Primary sources:**
- [support.atlassian.com — issue types](https://support.atlassian.com/jira-cloud-administration/docs/what-are-issue-types/)
- [community.atlassian.com — hierarchy guidance](https://community.atlassian.com/forums/Jira-questions/How-to-set-up-hierarchy-with-Epic-Story-Feature-Task-Sub-task-in/qaq-p/3091938)
- [salto.io — hierarchy explainer](https://www.salto.io/blog-posts/jira-issue-type-understanding)

- **Data model:** Issues ("work items" in new terminology) with issue types. Standard: Epic > Story/Task/Bug > Sub-task.
- **Hierarchy rules:** Numerical hierarchy levels — Epic = 1, Story/Task/Bug = 0, Sub-task = −1. Premium/Enterprise can add levels above Epic via Plans. As of Oct 2023, single unified "Parent" field replaces the older Epic Link + Parent Link fields.
- **Relationship types:** "Parent" (hierarchy), plus issue *links*: blocks, is blocked by, relates to, duplicates, is duplicated by, clones, is cloned by, causes, is caused by, plus fully custom link types. Link types are globally configured.
- **Custom fields:** Supported, typed (text, number, select, user, date, cascading, URL, etc.), can be required per screen/workflow.
- **State model:** Project-level *workflows* — finite state machines with transitions, conditions, validators, and post-functions. Different issue types can use different workflows.
- **Assignee model:** Single assignee + unlimited watchers/reporters. Bots are just users. Team-level assignment via plugins or Team field.
- **API surface:** REST v3 and GraphQL (new-ish, still uneven); webhooks; app framework (Connect/Forge).
- **Evidence linkage:** Smart Commits (commit message syntax), PR integrations with Bitbucket/GitHub/GitLab; development panel on issues; Automation for Jira.
- **Extension mechanism:** Atlassian Marketplace + Forge/Connect apps; Automation rules; custom fields; ScriptRunner.
- **Distinctive feature:** Workflow engine is the most configurable in the mainstream market — essentially a project-scoped BPMN.
- **Observed limitations:** Schema bloat at scale; workflow edit is a high-privilege operation; API rate limits; hierarchy depth costs money.

---

### Linear

**Status:** Active
**Primary sources:**
- [linear.app/developers](https://linear.app/developers/create-issues-using-linear-new)
- [linear.app/docs/api-and-webhooks](https://linear.app/docs/api-and-webhooks)
- [linear.app/docs/creating-issues](https://linear.app/docs/creating-issues)

- **Data model:** Issues, Projects, Cycles, Initiatives, Documents. Issues have optional Parent (single).
- **Hierarchy rules:** One parent issue per issue; arbitrary depth but flat culture discouraged. Projects group issues; Initiatives group projects.
- **Relationship types:** Blocks / blocked-by, Relates to, Duplicates, Parent/Child. 2026 filter improvements added AND/OR logic for dependency management.
- **Custom fields:** Recently added (Business/Enterprise); previously only labels + priority + estimate.
- **State model:** Workflow states per team with 5 *state types* (Backlog, Unstarted, Started, Completed, Canceled). State types drive UX (what appears in "In Progress").
- **Assignee model:** Single assignee.
- **API surface:** GraphQL-only (unusual — no REST); webhooks cover Issues, Comments, Projects, Cycles, Labels, Documents, etc.
- **Evidence linkage:** GitHub / GitLab / Bitbucket PR auto-linking via branch name or PR body; commits and PRs appear on issue.
- **Extension mechanism:** OAuth apps, webhooks, integrations (Slack, Figma, etc.). No marketplace in Jira's sense.
- **Distinctive feature:** GraphQL API is comprehensive and queryable — Linear is effectively scriptable as a database.
- **Observed limitations:** Single-assignee model is rigid. Custom fields gated behind higher tiers. No workflow engine — state transitions are free (any → any).

---

### GitHub Projects / GitHub Issues

**Status:** Active; Sub-issues GA 2025, Hierarchy View in projects public preview 2026-01-15
**Primary sources:**
- [docs.github.com/rest/projects](https://docs.github.com/en/rest/projects/projects)
- [github.blog — sub-issues](https://github.blog/engineering/architecture-optimization/introducing-sub-issues-enhancing-issue-management-on-github/)
- [github.blog changelog 2026-01-15](https://github.blog/changelog/2026-01-15-hierarchy-view-now-available-in-github-projects/)

- **Data model:** Issues + Projects v2 (board/table/roadmap/hierarchy views). Issue Types (new-ish: Bug, Feature, Task, custom) per org.
- **Hierarchy rules:** Sub-issues: up to 50 per parent, up to 8 levels deep. Cross-repo parent/child supported.
- **Relationship types:** Parent/child (via sub-issues), closes #N (PR→issue), duplicates (via comment/label convention — not a first-class edge). No native "blocks" edge as of April 2026.
- **Custom fields:** Projects v2 supports typed fields (text, number, date, single-select, iteration) scoped to the project, not the issue.
- **State model:** Open/closed at issue level; Projects v2 status field is user-definable (e.g., Backlog/In Progress/Done) per project.
- **Assignee model:** Up to 10 assignees (historically; single was the old default). Bots (e.g., GitHub App bots) are users.
- **API surface:** REST (v2026-03-10 release for Projects REST), GraphQL (richer), webhooks, GitHub Apps with fine-grained permissions.
- **Evidence linkage:** Native (GitHub *is* the code host). Commit/PR/issue cross-linking is table stakes.
- **Extension mechanism:** GitHub Apps, Actions, marketplace.
- **Distinctive feature:** Tight coupling to the code hosting platform — evidence linkage is the default, not an integration.
- **Observed limitations:** No native "blocks" relationship edge as of April 2026 (users work around with labels or sub-issue conventions). Projects v2 API has historical gaps (e.g., ProjectV2View mutations).

---

### Azure DevOps Boards

**Status:** Active
**Primary sources:**
- [learn.microsoft.com — work items overview](https://learn.microsoft.com/en-us/azure/devops/boards/work-items/about-work-items?view=azure-devops)
- [learn.microsoft.com — link types reference](https://learn.microsoft.com/en-us/azure/devops/boards/queries/link-type-reference?view=azure-devops)
- [learn.microsoft.com — features and epics](https://learn.microsoft.com/en-us/azure/devops/boards/backlogs/define-features-epics?view=azure-devops)

- **Data model:** Work item types vary by process template: Basic (Epic > Issue > Task), Agile (Epic > Feature > User Story > Task/Bug), Scrum (Epic > Feature > Product Backlog Item > Task/Bug), CMMI (Epic > Feature > Requirement > Task). Single project can mix.
- **Hierarchy rules:** Parent-child is a tree (one parent, many children; circular refs prevented).
- **Relationship types:** Parent/Child, Related, Predecessor/Successor (dependency), Duplicate/Duplicate of, Tests/Tested by, Affects/Affected by, Hyperlink, Attached file, Plus custom link types. Richer relationship taxonomy than most.
- **Custom fields:** Inherited process model supports typed custom fields.
- **State model:** Per work item type; configurable state transitions. States grouped into workflow state *categories* (Proposed, In Progress, Resolved, Completed, Removed) for cross-type reporting.
- **Assignee model:** Single "Assigned To" user per work item.
- **API surface:** REST, process inheritance API, webhooks/service hooks.
- **Evidence linkage:** Native (part of Azure DevOps suite with Repos/Pipelines).
- **Extension mechanism:** Extensions marketplace, inherited processes.
- **Distinctive feature:** The richest *named* relationship taxonomy of any mainstream tracker (predecessor/successor + tests/tested-by are rarely first-class elsewhere).
- **Observed limitations:** Heavyweight configuration; declining Microsoft investment perception as GitHub becomes the strategic product.

---

### Tier 2

### Shortcut

**Status:** Active
**Primary sources:**
- [developer.shortcut.com](https://developer.shortcut.com/api/rest/v3)
- [shortcut.com/release-notes](https://www.shortcut.com/release-notes)
- [shortcut.com/blog — story relationships](https://www.shortcut.com/blog/visualize-dependencies-between-related-stories)

- **Data model:** Stories, Epics, Iterations, Objectives. Sub-tasks coming (2026 roadmap).
- **Relationship types:** Blocks / blocked by; relates to; duplicates. Auto-generated Mermaid graph on Epic/Iteration pages.
- **State model:** 5 default states across 4 state *types* (Backlog/Unstarted/Started/Done). Custom epic workflows (Business/Enterprise).
- **Custom fields:** Advanced Custom Fields on Business/Enterprise.
- **API:** REST v3, actively updated (last 2026-04-14).
- **Distinctive feature:** First-class dependency visualization (Mermaid charts in UI).
- **Observed limitations:** Sub-tasks still rolling out; historically flatter than Jira.

### Asana

**Status:** Active
**Primary sources:** [developers.asana.com](https://developers.asana.com/reference/tasks), [asana.com/guide/help/tasks/dependencies](https://asana.com/guide/help/tasks/dependencies)

- **Data model:** Tasks (up to 5 subtask levels), Projects, Portfolios, Goals.
- **Relationships:** Dependencies (depends on / dependent of) — max 30 deps+dependents combined per task.
- **Custom fields:** Yes, typed.
- **State:** Section-based + custom status; no formal workflow engine.
- **API:** REST + webhooks.
- **Distinctive feature:** Portfolio-level rollup strong for ops / non-engineering.
- **Observed limitations:** Dependency cap (30) is unusual. Engineering-workflow fit is weaker.

### Basecamp

**Status:** Active
**Primary sources:** [github.com/basecamp/bc3-api](https://github.com/basecamp/bc3-api)

- **Data model:** Projects ("buckets") > To-do lists > To-dos. Subtasks only via checklists inside to-dos (no independent assignee/status).
- **Relationships:** None first-class.
- **API:** REST / JSON + OAuth 2.0.
- **Distinctive feature:** Intentional simplicity; optimizes for non-engineering teams.
- **Observed limitations:** Poor fit as an agent tracker — no relationships, no deps, no dedicated subtask state.

### Beads

**Status:** Active (research/early adoption); current Gemba backend
**Primary sources:**
- [github.com/steveyegge/beads](https://github.com/steveyegge/beads)
- [github.com/steveyegge/beads/blob/main/docs/ARCHITECTURE.md](https://github.com/steveyegge/beads/blob/main/docs/ARCHITECTURE.md)
- [steveyegge.github.io/beads](https://steveyegge.github.io/beads/)

- **Data model:** Issues (beads) with types (task, bug, message, etc.), priority levels (P0-P3), textual description.
- **Hierarchy rules:** Parent-child via dep graph.
- **Relationship types:** Per prompt and README: `blocks`, `related`, `parent-child`, `discovered-from`, `waits-for`, `replies-to`, `conditional-blocks` — seven edge types. (Web-search recall of the README also listed `relates_to`, `duplicates`, `supersedes`, `replies_to` at edge level — some naming drift between authoritative prompt list and public README.)
- **Custom fields:** Limited; priority, type, assignee standard.
- **State model:** open → in_progress → closed; blocked is *derived* from dep graph (a bead with open blockers is "not ready").
- **Assignee model:** Single "claim" operation per bead; optional.
- **API surface:** CLI (`bd`) + Dolt SQL directly; JSON output mode.
- **Evidence linkage:** Agent work history tables in Dolt link beads ↔ commits ↔ sessions.
- **Extension mechanism:** `bd remember` for persistent knowledge; Dolt remotes for sync.
- **Distinctive feature:** Dolt-backed — cell-level merge, native branching, time-travel queries on your *issues*. Nothing else in the tracker landscape offers this.
- **Observed limitations:** Labeled "fragile" in Gas Town operational docs; orphan test-database pollution is a known recurring problem; single-writer local mode vs server mode is a sharp operational cliff. API is CLI-first, not HTTP/REST — integrations build their own bridges.

### Plane.so

**Status:** Active (open source Jira alternative)
**Primary sources:** [github.com/makeplane/plane](https://github.com/makeplane/plane), [developers.plane.so](https://developers.plane.so/api-reference/introduction)

- **Data model:** Workspaces > Projects > Work items (custom states, labels, priorities, estimates).
- **Relationships:** Blocks/blocked-by; relates to; duplicates; parent/child (recent).
- **API:** REST + OAuth 2.0 + HMAC webhooks + Node/Python SDKs.
- **Distinctive feature:** Self-hostable Linear/Jira alternative with first-class REST + webhooks.
- **Observed limitations:** Smaller ecosystem; issue-type-as-configuration less mature than Jira.

### Height

**Status:** SHUT DOWN — ceased operations September 24, 2025 ([skywork analysis](https://skywork.ai/skypage/en/Height-App-The-Rise-and-Sunset-of-an-AI-Project-Management-Pioneer/1975012339164966912))

- **Data model:** Tasks with cascading subtasks and custom attributes.
- **Distinctive feature (historical):** Autonomous PM claims — bug triage, backlog pruning, spec updates automated; spiritually the closest prior-art to Gemba's vision.
- **Note:** Included because the design patterns (and failure) are informative for Gemba.

---

## 4. Terminology crosswalk

Where a cell says `—`, no native term exists and users improvise (noted in footer).

| Concept | Gemba (proposed generic) | Beads | Jira | Linear | GitHub Projects | Azure DevOps | Shortcut | Gas Town | LangGraph | CrewAI | OpenHands |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Work item | Work Item | Issue (bead) | Issue / Work item | Issue | Issue | Work Item | Story | Bead | (none) | Task | Task / Conversation |
| Epic | Epic | — [^1] | Epic | Project / Initiative | Issue w/ Issue Type "Epic" | Epic | Epic | — | — | — | — |
| Story | Story | Issue (task type) | Story | Issue | Issue | User Story / Requirement / PBI | Story | Bead | — | Task | Task |
| Sub-task | Sub-task | Child bead via parent-child edge | Sub-task | Child issue | Sub-issue | Task (under Story) | Sub-task (rolling out) | Child bead | — | Task | Sub-task |
| Bug | Bug | Issue w/ type=bug | Bug | Issue + label | Issue Type=Bug | Bug | Story w/ type=bug | Bead w/ type=bug | — | — | — |
| Relationship edge | Edge | One of 7 typed edges | Issue link (blocks/relates/dup/clones/causes + custom) | blocks/relates/dup/parent | parent/child; closes (PR→issue) | Parent/Child, Related, Pred/Succ, Tests/Tested, Affects, Duplicate | blocks/relates/dup | Edges in Beads | Graph edge | Flow event / delegation | Event-stream link |
| Workflow state | State | open/in_progress/closed (+derived blocked) | Workflow state (FSM) | State (typed Backlog/Unstarted/Started/Completed/Canceled) | Project v2 Status field | State + State Category | Workflow State | Beads state | Graph node state | Task status | Session status + event-log |
| Assignee | Assignee | Claim (single) | Assignee (single) | Assignee (single) | Assignees (up to 10) | Assigned To (single) | Owner (single) | Agent identity + rig | (node function) | Agent | Agent template |
| Workspace / rig | Workspace | — | Project | Team / Workspace | Repository + Project | Project | Workspace | Rig (worktree + tmux session) | — | — | Sandbox / Conversation runtime |
| Agent | Agent | — (external; agent claims beads) | User / Bot user | User / Bot | User / App | User | User | Agent identity (persistent) + Agent session (ephemeral) | Node | Agent (role+goal+backstory) | Agent template |
| Agent group | Agent Group | — (convoys in Gas Town layer) | Team / Group | Team | Team | Team | Team | Convoy / Pool | Subgraph | Crew | (ad-hoc) |
| Evidence artifact | Evidence | Work history rows; linked commit SHAs; `bd remember` notes | Dev panel (commits, PRs, builds, deployments) | PR auto-link | Linked PRs, timeline | Linked commits/PRs/builds/tests | Linked PRs | Session transcript + Dolt history | Checkpoint / trace | Task output | Event log |
| DoD check | DoD Check | — (manual on close) | Workflow transition validator / DoD checklist | — | CI status checks; Required reviews | Build/test linking | — | — (ad-hoc) | Conditional edge guard | expected_output (free-text contract) | — |
| Sprint / iteration / cycle | Sprint (**redefined: bounded by token budget, not calendar**) [^2] | — | Sprint (calendar-bounded) | Cycle (calendar-bounded) | — (Project v2 has Iteration field, calendar-bounded) | Iteration (calendar-bounded) | Iteration (calendar-bounded, rolling out) | — | — | — | — |

[^1]: Beads has no native "epic" type; teams use parent-child beads as de facto epics. Multiple cells marked `—` for Epic reflect that *most work trackers treat epics as a type-tag on an issue, not a distinct entity*.

[^2]: Gemba retains the familiar Agile term "Sprint" but redefines its bounding constraint: a Sprint is bounded by a **token budget**, not a calendar duration (DD-14 in the domain doc). Calendar duration is optional planning metadata. The entity is not native to any surveyed work tracker or orchestrator — Jira/Linear/Azure/Shortcut all tie sprint/cycle/iteration to calendar time; agentic frameworks (Gas Town, LangGraph, CrewAI, OpenHands) have no sprint concept at all. This is a Gemba novelty justified by the observed D9 gap (no cross-system cost/budget accounting primitive) combined with the ceremony-gap surfaced in the Phase 2 self-critique.

**Notable gaps surfaced by the crosswalk:**
- Only two of these systems (Jira, CrewAI) have anything resembling a native Definition-of-Done primitive.
- "Agent" has *no* native concept in Jira, Linear, GitHub Projects, Azure, or Shortcut — they all collapse agents into "user or bot user."
- "Agent group" exists in Gas Town (convoys) and CrewAI (crews) but is essentially unrepresented in trackers.
- "Rig / workspace" has no first-class term in any tracker — it's a runtime concern.
- "Sprint as token-budget" is novel — every surveyed tracker's sprint/cycle/iteration is calendar-bounded; no agentic framework has the concept at all. Gemba fills both gaps by reusing the term and redefining the axis.

---

## 5. Convergent vs divergent patterns

This section is the most important research output. Each item cites at least one piece of evidence from the surveyed systems.

### Convergent patterns (≥70% agreement)

**C1. Issues have an identity (ID), a type, a state, and a single primary assignee.** `[CORE]`
Every tracker surveyed (Jira, Linear, GitHub, Azure, Shortcut, Asana, Basecamp, Plane, Beads) implements this skeleton. A Gemba core contract that doesn't start here is picking a fight with reality.

**C2. Parent-child is the only near-universal relationship edge.** `[CORE]`
Jira, Linear, GitHub (sub-issues), Azure, Shortcut, Asana, Plane, Beads all have parent-child. Everything else (blocks, related, duplicates) is present in most but not all — and GitHub still lacks native "blocks" as of April 2026. The abstraction must model parent-child first-class.

**C3. "Blocks / blocked by" is the near-universal *second* edge.** `[CORE-with-extension]`
Present in Jira, Linear, Azure, Shortcut, Plane, Beads, Asana (as "dependency"). Missing only in GitHub (worked around) and Basecamp (no relationships at all). The extension: naming drift (Asana says "dependency," Azure says "predecessor/successor"). Normalize to one core name; adaptor translates.

**C4. Workflow states are finite and grouped into state *categories*.** `[CORE-with-extension]`
Linear (5 types), Azure (5 categories), Jira (categories on workflow statuses), Beads (derived). The specific states vary but every system that surfaces "is this thing started?" does it via a category. Gemba should model a fixed set of state *categories* with free-form state *names*.

**C5. Evidence is linked to work items out-of-band, not inline.** `[CORE-with-extension]`
GitHub is the only tracker where evidence (commits, PRs) is *natively* part of the work item. Jira/Linear/Azure/Shortcut/Plane all do it via integrations — branch names, smart commits, PR body references. Beads does it via agent work history tables in Dolt. Core contract: evidence is a *link collection* with typed refs. Extension: the link types.

**C6. Multi-agent coordination happens via a shared state/task list rather than point-to-point messaging.** `[CORE-with-extension]`
Claude Code Agent Teams (shared task list), LangGraph (StateGraph), Gas Town (Beads), CrewAI (Crew state), Cursor 3 (parallel with shared plan). The protocols (A2A, ACP) give point-to-point, but products converge on shared state because it's simpler to reason about. Core: shared, queryable work-item store. Extension: the coordination pattern on top.

**C7. Agents isolate their work via per-agent working directories.** `[CORE-with-extension]`
Gas Town (rigs = worktrees), Cursor (worktrees / cloud VMs), OpenHands (sandboxed containers), Claude Code (worktrees recommended + permission system), Devin (managed VM), Factory (managed env). Every serious product does this. The extension is *what* the isolated unit is (worktree vs container vs VM).

**C8. MCP has won as the capability protocol.** `[CORE]`
Claude Agent SDK, OpenAI Agents SDK, Cursor, Cline, Roo, Continue, Goose, Windsurf, Microsoft Agent Framework, Google ADK, OpenHands — all are MCP clients. 97M monthly SDK downloads (Anthropic Dec 2025). For Gemba's capabilities-to-agent interface, MCP is a safe default.

**C9. JSON-RPC 2.0 is the default wire encoding for agent protocols.** `[CORE]`
MCP, A2A, ACP all pick this. LSP heritage. Safe default.

**C10. An "agent" has persistent identity + ephemeral sessions.** `[CORE]`
Gas Town (identity vs session), Devin (knowledge persists across sessions), Claude Code (subagents ephemeral, skills persistent), OpenHands (AgentHub templates vs runs), CrewAI (role persistent, task-bound execution). The split is near-universal.

### Divergent patterns (fundamental disagreement)

**D1. Relationship edge taxonomy differs sharply.** `[ADAPTOR]`
Beads has 7 edges (`blocks, related, parent-child, discovered-from, waits-for, replies-to, conditional-blocks`); Azure DevOps has ~10 with `predecessor/successor`, `tests/tested-by`, `affects/affected-by`; Jira has ~6 baseline + unlimited custom; Linear has 4; GitHub has ~2; Asana collapses to "dependency." There's no hope of a canonical superset that everyone respects. Default core: {parent-child, blocks, relates}. Everything else goes to adaptors.

**D2. Issue hierarchy depth varies from 1 level (Basecamp checklists) to 8+ levels (GitHub sub-issues, Jira Premium).** `[ADAPTOR]`
Pick a minimum (2 levels: parent + child) and let adaptors collapse/expand.

**D3. Workflow engines range from *none* (Linear — free transitions) to *fully-configurable FSM with guards* (Jira workflows, Azure DevOps).** `[ADAPTOR]`
Cannot be reconciled. Gemba should model *state* (the label) and *state category*; transition rules are adaptor territory.

**D4. "Agent" has no native representation in most work trackers.** `[OPEN]`
Jira/Linear/GitHub/Azure/Shortcut treat agents as bot-users. Gas Town treats agents as first-class identities. Gemba's semantics (agent identity with a role) don't fit into bot-user. This is the biggest impedance mismatch in the domain. Needs explicit design decision — can't be punted to adaptors because the UI *is* agent-shaped.

**D5. Worktree vs container vs cloud VM as the isolation primitive.** `[PROTOCOL]`
Gas Town = worktrees; OpenHands = Docker; Devin = cloud VM; Cursor = both. Needs a capability negotiation ("does this execution product support worktrees?") rather than a hard core choice.

**D6. Multi-agent topology: hierarchy (Gas Town, ADK), graph (LangGraph), handoff chain (OpenAI Agents SDK), shared-list peers (Claude Code Agent Teams, CrewAI sequential), event-driven flows (CrewAI Flows).** `[ADAPTOR]`
Gemba is opinionated at the UI level (Kanban) — topology is downstream of the UI choice. The abstraction should expose "list of agents in a pool + their current claim" and let the orchestrator handle how they coordinate internally.

**D7. Whether the work tracker is the source of truth or a cache.** `[OPEN]`
Beads/Jira/Linear/etc. claim source-of-truth. OpenAI Agents SDK's session + Devin's session + LangGraph's StateGraph all also claim source-of-truth *for the agent run*. When they disagree, who wins? No consensus — some products (Factory, Continue) bidirectionally sync; others (Gas Town) treat Beads as primary and the agent state as derived. Needs explicit human decision for Gemba.

**D8. Evidence / DoD verification is unstandardized.** `[OPEN]`
Continue.dev invents "AI checks as PR status checks" (proprietary). CrewAI's `expected_output` is a prose contract. Jira has transition validators. Gas Town has no native DoD. There is no convergent model. If Gemba wants cross-product DoD, it has to *create* the standard — nobody else has.

**D9. Cost / budget accounting.** `[OPEN]`
Devin has ACUs as a first-class economic unit. OpenAI Agents SDK has token tracing. Claude Agent SDK has context usage categories. LangGraph/CrewAI have per-call telemetry. Jira/Linear have time-tracking for *humans*. Nothing is comparable across systems. If Gemba shows "how much did this cost?" it must build its own meter and adapt each backend. Research gap: there's no proposed standard.

**D10. Tracker ↔ agent identity linkage.** `[OPEN]`
In Jira/Linear/GitHub, a bot user is an opaque blob. In Beads, an agent is a string. In Gas Town, an agent has a role, a rig, a session, and an identity. Mapping a Gas Town "mike" agent to a Jira assignee loses ~4 dimensions of information. There is no industry pattern for round-tripping this.

**D11. Human-escalation seams.** `[PROTOCOL]`
MCP has elicitation (spec revision 2025-06-18, still marked draft). A2A has `input-required` as a task state. Microsoft Agent Framework has HITL approvals. Devin pauses in its VM. Claude Code has permission prompts. No convergent UX. For Gemba's use case (watching many agents), elicitation should be surfaced as a first-class UI concept with a protocol negotiation underneath — `input-required` (A2A) and `elicitation` (MCP) can be unified behind a common Gemba surface.

**D12. Async / long-running: streaming vs push-notify vs polling.** `[PROTOCOL]`
A2A supports all three (sync, SSE, async push). MCP added Streamable HTTP in March 2025. Gas Town is polling-on-tmux. LangGraph is checkpoint+resume. For a Kanban UI, SSE or push is needed; protocol negotiation is the cleanest answer.

### Summary of convergent/divergent patterns for design phase

| Pattern | Tag | Design phase action |
|---|---|---|
| C1 Issue = id+type+state+assignee | CORE | Bake in |
| C2 Parent-child | CORE | Bake in |
| C3 Blocks | CORE-with-extension | Bake in + allow aliases |
| C4 State categories | CORE-with-extension | Bake in 5 categories (Backlog/Unstarted/Started/Completed/Canceled) |
| C5 Evidence is typed-link collection | CORE-with-extension | Bake in + adaptor maps types |
| C6 Shared state over P2P | CORE-with-extension | Bake in; topology in adaptor |
| C7 Per-agent isolation | CORE-with-extension | Bake in; primitive negotiated |
| C8 MCP as capability protocol | CORE | Assume available |
| C9 JSON-RPC 2.0 wire | CORE | Assume wire |
| C10 Identity vs session | CORE | Bake in |
| D1 Edge taxonomy | ADAPTOR | {parent-child, blocks, relates} core; rest adapt |
| D2 Hierarchy depth | ADAPTOR | 2+ levels minimum |
| D3 Workflow rules | ADAPTOR | State-only in core |
| D4 "Agent" concept missing in trackers | OPEN | Human design call |
| D5 Isolation primitive | PROTOCOL | Capability negotiation |
| D6 Multi-agent topology | ADAPTOR | Pool + claim abstraction |
| D7 Source of truth | OPEN | Human design call |
| D8 DoD | OPEN | Gemba may need to *create* a standard |
| D9 Cost accounting | OPEN | Build own meter; adapt per backend |
| D10 Agent ↔ tracker identity | OPEN | Human design call |
| D11 Human escalation | PROTOCOL | Negotiate; unify MCP elicitation + A2A input-required |
| D12 Async transport | PROTOCOL | Negotiate (SSE/push/poll) |

---

## 6. What's missing / what's emerging

### Gaps in the landscape

- **No standard for "agent" as a first-class work-tracker citizen.** Every tracker collapses agents to bot-users. Nothing models role, rig, parent-agent, or session separately. (Gas Town invented this but it hasn't crossed over.)
- **No cross-system DoD primitive.** Jira transition validators, Continue's AI checks, CrewAI's `expected_output`, Linear's acceptance criteria field (ad-hoc custom field) — all disjoint. A Gemba proposal here could be actually net-new in the industry.
- **No cross-system cost/budget accounting.** ACUs are proprietary; tokens are model-specific; PR-level cost rollup doesn't exist in any tracker.
- **Cross-repo coordination is barely solved.** Worktrees are single-repo. Even sophisticated products (Devin, Factory) struggle with multi-repo changes. A2A's opaque-agent model could in principle unlock this, but nobody has productized it at tracker scope.
- **Agent-group membership model is immature.** CrewAI's crew is static. Gas Town's convoy is static. Claude Code Agent Teams membership is dynamic but not persistable. Nothing lets you say "this epic's pool is these 4 agent archetypes, scale elastically."
- **Evidence-backed DoD verification is bespoke everywhere.** Continue's AI checks come closest to productizing it; the rest is custom scripts.
- **Human-escalation seams are inconsistent.** MCP elicitation is draft; A2A has input-required; most IDE agents use ad-hoc permission prompts. Gemba's multi-agent UI will force a unified model onto this space.
- **Work-item-level cost attribution.** "How much did bead gt-abc12 cost to ship?" is answerable in zero systems.

### Emerging work (launched or materially updated in the last ~6 months)

- **MCP Streamable HTTP + Elicitation + MCP 2025-11-25 spec** ([modelcontextprotocol.io](https://modelcontextprotocol.io/specification/2025-11-25)).
- **A2A v1.0 + Signed Agent Cards + AP2 extension** (early 2026, [a2a-protocol.org](https://a2a-protocol.org/)).
- **OpenAI Agents SDK sandboxing + harness** (April 16, 2026, [openai.com](https://openai.com/index/the-next-evolution-of-the-agents-sdk/)).
- **Microsoft Agent Framework v1.0** (April 3, 2026, [devblogs.microsoft.com](https://devblogs.microsoft.com/agent-framework/microsoft-agent-framework-version-1-0/)).
- **Cursor 3 agent-first UI + parallel planner fan-out** (April 2026, [cursor.com](https://cursor.com/blog/cursor-3)).
- **Claude Code Agent Teams** (shared-task-list multi-agent; experimental) ([code.claude.com/docs/agent-teams](https://code.claude.com/docs/en/agent-teams)).
- **Factory GA + Series C** (April 2026) — enterprise Droids playbook.
- **GitHub Projects Hierarchy View** (public preview 2026-01-15).
- **OpenHands V1 SDK + V0 removal** (April 1, 2026 cutover).
- **AG-UI protocol** (agent↔frontend, [docs.ag-ui.com](https://docs.ag-ui.com/)) — directly adjacent to Gemba's problem.
- **Gas City alpha** — declarative Gas Town successor.
- **Agentic AI Foundation (AAIF)** at Linux Foundation — MCP, ACP, Goose governance moved here.
- **Gemba's "Sprint as token-budget" (DD-14, Phase 2 design)** — reuses the Agile term but swaps the bounding axis from calendar to tokens. No surveyed system has this primitive; closest precedents are Devin's ACU accounting (no sprint container) and Jira Sprint (no token awareness). Fills the dual gap between "work trackers have sprints but no cost axis" and "agentic frameworks have tokens but no sprint container."
- **Gemba transport plurality (DD-15)** — adaptors declare one of `api | jsonl | mcp`. MCP is recommended but not required, loosening the otherwise-observed industry gravity toward MCP-only wire formats for adaptor contracts.

### Known-unknowns (design phase must address)

1. **How does Gemba surface an agent "identity with history" into a tracker that only has "assignee = user id"?** (D4/D10)
2. **When tracker state and orchestrator state diverge, who is source of truth?** (D7) Does Gemba take a position or defer per-deployment?
3. **Is Gemba's DoD a new standard or a pass-through to tracker-native mechanisms?** (D8) If new, what's the minimum viable schema?
4. **Should Gemba meter cost itself, or require backends to expose cost?** (D9) ACUs, tokens, and wall-clock are not convertible.
5. **What's the minimum viable isolation contract?** (D5) "Has a working directory scoped to this work item" may be the only universally-honorable promise.
6. **How are elicitation/input-required events surfaced in a Kanban UI?** (D11) Do they become cards? Badges? A separate inbox?
7. **What's the mapping between Gemba's "agent group" and each backend's "team / crew / graph / convoy / pool"?** (D6)
8. **Does Gemba require MCP support from execution products, or optional?** (C8 — probably required in practice, but the contract should say.)
9. **Is Beads' 7-edge taxonomy the Gemba canonical, or does Gemba normalize to 3 and adapt?** (D1) The Beads author ships Gemba, so the political/technical answer may not align.
10. **Multi-repo work items: punt to v2, or admit v1 is single-repo-only?** (Gap.)
11. **What does Gemba do when an agent finishes but the work item has no DoD to check against?** Silent pass? Forbidden transition? Human-prompt card?

---

## 7. Agentic data plane — category map

This section maps reference systems to the eight canonical requirements (R1–R8) that define the **agentic data plane** category. Full taxonomy + per-requirement evidence is in `domain.md` §1.0 and `dataplane-requirements.md`.

**Scope:** software-engineering agents tied to Git repositories. Not general business workflow.

**Reference members:** Beads (reference WorkPlane), AgentHub, Ralph, Symphony, Raindrop (Liquid Metal), Gastown (orchestrator on Beads), Metaswarm (multi-agent platform on Beads). Gas Town is listed in §2 as an execution product; its role as an **orchestrator** over Beads places it in the data-plane-*consumer* column, not the data-plane column itself — same for Metaswarm.

Broader "agentic platforms" (Kore.ai, Glean, enterprise control planes) match partial requirements but are SaaS/UI-centric and not VCS-native. **Explicitly out of scope.**

### 7.1 The eight requirements (reference)

| # | Requirement | One-line |
|---|---|---|
| R1 | Structured, schemaful agent memory | Tasks/artifacts in a relational/SQL store; writes through schema enforcement. |
| R2 | Queryable rather than parse-only | Machine-friendly JSON queries; no HTML/UI on the agent path. |
| R3 | Dependency-aware task graph | Edges first-class; `ready-set` and `blocked` queries; graph evolves mid-execution. |
| R4 | Git-native / versioned transport | State distributable and versioned alongside code; no hard SaaS dependency. |
| R5 | Multi-agent concurrency + transaction semantics | Many writers with transactional / VCS primitives; predictable read-after-write. |
| R6 | Decoupling of work from any single agent | Work outlives sessions/context windows; pickup by any agent or human. |
| R7 | Agent-native interfaces and ergonomics | CLI/JSON/API primary; vocabulary tuned for agent callers. |
| R8 | Tight integration with orchestrators and workflows | Plane is source-of-truth for "what to do next"; pluggable into Gastown/Metaswarm/Gemba. |

**Do not renumber R1–R8 without user sign-off.** Cross-document numbering is canonical.

### 7.2 Reference-system projection

Cells are projected manifest values per system — the value each system would declare in its `WorkPlaneCapabilityManifest` (`domain.md` §2.5). Projection is informed by surveys in §2–§3 of this document and by direct inspection where noted; empirical audits land as beads under `gm-e6` (Beads) and follow-up research beads for the rest.

Legend: ✓ = clears R; ~ = partial / weak; ✗ = fails R; — = not applicable (system is a data-plane *consumer*, not a data plane).

| System | R1 schema | R2 query | R3 graph | R4 versioned-tx | R5 concurrency | R6 decoupling | R7 agent-native | R8 orchestrator hooks | Category fit |
|---|---|---|---|---|---|---|---|---|---|
| **Beads** | ✓ native (Dolt SQL) | ✓ sql-subset | ✓ native + ready-set | ✓ git + dolt + jsonl | ✓ dolt-merge | ✓ | ✓ cli + json-api | ✓ ready-set-subscribe, claim-atomic, escalation-ingest, work-complete-ack | **Full** |
| **AgentHub** | ~ synthesized (DAG+board) | ~ filter-only | ~ partial (weak deps) | ✓ git | ~ git-merge | ✓ | ✓ cli | ~ ready-set-subscribe (weak) | **Partial** |
| **Ralph** | ~ synthesized (per-iter files) | ~ filter-only | ✗ none | ✓ git | ✗ single-agent | ✗ | ✓ cli | ✗ | **Weak — single-agent** |
| **Symphony** | ~ synthesized (`WORKFLOW.md` + workspace) | ~ filter-only | ✗ none | ✓ git | ✗ | ✓ | ~ cli (markdown-shaped) | ✗ | **Weak — markdown-centric** |
| **Raindrop (Liquid Metal)** | ✓ native | ~ filter-only | ~ partial | ✗ none (SaaS) | ✓ mvcc | ✓ | ✓ json-api | ~ | **Partial — SaaS gap on R4** |
| **Gastown** | — | — | — | — | — | — | — | — | Consumer (orchestrator over Beads) |
| **Metaswarm** | — | — | — | — | — | — | — | — | Consumer (multi-agent platform over Beads) |

For reference-only comparison (systems already in §3 but at the SaaS edge of the category):

| System | R1 | R2 | R3 | R4 | R5 | R6 | R7 | R8 | Category fit |
|---|---|---|---|---|---|---|---|---|---|
| **Jira** | ✓ native | ✓ JQL (graphql-ish) | ✓ via issue links | ✗ none (SaaS Cloud) / ~ (Data Center export) | ✓ optimistic | ✓ | ~ rest-only | ✗ | **SaaS-edge — fails R4** |
| **Linear** | ✓ native | ✓ graphql | ~ partial | ✗ none (SaaS) | ✓ optimistic | ✓ | ~ rest-only (+ GraphQL) | ✗ | **SaaS-edge — fails R4** |
| **GitHub Projects v2** | ✓ native | ✓ graphql | ~ partial (sub-issues + closes) | ~ per-repo-ish (API export) | ✓ optimistic | ✓ | ~ rest-only | ✗ | **SaaS-edge — fails R4 cleanly** |

These three remain supportable as WorkPlane adaptors — the UI will expose them correctly and orchestrators that don't require R4 can bind. But an orchestrator like Gastown or Metaswarm that requires VCS-native state will refuse to bind them, and that is the *designed* outcome.

### 7.3 What the matrix implies for design

- **Beads is the only surveyed system that clears all eight requirements.** That confirms it as Gemba's reference WorkPlane (RFC §two-plane contract) and validates the category as a category (not an idiosyncrasy).
- **Ralph and Symphony fail R3 and R5.** They are not agentic-data-plane class. They can still load as reduced-capability adaptors for teams that accept the tradeoff; the manifest tells the UI to hide concurrency-dependent affordances (force-steal, concurrent-claim UX, dep-graph editing).
- **AgentHub clears most but has weak dep semantics (R3).** A Gemba adaptor can compensate by synthesizing stronger dep-graph queries at the adaptor edge, but some features (discovered-from visualization, mid-execution graph evolution) will be weaker than on Beads.
- **Raindrop fails R4.** That's a SaaS-dependency call — acceptable for users who want Gemba UI over a hosted plane but unacceptable for Git-native deployments.
- **Gastown and Metaswarm are data-plane consumers.** Their integration is evaluated at the OrchestrationPlane boundary (`domain.md` §3), not the WorkPlane boundary. Their R8 "satisfaction" is the *orchestrator side* of the R8 handshake — they call the hooks that WorkPlane adaptors advertise.

### 7.4 Update cadence

Cells are projection, not audit. Empirical validation is staged as beads:
- `gm-e6.audit` — Beads adaptor R1–R8 conformance audit (gap beads file under gm-e6).
- Future beads — AgentHub, Ralph, Symphony, Raindrop adaptor assessments, when / if adaptors are authored.

Do not add a 9th requirement or renumber R1–R8 without user sign-off. If a new category-level capability emerges, file a design bead and reconcile via amendment, not silent renumbering.

---

## 8. Addendum (2026-04-20): Beads-ecosystem UI prior art

**Source:** External user analysis provided to gemba_prime on 2026-04-20. URLs cited inline; original searches performed by the external analysis. Category added *after* Phases 1–3 because the original landscape survey focused on generic trackers × orchestrators, which missed the emerging Beads-native GUI layer. These tools are directly relevant to **where Gemba's UI phase (gm-e12.*) overlaps with already-shipped work**, so documenting them separately from the main taxonomy is deliberate.

### 8.1 VS Code Beads extensions

Three extensions exist in the VS Code Marketplace, all targeting Beads as the single supported WorkPlane:

- **Beads Kanban** (`DavidCForbes.beads-kanban`) — kanban board, table view, dependency graph, drag-and-drop status changes, real-time `.beads` updates. VS Code-hosted. Beads-only. ([marketplace](https://marketplace.visualstudio.com/items?itemName=DavidCForbes.beads-kanban))
- **Beads Project Manager** (`4UtopiaInc.beads-vscode`) — explorer/list-first with stronger table/list browsing, filters, issue metadata editing, workspace-aware daemon handling. VS Code-hosted. Beads-only. ([marketplace](https://marketplace.visualstudio.com/items?itemName=4UtopiaInc.beads-vscode))
- **vscode-beads** (`planet57.vscode-beads`) — third VS Code extension; overlapping scope with Beads Project Manager. ([marketplace](https://marketplace.visualstudio.com/items?itemName=planet57.vscode-beads))

**Category:** Beads-native UI surface. None exposes an adaptor interface; none targets any tracker besides Beads.

**Relevance to Gemba:**
- Collectively these three cover ~60-70% of Gemba's Phase 12 "work grid + kanban + dep graph + drawer" surface — *for Beads*.
- They do **not** cover: cross-tracker rendering, OrchestrationPlane integration (no agent/session/workspace/group/escalation surfaces), capability manifests, transport plurality, structured DoD/Evidence.
- UX patterns worth borrowing: drag-drop semantics, dep-graph rendering conventions, `.beads/` change-detection idioms.

### 8.2 T3 Code

Agent-execution GUI. Provider selection across coding agents, planning/chat modes, worktree-based workflows, agent session management. Not tracker-aware; no native issue/kanban surface. ([Better Stack guide](https://betterstack.com/community/guides/ai/t3-code/), [Addrom walkthrough](https://addrom.com/t3-code-minimal-web-gui-for-ai-coding-agents-complete-installation-and-usage-guide/), [pyshine](https://pyshine.com/T3Code-Minimal-Web-GUI-Coding-Agents/))

**Category:** OrchestrationPlane-side UI. Closest analog to Gemba's "agent detail + session peek + dispatch" surface for coding agents.

**Relevance to Gemba:**
- Covers ~50% of Gemba's agent-run-control surface (provider-selection, worktree-worflow, session supervision) but is **runtime-specific** — not an abstraction.
- Could be a candidate OrchestrationPlane target (T3-Code-managed agents rendered by Gemba) — not a UI replacement.
- Does not touch the work-tracker side of the house.

### 8.3 Foolery

Local web UI over Beads. Stated feature set includes **dependency-aware wave planning**, **built-in terminal for live agent monitoring**, and a **verification queue for human approval/rejection**. Positioned as the most ambitious Beads-native PM+agent-supervision tool; newer than the VS Code extensions. ([HN submission](https://news.ycombinator.com/item?id=47075901))

**Category:** Closest existing tool to Gemba's positioning. Single workspace with kanban-adjacent planning + live agent observation + human-in-loop approval. **Beads-only** per observable surface.

**Relevance to Gemba:**
- The three features listed map directly onto Gemba's (a) Kanban + dep graph, (b) session peek + escalation banner, (c) X-GEMBA-Confirm nonce + EscalationRequest UI.
- If Foolery is open-source, licensable, or extensible, it is a **serious** "extend rather than build" candidate for Gemba's Phase 12 UI surface.
- Still Beads-only, but that's a software problem (could host Gemba's adaptor layer underneath) rather than an architectural impedance mismatch.

### 8.4 How this addendum changes the picture

The original landscape (§2–§6) correctly identified a gap: *no cross-plane tool pairs any tracker with any orchestrator under one UI*. That gap is unchanged by this addendum — none of the Beads-native UIs generalize across trackers, and T3 Code doesn't generalize across work-tracker systems.

**What changes:** the assumption that Gemba must build the **entire UI surface from scratch** is weaker than it looked in April 18's planning. Roughly:

- Phase 12 UI (~17 tasks) is ~40–60% overlap with Beads Kanban + T3 Code + Foolery *for the single-plane case*.
- The **abstraction layer** Gemba is building (WorkPlaneAdaptor × OrchestrationPlaneAdaptor × CapabilityManifest × conformance suite) is still unique.
- Strategic question: **is Gemba the engine (adaptor layer) that powers an existing/future UI like Foolery, or a standalone product with its own SPA?** This should be decided before gm-e12.2..e12.17 dispatch — see the decision bead filed separately.

### 8.5 Key differentiators — Foolery ↔ Gemba

Resolution of the strategic question (gm-9h6, closed 2026-04-20): Gemba ships its own SPA (Path A). Foolery remains a candidate consumer of Gemba via a future npm package (Path D, deferred). The categorization below is what distinguishes the two products at their respective ships, irrespective of the UI-strategy pick.

| Dimension | Foolery (as of v0.10.0) | Gemba (designed) |
|---|---|---|
| **Scope** | Memory-manager backend UI: Beads or Knots, one at a time | Cross-plane UI: any `WorkPlaneAdaptor` × any `OrchestrationPlaneAdaptor` |
| **Adaptor contract** | Single `BackendPort` interface with flat `BackendCapabilities` booleans | Two typed contracts (`WorkPlaneAdaptor`, `OrchestrationPlaneAdaptor`) with rich `CapabilityManifest` (state_map, edge_extensions, field_extensions) |
| **Transport plurality** | HTTP + CLI subprocess only | `api` · `jsonl` · `mcp` (DD-15) |
| **Cross-plane concerns** | Tracker-side only; no agent-orchestration primitives beyond session attach | First-class `Agent`, `AgentGroup{mode: static\|pool\|graph}`, `Workspace`, `Session`, `EscalationRequest`, `CostMeter`, `Sprint`, `TokenBudget` |
| **Desired vs actual** | Not present | Adaptor declares `declared_state()` / `observed_state()`; drift rendered in UI (`gm-e12.13`) |
| **Capability browser** | Flags exist as data, no UI | First-class user surface (`gm-e12.14`) |
| **Budget enforcement** | Not present | Sprint+TokenBudget with three-tier inform/warn/stop (DD-14) |
| **Evidence model** | Conversation logs + PR link heuristics | Typed `Evidence` collection with shared synthesis library + synthesized-flag provenance (DD-13) |
| **Escalation model** | Implicit in session state | Unified `EscalationRequest{orchestrator_pause\|hitl_interrupt\|budget_warn\|budget_stop\|rate_limit_wait\|dod_incomplete}` + `/escalations` inbox (DD-6) |
| **Insights** | Runtime perf + Leases diagnostic | OTEL-driven work metrics (spawn rate, stuck-session minutes, sprint burn-down, token cost, escalation backlog) + leases-rollup surface (`gm-e12.17`, lease-entity bead) |
| **Mutation safety** | Standard HTTP + local-only defaults | `X-GEMBA-Confirm` single-use nonce; argon2id-hashed 256-bit token auth; TLS via user cert or `--tls-self-signed`; `--dangerously-skip-permissions` copied verbatim from Claude Code (locked decisions 7, 8) |
| **Workspace kinds** | tmux + agent dialect (claude/codex/copilot/opencode/gemini) — two-axis | `Workspace.kind ∈ worktree\|container\|k8s_pod\|vm\|exec\|subprocess` + orthogonal agent `dialect` — two-axis abstraction (locked decision 5) |
| **Multi-workspace** | Per-repo hotkey navigation (`Shift+R`) | First-class `Workspace` entity; every identity carries `WorkspaceID`; fed:safe/bridge/blocked labels reserve federation (locked decision 6) |
| **Target audience** | Individual developers running single-memory-manager agent workflows | Team/org deployments running mixed stacks (Beads+Gas Town; Jira+LangGraph; Linear+OpenHands; etc.) under one pane of glass |
| **UX opinion** | Keyboard-first, 5-view model (Queues/Active/Retakes/History/Diagnostics) with embedded xterm | Adaptor-agnostic; Kanban + WorkItem grid + dep graph + drift + capability browser + escalation inbox + insights; mouse + cmdk + global hotkey system (`gm-7hj`) |
| **Distribution** | Next.js app launched via CLI wrapper | Single Go binary with `go:embed`-bundled SPA; `brew install`, `npm install -g`, GitHub Releases across macOS/Linux/Windows/FreeBSD (locked decisions 2, 12) |

**What Foolery does better, and what Gemba borrows.** Foolery's keyboard ergonomics, 5-view decomposition, embedded xterm, and tight contract-test harness are genuinely ahead of what Gemba would ship without the lesson. Gemba's roadmap absorbs these via `gm-7hj` (hotkey system), `gm-8h9`/`gm-3dp` (Retakes + Session History views), `gm-e12.15` (xterm), and `gm-2am` (conformance harness as importable package).

**What Gemba does that Foolery cannot, without becoming a different product.** The two-plane contract, declarative-drift, multi-workspace, budget enforcement, and unified escalation are load-bearing for Gemba's target audience (team/org deployments with heterogeneous backends) but would require Foolery to either (a) rebuild its backend port into the WorkPlane×OrchestrationPlane shape or (b) pair with a backend (like the future `@gemba/foolery-backend`) that carries those surfaces through. Both are acceptable outcomes in our framing; neither is a v1 commitment.

**Why the two are complementary, not competing.** Gemba fails if it tries to out-UX Foolery on the single-plane Beads case; Foolery fails if it tries to absorb cross-plane orchestration primitives without a typed contract. The intentional overlap is the keyboard-first grid + Kanban + dep graph. The intentional divergence is everything above. This framing governs any future integration (Path D and beyond).

### 8.6 Key differentiators — t3code ↔ Gemba

t3code (`pingdotgg/t3code`, MIT, in active refactor as of 2026-04-20 — see t3-pkb audit) is a minimal web GUI for coding agents. A dedicated gap + extensibility audit of its `apps/server/src/provider/` subsystem (four audit docs + an extension guide + an ADR) produced a different lesson set from the Foolery spike, because t3code's contract work is OrchestrationPlane-shaped, not WorkPlane-shaped.

| Dimension | t3code (as of 2026-04-20 audit) | Gemba (designed) |
|---|---|---|
| **Scope** | Coding-agent orchestration GUI; four provider adapters (Claude / Codex / Cursor / OpenCode) | Cross-plane UI: any WorkPlaneAdaptor × any OrchestrationPlaneAdaptor |
| **Adaptor contract** | `ProviderAdapterShape` port with snapshot/session split; 15 service tokens, 15 live layers; ACP toolkit (`provider/acp/`) reusable | `OrchestrationPlaneAdaptor` with declared `workspace_kinds`, `group_modes`, `cost_axes`, `escalation_kinds`; WorkPlane is separate |
| **Error model** | Tagged errors via `Schema.TaggedErrorClass`; **no `retryable: bool`** — callers string-match detail strings | Discriminated errors with mandatory `retryable: bool` + structured cause (`gm-faz`) |
| **Session contract** | Close reasons inferred from stderr; `startSession(..., resumeCursor)` overloaded; reaper skips active turns per-adaptor | Typed `SessionCloseReason` enum; first-class `resume_session`; idempotent `end_session`; `active_turn_id` in contract; normalized `list_pending_requests` (`gm-xj5`) |
| **Capability enforcement** | Per-adaptor (drift across four adapters) | Port-level gate; adaptors fail-fast on undeclared ops (`gm-4qf`) |
| **Event log** | Canonical NDJSON, unbounded | Rotation + retention + archival hook from day one (`gm-3hg`) |
| **Boundary decoding** | Decode at service layer, adapters trust inputs | Decode at transport layer (api/jsonl/mcp), adapters trust inputs (`gm-io4`) |
| **Two-pipeline discipline** | Snapshot pipeline (ProviderRegistry) ≠ Session pipeline (ProviderAdapterRegistry); ADR explicitly forbids merging | CapabilityManifest.describe() vs live session operations — naturally separated; adopt t3code's explicit ADR framing |
| **Retry semantics** | No port-level retry; caller's problem | Adaptors do not retry; core/orchestration owns retry policy (consistent with t3code; codified in contract) |
| **Extension model** | `apps/server/src/provider/Services/<Name>Adapter.ts` + `Layers/<Name>Adapter.ts` + register in `ProviderAdapterRegistry.ts`; documented in `provider-extension-guide.md` | `internal/adapter/<name>/` with two interface implementations + manifest; documented in adaptor authoring guide (`gm-e14.5`, moved earlier) |
| **Target runtime** | Effect-TS service graph (layers + context + scopes) | Go interfaces + chi transport; scopes via `context.Context` + explicit cleanup |

**Three t3code observations Gemba already honors by design.** (a) `ProviderService` as the single boundary — equivalent to Gemba's transport router as the single entry point. (b) Fresh `listSessions()` with no caching at the service layer for live reads — matches Gemba's SSE-for-state-change rule (`gm-yi9`). (c) Per-adaptor capability flags rather than per-session — matches Gemba's CapabilityManifest granularity.

**Five t3code lessons Gemba did not have and now does.** All five filed as `origin:t3code-audit` beads:

- `gm-faz` — Error algebra (`retryable: bool`, discriminated kind, typed cause)
- `gm-xj5` — Session contract (SessionCloseReason, idempotent end, scope-first, active_turn_id, list_pending_requests)
- `gm-4qf` — Port-level capability enforcement
- `gm-3hg` — Event log rotation + retention
- `gm-io4` — Boundary decoding at the transport layer

**Complementary, not competing — same framing as Foolery.** t3code is a coding-agent GUI; Gemba is a cross-plane work-orchestration UI. A future `internal/adapter/t3code/` OrchestrationPlane adaptor would let Gemba render t3code-managed sessions alongside work from any WorkPlane (`gm-btm`, deferred). That integration is not pursued in v1; the architectural invariant in `gm-ege` keeps the option open.

**A smaller architectural note.** t3code's audit flags that Effect-TS's `Context.Service` pattern paired with `Layer.effect` gives a compile-time-verifiable service graph. Gemba's Go implementation can approximate this via interface-satisfaction + `wire`/`fx`-style constructor graphs, but does not inherit the same compiler guarantees. Worth tracking as a future consideration for adaptor registration tooling.

---

### 8.7 Direct citations

- Beads Kanban — https://marketplace.visualstudio.com/items?itemName=DavidCForbes.beads-kanban
- Beads Project Manager — https://marketplace.visualstudio.com/items?itemName=4UtopiaInc.beads-vscode
- vscode-beads (planet57) — https://marketplace.visualstudio.com/items?itemName=planet57.vscode-beads
- T3 Code (Better Stack guide) — https://betterstack.com/community/guides/ai/t3-code/
- T3 Code (Addrom walkthrough) — https://addrom.com/t3-code-minimal-web-gui-for-ai-coding-agents-complete-installation-and-usage-guide/
- T3 Code (pyshine) — https://pyshine.com/T3Code-Minimal-Web-GUI-Coding-Agents/
- Foolery — https://news.ycombinator.com/item?id=47075901
- Mintlify Beads community tools page — https://www.mintlify.com/steveyegge/beads/resources/community-tools

---

## Appendix: Methodology notes

- All web searches performed 2026-04-18 via WebSearch.
- WebFetch used selectively for README-level verification of Beads; other WebFetch calls would have improved rigor but were time-constrained.
- "Active / maintenance / stalled" labels are judgments based on recent commit activity and stated project status as of April 2026.
- Local workspace `/Users/mikebengtson/gt/` was consulted for Gas Town operational detail (Dolt fragility note in `CLAUDE.md`). Gas City local paths were not inspected to avoid biasing the public-source-first methodology.
- Known source-aged-18+-months: the original SWE-agent NeurIPS 2024 paper, original OpenDevin arXiv (July 2024); flagged in their cards.
- Known disputed areas: Devin's benchmark numbers (disputed throughout 2024-2025; current state still not settled — omitted from deep card rather than speculated on).
