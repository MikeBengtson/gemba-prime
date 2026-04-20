# Foolery Extension Plan — Path B and Path D

> Spike output for **gm-mth** (2026-04-20, polecat jasper).
>
> Concrete integration spec: license path, architecture seams, commit-level
> changes required to either host Gemba's UI in Foolery (Path B) or consume
> Foolery as an optional Gemba UI surface (Path D).
>
> Read alongside:
> - `foolery-fit-gap.md` — Phase 12 coverage matrix
> - `gemba/docs/prior-art/foolery.md` — spike summary + recommendation

## License path (applies to both paths)

- **Foolery is MIT** (`LICENSE`, copyright 2026 Andrew Cartine).
- **Gemba's options:**
  1. **Upstream contribution** — land a `gemba-backend.ts` `BackendPort` impl
     in `acartine/foolery`. Requires RFC acceptance by the single maintainer.
     Best outcome; lowest long-term maintenance cost for us.
  2. **Friendly fork** — maintain `gemba/foolery-gemba` as a downstream fork
     that tracks upstream. Viable fallback; costs a rebase cadence.
  3. **Dual publish** — ship `@gemba/foolery-backend` as an npm plugin module
     and submit upstream registration PR. Only viable if upstream agrees to
     add a dynamic-loader shim to `backend-factory.ts` (see §B.3 below).
- **No contributor-agreement risk.** Foolery has no CLA; MIT copyright stays
  with contributors.
- **Attribution requirement:** retain MIT notice if we ship or redistribute
  Foolery code. Trivial.

## Shared architecture primer

Foolery's seams that matter for Gemba integration:

```
Browser (React/Next.js)
   │  TanStack Query (polling) + SSE (terminal only)
   ▼
Next.js API routes   (src/app/api/*)
   │
   ▼
BackendPort          (src/lib/backend-port.ts)
   │  ← THIS IS THE SEAM
   ├── knots-backend.ts   (shells out to `kno`)
   ├── beads-backend.ts   (shells out to `bd`)
   └── [new] gemba-backend.ts  ← what we add
```

Gemba's seams that matter:

```
WorkPlaneAdaptor     (Beads / Gastown / …)
OrchestrationPlaneAdaptor   (claude / gastown / …)
CapabilityManifest   (declared per adaptor, gates UI)
Transport router     (api / jsonl / mcp)  — gm-e3.4
```

The integration contract is: **`gemba-backend.ts` speaks `BackendPort` to
Foolery on one side and speaks Gemba's Transport router on the other.** Gemba's
CapabilityManifest translates down to Foolery's `BackendCapabilities` boolean
flags (lossy but sufficient for UI gating).

---

## Path B: Foolery is Gemba's UI

Gemba ships no SPA of its own (or ships only a minimal viewer). Foolery
becomes the primary end-user surface.

### B.1 Integration shape

1. **New BackendPort impl** — `src/lib/backends/gemba-backend.ts` implements
   all `BackendPort` methods against Gemba's HTTP API (gm-e4). No CLI shell-out;
   this is the first HTTP-native backend.
2. **Capability translation shim** — `src/lib/backends/gemba-capabilities.ts`
   maps Gemba's `CapabilityManifest` → Foolery's `BackendCapabilities`. Things
   like `canSync`, `canDelete`, `maxConcurrency` are projected from declared
   adaptor capabilities. Extensions (sprints, budget, evidence) get
   best-effort flags (`supportsSprints`, …) added to `BackendCapabilities`.
3. **Beat ↔ WorkItem mapping** — declared at the boundary in
   `gemba-backend.ts`. Field mapping:
   - `Beat.id` ← `WorkItem.id`
   - `Beat.state` ← `WorkItem.state` (workflow-native, no translation)
   - `Beat.priority` ← `WorkItem.priority` (Foolery is 0-4; Gemba is 0-4 —
     verify at implementation time)
   - `Beat.metadata.gemba` ← full `WorkItem` for Gemba-native views that
     read past the Beat projection
4. **SSE push extension** (required) — extend Foolery's SSE pipeline to carry
   `beat_updated` events, not just terminal events. New event type
   `BeatUpdatedEvent` emitted from `gemba-backend.ts` in response to Gemba's
   transport-router SSE hub (gm-e4.3). TanStack Query consumers subscribe and
   invalidate by workitem id.
5. **New views** (required) — add three Gemba-only routes:
   - `/capabilities` — adaptor capability browser (gm-e12.14)
   - `/graph/:workitemId` — dependency graph via React Flow (gm-e12.16)
   - `/drift` — desired-vs-actual (gm-e12.13, P1, defer to v2)

