# shield/scripts/path_resolver.py
"""Resolve shield artifact paths from the central registry.

Runnable as a library: `from path_resolver import resolve`.
The registry lives at `shield/schema/output-paths.yaml`.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schema" / "output-paths.yaml"


def _load_registry() -> dict[str, Any]:
    with SCHEMA_PATH.open() as f:
        return yaml.safe_load(f)


def resolve(name: str, **bindings: str) -> str:
    """Resolve a registered path name to a concrete filesystem path.

    Args:
        name: Path name as declared in the registry's `paths:` block.
        **bindings: Variable substitutions (e.g. output_dir, feature, ...).

    Returns:
        The fully-substituted path string.
    """
    registry = _load_registry()
    template = registry["paths"][name]
    return template.format(**bindings)
