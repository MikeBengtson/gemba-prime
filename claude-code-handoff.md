# Gemba — Claude Code Session Bootstrap

**Last updated:** 2026-04-17
**Handoff from:** prior architect/PM session
**For:** a fresh Claude Code session continuing the Gemba build

---

## TL;DR

Gemba is a standalone Atlassian-style web UI for Gas Town v1, designed so the primary runtime can flip from `gt` to `gc` (Gas City) at GC GA via configuration. It ships as a single Go binary (`gemba`) with an embedded React SPA.

As of this handoff:
- **Repo**: `github.com/MikeBengtson/gemba` — scaffold committed, builds clean
- **Rig**: `gemba` (underscore — Gas Town enforces) — operational in Gas Town HQ at `~/gt/gemba/`
- **Dolt database**: `gemba` on the per-town Dolt server (port 3307), contains **60 beads total** (4 Gas Town infrastructure + 55 Gemba work package + 1 DoltHub setup task)
- **Ready work**: 12 unblocked beads, 5 at P0, Phase 1 ready to dispatch
- **HQ diagnostic bead exists** (hq-* ID TBD) for the `bd auto-export: git add failed` warning — not blocking work, but should be resolved
- **Scaffold builds green**: `cd ~/gt/gemba/refinery/rig && make build` → `bin/bc` (9.9 MB)
- **Nothing has been dispatched yet.** The Mayor has not been attached. Phase 1 is queued, not in flight.

---

## What Gemba is

Gemba is a browser-based control surface for multi-agent orchestration. Think Jira meets a distributed debugger meets a live ops dashboard. It runs alongside a Gas Town workspace (in v1) or a Gas City city (post-GA) and provides:

- **Work graph visualization** — the bead dependency DAG
- **Agent detail views** — pluggable per provider (tmux today, tmux/k8s/subprocess at GC GA)
- **Convoy and formula management**
- **SSE-driven live updates**
- **Pack-agnostic UI** — derives role columns from detected agents, does NOT hardcode Mayor/Witness/Refinery even though Gas Town v1 has fixed roles

## Stability posture (read this first, very important)

- **Gas Town 1.0** is the stable runtime. Released April 3, 2026 after 14 iterative releases. This is what Gemba v1 builds against and ships against.
- **Gas City** is alpha, on track for "fast GA." **Not a runtime target today.** It is the architectural compass only.
- The scaffold's `internal/adapter/gc/` package is designed and stubbed from day one so that when Gas City reaches GA, the primary runtime can flip from `gt` to `gc` via configuration — no code surgery, no UI rework.

Why architect around Gas City while building on Gas Town? Because Gas City's declarative-SDK shape (pack-agnostic agents, `city.toml` desired state, pluggable providers, progressive capability levels) tells us what the UI needs to look like to survive the transition. Building a Gas-Town-shaped UI now would mean a rewrite at GC GA.

---

## Environment

### Host machine (mikebengtson@Mac)

- macOS
- Go ≥ 1.23 installed
- Node ≥ 20 installed
- pnpm installed via corepack (v10.33.0)
- `gt` v1.0.0 (Gas Town CLI)
- `bd` v1.0.2 (Beads CLI)
- Dolt SQL server running on port 3307, managed by `gt daemon`

### Gas Town HQ layout (`~/gt/`)

```
~/gt/
  .beads/              HQ-level beads config (routes.jsonl, hooks/)
  .dolt-data/          Dolt server data dir — per-rig subdirectories
    hq/                Town-level beads (hq-* prefix)
    gemba/       THE RIG'S BEADS (bc-* prefix) — 60 beads here
    lume_spark_api/    Other rig
    sb/                Other rig
    second_brain/      Other rig
  gemba/         ← YOUR RIG ROOT
    .beads/            Rig-level config (metadata.json, config.yaml, hooks)
                       NOT bead storage. Storage is in Dolt. Config only.
    .claude/           Claude Code session metadata (gitignored in rig repo)
    mayor/rig/         Mayor's working clone of the gemba repo
    refinery/rig/      ← CODE LIVES HERE. Git worktree of gemba repo.
    witness/           Witness agent state
    polecats/          Worker agents (currently none)
    crew/              Human workspaces (currently none)
```

