# Discord post (short-form RFC)

## Message 1 — the pitch

Hey 👋 posting this for community feedback before I commit real build cycles. TL;DR below; full RFC attached.

**Gemba** (`gemba`) — a browser-based Kanban-style UI for multi-agent orchestration. **Ships against Gas Town v1.0 today** because that's the stable, production-ready runtime. **Architected around Gas City** because that's where the ecosystem is going. The adapter layer is designed so the primary runtime flips from `gt` to `gc` via configuration, not code surgery, the moment Gas City reaches GA.

Single Go binary, embedded React SPA. **The Convoy Kanban is the home screen** — columns derive from detected `[[agents]]`, no hardcoded Mayor/Witness/Polecat in the UI layer even though Gas Town v1 has those as fixed roles. When Gas City arrives with `gastown`, `ccat`, `ralph`, `wasteland-feeder`, and user packs, the same board renders whatever the active topology declares without code changes.

**What it's for — three concrete workflows:**
1. **Plan & refine.** Cross-rig 10k-bead work grid for triage (virtualized, saved filters, JSONL import); click any row for a Jira-style bead detail view with labels, deps, activity log, and quick actions. Author molecule formulas as workflow DAGs before any agent is dispatched.
2. **Scrum / day-of ops.** Convoy Kanban is the home screen — drag-drop round-trips through `bd update` and slings via `gt` (or `gc` at GA); multi-select cards to batch-create a convoy. Swimlanes, WIP limits, filter chips, cmdk keyboard. Desired-vs-actual drift tints column headers; provider-aware agent peek for the "why is this one stuck" moment. Every mutation `X-GEMBA-Confirm` nonce-gated.
3. **Retro & release.** Landed-convoy review, molecule step-by-step replay (prompts + outputs + checkpoint state), insights panel fed from OTEL + `bd stats` (spawn rate, stuck-agent minutes, token cost, merge-queue latency).

**Key question I most want answered** (for the Gas City team specifically): is the sequencing right? I'm planning to ship a Gas Town v1 UI now and swap in the Gas City adapter at GA. Alternatives: (a) wait for GC GA, ship only against that; (b) stop, because a reference UI is already planned on your side. Option (b) is the cheapest thing to find out early.

Why now? `gt dashboard` is intentionally htmx-light and Gas Town v1 is in maintenance mode — the in-tree dashboard won't grow drag-drop Kanban or a graph view. gvid and Smorgasbord serve Gas Town well but hardwire Town vocabulary in the UI layer, which makes the GC migration painful. Designing to Gas City's shape now, running against Gas Town today, hits both targets.

(thread 👇)

## Message 2 — the locked decisions

Ten locked decisions in the RFC; the five most pushback-worthy:

1. **Gas Town v1 is the primary runtime today.** `gt --json` + `bd --json`, reads `~/gt/` state. The `internal/adapter/gc/` package is designed and stubbed; it comes alive when Gas City hits GA. No code surgery to switch.
2. **Pack-agnostic UI.** No hardcoded role names even now. The Kanban's columns and swimlanes derive from detected agents. Works today against Gas Town's fixed roles; works unchanged against any Gas City pack when GC arrives.
3. **Declarative-reconciliation as a first-class surface (stubbed on Gas Town, full on Gas City).** Desired-vs-actual view reads Gas Town's implicit role structure today; reads `city.toml` + `.gc/agents/` when Gas City lands. The UI surface doesn't change.
4. **Provider-aware agent detail.** Gas Town runs agents in tmux today; Gas City generalizes to tmux/k8s/subprocess/exec. The detail view is built pluggable from day one.
5. **Full mutation surface, confirmation-gated by `X-GEMBA-Confirm` nonce.** `--dangerously-skip-permissions` (copied verbatim from Claude Code, not softened) disables for session.

Auth: localhost by default. Non-loopback without `--auth` is a startup error, not a warning. Token: 256-bit, argon2id, printed once. TLS via user certs or self-signed with fingerprint at startup. OIDC stubbed for v1.1.

Architecturally aligned with Gas City's stated principles — ZFC, GUPP (viewer not dispatcher), NDI (mutations idempotent via nonces), SDK Self-Sufficiency (works against Gas Town's fixed role set AND a Level 1 Gas City). Bitter Lesson exclusions honored everywhere: no skill catalog, no capability badges, no MCP panels, no decision trees, no role `switch` statements.

## Message 3 — what I'm asking for

1. **Gas City team: is sequencing right?** Ship GT v1 now, swap to GC at GA? Or wait? Or stop because a reference UI is planned? The single most valuable signal.
2. **Pack-agnostic UI sanity.** Any failure modes from the "no hardcoded role names" rule — even against Gas Town's fixed-role reality today?
3. **Desired-vs-actual prior art.** Is `gc config explain --drift` already planned? I'd rather consume than reinvent.
4. **Architectural red flags.** Sidecar vs plugin, Go+React, full mutation vs read-only v1.
5. **Prior art I missed** — especially anything designed for the Gas Town → Gas City transition specifically.
6. **Auth sanity check.** Bind-policy startup-error is opinionated.
7. **Anyone building the same thing?** Let's join forces.

Work is decomposed: 54 beads (1 root + 9 phase epics + 42 tasks + 3 bugs), 5 TOML molecule formulas, label taxonomy with `provider:*` and `area:desired-vs-actual`. Phase 1 scaffold builds and tests clean; bind policy verifiably rejects 0.0.0.0-without-auth; doctor detects both Gas Town (`~/gt`, `.gt/`, `rigs/`) and Gas City (`~/my-city`, `.gc/`, `city.toml`) workspaces so one binary serves both — useful today, future-proof.

Full RFC: https://gist.github.com/MikeBengtson/e27f3b651e8ffcfa258954099e0058ea
Work package: https://github.com/MikeBengtson/gemba

Not asking for maintainer time or upstream integration. Just want to know if the approach is sound before Phase 2. 🙏
