#!/usr/bin/env python3
"""
Generator for Gemba issues.jsonl.

Produces beads-compatible JSONL. Schema follows cmd/bd/create.go and the
BeadJson interface exposed by community tools (issue_type, priority, status,
dependencies, labels, description).

Dependencies are the only typed-edge format beads accepts inline:
    [{"depends_on_id": "<id>", "type": "<dep-type>"}]

Valid dep types: blocks, related, parent-child, discovered-from,
                 waits-for, replies-to, conditional-blocks
"""

import json
from pathlib import Path
from textwrap import dedent

ISSUES = []

PREFIX = "gemba"

# ----------------------------------------------------------------------
# Label vocabulary (mirrors README taxonomy)
# ----------------------------------------------------------------------
# surface: backend, frontend, infra, docs, protocol
# layer:   adapter-gc, adapter-bd, adapter-fs, api, events, auth
# area:    convoys, beads, agents, molecules, mail, graph, insights,
#          search, rigs, escalations, settings
# tier:    haiku, sonnet, opus
# risk:    low, medium, high
# fed:     safe, bridge, blocked


def add(issue_id, title, description, *,
        issue_type="task",
        priority=2,
        status="open",
        deps=None,
        labels=None,
        assignee=None):
    """Append a bead to the global ISSUES list."""
    deps = deps or []
    labels = labels or []
    issue = {
        "id": issue_id,
        "title": title,
        "description": dedent(description).strip(),
        "issue_type": issue_type,
        "priority": priority,
        "status": status,
        "labels": labels,
        "dependencies": deps,
    }
    if assignee:
        issue["assignee"] = assignee
    ISSUES.append(issue)


def dep(target, kind="blocks"):
    return {"depends_on_id": target, "type": kind}


# ======================================================================
# ROOT EPIC
# ======================================================================

add(
    f"{PREFIX}-root",
    "Gemba — Atlassian-style web UI for Gas Town v1, designed for the Gas City transition",
    """
    Root epic. Holds the twelve locked architectural decisions for the entire
    project. Do NOT close until every phase epic is closed.

    # Project Charter

    Gemba is a standalone sidecar binary (`gemba`) that provides a rich,
    browser-based control surface for multi-agent orchestration.

    STABILITY POSTURE (read this first):
    - Gas Town 1.0 is the stable runtime. Released April 3, 2026 after 14
      iterative releases. This is what Gemba v1 ships against.
    - Gas City is in alpha, on track for "fast GA." NOT a runtime target
      today. Architectural compass only.
    - The adapter layer is designed so the primary runtime flips from `gt`
      to `gc` via configuration when Gas City reaches GA — no code surgery,
      no UI rework.

    Why architect around Gas City when building on Gas Town? Because Gas
    City's declarative-SDK shape — pack-agnostic agents, city.toml desired
    state, pluggable providers, progressive capability levels — tells us
    exactly what the UI needs to look like so it survives the transition.
    Building a Gas-Town-shaped UI now would mean rewriting it at GC GA.

    # Twelve locked architectural decisions

    Changes to any of these require an escalation, not a local edit.

    1. TOPOLOGY. Standalone sidecar. Separate repo, separate binary. Not a
       plugin for either runtime. In v1: talks to `gt --json` and `bd --json`
       against a Gas Town workspace; reads `~/gt/` state. The `adapter/gc/`
       package is designed and stubbed from day one so the primary runtime
       flips at GC GA via configuration.
    2. BACKEND. Go single binary. go:embed ships the SPA. Cobra for CLI.
       chi for routing. SSE (not WebSockets) for live updates.
    3. FRONTEND. React + TypeScript + Vite. shadcn/ui + Tailwind. TanStack
       Query/Table. @dnd-kit. React Flow. cmdk.
    4. PACK-AGNOSTIC UI. No role name, column header, or panel may hardcode
       a specific pack's vocabulary — EVEN THOUGH Gas Town v1 has fixed
       roles (Mayor, Witness, Refinery, Polecats, Deacon). Columns are
       derived from detected agents. Today renders Gas Town's role set;
       at GC GA renders `ccat`, `ralph`, `wasteland-feeder`, or user packs
       without code changes.
    5. PROVIDER-AWARE (pluggable from day one). Gas Town v1 runs agents in
       tmux. Gas City generalizes to tmux/k8s/subprocess/exec. The agent
       detail view is built pluggable now so GC GA needs zero rework.
    6. MULTI-RIG, NOT-YET-FEDERATED. Multiple rigs in a single workspace
       for v1 (workspace = town today, city tomorrow). Not Wasteland-
       federated. Every identity carries WorkspaceID + RigID; labels mark
       fed:safe / fed:bridge / fed:blocked.
    7. MUTATION MODEL. Full mutation surface, confirmation-gated by
       server-enforced X-GEMBA-Confirm nonce. `--dangerously-skip-permissions`
       (copied verbatim from Claude Code, not softened) disables for
       session.
    8. AUTH. Localhost-bound by default. Non-loopback without `--auth` is
       a startup error. Token auth: 256-bit, argon2id, printed once. TLS
       via user certs or --tls-self-signed. OIDC stubbed for v1.1.
    9. DATA INTEGRITY. Never write to Dolt, JSONL, `.gt/`, `.gc/`, or any
       controller socket directly. Every mutation round-trips through
       `gt`/`gc`/`bd` CLIs or through a watched config-file edit the
       runtime reconciles.
    10. DECLARATIVE UX (full on GC, stubbed on GT). At GC GA: UI shows
        city.toml (desired) vs .gc/agents/ (actual) with drift highlighted.
        On Gas Town today: view renders the implicit "desired" from the
        fixed role set vs running sessions — useful but partial. The
        component tree doesn't change when Gas City arrives.
    11. ZFC FOR THE UI. Gemba presents data and offers actions. It
        does NOT embed decision logic about what agents should do. Same
        principle Gas City applies to its Go code, applied to our TS.
    12. DISTRIBUTION. Homebrew tap, npm wrapper, GitHub Releases for
        macOS/Linux/Windows/FreeBSD.

    # Gas City principle alignment (design compass, not runtime dependency)

    Every architectural decision above is made with Gas City's principles
    in mind, even though we're building on Gas Town today:

    - ZFC: no judgment calls in Go/TS code; move decisions to prompts
      (agents) or UI affordances (humans).
    - GUPP: Gemba is a viewer, not a dispatcher. Surface ready work,
      let humans or Mayors decide to sling.
    - NDI: every mutation endpoint safely retryable via X-GEMBA-Confirm nonce.
    - SDK Self-Sufficiency: must function against Gas Town's fixed role
      set AND (at GC GA) a Level 1 city with one agent. Any feature
      assuming specific roles violates.
    - Bitter Lesson exclusions honored: no UI-layer skill catalog, no
      capability badges beyond what config declares, no MCP/tool panels,
      no decision trees, no role-name switch statements anywhere.

    # Out of scope for v1

    - Wasteland federation (deferred; fed:* labels prevent precluding it)
    - Mobile native apps (responsive web is enough)
    - Confluence-like docs surface
    - Direct Dolt/JSONL/`.gt/`/`.gc/` writes (ever)
    - Replacing `gt dashboard` upstream (parallel tool, not replacement)
    - Becoming an in-tree Gas Town or Gas City feature (sidecar, always)
    - Waiting for Gas City GA before shipping anything (we ship on Gas
      Town today)

    # Definition of Done

    - All phase epics (gm-e1..gm-e8) closed
    - Binary published for all target platforms
    - `brew install gemba` works
    - `gemba doctor` passes clean on a Gas Town v1 install
    - `gemba doctor` passes clean on a Gas City install (once GC reaches GA)
    - Documentation site live
    - Works against Gas Town's fixed role set today AND (post-GC-GA) a
      Level 1 city with one agent through a full gastown-pack deployment
    """,
    issue_type="epic",
    priority=0,
    labels=["surface:docs", "area:settings", "tier:opus",
            "risk:high", "fed:safe"],
)


# ======================================================================
# PHASE 1 — FOUNDATION
# ======================================================================

add(
    f"{PREFIX}-e1",
    "Phase 1: Foundation — repo, skeleton binary, CI, embed pipeline",
    """
    Ship a binary that serves "hello world" SPA via go:embed, installs cleanly
    on all target platforms, and has a green CI pipeline. No features, just
    the scaffolding that every subsequent phase depends on.

    # Goal
    Establish the project skeleton so every later task can assume a working
    Go + Vite + embed + release pipeline.

    # Definition of Done
    - `go install github.com/.../gemba/cmd/gemba@latest` works
    - `gemba serve` binds :7666, serves embedded SPA, closes cleanly on SIGTERM
    - `make dev` runs Vite HMR + Go hot reload with working proxy
    - `make build` produces a single binary with SPA embedded
    - GitHub Actions: lint, vet, test, build matrix for all platforms
    - Release workflow exists (dry-run tested) but not yet cutting releases
    """,
    issue_type="epic",
    priority=0,
    deps=[dep(f"{PREFIX}-root", "parent-child")],
    labels=["surface:infra", "tier:sonnet", "risk:low", "fed:safe"],
)

