#!/usr/bin/env python3
"""
merge-import.py — Import Gemba work package into an EXISTING
Beads store without re-initializing.

Use this when `gt rig add` has already set up the rig with infrastructure
beads (rig identity, patrols, etc.) that you want to preserve. The
validator's `--target` path wants a clean .beads/; this script instead
layers the Gemba work package beads on top of whatever's there.

Usage:
    ./merge-import.py --target ~/gt/gemba

Assumes ./issues.jsonl and ./formulas/ are next to this script.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def run(*args, cwd=None, stdin=None):
    r = subprocess.run(
        args, cwd=cwd, input=stdin, text=True,
        capture_output=True,
    )
    return r


def ok(msg):   print(f"  \033[32m✓\033[0m {msg}")
def warn(msg): print(f"  \033[33m!\033[0m {msg}")
def fail(msg): print(f"  \033[31m✗\033[0m {msg}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", required=True,
                        help="Path to the rig directory (e.g. ~/gt/gemba)")
    parser.add_argument("--jsonl", default="issues.jsonl",
                        help="Path to issues.jsonl (default: ./issues.jsonl)")
    parser.add_argument("--formulas-dir", default="formulas",
                        help="Path to formulas/ (default: ./formulas)")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    script_dir = Path(__file__).resolve().parent
    jsonl_path = (script_dir / args.jsonl) if not Path(args.jsonl).is_absolute() else Path(args.jsonl)
    formulas_src = (script_dir / args.formulas_dir) if not Path(args.formulas_dir).is_absolute() else Path(args.formulas_dir)

    # Preflight
    print(f"\n\033[1m1. Preflight\033[0m")
    if not target.exists():
        fail(f"target does not exist: {target}")
        sys.exit(2)
    beads_dir = target / ".beads"
    if not beads_dir.is_dir():
        fail(f"{beads_dir} does not exist. Run `gt rig add` first, or use "
             f"validate-import.py --target --force for a fresh init.")
        sys.exit(2)
    ok(f"target rig exists: {target}")
    ok(f".beads/ store exists: {beads_dir}")

    if not jsonl_path.is_file():
        fail(f"issues.jsonl not found at {jsonl_path}")
        sys.exit(2)

    # Show pre-state
    r = run("bd", "list", "--all", "--limit", "0", "--json", cwd=str(target))
    if r.returncode != 0:
        fail(f"bd list failed — is the store healthy?\n{r.stderr}")
        sys.exit(3)
    existing = json.loads(r.stdout) if r.stdout.strip() else []
    existing_ids = {b.get("id") for b in existing if isinstance(b, dict)}
    ok(f"{len(existing)} existing beads in store")
    if existing:
        print(f"      existing IDs: {sorted(existing_ids)}")

    # Load work package
    print(f"\n\033[1m2. Load work package\033[0m")
    issues = [json.loads(line) for line in open(jsonl_path) if line.strip()]
    ok(f"loaded {len(issues)} beads from {jsonl_path}")

    incoming_ids = {i["id"] for i in issues}
    collisions = existing_ids & incoming_ids
    if collisions:
        fail(f"ID collision! These IDs exist in both store and work package:")
        for c in sorted(collisions):
            fail(f"    {c}")
        fail("  Either rename the conflicting beads or run validate-import "
             "with --force (destructive).")
        sys.exit(3)
    ok(f"no ID collisions with existing beads")

    # Pass 1: create beads
    print(f"\n\033[1m3. Create beads\033[0m")
    created = 0
    failures = []
    for issue in issues:
        cmd = [
            "bd", "create", issue["title"],
            "--id", issue["id"],
            "-t", issue["issue_type"],
            "-p", str(issue["priority"]),
            "--stdin",
        ]
        for label in issue.get("labels", []):
            cmd += ["-l", label]
        r = run(*cmd, cwd=str(target), stdin=issue["description"])
        if r.returncode == 0:
            created += 1
        else:
            stderr_last = r.stderr.strip().split("\n")[-1].lower() if r.stderr else ""
            if "already exists" in stderr_last or "duplicate" in stderr_last:
                # Benign — probably a retry
                continue
            failures.append((issue["id"], r.stderr.strip()))

    if failures:
        fail(f"{len(failures)} create failures:")
        for bid, err in failures[:10]:
            fail(f"    {bid}: {err.splitlines()[-1] if err else '(no stderr)'}")
        sys.exit(3)
    ok(f"created {created} beads")

    # Pass 2: deps
    print(f"\n\033[1m4. Dep edges\033[0m")
    BENIGN = ("already a child", "already exists", "duplicate")
    dep_count = 0
    dep_skipped_inferable = 0
    dep_benign = 0
    dep_errors = []

    for issue in issues:
        for d in issue.get("dependencies", []):
            child = issue["id"]
            parent = d["depends_on_id"]
            dtype = d["type"]

            # Skip inferable parent-child — bd v1 infers from dotted IDs
            if dtype == "parent-child" and child.startswith(parent + "."):
                dep_skipped_inferable += 1
                continue

            r = run("bd", "dep", "add", child, parent,
                    "--type", dtype, cwd=str(target))
            if r.returncode == 0:
                dep_count += 1
                continue

            stderr_last = r.stderr.strip().split("\n")[-1].lower()
            if any(pat in stderr_last for pat in BENIGN):
                dep_benign += 1
                continue
            dep_errors.append((child, parent, dtype,
                               r.stderr.strip().split("\n")[-1]))

    if dep_skipped_inferable:
        ok(f"skipped {dep_skipped_inferable} inferable parent-child edges "
           f"(bd v1 auto-infers these)")
    if dep_benign:
        warn(f"{dep_benign} edges already existed (benign)")
    if dep_errors:
        fail(f"{len(dep_errors)} dep errors:")
        for src, tgt, typ, err in dep_errors[:10]:
            fail(f"    {src} --{typ}--> {tgt}: {err}")
        sys.exit(3)
    ok(f"added {dep_count} explicit dep edges")

    # Link the work package to the rig identity bead so Gas Town's tooling
    # understands the association. The rig identity bead was created by
    # `gt rig add` and is labeled gt:rig.
    print(f"\n\033[1m5. Link to rig identity\033[0m")
    rig_bead = None
    for b in existing:
        if isinstance(b, dict) and "gt:rig" in (b.get("labels") or []):
            rig_bead = b
            break

    if rig_bead:
        rig_id = rig_bead["id"]
        r = run("bd", "dep", "add", "gm-root", rig_id,
                "--type", "related", cwd=str(target))
        stderr_last = (r.stderr or "").strip().split("\n")[-1].lower()
        if r.returncode == 0:
            ok(f"linked gm-root <-related-> {rig_id}")
        elif any(pat in stderr_last for pat in BENIGN):
            ok(f"gm-root already related to {rig_id} (benign)")
        else:
            warn(f"couldn't link gm-root to rig identity: {r.stderr.strip()}")
    else:
        warn("no gt:rig labeled bead found; skipping rig linkage")

    # Copy formulas
    print(f"\n\033[1m6. Formulas\033[0m")
    formulas_dst = beads_dir / "formulas"
    if formulas_src.is_dir():
        formulas_dst.mkdir(parents=True, exist_ok=True)
        copied = 0
        for toml in formulas_src.glob("*.toml"):
            shutil.copy2(toml, formulas_dst / toml.name)
            copied += 1
        if copied:
            ok(f"copied {copied} molecule formulas to {formulas_dst}")
        else:
            warn(f"no .toml files in {formulas_src}")
    else:
        warn(f"formulas dir not found at {formulas_src} — skipping")

    # Verify
    print(f"\n\033[1m7. Verify\033[0m")
    r = run("bd", "list", "--all", "--limit", "0", "--json", cwd=str(target))
    final = json.loads(r.stdout) if r.stdout.strip() else []
    expected = len(existing) + len(issues)
    if len(final) == expected:
        ok(f"bd list shows {len(final)} beads "
           f"({len(existing)} existing + {len(issues)} imported)")
    else:
        fail(f"bd list shows {len(final)}, expected {expected}")
        sys.exit(3)

    r = run("bd", "ready", "--json", "--limit", "0", cwd=str(target))
    ready = json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else []
    ok(f"bd ready returns {len(ready)} unblocked beads")

    r = run("bd", "show", "gm-root", "--json", cwd=str(target))
    if r.returncode == 0:
        shown = json.loads(r.stdout)
        if isinstance(shown, list) and shown:
            shown = shown[0]
        if isinstance(shown, dict) and shown.get("id") == "gm-root":
            ok(f"gm-root round-trips cleanly")

    print(f"\n\033[32m\033[1m✓ Import complete.\033[0m")
    print(f"\n  Next steps:")
    print(f"    cd {target}")
    print(f"    bd ready --json --limit 0 | jq '.[] | {{id, title, priority}}'")
    print(f"    bd show gm-root   # read the twelve locked decisions")
    print(f"    git add .beads/")
    print(f"    git commit -m 'Import Gemba v3.1 work package'")
    print(f"    git push")


if __name__ == "__main__":
    main()