### Routing (important)

`~/gt/.beads/routes.jsonl` maps bead prefix → rig path:

```
{"prefix":"hq-","path":"."}
{"prefix":"hq-cv-","path":"."}
{"prefix":"lsa-","path":"lume_spark_api"}
{"prefix":"bc-","path":"gemba"}
```

When `bd create gm-foo ...` is run from anywhere, routing sends the write to the `gemba` Dolt database. When run with an `hq-*` ID, it goes to the `hq` database.

**Which database `bd` writes to depends on two things:**
1. The bead ID prefix (if `--id` is explicit)
2. The `.beads/config.yaml` in your current directory (which pins the database when creating new beads)

`~/gt/gemba/.beads/config.yaml` is configured to use the `gemba` database. Running `bd` commands from inside `~/gt/gemba/` hits that database. Running from `~/gt/` hits HQ.

### Known oddity

Every `bd create`/`bd update` in the rig emits: `Warning: auto-export: git add failed: exit status 1`

This is cosmetic — bd writes succeed in Dolt. The warning is about the post-write JSONL mirror export and was probably caused by our earlier cleanup churn. An HQ bead was created to diagnose it (ID should start with `hq-`; find with `cd ~/gt && bd list --all --limit 0 --json | jq '.[] | select(.title | contains("auto-export"))'`). Not blocking work.

---

## Repository state

### `github.com/MikeBengtson/gemba` — current HEAD

Latest commit pushed (verify with `git log --oneline -5` from `~/gt/gemba/refinery/rig/`):
1. Initial commit (from `gt rig add` bootstrap) — full v3.1 scaffold
2. `.gitignore` update — ignore rig-level `.beads/` config (machine-specific)
3. **Pending push** (if the handoff happened mid-stream): scaffold buildability fixes (vite.config.ts vitest import, pnpm-lock.yaml, Makefile .keep restoration)

**Check before doing anything code-related:**
```bash
cd ~/gt/gemba/refinery/rig
git log --oneline -5
git status
```

If `git status` shows uncommitted modifications to `Makefile`, `web/vite.config.ts`, or untracked `web/pnpm-lock.yaml`, that's the scaffold fix commit that needs to be pushed. The commit message is:

```
Scaffold buildability fixes

- vite.config.ts: import defineConfig from vitest/config so the test
  block type-checks. Vitest is already in devDependencies.
- web/pnpm-lock.yaml: check in so 'corepack enable && pnpm install
  --frozen-lockfile' reproducibly installs frontend deps.
- Makefile: restore web/dist/.keep after vite's emptyOutDir sweep.
  Required because //go:embed all:web/dist demands the directory exist
  at go build time, even on fresh clones without a frontend build.

Verified: make build produces bin/bc (9.9MB) with embedded SPA.
```

Push it with:
```bash
git add Makefile web/vite.config.ts web/pnpm-lock.yaml web/dist/.keep
git commit -F- <<'EOF'
[message above]
EOF
git push origin main
```

### Scaffold structure

```
refinery/rig/
  cmd/gemba/              Go entrypoint, cobra CLI, "serve" and "doctor" subcommands
  embed.go             //go:embed all:web/dist for SPA embedding
  internal/
    adapter/
      gt/              Gas Town adapter (primary, v1 runtime) — STUBBED
      gc/              Gas City adapter (secondary, future runtime) — STUBBED
      bd/              Beads CLI adapter — STUBBED
      fs/              Filesystem adapter for reading ~/gt/ state — STUBBED
    model/             Domain model with federation-safe identity — TBD gm-e2.1
    http/              chi router, SSE, handlers — TBD gm-e2.x, gm-e3.x
    sse/               SSE broadcasting — TBD
  web/                 React + TypeScript + Vite SPA
    src/               React components, routes, hooks — TBD gm-e4.x, gm-e5.x
    vite.config.ts     vitest-aware config
    package.json       pnpm-based, vitest in devDependencies
    pnpm-lock.yaml     committed, use frozen-lockfile
  Makefile             dev/build/test/lint/release targets
  .github/             CI workflows (TBD)
  .goreleaser.yml      goreleaser config for release builds
```