### B.2 Commit-level changes required upstream

If we pursue upstream contribution, the minimum viable PR set is:

| PR | Scope | Rough lines |
|----|-------|-------------|
| 1 | Extend `BackendType` union + factory switch for `"gemba"` | ~50 |
| 2 | Add `gemba-backend.ts` + schemas + contract-test pass | ~800 |
| 3 | Add `gemba-capabilities.ts` + extend `BackendCapabilities` with a few optional flags (or carry them as `extras: Record<string, boolean>`) | ~150 |
| 4 | Extend SSE pipeline to carry `beat_updated` events (types + server emitter + client consumer + tests) | ~400 |
| 5 | Add `/capabilities` route + component, capability-flag gated | ~300 |
| 6 | Add `/graph/:workitemId` route + React Flow + tests | ~500 |
| 7 | Drift + insights as opt-in Gemba-only modules (P2, follow-up) | — |

PRs 1–4 are prerequisites; PRs 5–7 can ship incrementally. If upstream
rejects PR 4 (SSE broadening) — the highest-risk PR — Path B is effectively
blocked and we must fall back to Path D or a fork.

### B.3 Plugin-loader option (optional, upstream-dependent)

If we want a clean upstream story and to avoid forks for every consumer, we
can propose a dynamic-loader PR to Foolery:

- `FOOLERY_BACKEND_PLUGIN=/path/to/module` loads a module exporting a
  `createBackend(config): BackendPort` function.
- `BackendType` union gains `"plugin:<name>"` variants.
- Contract tests run against plugin instances.

This is a bigger ask (adds supply-chain surface) but would let Gemba ship its
backend as an npm package without touching Foolery's tree. **Recommendation:**
do not make this a prerequisite for Path B — propose it as a follow-on.

### B.4 Path B risks

- **Single-maintainer bus factor.** Andrew is the only committer. Our roadmap
  becomes coupled to his bandwidth on reviews.
- **UX divergence.** Foolery's keyboard-first, five-view model (Queues /
  Active / Retakes / History / Diagnostics) is opinionated. Gemba's "any work
  tracker × any agent orchestrator" thesis may require views or
  interactions that don't fit this frame (AgentGroup board with drag-drop;
  cross-workspace backlog; graph mode).
- **SSE broadening is the tall pole.** If upstream wants to keep SSE
  terminal-scoped, e12.2 can't meet its 500ms DoD inside Foolery.
- **State model drift.** Foolery's `nextActionState` /
  `requiresHumanAction` / `isAgentClaimable` semantics bake in opinions
  Gemba may not want to inherit.

---

## Path D: Foolery as optional consumer (RECOMMENDED)

Gemba ships its own thin cross-plane SPA (`gemba/web/`) and publishes a
Foolery `BackendPort` implementation as an optional integration. Users who
want Foolery's UX get it; Gemba's roadmap stays independent.

### D.1 Integration shape

1. **Gemba ships `gemba/web/`** — the Phase 12 SPA, adaptor-agnostic, reading
   from Gemba's HTTP API (gm-e4) and active `CapabilityManifest`. This is what
   the rest of Phase 12 was planning anyway. Nothing changes there.
2. **Gemba publishes `@gemba/foolery-backend`** — a small npm package
   (~800 lines) containing:
   - `GembaBackend implements BackendPort`
   - capability translator
   - README with `FOOLERY_BACKEND=gemba` + env-var setup
   - Vitest suite that runs against Foolery's published contract-test
     harness (Foolery currently exports it via path imports; we propose a
     published test-utils entrypoint)
3. **Outreach to upstream** — RFC issue on `acartine/foolery`:
   "RFC: publish contract-test harness as `foolery/testing`, and register
   Gemba as a third backend in the docs". No code in Foolery's tree.
4. **If upstream declines registration** — ship as-is; users set
   `FOOLERY_BACKEND_MODULE=@gemba/foolery-backend` via a thin loader PR (see
   B.3) or via fork. The absence of upstream blessing does not block us.

### D.2 Commit-level changes

In Gemba:

| File | Change |
|------|--------|
| `ops/packages/foolery-backend/` (new) | Whole package: `src/index.ts`, `src/backend.ts`, `src/capabilities.ts`, `src/schemas.ts`, `test/contract.test.ts`, `package.json`, README |
| `ops/packages/foolery-backend/src/backend.ts` | Implements `BackendPort` against Gemba's HTTP client |
| `ops/packages/foolery-backend/src/capabilities.ts` | Projects Gemba's `CapabilityManifest` → Foolery `BackendCapabilities` |

In Foolery (nice-to-have, one PR):

