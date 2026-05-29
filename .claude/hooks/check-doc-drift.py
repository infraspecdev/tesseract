#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pyyaml>=6.0",
# ]
# ///
"""check-doc-drift.py — Stop hook: soft reminder when source moves without docs.

Reads `.claude/hooks/doc-drift-map.yaml`, walks the current working-tree diff
against HEAD plus untracked files, and prints one stderr block per rule whose
source glob matches a touched file but whose listed docs are untouched.

Design properties
-----------------
- **Soft.** Exit code is always 0. The hook is advisory; it never blocks
  Claude, the user, or `git commit`. Drift severity is a separate concern
  (we could add a pre-commit gate later if reminders prove insufficient).
- **Stateless.** Diff is computed fresh each run from `git`. No cache; no
  hidden state file. The hook produces the same output for the same working
  tree, regardless of how often it's invoked.
- **Honest about scope.** Hint mentions the rule's source glob AND the
  touched files AND the candidate docs — never a vague "you might want to
  update docs." Easy to skim and decide whether to act.
- **Quiet by default.** Empty working tree → empty output. Test files,
  `*.lock`, `*.tmp` are filtered as noise per NOISE_PATTERNS.

Wired in `.claude/settings.json` under `hooks.Stop[]`:

    uv run --with pyyaml ${CLAUDE_PROJECT_DIR}/.claude/hooks/check-doc-drift.py

The `uv run` wrapper installs pyyaml ephemerally; no global pip needed.
"""
from __future__ import annotations

import fnmatch
import os
import re
import subprocess
import sys
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover — uv handles this in normal use
    # If pyyaml isn't available the hook can't read the map; degrade to silent
    # rather than spam the user with a setup error on every Stop.
    sys.exit(0)


def _repo_root() -> Path:
    """`$CLAUDE_PROJECT_DIR` when invoked by the Claude Code harness; cwd
    otherwise (handy for running the script by hand during smoke tests)."""
    env_root = os.environ.get("CLAUDE_PROJECT_DIR")
    return Path(env_root).resolve() if env_root else Path.cwd().resolve()


# Files we never warn about even when they match a source glob — these are
# internal-only and rarely need an artifacts.md / README.md update.
NOISE_PATTERNS = (
    "test_*.py",
    "*_test.py",
    "*.lock",
    "*.tmp",
    "*.bak",
    "__init__.py",
)


def _is_noise(path: str) -> bool:
    name = Path(path).name
    return any(fnmatch.fnmatch(name, pat) for pat in NOISE_PATTERNS)


def _glob_to_regex(glob: str) -> re.Pattern:
    """Compile a git/gitignore-style glob to a regex.

    Semantics:
      `*`  matches any chars EXCEPT `/`  (single path segment)
      `?`  matches a single char except `/`
      `**` matches any number of chars INCLUDING `/`  (cross-segment)

    Plain `fnmatch.fnmatch` doesn't distinguish `*` from `**` (its `*` happily
    matches `/`), and `pathlib.Path.match` has incomplete `**`-in-middle
    support, so we roll our own. Cheap; the path counts here are tiny.
    """
    parts = glob.split("**")
    chunks: list[str] = []
    for part in parts:
        sub = []
        for ch in part:
            if ch == "*":
                sub.append("[^/]*")
            elif ch == "?":
                sub.append("[^/]")
            else:
                sub.append(re.escape(ch))
        chunks.append("".join(sub))
    return re.compile(".*".join(chunks))  # `**` → `.*` (cross-segment)


def _matches(path: str, glob: str) -> bool:
    """True iff `path` matches `glob` under git-style semantics (see above)."""
    return bool(_glob_to_regex(glob).fullmatch(path))


def _modified_files(repo_root: Path) -> set[str]:
    """Files modified, staged, or untracked vs HEAD in `repo_root`.

    Returns an empty set on any git failure (no repo, git missing, etc.) so
    the hook degrades to silent rather than crashing the harness.
    """
    try:
        diff = subprocess.run(
            ["git", "-C", str(repo_root), "diff", "--name-only", "HEAD"],
            capture_output=True, text=True, timeout=5, check=False,
        )
        untracked = subprocess.run(
            ["git", "-C", str(repo_root), "ls-files",
             "--others", "--exclude-standard"],
            capture_output=True, text=True, timeout=5, check=False,
        )
    except (subprocess.SubprocessError, FileNotFoundError):
        return set()
    if diff.returncode != 0 and untracked.returncode != 0:
        return set()
    lines = diff.stdout.splitlines() + untracked.stdout.splitlines()
    return {p.strip() for p in lines if p.strip()}


def _load_rules(map_path: Path) -> list[dict]:
    """Parse the drift map. Returns an empty list on any error so a missing
    or malformed map degrades to silent rather than crashing."""
    if not map_path.is_file():
        return []
    try:
        parsed = yaml.safe_load(map_path.read_text()) or {}
    except yaml.YAMLError:
        return []
    rules = parsed.get("rules", [])
    return rules if isinstance(rules, list) else []


def compute_hints(rules: list[dict], touched: set[str]) -> list[str]:
    """Pure function over inputs — easy to unit-test without git or stdio."""
    hints: list[str] = []
    for rule in rules:
        src_glob = rule.get("source", "")
        docs = rule.get("docs", []) or []
        if not src_glob or not docs:
            continue

        touched_sources = sorted(
            p for p in touched
            if _matches(p, src_glob) and not _is_noise(p)
        )
        if not touched_sources:
            continue

        missing_docs = [d for d in docs if d not in touched]
        if not missing_docs:
            continue  # docs ARE being updated alongside — nothing to remind

        sources_str = "\n    ".join(touched_sources)
        docs_str = "\n    ".join(f"- {d}" for d in missing_docs)
        hints.append(
            "  Source moved without its docs:\n"
            f"    sources matching `{src_glob}`:\n      {sources_str}\n"
            f"    docs that may need updating:\n      {docs_str.replace(chr(10), chr(10) + '  ')}"
        )
    return hints


def main() -> int:
    repo_root = _repo_root()
    map_path = repo_root / ".claude" / "hooks" / "doc-drift-map.yaml"

    rules = _load_rules(map_path)
    if not rules:
        return 0

    touched = _modified_files(repo_root)
    if not touched:
        return 0

    hints = compute_hints(rules, touched)
    if not hints:
        return 0

    print(
        "\n[shield-docs] check-doc-drift — soft reminder "
        "(advisory; exit 0):",
        file=sys.stderr,
    )
    for hint in hints:
        print(hint, file=sys.stderr)
    print(
        "  Either update the docs above, or ignore this hint.\n",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
