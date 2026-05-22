# shield/scripts/migrate_outputs.py
"""Migrate a Shield output tree from the legacy numbered-run layout to the
flat per-feature layout defined in
docs/superpowers/specs/2026-05-22-shield-output-structure-design.md.

Runnable: `uv run --with pyyaml shield/scripts/migrate_outputs.py [--root docs/shield] [--apply]`
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

# Patterns: (compiled regex on POSIX relpath, callable returning new relpath or None)
_RESEARCH_FINDINGS = re.compile(r"^research/\d+-[^/]+/findings\.md$")
_RESEARCH_TRANSCRIPT = re.compile(r"^research/\d+-[^/]+/transcript\.md$")
_PLAN_ARCH_HTML = re.compile(r"^plan/\d+-[^/]+/architecture\.html$")


def map_legacy_path(relpath: str) -> Optional[str]:
    """Map a path under {output_dir}/{feature}/ to its new location.

    Returns None if the path is already at its new location (no move needed) or
    is unrecognized (caller decides whether to warn).
    """
    if _RESEARCH_FINDINGS.match(relpath):
        return "research.md"
    if _RESEARCH_TRANSCRIPT.match(relpath):
        return ".session-transcript.md"
    if _PLAN_ARCH_HTML.match(relpath):
        return "outputs/plan-architecture.html"
    return None
