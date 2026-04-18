# Gemba — Import Package

An Atlassian-style web UI for multi-agent orchestration. Ships against [Gas Town v1.0](https://github.com/gastownhall/gastown) today because it's the stable, production-ready runtime. Architected around [Gas City](https://github.com/gastownhall/gascity) because that's where the ecosystem is going. Packaged for direct import into a Beads database so a Mayor (or, once Gas City stabilizes, any orchestrator on any Gas City pack) can decompose and execute the build.

## What this is

A complete work package for building **Gemba** (`gemba`), a browser-based control surface that serves Gas Town v1 deployments today and, via a thin adapter flip, will serve any Gas City workspace — including the `gastown`, `ccat`, `ralph`, `wasteland-feeder`, and user-authored packs — when Gas City reaches GA.

## Stability posture (read this first)

- **Gas Town is v1.0 stable** (released April 3, 2026). Production-ready. This is the v1 runtime target.
- **Gas City is in alpha**, on track for "fast GA" per Steve's April 2026 announcement. Not a runtime target yet.
- **Gemba's architecture is Gas-City-shaped** so that when Gas City stabilizes, the primary adapter flips from `internal/adapter/gt/` to `internal/adapter/gc/` as a configuration change, not a rewrite.

The practical consequence: every locked decision below is worded in a runtime-neutral way. When a decision references `gc` behavior that doesn't exist in Gas Town (e.g., `city.toml` watching, pluggable providers, pack browsing), it means "stub-rendered against Gas Town today, comes alive when Gas City arrives." Nothing in the work package asks a Phase 1 or Phase 2 worker to depend on a Gas City feature that isn't shipped yet.

## Architectural summary (locked decisions)

Non-negotiable decisions baked into every bead's context. Changing one requires an escalation, not a local edit.

1. **Topology**: standalone sidecar, not a plugin for either runtime. Separate repo, separate binary (`gemba`). In v1: talks to `gt --json` and `bd --json` against a Gas Town workspace; reads `~/gt/` state. The `internal/adapter/gc/` package is designed and stubbed from day one so the primary runtime flips to `gc` at Gas City GA via configuration.
2. **Backend**: Go. Single binary. `go:embed` ships the built SPA. Cobra for CLI. chi for routing. SSE (not WebSockets) for live updates.
3. **Frontend**: React + TypeScript + Vite. shadcn/ui + Tailwind for the shell. @tanstack/react-query for data. @tanstack/react-table for virtualized grids. @dnd-kit/core for Kanban drag-drop. React Flow for the dep graph. cmdk for the command palette.
4. **Pack-agnostic UI**: No role name, column header, or panel hardcodes a specific pack's vocabulary — even though Gas Town v1 has fixed roles (Mayor, Witness, Refinery, Polecats, Deacon). Columns are derived from detected agents. Today this renders Gas Town's fixed role set; the moment Gas City lands, the same code renders `ccat`, `ralph`, any user pack.
5. **Provider-aware (pluggable from day one)**: Gas Town v1 runs agents in tmux. Gas City generalizes to tmux/k8s/subprocess/exec. The agent detail view is built pluggable now so no rework is needed when Gas City arrives. Each provider gets a distinct affordance set (tmux → Attach; k8s → Peek + pod status; subprocess → process tree; exec → last command + exit code).
6. **Multi-rig, not-yet-federated**: Multiple rigs within a single workspace for v1. Not Wasteland-federated. Identity types carry `WorkspaceID + RigID` (workspace = town today, city tomorrow). Labels mark `fed:safe` / `fed:bridge` / `fed:blocked`.
7. **Mutation model**: Full mutation surface, confirmation-gated by default. Every mutation requires server-enforced confirmation via `X-GEMBA-Confirm` nonce. `--dangerously-skip-permissions` (name copied verbatim from Claude Code, not softened) disables confirmations for the session.
8. **Auth**: Localhost-bound, no auth, by default. Binding a non-loopback interface without `--auth` is a startup error. Token auth: 256-bit, argon2id hashed, printed once. TLS via user certs or `--tls-self-signed`. OIDC stubbed for v1.1.
9. **Data integrity**: Never write to Dolt, JSONL, `.gt/`, `.gc/`, or any controller socket directly. Every mutation round-trips through `gt`/`gc`/`bd` CLIs or through a watched config-file edit that the runtime reconciles.
10. **Declarative UX (full on Gas City, stubbed on Gas Town)**: Once Gas City lands, the UI shows `city.toml` (desired) alongside `.gc/agents/` (actual) with drift highlighted. Against Gas Town today, the view renders the implicit "desired" derived from Gas Town's fixed role set — useful, but not the full surface. Designing for this now means no rework later.
11. **ZFC for the UI**: Gemba presents data and offers actions. It does not embed decision logic. "Why is this agent stuck?" is a question for the operator reading the session peek, not for the UI to answer. This mirrors Gas City's Go-layer principle applied to our TypeScript.
12. **Distribution**: Homebrew tap, npm wrapper, GitHub Releases binaries for macOS (Intel + Apple Silicon), Linux (amd64 + arm64), Windows, FreeBSD.

## How to import

Run `validate-import.py --dry-run` first (described below). Once it's clean:

```bash
# Recommended: use validate-import.py to do the import
./validate-import.py --target ~/gt/gemba --prefix bc

# What that does under the hood:
# 1. bd init --prefix bc in the target dir (creates .beads/)
# 2. Two-pass import: bd create --id for each bead, then bd dep add for each edge
# 3. Copies formulas/*.toml into .beads/formulas/
# 4. Sanity-checks with bd list, bd ready, bd show

# After import:
cd ~/gt/gemba
bd stats
bd list --status open --json | jq 'length'   # expect 54
bd ready --json | jq 'length'                # expect the Phase 1 starters
```

The import target shown above assumes a Gas Town v1 workspace at `~/gt/`. If you're on Gas City (alpha) the same command works — substitute `~/my-city/rigs/gemba`. The validator detects which runtime you're on.

Why not `bd init --from-jsonl`? That path has known bugs in current Beads versions (see gastownhall/beads#2433, March 2026) and doesn't preserve the `gm-eN.M` hierarchical IDs this package depends on. The two-pass `bd create --id` strategy sidesteps both problems.

## Work graph shape

- **1 root epic** (`gm-root`) — holds the twelve locked decisions above
- **9 phase epics** (`gm-e1` through `gm-e8` + post-v2 additions) — foundation, adapters, auth, beads/agents UI, boards/mutations, graph/insights/mail, molecules, release
- **42 tasks/features + 3 bugs** nested under phase epics with hierarchical IDs (`gm-e1.1`, `gm-e1.1.1`, etc.)
- **5 molecule formulas** (TOML) for multi-step, checkpoint-recoverable workflows
- **Three Gas City-native beads** (gm-e5.7, gm-e5.8, gm-e5.9) that stub-render against Gas Town and light up when Gas City is stable
- **Rich taxonomy** via labels (see below)

## Tagging taxonomy

Every issue carries labels from these orthogonal dimensions.

### Surface (pick one)
- `surface:backend` — Go code in `cmd/` or `internal/`
- `surface:frontend` — React/TS in `web/`
- `surface:infra` — build, CI, release, packaging
- `surface:docs` — user docs, architecture docs, READMEs
- `surface:protocol` — wire types shared between backend & frontend

### Layer (for backend; pick one or more)
- `layer:adapter-gc` — wraps `gc` CLI (Gas City — primary)
- `layer:adapter-bd` — wraps `bd` CLI
- `layer:adapter-fs` — reads `.gc/` runtime state
- `layer:api` — HTTP handlers
- `layer:events` — SSE fan-out
- `layer:auth` — authentication, authorization, TLS
- `layer:controller-watch` — `city.toml` + `.gc/` fsnotify integration (new for Gas City)

### Feature area (pick one)
- `area:agents`
- `area:beads`
- `area:rigs`
- `area:packs` (new for Gas City)
- `area:desired-vs-actual` (new for Gas City)
- `area:formulas`
- `area:mail`
- `area:graph`
- `area:insights`
- `area:search`
- `area:settings`

### Provider awareness (for agent-view work; pick one or more)
- `provider:tmux`
- `provider:k8s`
- `provider:subprocess`
- `provider:exec`

### Skill tier (pick one)
- `tier:haiku` — mechanical, well-specified work
- `tier:sonnet` — standard implementation
- `tier:opus` — architectural, ambiguous, security-sensitive

### Risk (pick one)
- `risk:low` — pure additive, well-tested area
- `risk:medium` — touches shared code, needs review
- `risk:high` — mutations against live `gc`/`bd`, auth surface, data integrity

### Federation-readiness (pick one)
- `fed:safe` — decision does not constrain future Wasteland support
- `fed:bridge` — requires explicit multi-city consideration
- `fed:blocked` — would need rework if we go federated; avoid

## Conventions for the orchestrator

- Every parent epic uses `issue_type: "epic"`. Children use the right leaf type (`task`, `feature`, `bug`, `story`).
- Every task has a detailed `description` with: **Goal**, **Inputs**, **Outputs**, **Definition of Done**. Agents do worse work when context is thin.
- `blocks` edges enforce ordering. `parent-child` is epic → child hierarchy. `discovered-from` is reserved for issues filed during execution.
- Honor `tier:*` when routing work. `tier:opus` should not be handed to Haiku.
- Ambiguity in any locked decision triggers an escalation, not a local call.
- When rendering agent-specific UI, honor `provider:*` — don't ship a tmux-only Attach flow to a k8s deployment.

## Files in this package

```
.
├── README.md                    # this file
├── issues.jsonl                 # all epics, tasks, bugs (one JSON per line)
├── validate-import.py           # prereq + schema + dry-run validator
├── bootstrap-prompt.md          # Mayor/controller bootstrap prompt
├── convoys.json                 # suggested convoy groupings
├── generate.py                  # regenerator for issues.jsonl
├── formulas/
│   ├── gm-m1-foundation.toml    # scaffold repo, CI, skeleton binary
│   ├── gm-m2-auth.toml          # localhost + token + TLS auth
│   ├── gm-m3-board.toml         # Kanban board with drag-drop
│   ├── gm-m4-graph.toml         # dependency graph visualization
│   └── gm-m5-release.toml       # release workflow
├── RFC.md                       # community RFC
├── discord-post.md              # Discord-ready short-form RFC
└── scaffold/                    # starter Go+React repo, buildable as-is
```
