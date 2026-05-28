"""shield/scripts/lld_blob_sha.py

Computes the git blob SHA of an LLD canonical file (`docs/lld/<name>.md`).
Wraps `git hash-object` so the result matches what /implement's
concurrency check at milestone-close will compute. Returns None when the
file is absent (net-new component).
"""
from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


def blob_sha(path: Path | str) -> Optional[str]:
    """Returns `git hash-object <path>` output (40-char hex), or None if absent.

    The hash is computed the same way as git's index — `blob` object type,
    SHA-1. /plan captures this at draft-creation time and persists it as
    plan.json `lld_components[].fork_blob_sha`. /implement re-computes at
    milestone close; mismatch indicates fork drift requiring auto-heal.
    """
    p = Path(path)
    if not p.exists():
        return None
    result = subprocess.run(
        ["git", "hash-object", str(p)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()
