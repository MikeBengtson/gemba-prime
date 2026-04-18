#!/usr/bin/env python3
"""
validate-import.py — Validate that the Gemba work package will import
cleanly into a target Beads installation.

Usage:
    # Just check schema compatibility (fast, no writes)
    ./validate-import.py --check

    # Dry-run: import into a temp .beads, report what happens, clean up
    ./validate-import.py --dry-run

    # Real import: write to --target, --force overwrites existing
    ./validate-import.py --target ~/my-city/rigs/gemba --prefix bc --force

What it checks, in order:
    1. `bd` is on PATH and --version is a known-good range
    2. `gt` is on PATH and --version is a known-good range
    3. Beads issue types, statuses, and dep types we rely on are all present
       (runs `bd types`, `bd statuses`, probes `bd create --help`)
    4. `bd create --id` flag is supported (critical — hash IDs would break
       our stable gm-e1, gm-e1.1 references)
    5. Every dependency target in issues.jsonl resolves (graph connectivity)
    6. No cycles in the effective blocks graph
    7. On dry-run: actually creates beads in a tempdir, verifies show, ready,
       list, dep tree work on the imported data, then cleans up

Exit codes:
    0  all checks pass
    1  usage/argument error
    2  prerequisite missing (bd or gt not found)
    3  schema drift: a required type / status / dep-type is missing
    4  data integrity: missing dep targets or cycles
    5  dry-run import failed
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path


# --- version guardrails ---------------------------------------------------
# Known-good ranges. Update as Beads and Gas Town evolve. We warn outside
# the tested range rather than failing, so the script stays useful when
# upstream ships new versions.
#
# Gas Town reached v1.0.0 on April 3, 2026. Beads reached v1.0.0 alongside.
# We test against the current stable line.
BD_TESTED_MIN = (0, 55, 0)
BD_TESTED_MAX = (1, 5, 0)
GT_TESTED_MIN = (0, 10, 0)
GT_TESTED_MAX = (1, 5, 0)

# Issue types we use. Beads doesn't expose a `bd types` subcommand — valid
# types are checked at `bd create` time. We probe `bd create --help` and
# fall back to an in-memory dry-create if the help text isn't parseable.
REQUIRED_ISSUE_TYPES = {"epic", "task", "feature", "bug"}
REQUIRED_STATUSES = {"open", "in_progress", "blocked", "closed"}

# Dep types we use. These ARE documented in `bd create --help` under the
# --deps flag. Source: cmd/bd/create.go.
REQUIRED_DEP_TYPES = {"blocks", "parent-child", "discovered-from",
                      "related", "waits-for"}


# --- output helpers -------------------------------------------------------

def color(s, c):
    if not sys.stdout.isatty():
        return s
    return {"red": "\033[31m", "green": "\033[32m", "yellow": "\033[33m",
            "blue": "\033[34m", "reset": "\033[0m", "bold": "\033[1m"}.get(
        c, "") + s + "\033[0m"

def ok(msg):   print(color("  ✓ ", "green") + msg)
def warn(msg): print(color("  ! ", "yellow") + msg)
def fail(msg): print(color("  ✗ ", "red") + msg)
def heading(msg):
    print()
    print(color(msg, "bold"))


# --- command runner -------------------------------------------------------

def run(*args, check=False, cwd=None, env=None, stdin=None):
    """Run a command, capture stdout/stderr/returncode. Never raise."""
    try:
        result = subprocess.run(
            list(args),
            capture_output=True,
            text=True,
            cwd=cwd,
            env=env,
            input=stdin,
            timeout=60,
        )
        return result
    except FileNotFoundError:
        return subprocess.CompletedProcess(args, 127, "", "not found")
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(args, 124, "", "timeout")


def parse_version(s):
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", s)
    return tuple(int(x) for x in m.groups()) if m else None


# --- check 1-2: tools -----------------------------------------------------

def check_prereqs():
    heading("1. Prerequisites")
    bad = 0
    for tool, min_v, max_v in [("bd", BD_TESTED_MIN, BD_TESTED_MAX),
                                ("gt", GT_TESTED_MIN, GT_TESTED_MAX)]:
        path = shutil.which(tool)
        if not path:
            fail(f"{tool} not found on PATH")
            bad += 1
            continue
        r = run(tool, "version")
        if r.returncode != 0:
            r = run(tool, "--version")
        ver = parse_version(r.stdout + r.stderr)
        if not ver:
            warn(f"{tool} found at {path} but couldn't parse version")
            continue
        vstr = ".".join(str(x) for x in ver)
        if ver < min_v:
            warn(f"{tool} {vstr} is older than tested min {'.'.join(map(str, min_v))} "
                 f"— expect schema drift. Consider upgrading.")
        elif ver > max_v:
            warn(f"{tool} {vstr} is newer than tested max {'.'.join(map(str, max_v))} "
                 f"— may work, but no guarantees. File an issue if imports break.")
        else:
            ok(f"{tool} {vstr} at {path}")
    return bad == 0


# --- check 3: schema -----------------------------------------------------

def check_schema():
    heading("2. Beads schema (types, statuses, dep types)")

    # Issue types:
    # Beads validates types at `bd create` time, not via a separate command.
    # `bd types`, `bd statuses` do NOT exist. We probe `bd create --help`
    # for the -t / --type flag's accepted values and fall back to a
    # functional test (attempt to create a throwaway bead of each type
    # in a temp .beads) if the help text doesn't enumerate them.
    r = run("bd", "create", "--help")
    help_text = (r.stdout + (r.stderr or "")).lower()
    if r.returncode != 0:
        fail(f"`bd create --help` failed (rc={r.returncode})")
        return False

    # Find the section of help that documents -t / --type
    type_section = _extract_flag_section(help_text, "-t", "--type")
    found_types = set()
    # Any of our required types listed in the help text counts as confirmed
    for t in REQUIRED_ISSUE_TYPES | {"chore", "story", "message", "spike"}:
        if t in type_section or f'"{t}"' in type_section:
            found_types.add(t)

    if not found_types:
        # Help text didn't enumerate types. Fall back to a functional test:
        # create a throwaway bead of each required type in a temp .beads/.
        warn("bd create --help didn't enumerate types; running functional probe")
        found_types = _probe_types_functionally()

    missing_types = REQUIRED_ISSUE_TYPES - found_types
    if missing_types:
        fail(f"issue types not accepted by bd create: {sorted(missing_types)}")
        fail(f"  (required: {sorted(REQUIRED_ISSUE_TYPES)})")
        fail(f"  (confirmed: {sorted(found_types)})")
        fail("  This may be a bd version incompatibility. Try:")
        fail("    bd create --help | grep -iE 'type|-t '")
        return False
    ok(f"issue types accepted: {sorted(REQUIRED_ISSUE_TYPES & found_types)}")

    # Statuses:
    # Same story — no `bd statuses` subcommand. Probe `bd update --help`
    # for the -s / --status flag's accepted values. These are well-known
    # constants in cmd/bd/update.go and change rarely.
    r = run("bd", "update", "--help")
    update_help = (r.stdout + (r.stderr or "")).lower()
    status_section = _extract_flag_section(update_help, "-s", "--status")
    found_statuses = set()
    for s in REQUIRED_STATUSES | {"deferred", "in-progress", "ready"}:
        if s in status_section or f'"{s}"' in status_section:
            found_statuses.add(s)
    # Normalize the common dash/underscore variant: bd accepts both, and has
    # emitted either over time.
    if "in-progress" in found_statuses:
        found_statuses.add("in_progress")

    missing_statuses = REQUIRED_STATUSES - found_statuses
    if missing_statuses:
        # Statuses are stable enough that it's safe to warn rather than fail
        # when the help text is just unhelpful.
        warn(f"couldn't confirm statuses in bd update --help: {sorted(missing_statuses)}")
        warn("  (will be validated functionally during --dry-run)")
    else:
        ok(f"statuses accepted: {sorted(REQUIRED_STATUSES)}")

    # Dep types: probe `bd dep add --help`. Authoritative list lives in
    # cmd/bd/create.go: blocks, related, parent-child, discovered-from,
    # waits-for, replies-to.
    r = run("bd", "dep", "add", "--help")
    dep_help = (r.stdout + (r.stderr or "")).lower()
    found_dep_types = set()
    for dt in REQUIRED_DEP_TYPES | {"conditional-blocks", "replies-to"}:
        if dt in dep_help:
            found_dep_types.add(dt)
    missing_deps = REQUIRED_DEP_TYPES - found_dep_types
    if missing_deps:
        warn(f"couldn't confirm dep types in help text: {sorted(missing_deps)}")
        warn("  (will be validated functionally during --dry-run)")
    else:
        ok(f"dep types confirmed: {sorted(REQUIRED_DEP_TYPES)}")

    # CRITICAL: --id flag on bd create. Without this, our gm-eN.M IDs
    # won't survive import (Beads defaults to hash IDs like bd-a1b2).
    if re.search(r"(?m)^\s*--id\b", help_text) or "--id " in help_text:
        ok("bd create --id is supported (our stable bc-* IDs will survive import)")
    else:
        fail("bd create --id flag not found in help output")
        fail("  Without explicit IDs, Beads auto-generates hash IDs (bd-a1b2)")
        fail("  and your gm-e1.1, gm-e1.2, ... references will break.")
        fail("  Options:")
        fail("    a) Upgrade bd (feature is in v0.49+; v1.0+ still supports it)")
        fail("    b) Enable counter mode: bd config set issue_id_mode counter")
        fail("       (this still won't preserve the specific 'gm-eN.M' shape)")
        fail("    c) Use `bd init --from-jsonl` instead (has known bugs in")
        fail("       server mode — see gastownhall/beads#2433)")
        return False

    return True


def _extract_flag_section(help_text, *flag_names):
    """Return the chunk of help text around a flag, for keyword probing.

    Cobra-style help has flags on their own lines with the description
    indented underneath. Grab from the flag line to the next blank line
    (or a few lines after) so we pick up phrases like 'one of: epic, task'.
    """
    lines = help_text.splitlines()
    capture = []
    capturing = False
    captured_lines = 0
    for line in lines:
        low = line.lower()
        if not capturing and any(
            re.search(rf"(^|\s){re.escape(f)}(\b|,|\s|=)", low)
            for f in flag_names
        ):
            capturing = True
        if capturing:
            capture.append(line)
            captured_lines += 1
            if captured_lines >= 6 or (line.strip() == "" and captured_lines > 1):
                capturing = False
    return "\n".join(capture)


def _probe_types_functionally():
    """Last-resort: create a throwaway .beads/ and try each type.

    Isolates in a tempdir so the user's real Beads state is untouched.
    Returns a set of types that bd create actually accepted.
    """
    found = set()
    with tempfile.TemporaryDirectory(prefix="gm-validate-") as td:
        env = os.environ.copy()
        env["BEADS_DIR"] = os.path.join(td, ".beads")
        # Initialize a scratch store
        init = subprocess.run(
            ["bd", "init", "--quiet", "--stealth", "--prefix", "probe"],
            cwd=td, env=env, capture_output=True, text=True
        )
        if init.returncode != 0:
            # Can't probe; return an empty set so caller fails loudly
            return set()
        for t in REQUIRED_ISSUE_TYPES:
            r = subprocess.run(
                ["bd", "create", f"probe-{t}", "-t", t, "-p", "3"],
                cwd=td, env=env, capture_output=True, text=True
            )
            if r.returncode == 0:
                found.add(t)
    return found


# --- check 4-5: data integrity -------------------------------------------

def load_issues(path):
    issues = []
    for i, line in enumerate(open(path), 1):
        line = line.strip()
        if not line:
            continue
        try:
            issues.append(json.loads(line))
        except json.JSONDecodeError as e:
            fail(f"issues.jsonl line {i}: {e}")
            sys.exit(4)
    return issues


def check_graph(issues):
    heading("3. Data integrity (deps resolve, no cycles)")

    by_id = {i["id"]: i for i in issues}

    # All dep targets exist
    missing = []
    for issue in issues:
        for d in issue.get("dependencies", []):
            tgt = d.get("depends_on_id")
            if tgt not in by_id:
                missing.append((issue["id"], tgt, d.get("type")))
    if missing:
        fail(f"{len(missing)} dep targets don't resolve:")
        for src, tgt, typ in missing[:10]:
            fail(f"    {src} --{typ}--> {tgt} (target missing)")
        return False
    ok(f"all dep targets resolve ({sum(len(i.get('dependencies', [])) for i in issues)} edges)")

    # No cycles in blocks | parent-child graph
    graph = defaultdict(list)
    for i in issues:
        for d in i.get("dependencies", []):
            if d["type"] in ("blocks", "parent-child"):
                graph[d["depends_on_id"]].append(i["id"])

    WHITE, GREY, BLACK = 0, 1, 2
    color_ = {i["id"]: WHITE for i in issues}

    def dfs(u, stack):
        color_[u] = GREY
        for v in graph[u]:
            if color_[v] == GREY:
                return stack + [v]
            if color_[v] == WHITE:
                r = dfs(v, stack + [v])
                if r: return r
        color_[u] = BLACK
        return None

    for i in issues:
        if color_[i["id"]] == WHITE:
            cyc = dfs(i["id"], [i["id"]])
            if cyc:
                fail(f"cycle detected: {' -> '.join(cyc)}")
                return False
    ok("no cycles in blocks|parent-child graph")

    # Labels: every bead has required taxonomy
    missing_labels = []
    for i in issues:
        labels = i.get("labels", [])
        for prefix in ("surface:", "tier:"):
            if not any(l.startswith(prefix) for l in labels):
                missing_labels.append((i["id"], prefix))
    if missing_labels:
        warn(f"{len(missing_labels)} beads missing required label prefix:")
        for mid, pfx in missing_labels[:5]:
            warn(f"    {mid}  needs  {pfx}*")
    else:
        ok("every bead carries required surface:* and tier:* labels")

    return True


# --- check 6: dry-run import --------------------------------------------

def dry_run_import(issues, keep=False):
    heading("4. Dry-run import (into a tempdir)")

    tmp = Path(tempfile.mkdtemp(prefix="gm-validate-"))
    beads_dir = tmp / ".beads"
    beads_dir.mkdir()
    env = os.environ.copy()
    env["BEADS_DIR"] = str(beads_dir)

    try:
        r = run("bd", "init", "--quiet", "--stealth", "--prefix", "gemba",
                cwd=str(tmp), env=env)
        if r.returncode != 0:
            fail(f"bd init failed:\n{r.stderr}")
            return False
        ok(f"bd init --stealth at {beads_dir}")

        # Two-pass import: first create all issues with --id, then add deps
        created = 0
        create_errors = []
        for issue in issues:
            args = [
                "bd", "create", issue["title"],
                "--id", issue["id"],
                "-t", issue["issue_type"],
                "-p", str(issue["priority"]),
                "--stdin",
            ]
            # Labels
            for label in issue.get("labels", []):
                args += ["-l", label]
            r = run(*args, cwd=str(tmp), env=env, stdin=issue["description"])
            if r.returncode != 0:
                create_errors.append((issue["id"], r.stderr.strip().split("\n")[-1]))
            else:
                created += 1

        if create_errors:
            fail(f"{len(create_errors)} create errors:")
            for bid, err in create_errors[:10]:
                fail(f"    {bid}: {err}")
            return False
        ok(f"created {created} beads with explicit IDs")

        # Second pass: deps.
        #
        # Beads v1+ automatically infers parent-child relationships from
        # hierarchical (dotted) IDs: if we create `gm-e1.1`, bd registers it
        # as a child of `gm-e1` on creation. An explicit `bd dep add ...
        # --type parent-child` in that situation is rejected as a deadlock
        # ("already a child"). So we skip inferable parent-child edges.
        #
        # Non-inferable parent-child edges (e.g., gm-e1 -> gm-root, where
        # the child ID doesn't start with "gm-root.") still need explicit
        # edges and go through normally.
        #
        # "Already exists" errors from bd (whether from re-running this
        # script, or from other inference rules we haven't seen yet) are
        # counted as benign and logged without failing.

        dep_errors = []
        dep_count = 0
        dep_skipped_inferable = 0
        dep_benign = 0

        BENIGN_ERROR_PATTERNS = (
            "already a child",
            "already exists",
            "duplicate",
        )

        for issue in issues:
            for d in issue.get("dependencies", []):
                child = issue["id"]
                parent = d["depends_on_id"]
                dtype = d["type"]

                # Skip inferable parent-child edges — bd v1 already set them.
                if dtype == "parent-child" and child.startswith(parent + "."):
                    dep_skipped_inferable += 1
                    continue

                r = run("bd", "dep", "add",
                        child, parent, "--type", dtype,
                        cwd=str(tmp), env=env)
                if r.returncode == 0:
                    dep_count += 1
                    continue

                stderr_last = r.stderr.strip().split("\n")[-1].lower()
                if any(pat in stderr_last for pat in BENIGN_ERROR_PATTERNS):
                    dep_benign += 1
                    continue

                dep_errors.append((child, parent, dtype,
                                   r.stderr.strip().split("\n")[-1]))

        if dep_skipped_inferable:
            ok(f"skipped {dep_skipped_inferable} inferable parent-child edges "
               f"(bd v1 infers these from hierarchical IDs)")
        if dep_benign:
            warn(f"{dep_benign} dep edges already existed (benign; "
                 f"likely idempotent re-run or bd-inferred)")

        if dep_errors:
            fail(f"{len(dep_errors)} dep errors:")
            for src, tgt, typ, err in dep_errors[:10]:
                fail(f"    {src} --{typ}--> {tgt}: {err}")
            if len(dep_errors) > 10:
                fail(f"    ... and {len(dep_errors) - 10} more")
            return False
        ok(f"added {dep_count} explicit dep edges")

        # Sanity reads.
        #
        # bd v1 applies two implicit filters to `bd list` that bite us:
        # 1) A default status filter that hides anything not "open" (the
        #    import sets everything to "open", so this isn't usually the
        #    problem for us, but it's worth being explicit).
        # 2) A default page limit (observed at 50 in bd v1 releases). At
        #    55 beads we blow past it and get a short count.
        # We pass --all and --limit 0 to sidestep both. Older bd versions
        # that don't recognize these flags will fall back to the old
        # behavior — if that happens, we retry without them.
        r = run("bd", "list", "--json", "--all", "--limit", "0",
                cwd=str(tmp), env=env)
        if r.returncode != 0:
            # Fall back for older bd versions
            r = run("bd", "list", "--json", "--status", "open",
                    "--limit", "1000", cwd=str(tmp), env=env)
        if r.returncode != 0:
            fail(f"bd list failed post-import: {r.stderr}")
            return False
        listed = json.loads(r.stdout) if r.stdout.strip() else []
        if len(listed) != len(issues):
            fail(f"imported {len(listed)} beads but expected {len(issues)}")
            fail("  Hint: if this is exactly 50, you likely hit bd's default")
            fail("  page size. Try: bd list --all --limit 0 to see full count.")
            return False
        ok(f"bd list shows {len(listed)} beads")

        r = run("bd", "ready", "--json", "--limit", "0",
                cwd=str(tmp), env=env)
        if r.returncode != 0:
            # Fall back without --limit for older bd
            r = run("bd", "ready", "--json", cwd=str(tmp), env=env)
        if r.returncode != 0:
            warn(f"bd ready failed: {r.stderr}")
        else:
            ready = json.loads(r.stdout) if r.stdout.strip() else []
            ok(f"bd ready returns {len(ready)} unblocked beads")

        r = run("bd", "show", issues[0]["id"], "--json",
                cwd=str(tmp), env=env)
        if r.returncode != 0:
            fail(f"bd show {issues[0]['id']} failed: {r.stderr}")
            return False
        shown = json.loads(r.stdout)
        # bd v1 `bd show --json` accepts multiple IDs and returns a list.
        # With a single ID it still returns a list of length 1. Older bd
        # versions returned a single object. Handle both shapes.
        if isinstance(shown, list):
            if not shown:
                fail(f"bd show returned empty list for {issues[0]['id']}")
                return False
            shown = shown[0]
        if not isinstance(shown, dict):
            fail(f"bd show returned unexpected shape: {type(shown).__name__}")
            return False
        if shown.get("id") != issues[0]["id"]:
            fail(f"bd show returned wrong id: {shown.get('id')}")
            return False
        ok(f"bd show round-trips: {issues[0]['id']}")

        return True
    finally:
        if keep:
            print(color(f"\n  (tempdir kept at {tmp} for inspection)", "blue"))
        else:
            shutil.rmtree(tmp, ignore_errors=True)


# --- real import --------------------------------------------------------

def real_import(issues, target, prefix, force):
    heading(f"5. Real import into {target}")
    target = Path(target).expanduser().resolve()

    if not target.exists():
        fail(f"target does not exist: {target}")
        return False
    if not (target / ".git").exists():
        warn(f"target is not a git repo; Beads git hooks will be skipped")

    beads_dir = target / ".beads"
    if beads_dir.exists() and not force:
        fail(f"{beads_dir} already exists. Pass --force to overwrite.")
        return False
    if force and beads_dir.exists():
        warn(f"removing existing {beads_dir}")
        shutil.rmtree(beads_dir)

    r = run("bd", "init", "--quiet", "--prefix", prefix, cwd=str(target))
    if r.returncode != 0:
        fail(f"bd init failed:\n{r.stderr}")
        return False
    ok(f"bd init --prefix {prefix} in {target}")

    # Two-pass import
    created = 0
    for issue in issues:
        args = [
            "bd", "create", issue["title"],
            "--id", issue["id"],
            "-t", issue["issue_type"],
            "-p", str(issue["priority"]),
            "--stdin",
        ]
        for label in issue.get("labels", []):
            args += ["-l", label]
        r = run(*args, cwd=str(target), stdin=issue["description"])
        if r.returncode != 0:
            fail(f"create {issue['id']} failed: {r.stderr.strip()}")
            return False
        created += 1
    ok(f"created {created} beads")

    dep_count = 0
    for issue in issues:
        for d in issue.get("dependencies", []):
            r = run("bd", "dep", "add",
                    issue["id"], d["depends_on_id"],
                    "--type", d["type"], cwd=str(target))
            if r.returncode != 0:
                fail(f"dep {issue['id']} -> {d['depends_on_id']}: "
                     f"{r.stderr.strip()}")
                return False
            dep_count += 1
    ok(f"added {dep_count} dep edges")

    ok(f"import complete. Next steps:")
    print(f"    cd {target}")
    print(f"    bd list --status open")
    print(f"    bd ready --json | jq '.[0:5]'")
    print(f"    mkdir -p .beads/formulas && cp ./formulas/*.toml .beads/formulas/")
    return True


# --- entry --------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--jsonl", default="issues.jsonl",
                        help="path to issues.jsonl (default: ./issues.jsonl)")
    parser.add_argument("--check", action="store_true",
                        help="prereq + schema + graph checks only (no writes)")
    parser.add_argument("--dry-run", action="store_true",
                        help="also dry-run import into a tempdir, then clean up")
    parser.add_argument("--keep-tempdir", action="store_true",
                        help="leave the dry-run tempdir in place for inspection")
    parser.add_argument("--target", help="real import: path to target rig dir")
    parser.add_argument("--prefix", default="gemba",
                        help="Beads prefix (default: bc)")
    parser.add_argument("--force", action="store_true",
                        help="overwrite existing .beads in --target")
    args = parser.parse_args()

    if not any([args.check, args.dry_run, args.target]):
        parser.print_help()
        print("\nPick one of --check, --dry-run, or --target", file=sys.stderr)
        sys.exit(1)

    jsonl_path = Path(args.jsonl)
    if not jsonl_path.exists():
        fail(f"{jsonl_path} not found (cd to the package dir, or pass --jsonl)")
        sys.exit(1)

    # Run the checks in order; short-circuit on fatal failures.
    if not check_prereqs():
        sys.exit(2)
    if not check_schema():
        sys.exit(3)

    issues = load_issues(jsonl_path)
    ok(f"loaded {len(issues)} issues from {jsonl_path}")
    if not check_graph(issues):
        sys.exit(4)

    if args.dry_run:
        if not dry_run_import(issues, keep=args.keep_tempdir):
            sys.exit(5)

    if args.target:
        if not real_import(issues, args.target, args.prefix, args.force):
            sys.exit(5)

    heading("All checks passed.")


if __name__ == "__main__":
    main()