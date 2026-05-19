#!/usr/bin/env python3
"""Validate Feature references in .devcontainer/devcontainer.json.

The Dev Containers CLI applies a path-validation regex to each Feature
reference's path component. The regex does NOT allow ':' in the path,
so a 'name:tag@sha256:digest' combined form is silently rejected before
the registry is even contacted. Caught the hard way on the first manual
'Reopen in Container' smoke run.

This check fires from pre-commit when .devcontainer/devcontainer.json
or scaffolder sources change. It re-implements the CLI's parsing rule
in pure Python so it's offline, fast, and runs without Node installed.

Reference: the CLI's regex is
  /^[a-z0-9]+([._-][a-z0-9]+)*(\\/[a-z0-9]+([._-][a-z0-9]+)*)*$/
applied to the path portion (everything between the registry and any
digest). Digests, when present, follow the path as `@sha256:<64-hex>`.

Exit codes:
  0 — no devcontainer.json present, OR all Feature refs valid
  1 — one or more Feature refs would be rejected by the CLI

Usage:
  python3 shield/scripts/check_devcontainer_refs.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


# Path component regex from the Dev Containers CLI. Lowercase alphanumeric
# segments separated by '/', segments may contain '.', '_', '-' but NOT ':'.
_PATH_RE = re.compile(
    r"^[a-z0-9]+([._-][a-z0-9]+)*"
    r"(/[a-z0-9]+([._-][a-z0-9]+)*)*$"
)
_DIGEST_RE = re.compile(r"@sha256:[a-f0-9]{64}$")


def validate_feature_ref(ref: str) -> str | None:
    """Return None if ref is valid; an error string otherwise."""
    if "/" not in ref:
        return f"missing registry/path separator: {ref!r}"

    # Strip a trailing @sha256:digest, if any. The CLI validates the
    # path-and-tag portion against _PATH_RE separately from the digest.
    if "@" in ref:
        path_part, _, digest_part = ref.rpartition("@")
        if not _DIGEST_RE.fullmatch("@" + digest_part):
            return (
                f"digest portion {('@' + digest_part)!r} does not match "
                f"@sha256:<64-hex>"
            )
    else:
        path_part = ref

    # Split off the registry (first '/' segment); validate the rest.
    _registry, _, after_registry = path_part.partition("/")
    if not after_registry:
        return f"missing path after registry: {ref!r}"

    if not _PATH_RE.fullmatch(after_registry):
        # Most common cause: tag-and-digest combined (':1@sha256:...').
        if ":" in after_registry:
            return (
                f"Feature ref {ref!r} contains ':' in the path component. "
                f"The Dev Containers CLI rejects combined 'name:tag@sha256:digest' "
                f"refs (path regex disallows ':'). Use the digest alone — "
                f"'name@sha256:digest' — no ':tag'."
            )
        return (
            f"Feature ref {ref!r} path {after_registry!r} fails the Dev "
            f"Containers CLI path regex "
            f"/^[a-z0-9]+([._-][a-z0-9]+)*(/[a-z0-9]+([._-][a-z0-9]+)*)*$/."
        )

    return None


def main() -> int:
    cfg_path = Path(".devcontainer/devcontainer.json")
    if not cfg_path.exists():
        return 0  # no devcontainer for this repo; nothing to check

    try:
        cfg = json.loads(cfg_path.read_text())
    except json.JSONDecodeError as e:
        print(f"check-devcontainer-refs: {cfg_path} is not valid JSON: {e}",
              file=sys.stderr)
        return 1

    features = cfg.get("features") or {}
    if not isinstance(features, dict):
        print(f"check-devcontainer-refs: 'features' in {cfg_path} is not an object",
              file=sys.stderr)
        return 1

    errors: list[str] = []
    for ref in features:
        err = validate_feature_ref(ref)
        if err:
            errors.append(err)

    if errors:
        print(f"check-devcontainer-refs: {len(errors)} invalid Feature ref(s) "
              f"in {cfg_path}:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
