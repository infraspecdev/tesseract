"""shield/scripts/run_step_5h.py — CLI wrapper for /implement's step 5h promotion.

Usage:
  python run_step_5h.py --plan-json <path> --milestone-id <id> --feature-dir <path>
      [--canonical-dir <path>]

Walks plan.json milestones[<id>].touches_lld[]; for each component:
- Locate draft at <feature-dir>/lld-<name>.md (auto-heal JIT if missing).
- Concurrency check: fork_blob_sha vs current canonical blob.
- Append §14 Changelog row.
- Atomic promote → <canonical-dir>/<name>.md.
- Back-fill design_refs[] anchor_url.

This wrapper is the executable form of the step-5h prose in
shield/skills/general/implement-feature/SKILL.md. The eval runner invokes it
to simulate milestone close.

`--canonical-dir` defaults to `<repo_root>/docs/lld`; eval runners pass an
isolated temp dir.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / "shield" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))
from lld_blob_sha import blob_sha  # noqa: E402
from lld_anchor_heuristic import select_anchor  # noqa: E402


def _load_template_sections(template_type: str) -> list[dict]:
    path = REPO_ROOT / "shield" / "schema" / f"lld-sections-{template_type}.yaml"
    return yaml.safe_load(path.read_text())["sections"]


def _slug_metadata(slug_id: str, sections: list[dict]) -> tuple[int, str]:
    for s in sections:
        if s["id"] == slug_id:
            return s["number"], s["title"]
    return 0, "Unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan-json", required=True)
    parser.add_argument("--milestone-id", required=True)
    parser.add_argument("--feature-dir", required=True)
    parser.add_argument("--canonical-dir", default=None,
                        help="Directory for canonical LLDs (default: <repo>/docs/lld)")
    args = parser.parse_args()

    plan_path = Path(args.plan_json)
    plan = json.loads(plan_path.read_text())
    feature_dir = Path(args.feature_dir)
    canonical_dir = Path(args.canonical_dir) if args.canonical_dir else REPO_ROOT / "docs" / "lld"
    canonical_dir.mkdir(parents=True, exist_ok=True)

    milestone = next(m for m in plan["milestones"] if m["id"] == args.milestone_id)
    touches = milestone.get("touches_lld", [])
    registry = {c["name"]: c for c in plan.get("lld_components", [])}

    exit_code = 0
    for name in touches:
        entry = registry.get(name)
        if not entry:
            print(
                f"ERROR: touches_lld references '{name}' but no lld_components[] entry",
                file=sys.stderr,
            )
            exit_code = 1
            continue
        ttype = entry["type"]
        fork_sha = entry.get("fork_blob_sha")
        if fork_sha == "FILL_AT_RUNTIME":
            fork_sha = None
        draft_path = feature_dir / f"lld-{name}.md"
        canonical_path = canonical_dir / f"{name}.md"

        # 2. Locate draft (JIT auto-heal if missing)
        if not draft_path.exists():
            print(
                f"\n⚠️  DRAFT AUTO-GENERATED AT PROMOTION\n"
                f"    Component: {name}\n"
                f"    The /plan run did not produce {draft_path}.\n"
                f"    /implement just-in-time-drafted the LLD; the design bypassed human review before promotion.\n"
                f"    Review {canonical_path} for content quality before next /plan-review.\n"
            )
            context = {"feature": feature_dir.name, "trd_path": "trd.md"}
            ctx_path = feature_dir / f".lld-context-{name}.json"
            feature_dir.mkdir(parents=True, exist_ok=True)
            ctx_path.write_text(json.dumps(context))
            try:
                subprocess.run(
                    [
                        sys.executable,
                        str(SCRIPTS_DIR / "run_lld_docs.py"),
                        "--component", name,
                        "--type", ttype,
                        "--mode", "draft",
                        "--target", str(draft_path),
                        "--context-json", str(ctx_path),
                    ],
                    check=True,
                )
            finally:
                ctx_path.unlink(missing_ok=True)

        # 3. Concurrency check
        if canonical_path.exists() and fork_sha:
            current_sha = blob_sha(canonical_path)
            if current_sha != fork_sha:
                print(f"Fork drift on {name}: {fork_sha} -> {current_sha}; auto-healing")
                fork_base = feature_dir.parent / "canonical-at-fork.md"
                if fork_base.exists():
                    ctx = {"base_path": str(fork_base), "theirs_path": str(canonical_path)}
                    ctx_path = draft_path.with_suffix(".remerge-ctx.json")
                    ctx_path.write_text(json.dumps(ctx))
                    try:
                        result = subprocess.run(
                            [
                                sys.executable,
                                str(SCRIPTS_DIR / "run_lld_docs.py"),
                                "--component", name,
                                "--type", ttype,
                                "--mode", "remerge",
                                "--target", str(draft_path),
                                "--context-json", str(ctx_path),
                            ],
                            capture_output=True,
                            text=True,
                        )
                    finally:
                        ctx_path.unlink(missing_ok=True)
                    if result.returncode != 0:
                        # Parse conflicting sections from stderr
                        conflicting = "unknown"
                        for line in result.stderr.splitlines():
                            if "conflicting sections:" in line.lower():
                                conflicting = line.split(":", 2)[-1].strip()
                        print(
                            f"ABORT: {plan['name']} — fork drift on '{name}' produced merge conflicts.\n"
                            f"Canonical {canonical_path} changed since /plan drafted.\n"
                            f"Re-run /plan to refresh the fork, then retry /implement.\n"
                            f"Conflicting sections: {conflicting}",
                            file=sys.stderr,
                        )
                        exit_code = 2
                        continue
                entry["fork_blob_sha"] = current_sha

        # 4. Append §14 Changelog row
        touched_stories: list[str] = []
        for epic in plan["epics"]:
            for story in epic["stories"]:
                if story.get("milestone_id") == args.milestone_id:
                    for ref in story.get("design_refs", []):
                        if ref.get("doc") == "lld" and ref.get("component") == name:
                            touched_stories.append(story["id"])
                            break
        row = f"| {args.milestone_id} | {date.today().isoformat()} | {milestone['name']} | {' '.join(touched_stories) or 'n/a'} |\n"
        draft_content = draft_path.read_text()
        if not draft_content.endswith("\n"):
            draft_content += "\n"
        draft_path.write_text(draft_content + row)

        # 5. Atomic promote
        tmp = canonical_path.with_suffix(".md.tmp")
        try:
            tmp.write_text(draft_path.read_text())
            os.replace(tmp, canonical_path)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise

        # 6. Back-fill design_refs[].anchor_url
        sections = _load_template_sections(ttype)
        slugs = [s["id"] for s in sections]
        backfill_counts = {"exact-match": 0, "heuristic": 0, "fallback": 0}
        for epic in plan["epics"]:
            for story in epic["stories"]:
                for ref in story.get("design_refs", []):
                    if (
                        ref.get("doc") == "lld"
                        and ref.get("component") == name
                        and ref.get("anchor_url") is None
                    ):
                        slug, match_type = select_anchor(story["name"], slugs)
                        ref["anchor_url"] = f"lld-{name}.md#{slug}"
                        number, title = _slug_metadata(slug, sections)
                        ref["section_id"] = slug
                        ref["label"] = f"§{number} {title}"
                        backfill_counts[match_type] += 1

        print(
            f"LLD promoted: {name} ({ttype})\n"
            f"  Anchor backfill: {sum(backfill_counts.values())} entries — "
            f"exact-match: {backfill_counts['exact-match']}, "
            f"heuristic: {backfill_counts['heuristic']}, "
            f"fallback: {backfill_counts['fallback']}\n"
        )

    # Write plan.json back
    plan_path.write_text(json.dumps(plan, indent=2))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