add(
    f"{PREFIX}-e1.1",
    "Bootstrap Go module with layout matching gvid conventions",
    """
    # Goal
    Create the Go module with the directory structure matching the proven
    gvid / gastown-viewer-intent layout. This layout has community precedent
    and is how most accepted viewers are organized.

    # Inputs
    - Repo created at github.com/YOU/gemba with MIT license
    - Go 1.23+ available

    # Outputs
    Directory layout:
    ```
    cmd/gemba/                   # Cobra root, `gemba serve`, `gemba doctor`
    internal/adapter/gt/      # wraps gt CLI
    internal/adapter/bd/      # wraps bd CLI
    internal/adapter/fs/      # filesystem reads
    internal/api/             # HTTP handlers, SSE hub
    internal/model/           # shared domain types
    internal/events/          # .events.jsonl tailer
    internal/auth/            # token, TLS
    internal/config/          # config loader
    web/                      # Vite + React + TS (stub for now)
    embed.go                  # go:embed web/dist
    Makefile
    ```

    # Definition of Done
    - `go build ./...` clean
    - `go vet ./...` clean
    - Every package has a `doc.go` with one-line purpose comment
    - README.md in repo root stub with install instructions
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e1", "parent-child")],
    labels=["surface:backend", "surface:infra", "tier:haiku",
            "risk:low", "fed:safe"],
)

add(
    f"{PREFIX}-e1.2",
    "Cobra CLI skeleton: `gemba serve`, `gemba doctor`, `gemba version`",
    """
    # Goal
    Create the three top-level subcommands. `serve` is the main entry point,
    `doctor` checks prerequisites, `version` prints build info injected at
    link time.

    # Inputs
    - gm-e1.1 complete (repo structure exists)

    # Outputs
    - `cmd/gemba/main.go` wires Cobra root and subcommands
    - `cmd/gemba/serve.go` with flags: `--listen`, `--port`, `--town`, `--city`,
      `--open`, `--auth`, `--tls-cert`, `--tls-key`,
      `--dangerously-skip-permissions` (flag name is deliberate; see
      gm-root locked decision #7). `--town` is the v1 primary path;
      `--city` is designed-for Gas City GA.
    - `cmd/gemba/doctor.go` checks: gt binary (v1 primary) OR gc binary
      (designed-for) found, bd binary found, current directory is a
      Gas Town HQ (`.gt/` or `rigs/`) or a Gas City workspace (`.gc/`
      or `city.toml`), ports available
    - `cmd/gemba/version.go` prints version/commit/date injected via -ldflags

    # Definition of Done
    - `gemba --help` renders cleanly
    - `gemba doctor` in a non-workspace directory exits 1 with helpful error
    - `gemba doctor` in ~/gt (or, post-GC-GA, ~/my-city) with gt/gc+bd
      installed exits 0
    - `gemba version` shows real build info in CI builds
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e1.1")],
    labels=["surface:backend", "tier:haiku", "risk:low", "fed:safe"],
)

add(
    f"{PREFIX}-e1.3",
    "go:embed the SPA dist directory, serve from binary",
    """
    # Goal
    Bundle the built Vite output into the binary so there is exactly one
    artifact to install. Match gvid's approach.

    # Inputs
    - gm-e1.2 complete

    # Outputs
    - `embed.go` at repo root uses `//go:embed all:web/dist` to embed files
    - `internal/api/static.go` serves embedded FS with correct MIME types and
      a SPA fallback route (unknown paths -> index.html)
    - Dev mode: when `GEMBA_DEV=1`, serve from disk instead for HMR workflow

    # Definition of Done
    - Stripped binary under 30 MB
    - `curl http://localhost:7666/` returns index.html
    - `curl http://localhost:7666/convoys/gm-abc` also returns index.html
      (SPA fallback works)
    - `curl http://localhost:7666/assets/index-xxx.js` returns correct JS
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e1.2")],
    labels=["surface:backend", "layer:api", "tier:sonnet",
            "risk:low", "fed:safe"],
)

add(
    f"{PREFIX}-e1.4",
    "Scaffold Vite + React + TypeScript + Tailwind + shadcn/ui",
    """
    # Goal
    Set up the frontend toolchain inside `web/` with all the Atlassian-style
    ingredients ready to go.

    # Inputs
    - gm-e1.1 complete

    # Outputs
    - `web/package.json` with: react@18+, react-dom, typescript, vite,
      @vitejs/plugin-react, tailwindcss, autoprefixer, postcss, @tanstack/react-query,
      @tanstack/react-table, @dnd-kit/core, @dnd-kit/sortable, reactflow,
      cmdk, lucide-react, zod, tailwind-merge, clsx, class-variance-authority
    - shadcn/ui initialized with `npx shadcn@latest init` using default dark
      theme, output path `web/src/components/ui`
    - `web/src/app/App.tsx` renders a placeholder dashboard shell with
      sidebar, topbar, main content area
    - Vite config has dev proxy for `/api/*` and `/events/*` -> `localhost:7666`

    # Definition of Done
    - `pnpm --prefix web install` clean
    - `pnpm --prefix web build` produces `web/dist`
    - `pnpm --prefix web dev` serves on :5173 and proxies API calls
    - Tailwind classes work; shadcn Button renders correctly
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e1.1")],
    labels=["surface:frontend", "tier:sonnet", "risk:low", "fed:safe"],
)

add(
    f"{PREFIX}-e1.5",
    "Makefile: `make dev`, `make build`, `make release`",
    """
    # Goal
    Ergonomic developer workflow. `make dev` should Just Work.

    # Inputs
    - gm-e1.3 and gm-e1.4 complete

    # Outputs
    Targets:
    - `make dev` — runs air (or reflex) for Go hot reload AND vite dev server
      in parallel; both survive until Ctrl-C kills both
    - `make build` — runs `pnpm --prefix web build` then `go build -o bc ./cmd/gemba`
    - `make test` — `go test ./...` and `pnpm --prefix web test`
    - `make lint` — `golangci-lint run` and `pnpm --prefix web lint`
    - `make release` — cross-compiles for all platforms via goreleaser config
    - `make clean` — removes `web/dist`, `gemba`, build artifacts

    # Definition of Done
    - Fresh clone + `make dev` produces working localhost:5173 with live API
    - `make build` produces a single binary that runs standalone
    - `make test`, `make lint` both pass on clean tree
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e1.3"), dep(f"{PREFIX}-e1.4")],
    labels=["surface:infra", "tier:sonnet", "risk:low", "fed:safe"],
)

add(
    f"{PREFIX}-e1.6",
    "GitHub Actions CI: lint, test, build matrix",
    """
    # Goal
    Green CI on every PR. Build matrix covers all release targets.

    # Inputs
    - gm-e1.5 complete

    # Outputs
    - `.github/workflows/ci.yml`: lint, test, build on
      ubuntu-latest/macos-latest/windows-latest, Go 1.23 + 1.24
    - `.github/workflows/release.yml`: goreleaser on tag push (disabled until
      gm-e8, but present and dry-run tested)
    - Dependabot config for gomod and npm

    # Definition of Done
    - CI badge in README reads green on main
    - PR workflow completes in under 5 minutes
    - Release workflow dry-run produces artifacts in `dist/`
    """,
    priority=1,
    deps=[dep(f"{PREFIX}-e1.5")],
    labels=["surface:infra", "tier:haiku", "risk:low", "fed:safe"],
)


# ======================================================================
# PHASE 2 — ADAPTERS + CORE API (the hard middle)
# ======================================================================

add(
    f"{PREFIX}-e2",
    "Phase 2: Adapters + Core API",
    """
    Build the three adapter layers (gt, bd, fs) and the REST + SSE surface
    the frontend will consume. This is where data-model mistakes are
    expensive, so tests and contract stability matter.

    # Goal
    End of this phase: the frontend can fetch a typed list of rigs, agents,
    convoys, beads from an endpoint; subscribe to SSE events; and submit
    mutations that round-trip through the real gt/bd binaries.

    # Definition of Done
    - All adapters have unit tests with mocked process execution
    - Integration test harness that spins up a real gt + bd in a tmpdir
    - OpenAPI spec published at `/api/openapi.json`
    - TypeScript types codegenned from Go structs via a build step
    """,
    issue_type="epic",
    priority=0,
    deps=[dep(f"{PREFIX}-root", "parent-child"), dep(f"{PREFIX}-e1")],
    labels=["surface:backend", "tier:sonnet", "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e2.1",
    "Domain model (`internal/model/`) with federation-safe identity",
    """
    # Goal
    Define the shared domain types. Every identifier is a typed newtype, not
    a bare string. Rigs and beads carry explicit town+prefix+id triples so
    future Wasteland federation works without retrofit.

    # Inputs
    - Locked decision #4 (federation-readiness)

    # Outputs
    Types in `internal/model/`:
    - `TownID string` — hq/town identifier (empty for current town)
    - `RigName string`, `AgentID`, `BeadID`, `ConvoyID`, `MolID`
    - `Bead` — id, town, prefix, type, priority, status, assignee, title,
      description, labels, deps, timestamps
    - `Dep` — depends_on, type (blocks/related/parent-child/discovered-from/
      waits-for/replies-to/conditional-blocks)
    - `Agent` — id, role, rig, status (idle/active/suspended/stuck/zombie),
      session_name, last_heartbeat, current_bead
    - `Convoy` — id, title, status, members[], completion counts
    - `Rig` — name, repo_path, beads_prefix, agents[]
    - `Molecule` — id, formula, steps[], checkpoints

    Every type has `Origin() TownID` method; for local this returns "".

    # Definition of Done
    - `go doc` for every exported type reads well
    - No string IDs anywhere in `internal/` outside of model package
    - `go test ./internal/model/...` covers type round-trip through JSON
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e2", "parent-child")],
    labels=["surface:backend", "surface:protocol", "tier:opus",
            "risk:high", "fed:bridge"],
)

add(
    f"{PREFIX}-e2.2",
    "`bd` adapter: wrap every mutation + `--json` read command",
    """
    # Goal
    A typed Go wrapper over the `bd` CLI. Every call shells out and parses
    `--json`. Surface covers: list, show, ready, create, update, close, dep
    add/remove, label add/remove, comment add, search, stats, dolt push/pull.

    # Inputs
    - gm-e2.1 complete
    - Running `bd version` returns >= 0.60.0

    # Outputs
    - `internal/adapter/bd/client.go`: `type Client struct { bin string; dir string }`
    - `Client.List(ctx, filter)` -> []Bead
    - `Client.Ready(ctx)` -> []Bead
    - `Client.Show(ctx, id)` -> Bead (with deps, children, comments)
    - `Client.Create(ctx, input)` -> Bead (uses `bd create` with flags)
    - `Client.Update(ctx, id, patch)` -> Bead
    - `Client.Close(ctx, id, reason)` -> Bead
    - `Client.DepAdd(ctx, from, to, kind)` -> error
    - `Client.Stats(ctx)` -> Stats
    - Context cancellation kills the subprocess
    - Errors are classified: NotFound, Conflict, SchemaMismatch, CLINotFound
    - A process pool so we don't fork 50 `bd` invocations per dashboard load

    # References
    - beads/docs/COMMUNITY_TOOLS.md warns: never read JSONL or Dolt directly;
      always go through `bd --json`
    - Prior art: @herbcaudill/beads-sdk (TypeScript) has the right surface shape

    # Definition of Done
    - Unit tests mock `exec.Cmd` and verify argv construction
    - Integration test uses real bd in tmpdir, exercises every method
    - Known-fragile cases (concurrent writes, daemon offline) have explicit
      test coverage
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e2.1")],
    labels=["surface:backend", "layer:adapter-bd", "tier:sonnet",
            "risk:high", "fed:safe"],
)

add(
    f"{PREFIX}-e2.3",
    "`gt` adapter: wrap orchestration commands",
    """
    # Goal
    Typed wrapper over `gt` CLI. Covers the orchestration surface: status,
    agents, sling, mail, convoy (list/create/close/feed/watch), escalate,
    scheduler, rig list/add, seance.

    # Inputs
    - gm-e2.1 complete
    - `gt version` >= 0.12.0

    # Outputs
    - `internal/adapter/gt/client.go`:
      - `Client.Status(ctx)` -> TownStatus
      - `Client.Agents(ctx)` -> []Agent
      - `Client.Sling(ctx, bead, rig, opts)` -> error
      - `Client.ConvoyList(ctx)` -> []Convoy
      - `Client.ConvoyCreate(ctx, title, beads, opts)` -> Convoy
      - `Client.ConvoyClose(ctx, id, force bool)` -> error
      - `Client.MailInbox(ctx, addr)` -> []Message
      - `Client.MailSend(ctx, to, subject, body)` -> error
      - `Client.Escalate(ctx, severity, desc)` -> Escalation
      - `Client.Nudge(ctx, agent, msg)` -> error
      - `Client.Handoff(ctx, agent, opts)` -> error
      - `Client.RigList(ctx)` -> []Rig

    # Definition of Done
    - Same test pattern as bd adapter (mocks + real integration)
    - Every method has a doc comment linking to the underlying gt subcommand
    - Errors distinguish: AgentStuck, ConvoyEmpty, RigNotFound, daemon down
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e2.1")],
    labels=["surface:backend", "layer:adapter-gt", "tier:sonnet",
            "risk:high", "fed:safe"],
)

add(
    f"{PREFIX}-e2.3b",
    "`gc` adapter: Gas City stub (designed, not primary yet)",
    """
    # Goal
    Build and stub the Gas City adapter alongside the Gas Town adapter,
    tracking the Gas City CLI surface as it stabilizes. Not the v1 runtime
    target — this adapter becomes primary when Gas City reaches GA.

    Why stub this now, not later: if we don't keep `internal/adapter/gc/`
    in active development, the Gas City transition turns into a rewrite.
    We want the Gas City shape informing our decisions continuously, not
    just at the end.

    # Inputs
    - gm-e2.1 complete
    - gm-e2.3 (gt adapter) complete — same shape, so gt is the reference
    - Access to gastownhall/gascity README + `gc` CLI for smoke testing

    # Outputs
    - `internal/adapter/gc/client.go` with the same interface as the gt
      client, but dispatching to `gc` subcommands:
      - `Client.Status(ctx)` -> WorkspaceStatus   (gc status)
      - `Client.Agents(ctx)` -> []Agent           (gc session list + agents/*.json)
      - `Client.RigList(ctx)` -> []Rig            (gc rig list)
      - `Client.ConfigExplain(ctx, rig)` -> Resolved  (gc config explain)
      - `Client.SessionPeek(ctx, name)` -> string (gc session peek)
      - `Client.TopoList(ctx)` -> []Pack          (gc topo list)
    - An adapter selector in `internal/adapter/` that picks gt vs gc based
      on workspace detection and `--city` / `--town` flags
    - Smoke-test integration against a Gas City alpha install (skipped in
      CI when `gc` isn't present)

    # Definition of Done
    - Interface parity with gt client where the operations overlap
    - Gas City-specific operations (config explain, topo list) implemented
      against alpha `gc`
    - Integration skip-if-missing, doesn't break CI without Gas City
    - Adapter selector correctly picks gt for ~/gt workspaces and gc for
      ~/my-city workspaces
    - Doc comment in `adapter/gc/doc.go` makes clear this is a forward-
      looking stub, primary at GC GA
    """,
    priority=2,
    deps=[dep(f"{PREFIX}-e2.3")],
    labels=["surface:backend", "layer:adapter-gc", "tier:sonnet",
            "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e2.4",
    "Filesystem adapter: `~/gt/` runtime state reader (`.gc/` designed-for)",
    """
    # Goal
    Low-latency reads of workspace state files that rarely change and
    don't need a CLI round-trip. For v1, this targets Gas Town's `~/gt/`
    layout — reads routes.jsonl, daemon.json, and per-rig .events.jsonl.
    The adapter is designed to handle Gas City's `.gc/` layout too so
    the v1 code survives the GC GA transition unchanged.

    # Inputs
    - gm-e2.1 complete
    - A readable Gas Town HQ (`~/gt/`) — v1 target
    - (When available) a readable Gas City workspace (~/my-city with
      .gc/ and city.toml) for forward-looking testing

    # Gas Town layout (primary in v1)
    ~/gt/
      .gt/
        daemon.json            — scheduler state
      .beads/
        routes.jsonl           — prefix -> rig directory map
      <rig>/
        .events.jsonl          — per-rig event log (tail via fsnotify)

    # Gas City layout (designed-for, becomes primary at GC GA)
    ~/my-city/
      city.toml                — desired config (watch for drift display)
      .gc/
        controller.lock        — flock marker; DO NOT attempt to acquire
        controller.sock        — unix socket; DO NOT connect (gc's private)
        agents/<name>.json     — live agent registry: session id, pid, provider
        events.jsonl           — append-only event log
      rigs/<rig>/
        rig.toml
        .beads/                — read via bd adapter, not here

    # Outputs
    - `internal/adapter/fs/routes.go` — parses `.beads/routes.jsonl`
      (Gas Town today; same file shape expected in Gas City)
    - `internal/adapter/fs/daemon.go` — parses `.gt/daemon.json` for
      Gas Town scheduler state
    - `internal/adapter/fs/events.go` — tails events via fsnotify; one
      code path works for per-rig .events.jsonl (GT) and global
      events.jsonl (GC); handles rotation and truncation
    - `internal/adapter/fs/agents.go` — designed-for Gas City: reads
      .gc/agents/*.json with shared flock. Stubbed in v1 against
      `gt agents --json` output cached to disk so the code path exists
    - `internal/adapter/fs/citytoml.go` — designed-for Gas City: parses
      city.toml into typed desired-state struct. Stubbed in v1 against
      Gas Town's implicit role set so gm-e5.7 has a desired-state source
    - `internal/adapter/fs/watch.go` — fsnotify watcher with 200ms
      debounce; watches daemon.json + per-rig events today, city.toml
      + global events at GC GA

    # Definition of Done
    - Event tailer survives file rotation in integration test
    - Never connects to controller.sock, never acquires controller.lock
      exclusively (shared locks only), never writes to .gt/ or .gc/
    - Debounced watch emits within 250ms of a config file change
    - Covered by unit tests using a fake filesystem, exercising both
      `~/gt/` and `~/my-city/` layouts
    - Workspace detection logic correctly identifies which layout is
      present and dispatches to the right read paths
    """,
    priority=1,
    deps=[dep(f"{PREFIX}-e2.1")],
    labels=["surface:backend", "layer:adapter-fs", "layer:controller-watch",
            "tier:sonnet", "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e2.5",
    "SSE hub in `internal/events/`",
    """
    # Goal
    One-way server-push fanout. Frontend subscribes once; any event source
    (event-file tailer, mutation completion, periodic pulse) can publish.
    Matches the gt dashboard v0.10 SSE pattern.

    # Inputs
    - gm-e2.4 complete (event source available)

    # Outputs
    - `internal/events/hub.go` — Hub with Subscribe/Unsubscribe/Publish
    - `internal/events/types.go` — Event types: AgentStateChange,
      BeadCreated/Updated/Closed, ConvoyProgress, EscalationRaised,
      MailReceived
    - Each subscriber gets a buffered channel; slow consumers are dropped
      with a log warning, not blocked
    - Heartbeat event every 15s so proxies don't kill idle connections

    # Definition of Done
    - Unit test with 100 concurrent subscribers sees every event
    - Slow-subscriber test verifies no backpressure on the hub
    - Integration test: make a bead via bd adapter, observe SSE event
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e2.4")],
    labels=["surface:backend", "layer:events", "tier:sonnet",
            "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e2.6",
    "HTTP API layer with chi, OpenAPI, TS codegen",
    """
    # Goal
    REST surface over the adapters. OpenAPI 3.1 spec checked in. TypeScript
    types generated from Go structs so the frontend can't drift.

    # Inputs
    - gm-e2.2, gm-e2.3, gm-e2.4, gm-e2.5 all complete

    # Outputs
    Endpoints (namespaced under `/api/`):
    - `GET /api/town` — TownStatus
    - `GET /api/rigs` — []Rig
    - `GET /api/agents` — []Agent; `GET /api/agents/:id` — Agent with recent events
    - `POST /api/agents/:id/nudge` — send nudge
    - `POST /api/agents/:id/handoff` — trigger handoff
    - `GET /api/convoys` — []Convoy; `GET /api/convoys/:id` — Convoy with beads
    - `POST /api/convoys` — create; `POST /api/convoys/:id/close` — close
    - `POST /api/convoys/:id/feed` — feed bead to convoy
    - `GET /api/beads` — query with filters (status, priority, type, label,
       assignee, prefix)
    - `GET /api/beads/:id` — Bead with children, deps, comments
    - `POST /api/beads` — create
    - `PATCH /api/beads/:id` — update
    - `POST /api/beads/:id/close` — close with reason
    - `POST /api/beads/:id/deps` — add dep
    - `DELETE /api/beads/:id/deps/:target` — remove dep
    - `POST /api/beads/:id/sling` — sling to rig
    - `GET /api/beads/ready` — ready list
    - `GET /api/mail/inbox/:addr` — mail
    - `POST /api/mail` — send
    - `GET /api/escalations` — list
    - `POST /api/escalations/:id/ack` — ack
    - `GET /api/formulas` — list formulas
    - `POST /api/formulas/:id/cook` — cook
    - `POST /api/molecules/:id/pour` — pour
    - `GET /events` — SSE stream (subscribe with query filter)
    - `GET /api/openapi.json` — spec
    - `GET /api/health` — liveness
    - `GET /api/version` — build info

    TS codegen target: `web/src/lib/api-types.ts` via tygo or
    github.com/deepmap/oapi-codegen.

    # Definition of Done
    - `make spec` regenerates openapi.json deterministically
    - `make codegen` regenerates TS types; CI fails if not committed
    - Every endpoint has request/response tests
    - `curl http://localhost:7666/api/openapi.json | jq .info.version` works
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e2.2"), dep(f"{PREFIX}-e2.3"),
          dep(f"{PREFIX}-e2.4"), dep(f"{PREFIX}-e2.5")],
    labels=["surface:backend", "surface:protocol", "layer:api",
            "tier:opus", "risk:high", "fed:bridge"],
)

add(
    f"{PREFIX}-e2.7",
    "Mutation confirmation gating with --dangerously-skip-permissions",
    """
    # Goal
    Every mutation endpoint returns 409 Confirmation Required unless the
    request carries a `X-GEMBA-Confirm: <token>` header. Frontend shows a
    confirmation dialog and retries with the token. The session flag
    `--dangerously-skip-permissions` (copied verbatim from Claude Code,
    see gm-root locked decision #5) disables the gating server-wide for
    that session.

    # Inputs
    - gm-e2.6 complete

    # Outputs
    - `internal/api/confirm.go` middleware
    - Token is a single-use nonce tied to the exact request payload hash so
      token replay against a different payload fails
    - Audit log: every confirmed mutation writes a line to `~/.bc/audit.log`
      with timestamp, user (if auth enabled), endpoint, bead ID, argv hash

    # Definition of Done
    - Mutation without header -> 409 with a nonce for that payload
    - Mutation with matching header -> 200
    - Mutation with mismatched payload -> 409 (replay protection)
    - `gemba serve --dangerously-skip-permissions` logs a prominent warning
      at startup and bypasses the middleware
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e2.6")],
    labels=["surface:backend", "layer:api", "layer:auth",
            "tier:opus", "risk:high", "fed:safe"],
)


# ======================================================================
# PHASE 3 — AUTH & REMOTE ACCESS
# ======================================================================

add(
    f"{PREFIX}-e3",
    "Phase 3: Auth & Remote Access",
    """
    Make remote access possible without making it dangerous. Default posture
    stays localhost-only. Opt-in token auth. Opt-in TLS. Clear error
    messages when configuration is inconsistent.

    # Goal
    `gemba serve` alone binds 127.0.0.1:7666 with no auth. Adding `--listen
    0.0.0.0` without `--auth` is an explicit error, not a footgun.

    # Definition of Done
    - Binding a non-loopback interface without auth exits 1 with a helpful
      error message
    - Token auth flow documented and tested
    - TLS flow documented and tested
    - OIDC stubbed but not required for v1
    """,
    issue_type="epic",
    priority=0,
    deps=[dep(f"{PREFIX}-root", "parent-child"), dep(f"{PREFIX}-e2")],
    labels=["surface:backend", "layer:auth", "tier:opus",
            "risk:high", "fed:safe"],
)

add(
    f"{PREFIX}-e3.1",
    "Bind policy: localhost-only default, explicit gate for remote",
    """
    # Goal
    Make it structurally impossible to accidentally expose Gemba to
    the network without auth. This is the single most important auth
    decision.

    # Rules
    - `gemba serve` default bind is `127.0.0.1:7666`
    - `--listen 0.0.0.0[:port]` requires `--auth` to be one of
      `token` | `oidc`. Otherwise: startup error with message
      "Refusing to bind non-loopback interface without authentication.
       Pass --auth=token to generate a token, or keep the default bind."
    - `--listen` accepts any interface; the loopback check is on the
      resolved IP, not the string

    # Outputs
    - `internal/config/bind.go` with the policy
    - Unit tests cover: localhost + no auth = ok; localhost + auth = ok;
      0.0.0.0 + no auth = error; 0.0.0.0 + auth = ok; `192.168.x.x` + no
      auth = error

    # Definition of Done
    - `gemba serve --listen 0.0.0.0` without auth prints the exact error
      above and exits 1
    - Docs page for "accessing Gemba remotely" is accurate
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e3", "parent-child")],
    labels=["surface:backend", "layer:auth", "tier:opus",
            "risk:high", "fed:safe"],
)

add(
    f"{PREFIX}-e3.2",
    "Token auth: generate, store hashed, verify via header or cookie",
    """
    # Goal
    Simple bearer-token auth. One secret per deployment.

    # Inputs
    - gm-e3.1 complete

    # Outputs
    - `gemba serve --auth token` on first run:
      - generates a 256-bit random token
      - prints it once to stdout with clear instructions
      - stores argon2id hash at `~/.bc/tokens/primary` with mode 0600
    - Subsequent runs read the hash and verify incoming tokens
    - Accepts `Authorization: Bearer <token>` OR signed cookie
    - Rotating tokens: `bc auth rotate` generates a new one, invalidates
      the old after a configurable grace period
    - Session cookies are HttpOnly, Secure (when TLS), SameSite=Strict

    # Definition of Done
    - Token displayed ONCE at generation; never logged or stored plaintext
    - Wrong token -> 401 with generic message (no user enumeration)
    - Token rotation covered by integration test
    - Audit log records auth attempts
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e3.1")],
    labels=["surface:backend", "layer:auth", "tier:opus",
            "risk:high", "fed:safe"],
)

add(
    f"{PREFIX}-e3.3",
    "TLS: `--tls-cert`/`--tls-key` OR `--tls-self-signed`",
    """
    # Goal
    HTTPS available without requiring users to have real certificates. Self-
    signed flow generates a cert on first run and prints a fingerprint.

    # Inputs
    - gm-e3.1 complete

    # Outputs
    - Custom cert/key paths: use them, log the subject and expiry
    - `--tls-self-signed`: generate at `~/.bc/tls/self-signed.{crt,key}`,
      valid 1 year, include localhost + 127.0.0.1 + resolved bind IP in SAN
    - Print SHA-256 fingerprint at startup so users can pin in their browser
    - HTTP-on-TLS-port returns a redirect, not a hang

    # Definition of Done
    - curl with `--cacert ~/.bc/tls/self-signed.crt` works cleanly
    - Fingerprint in CLI output matches the one Chrome/Firefox shows
    - `openssl x509 -in self-signed.crt -noout -text` shows correct SANs
    """,
    priority=1,
    deps=[dep(f"{PREFIX}-e3.1")],
    labels=["surface:backend", "layer:auth", "tier:sonnet",
            "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e3.4",
    "OIDC auth adapter (stubbed for v1, shipped in v1.1)",
    """
    # Goal
    Not required for v1 release. Ship the interface and a mock provider so
    later work can slot in real providers (GitHub, Google, Okta) without
    a rewrite.

    # Inputs
    - gm-e3.2 complete

    # Outputs
    - `internal/auth/oidc.go` with `type Provider interface` covering
      discovery, token exchange, userinfo
    - Mock provider usable in tests
    - Design doc in `docs/auth-oidc.md` with provider-selection rubric

    # Definition of Done
    - Interface compiles and has mock implementation
    - Real providers tracked as `gm-e3.4.1` (GitHub) and `gm-e3.4.2`
      (Google) as discovered-from work for v1.1
    """,
    priority=3,
    deps=[dep(f"{PREFIX}-e3.2")],
    labels=["surface:backend", "layer:auth", "tier:opus",
            "risk:medium", "fed:safe"],
)


# ======================================================================
# PHASE 4 — BEADS & AGENTS UI
# ======================================================================

add(
    f"{PREFIX}-e4",
    "Phase 4: Beads & Agents UI — first end-to-end user value",
    """
    # Goal
    A user can open Gemba, see every bead across every rig, filter,
    sort, open a detail drawer, and inspect every agent's live status. This
    phase is intentionally read-mostly; mutations land in phase 5.

    # Definition of Done
    - Jira-style work grid with virtualized rows, column toggles, saved views
    - Agent cards that update live via SSE
    - Bead detail drawer with deps, comments, history
    - Global cmdk palette finds beads, agents, rigs, convoys
    """,
    issue_type="epic",
    priority=0,
    deps=[dep(f"{PREFIX}-root", "parent-child"), dep(f"{PREFIX}-e2")],
    labels=["surface:frontend", "area:beads", "area:agents",
            "tier:sonnet", "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e4.1",
    "App shell: sidebar, topbar, routing, theme",
    """
    # Goal
    The chrome every other feature lives inside. Mirror Jira's layout:
    collapsible left sidebar for navigation, top bar for global search +
    actions + user menu.

    # Inputs
    - gm-e1.4 complete (scaffolding)

    # Outputs
    - Routes: /, /beads, /convoys, /agents, /graph, /mail, /insights,
      /rigs, /settings
    - React Router v6 with lazy-loaded routes
    - Dark theme default, light theme toggle, system preference respected
    - Global error boundary with useful error card, not a blank page
    - Offline banner when the SSE connection drops

    # Definition of Done
    - Keyboard nav works: `g b` jumps to beads, `g c` to convoys, etc.
      (match gmail/linear conventions)
    - Lighthouse accessibility score >= 95
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e4", "parent-child")],
    labels=["surface:frontend", "tier:sonnet", "risk:low", "fed:safe"],
)

add(
    f"{PREFIX}-e4.2",
    "react-query data layer with SSE-driven invalidation",
    """
    # Goal
    One consistent data layer. Queries invalidate automatically when an SSE
    event says their data changed. Mutations optimistic-update and roll back
    on failure.

    # Inputs
    - gm-e4.1, gm-e2.6 complete

    # Outputs
    - `web/src/lib/query.ts` — QueryClient config, retry/stale/gc defaults
    - `web/src/lib/sse.ts` — EventSource wrapper with reconnect and backoff
    - `web/src/lib/invalidation.ts` — map event types -> query keys to bust
    - Typed query hooks per resource: `useBeads`, `useBead(id)`, `useAgents`,
      `useConvoys`, etc.
    - Typed mutation hooks with confirmation flow integrated

    # Definition of Done
    - Creating a bead via mutation appears in the beads list within 500ms
    - Closing the SSE stream triggers an offline banner; reopening works
    - React DevTools shows no stuck pending queries under normal ops
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e4.1"), dep(f"{PREFIX}-e2.6")],
    labels=["surface:frontend", "tier:opus", "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e4.3",
    "Beads work grid (Jira-style) with @tanstack/react-table",
    """
    # Goal
    The headline screen. Thousands of beads browsable smoothly.

    # Inputs
    - gm-e4.2 complete

    # Outputs
    - Virtualized table via react-table + react-virtual
    - Columns: ID, title, status, priority, type, assignee, rig, age,
      updated, labels (chips)
    - Column toggles persisted to localStorage
    - Filter bar: status, priority, type, rig, assignee, labels (multi)
    - Text search across title + description
    - Saved views: name + filter set, persisted server-side via a small
      `GET/POST /api/views` endpoint (add as gm-e4.3.1 if missing)
    - Row click -> detail drawer (gm-e4.5)

    # Definition of Done
    - 10k bead dataset scrolls at 60fps on a mid-range laptop
    - All keyboard shortcuts from Jira/Linear work (j/k to move, x to
      select, return to open)
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e4.2")],
    labels=["surface:frontend", "area:beads", "tier:sonnet",
            "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e4.4",
    "Agents dashboard with live tiles",
    """
    # Goal
    One glance tells you the health of every agent. Group by rig, show
    role (Mayor, Witness, Refinery, Polecat, Dog, Crew), status, current
    bead, last heartbeat.

    # Inputs
    - gm-e4.2 complete

    # Outputs
    - Tiles with live pulse indicator (green/amber/red/grey)
    - Click -> agent drawer: recent events, current tmux session name,
      nudge + handoff buttons (gated by confirm middleware)
    - Problems mode: filter to stuck/zombie/escalating agents only
      (matches `gt feed --problems`)

    # Definition of Done
    - Nudging an agent here produces an event in the agent's tmux session
    - Heartbeat >3min shows amber; >10min shows red
    - Handoff button spawns a confirmation dialog with the replacement
      agent's name preview
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e4.2")],
    labels=["surface:frontend", "area:agents", "tier:sonnet",
            "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e4.5",
    "Bead detail drawer with tabs",
    """
    # Goal
    Everything you'd want to know about a bead, one click away, without
    losing context on the list page.

    # Inputs
    - gm-e4.3 complete

    # Outputs
    Side drawer, not modal. Tabs:
    - Overview: description (markdown rendered), metadata, labels
    - Dependencies: blocks/blocked-by/parent/children/discovered-from;
      mini graph embed
    - Activity: comments, status changes, assignment changes
    - History: Dolt-backed diff of cell changes (read from bd)
    - Convoys: list of convoys this bead is part of
    Actions in the drawer header: close, update priority, reassign,
    sling to rig, add dep, add label, add comment

    # Definition of Done
    - Opening the drawer preserves scroll position on the underlying list
    - Editing a field shows confirmation dialog (unless yolo mode)
    - Keyboard: `esc` closes, `e` enters edit mode
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e4.3")],
    labels=["surface:frontend", "area:beads", "tier:sonnet",
            "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e4.6",
    "Global cmdk command palette",
    """
    # Goal
    `cmd/ctrl + k` anywhere. Finds beads by ID or title, agents by name,
    convoys, rigs. Also exposes verb-first commands: "Create bead",
    "Nudge mayor", "Open convoy".

    # Inputs
    - gm-e4.1 complete

    # Outputs
    - cmdk integration with keyboard-first affordances
    - Recent items pinned at top
    - Fuzzy match on title + description + labels
    - Type-ahead for bead IDs (tolerates missing prefix)
    - Actions open the right screen or trigger the right mutation

    # Definition of Done
    - `cmd-k -> "bc-" -> first 5 matches` in under 100ms on 10k beads
    - Every major action reachable without a mouse
    """,
    priority=1,
    deps=[dep(f"{PREFIX}-e4.1")],
    labels=["surface:frontend", "area:search", "tier:sonnet",
            "risk:low", "fed:safe"],
)


# ======================================================================
# PHASE 5 — BOARDS & MUTATIONS
# ======================================================================

add(
    f"{PREFIX}-e5",
    "Phase 5: Boards & Mutations — Kanban, convoys, full write path",
    """
    # Goal
    The Atlassian heart of the product: a drag-drop Kanban board per
    convoy, a backlog board across rigs, and a full-fat create/update flow.
    Every mutation goes through the confirmation middleware from gm-e2.7
    unless yolo mode is on.

    # Definition of Done
    - Drag a bead between columns -> status change round-trips through bd
    - Create convoy from multi-selected beads -> convoy appears live
    - Bulk actions: select rows in grid, assign, label, close
    - Every mutation auditable in ~/.bc/audit.log
    """,
    issue_type="epic",
    priority=0,
    deps=[dep(f"{PREFIX}-root", "parent-child"), dep(f"{PREFIX}-e4")],
    labels=["surface:frontend", "area:convoys", "area:beads",
            "tier:sonnet", "risk:high", "fed:safe"],
)

add(
    f"{PREFIX}-e5.1",
    "Kanban board component with @dnd-kit",
    """
    # Goal
    Reusable board component with typed columns and typed cards. Used for
    convoy boards, backlog, and the per-rig view.

    # Inputs
    - gm-e4.2 complete

    # Outputs
    - `web/src/features/board/Board.tsx` — generic, configurable columns
    - `Card` component matches bead detail drawer summary
    - Drag-drop with accessibility (keyboard: space to grab, arrows to move,
      space to drop; matches dnd-kit defaults)
    - Optimistic update with rollback on mutation error
    - Empty state, loading skeleton, error state all handled

    # Definition of Done
    - Screen reader announces drag start, drop target, drop result
    - Board renders 500 cards per column without jank
    - All interactions work with keyboard only
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e5", "parent-child"), dep(f"{PREFIX}-e4.2")],
    labels=["surface:frontend", "tier:opus", "risk:high", "fed:safe"],
)

add(
    f"{PREFIX}-e5.2",
    "Convoy board view",
    """
    # Goal
    Open a convoy, see all its beads in Pending/Active/Blocked/Done columns.
    Drag to change status.

    # Inputs
    - gm-e5.1 complete

    # Outputs
    - `/convoys/:id` route uses the board component
    - Convoy header shows progress bar, title, linked rig(s), members count
    - Feed button adds more beads (multi-select picker)
    - Close button closes the convoy (with safety check -> force flag on
      re-confirm, matching `gt convoy close --force`)

    # Definition of Done
    - Drag between columns calls `bd update --status` via adapter
    - Closing empty convoy works without force; closing non-empty requires
      the second confirmation
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e5.1")],
    labels=["surface:frontend", "area:convoys", "tier:sonnet",
            "risk:high", "fed:safe"],
)

add(
    f"{PREFIX}-e5.3",
    "Backlog board across all rigs",
    """
    # Goal
    One place to see everything `bd ready` across all rigs, grouped by rig,
    prioritized. Agents can be slung from here.

    # Inputs
    - gm-e5.1 complete

    # Outputs
    - `/beads` route with a "board" view toggle alongside the grid
    - Columns: Ready, In Progress, Blocked, Done (by rig groups)
    - Hover action: "Sling to <rig>" with rig picker
    - Filter chips persist between grid and board views

    # Definition of Done
    - Slinging here produces a tmux session in the target rig within 30s
    - Empty "Ready" column shows a helpful empty state, not a blank column
    """,
    priority=1,
    deps=[dep(f"{PREFIX}-e5.1")],
    labels=["surface:frontend", "area:beads", "tier:sonnet",
            "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e5.4",
    "Bead creation flow with smart defaults",
    """
    # Goal
    Creating a bead is fast. Type, priority, assignee, rig are pre-filled
    based on context (the rig you're on, the epic you're inside).

    # Inputs
    - gm-e4.5 complete

    # Outputs
    - Modal form reachable by `c` anywhere, or "+" button
    - Fields: title (required), description (markdown editor), type (radio),
      priority (radio), rig (select), parent (typeahead bead picker), deps
      (multi-select), labels (tag picker using the taxonomy from README)
    - Template picker: "Bug", "Feature", "Spike" fill the description with
      a minimal template

    # Definition of Done
    - Creating from inside an epic's page pre-selects parent
    - Label picker enforces at least one `surface:*` and one `tier:*`
    - Markdown editor has fence highlighting for diff and json
    """,
    priority=0,
    deps=[dep(f"{PREFIX}-e4.5")],
    labels=["surface:frontend", "area:beads", "tier:sonnet",
            "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e5.5",
    "Bulk actions in grid view",
    """
    # Goal
    Select multiple rows, apply one change. Standard Jira move.

    # Inputs
    - gm-e4.3 complete

    # Outputs
    - Row checkboxes + "select all" with rangeshift support
    - Floating action bar when >0 selected
    - Actions: change priority, assign to agent, add/remove label, close,
      create convoy from selection
    - Confirmation dialog lists all affected bead IDs
    - Backend: new `POST /api/beads/batch` endpoint that does an N-way
      transaction through bd (creating gm-e2.6.1 as follow-up task)

    # Definition of Done
    - Partial failure (some succeed, some don't) shows a summary modal
      with retry for the failed ones
    """,
    priority=1,
    deps=[dep(f"{PREFIX}-e4.3"), dep(f"{PREFIX}-e2.7")],
    labels=["surface:frontend", "area:beads", "tier:sonnet",
            "risk:high", "fed:safe"],
)

add(
    f"{PREFIX}-e5.6",
    "YOLO mode toggle in UI (gated by server flag)",
    """
    # Goal
    If the server is running with `--dangerously-skip-permissions`, show a
    prominent banner in the UI. Also offer a per-session "skip confirms"
    toggle that only applies when the server is in yolo mode.

    # Inputs
    - gm-e2.7 complete

    # Outputs
    - `/api/config` returns yolo_available (did server start with flag)
    - If available, settings panel offers "Skip confirmation dialogs"
    - If enabled, skip the client-side confirm modal, but server still
      enforces confirm token -- server yolo mode is what actually matters
    - Banner text matches Claude Code's energy: "Dangerously skip
      permissions is active. Mutations will not require confirmation."

    # Definition of Done
    - UI toggle has no effect unless server was started with the flag
    - Banner visible on every page when active
    - Audit log still records every mutation even in yolo mode
    """,
    priority=1,
    deps=[dep(f"{PREFIX}-e2.7")],
    labels=["surface:frontend", "area:settings", "tier:sonnet",
            "risk:high", "fed:safe"],
)


# ----------------------------------------------------------------------
# GAS CITY-NATIVE SURFACES (added post-v2 review)
# These three beads capture the surfaces that Gas City's declarative
# architecture makes possible and that no existing community tool ships.
# ----------------------------------------------------------------------

add(
    f"{PREFIX}-e5.7",
    "Desired-vs-actual view (city.toml drift dashboard)",
    """
    # Goal
    Render `city.toml` as desired state alongside `.gc/agents/` as actual
    state. Highlight drift: agents declared but not running, agents running
    but not declared, agents running with a config fingerprint that differs
    from declared. This is the Kubernetes-dashboard surface for multi-agent
    systems — the single biggest new thing Gemba brings.

    # Inputs
    - gm-e2.3 (gc adapter) complete
    - gm-e2.4 (fs adapter with city.toml watch) complete
    - gm-e4.2 (agents list view) complete

    # Outputs
    - `/api/drift` endpoint that diffs declared agents vs live sessions
      - Returns: {declared: [Agent], live: [Agent], drift: [Drift]}
      - Drift kinds: missing (declared but not live), extra (live but not
        declared), fingerprint_mismatch (same name, different config hash)
    - Frontend: split-pane view at /drift with "Desired" on left,
      "Actual" on right, drift items highlighted with amber/red
    - Per-drift "Reconcile" action that shells out to `gc config` or
      shows a copy-pasteable city.toml diff for the user to apply
    - Live update via SSE when fs adapter reports city.toml changed OR
      .gc/agents/ changed

    # Definition of Done
    - Correctly identifies all three drift kinds in integration tests
    - Reconcile action never writes .gc/ directly (round-trips through gc)
    - Renders cleanly for a Level 1 city (one agent, maybe no drift)
    - Renders cleanly for a full gastown pack (8 agents)
    - Never hangs if controller isn't running (read-only fs access works
      even without controller.sock connection)
    """,
    priority=1,
    deps=[dep(f"{PREFIX}-e2.3"), dep(f"{PREFIX}-e2.4"),
          dep(f"{PREFIX}-e4.2")],
    labels=["surface:frontend", "area:desired-vs-actual",
            "layer:controller-watch", "tier:opus",
            "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e5.8",
    "Pack browser and per-rig overrides viewer",
    """
    # Goal
    Enumerate `packs/` directory, preview each pack's `pack.toml` + prompts,
    show per-rig overrides as diffs against the base pack. This is the
    Kustomize-for-agents UX that Gas City's declarative config model
    implies but nothing ships.

    # Inputs
    - gm-e2.3 (gc adapter) complete — uses `gc config explain` for resolution
    - gm-e2.4 (fs adapter) complete — reads packs/ directory

    # Outputs
    - `/api/packs` endpoint returns list of available packs with metadata
      (name, version, agent count, schema version)
    - `/api/packs/<name>` returns full pack definition (agents, prompts
      preview, default isolation/pool settings)
    - `/api/rigs/<name>/overrides` returns resolved override diff vs base
      pack (which agents patched, which suspended)
    - Frontend: pack list with cards; click a pack to see its agents,
      prompts (markdown-rendered), default config
    - Per-rig view shows base pack + override diff with syntax highlighting
    - "Stamp pack onto rig" action that generates a city.toml edit (never
      writes directly)

    # Definition of Done
    - Works for all shipped packs (gastown, ccat, ralph, hello-world,
      wasteland-feeder)
    - Override diffs render Add/Patch/Suspend operations distinctly
    - User-authored packs in packs/ show up without any configuration
    - Never auto-applies an override — always produces a diff for user
      review first
    """,
    priority=2,
    deps=[dep(f"{PREFIX}-e2.3"), dep(f"{PREFIX}-e2.4")],
    labels=["surface:frontend", "area:packs", "tier:opus",
            "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e5.9",
    "Provider-aware agent detail view",
    """
    # Goal
    The agent detail page must adapt to the session provider. A tmux
    session is not a k8s pod is not a subprocess is not an exec script.
    Each deserves distinct affordances.

    # Inputs
    - gm-e4.2 (agents list) complete — clicking an agent opens detail view

    # Outputs
    - Base detail view: agent name, role, prompt template (rendered),
      pool config, current status, recent event log
    - Provider-specific sections:
      - tmux: "Attach in terminal" button (opens terminal with
        `tmux attach-session -t <name>`), session pane thumbnail if peek
        is available
      - k8s: pod status, namespace, node, restart count, "View pod logs"
        link, "Peek last N lines" action
      - subprocess: process tree (parent PID, child PIDs), stdin/stdout
        file sizes, exit code if any, "Inspect env vars" collapsed section
      - exec: last command invoked, exit code, stdout tail, "Run diagnostic"
        button for the exec script's `is-running` check
    - All sections fed by `gc session <action>` CLI calls — never connect
      to controller.sock directly
    - "Last command output" area respects Peek semantics for all providers

    # Definition of Done
    - tmux section works against a real tmux session
    - k8s section works against a real pod (integration test with kind)
    - subprocess and exec sections render correctly with stub backends
    - UI degrades gracefully when a provider-specific command is missing
      (e.g., `gc session peek` not supported for a legacy provider)
    - No provider-specific code in the components that aren't rendering
      that provider (clean switch based on `agent.provider` field)
    """,
    priority=1,
    deps=[dep(f"{PREFIX}-e4.2")],
    labels=["surface:frontend", "area:agents",
            "provider:tmux", "provider:k8s", "provider:subprocess",
            "provider:exec", "tier:opus", "risk:medium", "fed:safe"],
)


# ======================================================================
# PHASE 6 — GRAPH, INSIGHTS, MAIL
# ======================================================================

add(
    f"{PREFIX}-e6",
    "Phase 6: Graph, Insights, Mail — the differentiators",
    """
    # Goal
    What makes Gemba a keeper rather than just another dashboard:
    (1) interactive dependency graph with every Beads edge type visualized
    (2) OTEL-fed insights panel with real signals, not vanity charts
    (3) mail UI that unifies every inbox (Overseer, Mayor, agents)

    # Definition of Done
    - Dep graph pans/zooms smoothly on 1k+ nodes
    - Insights panel answers "is my town healthy right now?"
    - Mail view matches gmail ergonomics
    """,
    issue_type="epic",
    priority=1,
    deps=[dep(f"{PREFIX}-root", "parent-child"), dep(f"{PREFIX}-e4")],
    labels=["surface:frontend", "area:graph", "area:insights",
            "area:mail", "tier:sonnet", "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e6.1",
    "Dependency graph with React Flow",
    """
    # Goal
    Interactive graph. Every Beads edge type rendered with a distinct
    style. Click a node -> open bead drawer.

    # Inputs
    - gm-e4.5 complete

    # Outputs
    - `/graph` route; optionally `/graph/:beadId` centers on one bead
    - Force-directed layout (d3-force via reactflow) for small graphs,
      layered dagre layout for large epics
    - Edge colors by type: blocks (red), parent-child (blue), related
      (grey), discovered-from (purple), waits-for (orange), replies-to
      (teal), conditional-blocks (dashed red)
    - Node shape by issue_type: epic (rounded rect), task (rect), bug
      (diamond), story (tag), feature (hex), message (speech bubble)
    - Minimap, zoom controls, fit-to-screen
    - Filters: by rig, by label, by status

    # Definition of Done
    - 1000-node graph renders in under 2s
    - Cycle detection highlights cycles in orange
    - Critical path mode highlights longest blocks-chain
    """,
    priority=1,
    deps=[dep(f"{PREFIX}-e4.5")],
    labels=["surface:frontend", "area:graph", "tier:opus",
            "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e6.2",
    "Insights panel with OTEL-driven charts",
    """
    # Goal
    Real metrics, surfaced well. Signals that answer "what changed?" and
    "is the town healthy?"

    # Inputs
    - gm-e2.4 complete (OTEL reader)

    # Outputs
    - `/insights` route
    - Charts (via recharts or observable plot):
      - Spawn rate (gastown.polecat.spawns.total) over 24h
      - Completion rate (gastown.done.total)
      - Convoy throughput
      - Stuck-agent minutes (derived)
      - Merge queue latency
      - Token cost over time (via gt costs)
      - API error rate from bd.calls.total
    - Time range: 1h / 6h / 24h / 7d
    - Per-rig breakdown toggle

    # Definition of Done
    - Charts render without jank on a month of data
    - "what changed" box highlights anomalies (simple 3-sigma flag is fine
      for v1; ML is out of scope)
    """,
    priority=2,
    deps=[dep(f"{PREFIX}-e2.4")],
    labels=["surface:frontend", "area:insights", "tier:sonnet",
            "risk:low", "fed:safe"],
)

add(
    f"{PREFIX}-e6.3",
    "Mail view: unified inbox + per-agent views",
    """
    # Goal
    `gt mail` in a nice UI. Overseer inbox is primary. Per-agent mailboxes
    accessible. Threading via the --thread feature.

    # Inputs
    - gm-e2.3 complete

    # Outputs
    - `/mail` route with folder list (inbox, sent, per-agent)
    - Three-pane: folders | thread list | message
    - Compose button opens modal with typeahead `to` field
    - Reply threading preserves thread ID
    - Search across all mailboxes

    # Definition of Done
    - Sending mail from here produces a bead readable by the recipient's
      session within the Gastown mail cycle window
    - Threaded replies appear as a single thread in the list
    """,
    priority=2,
    deps=[dep(f"{PREFIX}-e2.3")],
    labels=["surface:frontend", "area:mail", "tier:sonnet",
            "risk:low", "fed:safe"],
)

add(
    f"{PREFIX}-e6.4",
    "Escalations drawer with one-click ack",
    """
    # Goal
    CRITICAL/HIGH/MEDIUM escalations visible at a glance, acknowledgeable
    from the UI.

    # Inputs
    - gm-e2.3 complete

    # Outputs
    - Bell icon in topbar with badge count
    - Drawer lists escalations grouped by severity, sorted by recency
    - Click escalation -> bead drawer for the linked bead
    - Ack button calls `gt escalate ack <id>` via adapter

    # Definition of Done
    - New escalation produces desktop notification (via Notification API)
      if user has granted permission
    - Severity colors: CRITICAL red, HIGH orange, MEDIUM yellow
    """,
    priority=2,
    deps=[dep(f"{PREFIX}-e2.3")],
    labels=["surface:frontend", "area:escalations", "tier:sonnet",
            "risk:medium", "fed:safe"],
)


# ======================================================================
# PHASE 7 — MOLECULES, FORMULAS, WORKFLOWS
# ======================================================================

add(
    f"{PREFIX}-e7",
    "Phase 7: Molecules — make workflows visual",
    """
    # Goal
    Gastown's most differentiated capability is molecules / formulas: TOML
    workflows with steps, dependencies, and checkpoint recovery. Bullet
    Farm should render these first-class, not as just-another-bead.

    # Definition of Done
    - Formula catalog browseable
    - Cook formula from UI, pour into molecule
    - Molecule progress view shows step-by-step bar with current step
    - Discovered sub-beads link back to their origin molecule
    """,
    issue_type="epic",
    priority=2,
    deps=[dep(f"{PREFIX}-root", "parent-child"), dep(f"{PREFIX}-e5")],
    labels=["surface:frontend", "area:molecules", "tier:sonnet",
            "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e7.1",
    "Formula catalog view",
    """
    # Goal
    Browse all formulas — embedded in gt binary, in `plugins/`, and in
    `.beads/formulas/`. Show TOML source, description, input parameters.

    # Inputs
    - gm-e2.3 complete

    # Outputs
    - `/formulas` route
    - Card grid with search
    - Detail view renders TOML with syntax highlighting + markdown body
    - "Cook" button opens form for required inputs

    # Definition of Done
    - All three formula sources visible
    - Cook button round-trips through `bd cook <formula>` and shows the
      resulting protomolecule
    """,
    priority=2,
    deps=[dep(f"{PREFIX}-e7", "parent-child")],
    labels=["surface:frontend", "area:molecules", "tier:sonnet",
            "risk:low", "fed:safe"],
)

add(
    f"{PREFIX}-e7.2",
    "Molecule progress view with step timeline",
    """
    # Goal
    See a molecule's execution at a glance. Each step is a bead; completion
    rolls up.

    # Outputs
    - `/molecules/:id` route
    - Horizontal timeline: steps as nodes, edges as dependencies
    - Step status: pending / running / done / failed / skipped
    - Click a step -> bead drawer for that step
    - Overall progress bar at top

    # Definition of Done
    - Reactive: step completion event via SSE updates progress without reload
    - Failed step shows retry + debug actions
    """,
    priority=2,
    deps=[dep(f"{PREFIX}-e7.1")],
    labels=["surface:frontend", "area:molecules", "tier:sonnet",
            "risk:medium", "fed:safe"],
)


# ======================================================================
# PHASE 8 — RELEASE & DISTRIBUTION
# ======================================================================

add(
    f"{PREFIX}-e8",
    "Phase 8: Release & Distribution",
    """
    # Goal
    Ship v1. Homebrew tap works. npm wrapper works. Installing on Windows
    works. Docs site live. First tagged release.

    # Definition of Done
    - `brew install gemba/tap/gemba` on a fresh macOS -> working
    - `npm install -g gemba` on a fresh machine -> working
    - `gemba serve` + first-run works end-to-end with the top 3 agent
      runtimes (Claude Code, Codex, Gemini)
    - Docs site at bulletcity.dev (or similar) with quickstart, tour,
      reference
    """,
    issue_type="epic",
    priority=1,
    deps=[dep(f"{PREFIX}-root", "parent-child"),
          dep(f"{PREFIX}-e5"), dep(f"{PREFIX}-e3")],
    labels=["surface:infra", "surface:docs", "tier:sonnet",
            "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e8.1",
    "goreleaser configuration for all platforms",
    """
    # Goal
    One command (`make release`) cuts a release for macOS (Intel/ARM),
    Linux (amd64/arm64), Windows, FreeBSD. Homebrew formula auto-updated.

    # Outputs
    - `.goreleaser.yml` with cross-compile targets and archive configs
    - Apple codesigning + notarization (cert in GH secrets)
    - Windows Authenticode signing (optional v1.1; warn in release notes)
    - Checksums published; cosign signatures optional
    - Homebrew tap repo `YOU/homebrew-gemba` auto-updated on release

    # Definition of Done
    - A tag push produces all artifacts in Releases page
    - `brew update && brew upgrade gemba` pulls the new version
    - SBOM generated and published
    """,
    priority=1,
    deps=[dep(f"{PREFIX}-e8", "parent-child"), dep(f"{PREFIX}-e1.6")],
    labels=["surface:infra", "tier:sonnet", "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e8.2",
    "npm wrapper package: `npm install -g gemba`",
    """
    # Goal
    Node-land users install via npm. Postinstall script downloads the
    correct binary for the platform from GH Releases.

    # Outputs
    - `packaging/npm/` directory with `package.json`, `bin/cli.js` wrapper,
      `scripts/postinstall.js`
    - Postinstall verifies checksum before installing binary
    - Wrapper cli passes all argv through to the real binary

    # Definition of Done
    - `npm install -g gemba` then `bc --version` works on
      macOS / Linux / Windows
    - Fails loudly on checksum mismatch
    """,
    priority=2,
    deps=[dep(f"{PREFIX}-e8.1")],
    labels=["surface:infra", "tier:sonnet", "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-e8.3",
    "Docs site: Docusaurus or Astro Starlight",
    """
    # Goal
    Good docs. Quickstart gets you to "see your Gastown data" in under
    60 seconds. Reference covers every CLI flag and every API endpoint.

    # Outputs
    - `docs/` in repo using Astro Starlight (or Docusaurus; pick based on
      match with Gastown's gastown.dev site if it exists)
    - Pages: Introduction, Install, Quickstart, Configuration, Remote
      Access, API Reference (generated from OpenAPI), CLI Reference,
      Architecture, Contributing, FAQ
    - Deployed to bulletcity.dev via Cloudflare Pages or GitHub Pages

    # Definition of Done
    - Every CLI flag documented
    - Every API endpoint documented
    - Search works
    - Dark theme default
    """,
    priority=1,
    deps=[dep(f"{PREFIX}-e8", "parent-child")],
    labels=["surface:docs", "tier:sonnet", "risk:low", "fed:safe"],
)

add(
    f"{PREFIX}-e8.4",
    "Announcement: gastown discussions + HN + Reddit + blog post",
    """
    # Goal
    Ship with a proper coming-out. Post to the Gastown community
    (discussions thread, not an integration PR — mirroring issue #228's
    precedent), write a short blog post, submit to HN.

    # Outputs
    - Discussion post on github.com/gastownhall/gastown
    - Blog post on project site with screenshots and a 30s screencast
    - HN submission
    - Reddit posts to r/ClaudeAI and r/LocalLLaMA

    # Definition of Done
    - v1.0.0 tagged
    - Announcement thread has non-zero engagement and no angry issues
      filed in the first 24h (real bar; triage ready)
    """,
    priority=2,
    deps=[dep(f"{PREFIX}-e8.1"), dep(f"{PREFIX}-e8.3")],
    labels=["surface:docs", "tier:sonnet", "risk:low", "fed:safe"],
)


# ======================================================================
# Known bugs / hardening backlog (post-v1 discoveries captured pre-emptively)
# ======================================================================

add(
    f"{PREFIX}-b1",
    "BUG: handle `bd` daemon-offline gracefully",
    """
    # Symptom
    When bd daemon is down or restarting, bd CLI returns errors that look
    like 500s from our adapter. Users see a red modal for a transient
    condition.

    # Expected
    Detect daemon-offline errors in the bd adapter, back off exponentially,
    retry, and surface a "bd daemon reconnecting" banner in the UI only if
    the condition persists >5 seconds.

    # Acceptance
    Killing the bd daemon during a demo produces a yellow banner, not a
    red error; operations resume automatically when daemon restarts.
    """,
    issue_type="bug",
    priority=2,
    deps=[dep(f"{PREFIX}-e2.2", "discovered-from")],
    labels=["surface:backend", "layer:adapter-bd", "tier:sonnet",
            "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-b2",
    "BUG: SPA fallback must not shadow API 404s",
    """
    # Symptom
    If the API returns 404 for a bead, the SPA fallback might intercept it
    and serve index.html, breaking client fetch error handling.

    # Expected
    Route matching is explicit: `/api/*` and `/events/*` are never
    rewritten; everything else falls back to index.html.

    # Acceptance
    `curl -i http://localhost:7666/api/beads/nonexistent` returns HTTP 404
    with JSON body, not index.html.
    """,
    issue_type="bug",
    priority=1,
    deps=[dep(f"{PREFIX}-e1.3", "discovered-from")],
    labels=["surface:backend", "layer:api", "tier:haiku",
            "risk:medium", "fed:safe"],
)

add(
    f"{PREFIX}-b3",
    "BUG: token auth must not be enabled on a loopback-only bind silently",
    """
    # Symptom
    If a user passes `--auth token` without `--listen`, we generate a
    token for a bind that doesn't need one. User confusion.

    # Expected
    On localhost with `--auth token`, either:
    (a) warn that auth is unnecessary but still enforce it (preferred), or
    (b) print a clear note that --listen controls network exposure
    Choose (a) and document.

    # Acceptance
    Config combining --auth token with default bind prints an info-level
    note about redundancy but still requires the token.
    """,
    issue_type="bug",
    priority=3,
    deps=[dep(f"{PREFIX}-e3.2", "discovered-from")],
    labels=["surface:backend", "layer:auth", "tier:haiku",
            "risk:low", "fed:safe"],
)


# ======================================================================
# WRITE OUT
# ======================================================================

def ensure_parent_child_edges():
    """
    Hierarchical IDs (gm-e1.1, gm-e1.2, gm-e1.1.1) imply parent-child but
    Beads doesn't auto-materialize that edge. Add an explicit parent-child
    dep on every child pointing at its immediate parent, unless one is
    already present. This makes `parent:gm-e1` queries and bd blocked
    cascade work correctly.
    """
    by_id = {i["id"]: i for i in ISSUES}
    added = 0
    for issue in ISSUES:
        iid = issue["id"]
        if "." not in iid:
            continue
        parent_id = iid.rsplit(".", 1)[0]
        if parent_id not in by_id:
            continue
        deps = issue.setdefault("dependencies", [])
        already = any(d["depends_on_id"] == parent_id
                      and d["type"] == "parent-child" for d in deps)
        if not already:
            deps.append({"depends_on_id": parent_id, "type": "parent-child"})
            added += 1
    print(f"Injected {added} explicit parent-child edges.")


def main():
    ensure_parent_child_edges()
    out = Path(__file__).parent / "issues.jsonl"
    with out.open("w") as f:
        for issue in ISSUES:
            # sanity: everything has required fields
            for required in ("id", "title", "description", "issue_type",
                             "priority", "status"):
                assert required in issue, f"missing {required} in {issue.get('id')}"
            f.write(json.dumps(issue, separators=(",", ":")))
            f.write("\n")
    print(f"Wrote {len(ISSUES)} issues to {out}")

    # Quick summary by type
    from collections import Counter
    type_counts = Counter(i["issue_type"] for i in ISSUES)
    priority_counts = Counter(i["priority"] for i in ISSUES)
    print(f"By type:     {dict(type_counts)}")
    print(f"By priority: {dict(priority_counts)}")

    # Dependency sanity: every id in a dep exists
    all_ids = {i["id"] for i in ISSUES}
    missing = []
    for issue in ISSUES:
        for d in issue.get("dependencies", []):
            if d["depends_on_id"] not in all_ids:
                missing.append((issue["id"], d["depends_on_id"]))
    if missing:
        print(f"WARN: {len(missing)} dependency targets missing:")
        for src, tgt in missing:
            print(f"  {src} -> {tgt}")
    else:
        print("All dependency targets resolve.")


if __name__ == "__main__":
    main()