### Build verification (run this first in a fresh session)

```bash
cd ~/gt/gemba/refinery/rig
corepack enable                  # ensure pnpm is available
make build                       # should produce bin/bc
./bin/gemba version                 # should print: bc <commit> (commit <sha>, built <date>)
./bin/gemba --help                  # should list subcommands
```

If `bin/bc` is produced and `--version` and `--help` work, the scaffold is intact and the environment is healthy.

---

## The work graph

**60 beads total in the `gemba` Dolt database.** The structure:

- `gm-root` — root epic, holds the twelve locked architectural decisions
- `gm-e1` through `gm-e8` — phase epics (Foundation, Backend, Security, Frontend, Agent views, Work management, Formulas, Release)
- `gm-e1.1`, `gm-e1.2`, ... `gm-e8.5` — tasks within each phase
- `gm-e8.5` — DoltHub remote setup and gt dolt sync wiring (just added)
- `gm-b1`, `gm-b2`, `gm-b3` — three bug beads (daemon offline handling, SPA 404 shadowing, token-auth on loopback)
- 4 Gas Town infrastructure beads: `gm-fmn`, `gm-qul`, `gm-vus`, `gm-rig-gemba` (don't touch these, they belong to Gas Town)

### The twelve locked decisions (read `bd show gm-root` for the full charter)

Changes to any of these require an escalation, not a local edit.

1. **Topology**: Standalone sidecar. Separate repo, separate binary. Not a plugin for either runtime.
2. **Backend**: Go single binary, `go:embed` for SPA, cobra for CLI, chi for routing, SSE (not WebSockets) for live updates.
3. **Frontend**: React + TypeScript + Vite. shadcn/ui + Tailwind. TanStack Query/Table. @dnd-kit. React Flow. cmdk.
4. **Pack-agnostic UI**: No role name, column header, or panel may hardcode a specific pack's vocabulary. Columns derive from detected agents.
5. **Provider-aware (pluggable from day one)**: Agent detail view built pluggable now; tmux today, tmux/k8s/subprocess/exec at GC GA.
6. Remaining decisions (6–12): read `bd show gm-root` for the full list. They cover federation-safe identity, bind policy, declarative-UX stubbing, adapter contract shape, SSE protocol, audit log location, and release surface.

### Ready pool (as of last check)

12 unblocked beads, shown by `bd ready --json --limit 0`:

- **P0** (dispatch first): `gm-e1.1` (Bootstrap Go module), `gm-e1` (Phase 1 epic — don't sling, let it close when children close), `gm-e2.1` (Domain model), `gm-e3.1` (Bind policy), `gm-e4.1` (App shell)
- **P1**: `gm-b2` (SPA fallback vs API 404 bug), `gm-e8.3` (Docs site)
- **P2**: `gm-b1` (bd daemon offline handling), `gm-e7.1` (Formula catalog view), `gm-rig-gemba` (Gas Town identity bead)
- **P3**: `gm-b3` (token auth on loopback bug)

**Important nuance about `gm-e1.1`**: the scaffold is already in place. A worker taking this bead should *verify* the scaffold matches the bead's acceptance criteria and close it with a reason like "scaffold satisfies criteria; verified with `make build`" — NOT re-bootstrap anything. If a worker starts trying to re-create `go.mod`, that's a signal they haven't read the existing state.

---

## Running work against the rig

### Where to run `bd` commands

- **For `bc-*` beads (Gemba work)**: run from `~/gt/gemba/` or any subdirectory thereof
- **For `hq-*` beads (town-wide)**: run from `~/gt/` itself (not inside a rig)
- **Always pass `--all --limit 0` to `bd list`** — bd's default limit is 50, easy to miss beads otherwise

### Writing code

- **Working clone is `~/gt/gemba/refinery/rig/`** — this is the git worktree pointed at `github.com/MikeBengtson/gemba.git`
- Commits and pushes happen from here
- Don't touch `.beads/` in the working clone — it's gitignored and contains machine-specific rig config, not bead data

### Architectural pressure tests

As Phase 1 proceeds, watch which locked decisions generate the most escalations. That's the signal telling you which decisions are genuinely load-bearing vs. design-scratch. Anything with friction is where the real constraints live.

---

## Pending things to consider (NOT urgent, but worth knowing)

### 1. Start Phase 1 (the actual next step)

```bash
cd ~/gt/gemba
gt mayor attach
# Paste the contents of bootstrap-prompt.md (lives in gemba-prime/ or wherever the work package is staged)
```

The Mayor will read gm-root, absorb the twelve decisions, create a Phase 1 convoy from `gm-e1.*` children, and dispatch `gm-e1.1` and `gm-e1.4` to polecats in parallel.

### 2. Post the RFC to Discord

The RFC lives in the work package (not in the repo — it's a delivery artifact). Target channel: `#gas-town-construction` on the Gas Town Hall Discord (`https://discord.gg/xHpUGUzZp2`). Three messages prepared in `discord-post.md`. Reference Julian Knutsen and Chris Sells for the sequencing question.

### 3. Set up DoltHub remote (gm-e8.5)

Currently the 60 beads live only on this local machine's Dolt server. No off-machine backup. Bead `gm-e8.5` tracks getting Dolt data pushed to DoltHub for backup, federation, and Wasteland-readiness. Not urgent, but the more work accumulates locally, the worse a disk failure would be.

### 4. Fix the auto-export warning (HQ bead)

Every `bd` write in the rig prints a git-add-failed warning. Cosmetic only. HQ bead exists to diagnose. May turn out the right fix is to disable auto-export entirely, since DoltHub sync (gm-e8.5) makes the JSONL-in-git mirror redundant.

### 5. bd doctor warnings to clean up

From `bd doctor` in the rig:
- `.beads/` permissions are 0755, recommended 0700 → `chmod 700 ~/gt/gemba/.beads`
- Missing `project_id` (pre-GH#2372 project) → `bd doctor --fix`
- Missing `.beads/.gitignore` → `bd doctor --fix`
- No git hooks → `bd hooks install`

None of these block anything, but clearing them removes noise.

### 6. scaffold/Makefile targets not yet wired to CI

`.github/workflows/` directory exists but CI wiring is Phase 8 work (gm-e8.1 or similar). No CI runs on push yet.

---

## Important context for Claude Code

### Work package and meta-artifacts location

These live outside the git repo in `~/gemba-prime/` (or wherever the human staged them locally):

- `RFC.md` — full design doc
- `issues.jsonl` — the 55 Gemba beads in JSONL form (source of truth for the import)
- `bootstrap-prompt.md` — the Mayor orchestration prompt
- `discord-post.md` — Discord announcement messages
- `formulas/*.toml` — 5 molecule formulas (copied into `~/gt/gemba/.beads/formulas/` during import)
- `validate-import.py` + `merge-import.py` — import scripts (include bd v1 server-mode fixes)
- `scaffold/` — buildable Go+React scaffold (this was copied into the GitHub repo via `gt rig add`)

**Philosophy**: these are delivery artifacts, not source. They've served their purpose (beads are live, scaffold is committed). Keep them if useful for reference, but don't commit them to the gemba repo.

### bd v1 server-mode gotchas we discovered

These aren't well documented and tripped the import repeatedly:

1. **No `bd types` or `bd statuses` subcommands exist.** Probe `bd create --help` / `bd update --help` instead.
2. **Hierarchical IDs (`gm-e1.1`) auto-imply parent-child.** Explicit `bd dep add --type parent-child` is rejected as a deadlock. Skip those edges during import.
3. **`bd list` default paginates at 50.** Use `--all --limit 0`.
4. **`bd show --json` returns a list, not an object**, even for single IDs. Handle both shapes.
5. **`.beads/config.yaml` must point at the correct Dolt database.** `gt dolt fix-metadata` restores metadata.json but NOT config.yaml if it was deleted. Hand-writing config.yaml with `dolt: mode: server, host: 127.0.0.1, port: 3307, database: gemba` resolves it.

If Claude Code hits bd errors, these are the usual suspects.

### Claude Code integration notes

Beads installed Claude Code integration into the rig during setup:
- `~/gt/gemba/CLAUDE.md` — beads-integration instructions (committed? check with `git ls-files CLAUDE.md`; it should be gitignored per Gas Town's `.gitignore` rules in the scaffold)
- `~/gt/gemba/.claude/settings.json` — Claude Code settings

When Claude Code starts a session in the rig:
- `bd prime` should be auto-injected via SessionStart hook
- The CLAUDE.md file should surface beads workflow context
- Slash commands like `/beads:ready`, `/beads:create-issue` should be available if the beads plugin is installed

If beads integration feels off, run `bd setup claude` to reinstall.

### Tools available to Claude Code

Assume standard Claude Code tools (file editing, bash, etc.) plus:

- `bd` — Beads CLI. Use from `~/gt/gemba/` for rig work.
- `gt` — Gas Town CLI. `gt ready`, `gt convoy`, `gt sling`, `gt doctor`, etc.
- Go toolchain, pnpm, node
- Dolt SQL shell via `gt dolt sql` (no `-q` flag; it's interactive)

---

## Suggested first actions for a fresh Claude Code session

```bash
# 1. Orient in the environment
cd ~/gt/gemba/refinery/rig
pwd
git log --oneline -5
git status

# 2. Verify scaffold still builds
make build
./bin/gemba --help

# 3. See the work graph
cd ~/gt/gemba
bd list --all --limit 0 --json | jq 'length'         # expect 60
bd ready --json --limit 0 | jq '.[] | {id, title, priority}'
bd show gm-root | head -80                            # read the twelve decisions

# 4. Check for any uncommitted/unpushed work from the prior session
cd ~/gt/gemba/refinery/rig
git status
# If there are modifications to Makefile, vite.config.ts, or untracked pnpm-lock.yaml,
# commit with the message documented above and push to origin/main.

# 5. Decide what to do next:
#    a) Start Phase 1 — gt mayor attach + paste bootstrap-prompt.md
#    b) DoltHub setup — work gm-e8.5
#    c) Post RFC to Discord
#    d) Fix bd doctor warnings
```

---

## Key commands reference

```bash
# Orient
cd ~/gt/gemba
gt rig status gemba
gt dolt status
bd doctor 2>&1 | head -30

# Work graph
bd list --all --limit 0 --json | jq 'length'
bd ready --json --limit 0
bd show gm-root
bd show gm-e1
bd show gm-e1.1

# Create beads (hierarchy under gm-e1)
cd ~/gt/gemba
bd create "Title" --id gm-e1.7 -t task -p 1 -l surface:backend --stdin <<< "description"

# Update / close
bd update gm-e1.1 --status in_progress --assignee claude-code
bd close gm-e1.1 --reason "Completed: scaffold verified, matches spec"

# Dependencies (skip parent-child for hierarchical IDs — auto-inferred)
bd dep add gm-e2.1 gm-e1.1 --type blocks

# Build + test
cd ~/gt/gemba/refinery/rig
make build
make test        # Go + Vitest frontend tests
make lint        # golangci-lint + eslint
./bin/gemba --help
./bin/gemba doctor
./bin/gemba serve

# Gas Town orchestration
gt mayor attach
gt convoy create "Phase 1 Foundation" $(bd list --parent gm-e1 -o id --json | jq -r '.[]' | tr '\n' ' ')
gt sling gm-e1.1 gemba         # note UNDERSCORE in rig name
gt sling gm-e1.4 gemba
gt feed                              # real-time activity feed
```

---

## Final note

The prior session did a lot of plumbing to get to this green state — five rounds of bd v1 debugging, a Dolt-database-orphan incident, a cleaned `.beads/` that turned out to not be the storage layer at all, and several small scaffold fixes. The state you're inheriting is clean but the path to it was not. If something seems surprisingly broken, consult this document's "bd v1 server-mode gotchas" section first before assuming it's a new problem.

Good luck with Phase 1.