| File | Change |
|------|--------|
| `package.json` | Add `"./testing"` export for `BackendPort` contract harness |
| `src/lib/__tests__/backend-contract.test.ts` | Factor out harness to `src/testing/contract.ts` |
| `docs/backend-extension-guide.md` | Add "Registered third-party backends" section with Gemba link |

### D.3 Why this is the recommended path

- **Independent roadmap.** Gemba ships Phase 12 on Gemba's schedule. No
  dependency on a single external maintainer's review queue.
- **No SSE broadening required.** Gemba's own SPA handles SSE properly from
  day one via its transport router. The Foolery integration operates at the
  cadence Foolery already supports (polling with optional terminal SSE), and
  degrades gracefully for Foolery consumers.
- **Preserves Foolery's UX ownership.** We're not asking Andrew to take
  opinions he doesn't want; we're contributing a plug.
- **Provides a real consumer of Gemba's adaptor surface.** Proves the
  "any UI × any backend" thesis by exhibiting a second UI consuming Gemba.
- **Reversible.** If Path D succeeds and a future Path B looks attractive, we
  can propose it with shipped, audited code in hand. Hard to do in the
  opposite order.

### D.4 Path D risks

- **Dual-UI maintenance burden.** Gemba's SPA and the Foolery backend both
  need updates when Gemba's WorkItem schema evolves. Mitigation: generate
  both from the OpenAPI spec (gm-e4) via the TS codegen.
- **Contract-test drift.** If Foolery renames `BackendPort` methods, our
  package breaks. Mitigation: pin the Foolery version range and run Foolery's
  contract tests in our CI.
- **User confusion.** "Which UI should I use?" Mitigation: Gemba's docs
  should say "use `gemba/web/` for full features; use Foolery if you prefer
  its keyboard UX and can accept the covered-feature subset".

---

## Decision-matrix row for gm-9h6

Paste into `gm-9h6`'s decision matrix when the UI-strategy decision is taken:

| Option | Coverage (Phase 12) | License risk | Schedule risk | Bus factor | Reversibility | Recommendation |
|--------|---------------------|--------------|---------------|------------|---------------|----------------|
| Path B — Foolery hosts Gemba | 6🟢 / 6🟡 / 5🔴 → ~70% with upstream work | None (MIT) | HIGH (single-maintainer upstream, SSE broadening required) | High external | Hard once committed | CONDITIONAL — only if upstream pre-commits to PR 4 (SSE broadening) |
| Path D — Foolery as consumer | N/A — Gemba ships its own SPA | None (MIT) | LOW (independent) | None external | Easy | **RECOMMENDED** |

---

## Outreach draft (for human review before send)

**Title:** RFC: Gemba BackendPort — register Gemba as a third memory-manager backend

**Body sketch:**

> Hi Andrew — I've been evaluating Foolery as an integration point for Gemba
> (<link>), which generalizes Beads/Gastown-style work orchestration so any
> UI can sit over any tracker × any agent. Your `BackendPort` + capabilities
> model is a great seam; we'd like to publish `@gemba/foolery-backend` as a
> third implementation.
>
> Two asks:
>
> 1. Would you be open to a small PR exposing your contract-test harness via
>    `foolery/testing` so downstreams run your tests?
> 2. Would you be open to a one-line registration in
>    `backend-extension-guide.md` pointing at our package once we ship it?
>
> We commit to:
> - passing your full contract-test suite
> - attribution + MIT-compatible licensing
> - a maintained package pinned to your minor versions
>
> Happy to open a follow-up RFC for a dynamic-plugin loader if you'd welcome
> that; not a prerequisite for us.

Recommend: do **not** mention Path B in the first outreach. It's a much
larger ask and will color the conversation. Path D first; if upstream is
enthusiastic, revisit.

---

## Open items / follow-ups (file as beads after decision)

- **Capability translation table.** Enumerate every Gemba `CapabilityManifest`
  flag + decide which project to `BackendCapabilities.extras` vs gate at the
  Gemba-SPA layer only.
- **Priority scale.** Confirm Foolery's 0-4 priority matches Gemba's. If not,
  add `priorityScale` to `BackendCapabilities`.
- **Dependency type.** Foolery's `BeatDependency` has no `type` field; Gemba
  may need typed deps (blocks/relates/parent). Check before implementing
  `addDependency` in `gemba-backend.ts`.
- **Knots vs Beads as a reference.** `knots-backend.ts` is the more-active
  implementation and probably the cleanest reference for `gemba-backend.ts`
  shape.
- **SSE semantics for Path B** (only if Path B is chosen). Needs its own
  spike.
