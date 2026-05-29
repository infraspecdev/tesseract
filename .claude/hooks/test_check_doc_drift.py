"""Tests for .claude/hooks/check-doc-drift.py.

Two layers:
- Unit tests over `compute_hints` — pure function, no git/stdio.
- One integration test that builds a tempdir git repo, mutates a source
  file (no doc update), and asserts the script's stderr contains the hint.

Run via uv:

    uv run --with pyyaml .claude/hooks/test_check_doc_drift.py
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parent
SCRIPT = HOOK_DIR / "check-doc-drift.py"

# Load the hook as a module so we can import compute_hints / _is_noise /
# _matches for the unit tests. The script's filename has a hyphen, so plain
# `import` won't work — use importlib.util instead.
_spec = importlib.util.spec_from_file_location("check_doc_drift", SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)  # type: ignore[union-attr]
compute_hints = mod.compute_hints
_is_noise = mod._is_noise
_matches = mod._matches


# ───────────────────────── pure-function tests ─────────────────────────

def test_match_fnmatch_no_doublestar() -> None:
    assert _matches("shield/commands/foo.md", "shield/commands/*.md")
    assert not _matches("shield/commands/sub/foo.md", "shield/commands/*.md")


def test_match_doublestar_walks_dirs() -> None:
    assert _matches("shield/skills/general/plan-docs/SKILL.md",
                    "shield/skills/**/SKILL.md")
    assert _matches("shield/skills/devcontainer/SKILL.md",
                    "shield/skills/**/SKILL.md")
    assert not _matches("shield/scripts/foo.py", "shield/skills/**/SKILL.md")


def test_noise_filters_test_files() -> None:
    assert _is_noise("shield/scripts/test_foo.py")
    assert _is_noise("shield/scripts/foo_test.py")
    assert not _is_noise("shield/scripts/render_trd_section.py")


def test_no_rules_no_hints() -> None:
    assert compute_hints([], {"shield/scripts/foo.py"}) == []


def test_source_touched_doc_not_touched_yields_hint() -> None:
    rules = [{
        "source": "shield/scripts/*.py",
        "docs": ["shield/docs/artifacts.md"],
    }]
    hints = compute_hints(rules, {"shield/scripts/foo.py"})
    assert len(hints) == 1
    assert "shield/scripts/foo.py" in hints[0]
    assert "shield/docs/artifacts.md" in hints[0]


def test_source_and_doc_co_touched_no_hint() -> None:
    """The whole point of the hook — co-modification clears the reminder."""
    rules = [{
        "source": "shield/scripts/*.py",
        "docs": ["shield/docs/artifacts.md"],
    }]
    hints = compute_hints(
        rules,
        {"shield/scripts/foo.py", "shield/docs/artifacts.md"},
    )
    assert hints == []


def test_noise_files_dont_trigger_hint() -> None:
    rules = [{
        "source": "shield/scripts/*.py",
        "docs": ["shield/docs/artifacts.md"],
    }]
    # test_*.py is the only source matching the glob → filtered as noise
    hints = compute_hints(rules, {"shield/scripts/test_foo.py"})
    assert hints == []


def test_multiple_docs_partial_co_modification_still_hints() -> None:
    """If a rule lists multiple docs and only one is touched, the others
    still get flagged — the rule is treated as AND, not OR."""
    rules = [{
        "source": "shield/skills/**/SKILL.md",
        "docs": ["shield/docs/artifacts.md", "shield/README.md"],
    }]
    hints = compute_hints(
        rules,
        {"shield/skills/general/plan-docs/SKILL.md",
         "shield/docs/artifacts.md"},
    )
    assert len(hints) == 1
    assert "shield/README.md" in hints[0]
    assert "shield/docs/artifacts.md" not in hints[0]


def test_rule_with_no_matching_source_silent() -> None:
    rules = [{"source": "shield/commands/*.md", "docs": ["shield/README.md"]}]
    assert compute_hints(rules, {"shield/scripts/foo.py"}) == []


# ───────────────────────── integration ─────────────────────────

def test_end_to_end_in_temp_repo() -> None:
    """Build a tiny git repo, mutate a Shield source, run the hook, assert
    the reminder lands on stderr. Covers the script's git-diff path and CLI."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        subprocess.run(["git", "-C", str(root), "init", "-q"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.email",
                        "test@example.com"], check=True)
        subprocess.run(["git", "-C", str(root), "config", "user.name",
                        "test"], check=True)

        # Seed: a SKILL.md, a docs file, and the drift map. Commit so HEAD
        # exists and `git diff --name-only HEAD` is meaningful.
        (root / "shield" / "skills" / "demo").mkdir(parents=True)
        (root / "shield" / "skills" / "demo" / "SKILL.md").write_text(
            "---\nname: demo\ndescription: x\n---\nbody")
        (root / "shield" / "docs").mkdir(parents=True)
        (root / "shield" / "docs" / "artifacts.md").write_text(
            "# Artifacts\n\nDemo skill: x.")
        (root / ".claude" / "hooks").mkdir(parents=True)
        (root / ".claude" / "hooks" / "doc-drift-map.yaml").write_text(
            textwrap.dedent(
                """
                rules:
                  - source: shield/skills/**/SKILL.md
                    docs: [shield/docs/artifacts.md]
                """
            )
        )
        subprocess.run(["git", "-C", str(root), "add", "-A"], check=True)
        subprocess.run(
            ["git", "-C", str(root), "commit", "-q", "-m", "seed"],
            check=True,
        )

        # Drift: mutate SKILL.md, leave docs untouched.
        (root / "shield" / "skills" / "demo" / "SKILL.md").write_text(
            "---\nname: demo\ndescription: changed\n---\nnew body")

        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
        proc = subprocess.run(
            ["uv", "run", "--with", "pyyaml", str(SCRIPT)],
            capture_output=True, text=True, env=env, check=False,
        )
        assert proc.returncode == 0, "hook must exit 0 (advisory)"
        assert "check-doc-drift" in proc.stderr, proc.stderr
        assert "shield/skills/demo/SKILL.md" in proc.stderr, proc.stderr
        assert "shield/docs/artifacts.md" in proc.stderr, proc.stderr

        # Co-modify the doc → reminder clears.
        (root / "shield" / "docs" / "artifacts.md").write_text(
            "# Artifacts\n\nDemo skill: x. UPDATED.")
        proc = subprocess.run(
            ["uv", "run", "--with", "pyyaml", str(SCRIPT)],
            capture_output=True, text=True, env=env, check=False,
        )
        assert proc.returncode == 0
        assert "check-doc-drift" not in proc.stderr, (
            "hint should clear once docs are co-modified, got:\n"
            + proc.stderr
        )


# ───────────────────────── runner ─────────────────────────

def _runner() -> int:
    failures: list[str] = []
    tests = sorted(
        (name, fn)
        for name, fn in globals().items()
        if name.startswith("test_") and callable(fn)
    )
    for name, fn in tests:
        try:
            fn()
            print(f"  ok   {name}")
        except AssertionError as e:
            failures.append(f"  FAIL {name}: {e}")
            print(failures[-1])
        except Exception as e:  # noqa: BLE001
            failures.append(f"  ERR  {name}: {type(e).__name__}: {e}")
            print(failures[-1])
    print(f"\n{len(failures)} failure(s)" if failures else "\nall green")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(_runner())
