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

    Nested references (e.g. `{feature_dir}` inside another template) are
    resolved recursively from the registry. Variable bindings (e.g. `output_dir`)
    come from the caller.
    """
    registry = _load_registry()
    paths = registry["paths"]

    def expand(name_: str, seen: set[str]) -> str:
        if name_ in seen:
            raise ValueError(f"Circular reference detected for path '{name_}'")
        template = paths[name_]
        # Build a merged binding map: nested templates take precedence over bindings.
        merged: dict[str, str] = dict(bindings)
        for nested_name in list(paths.keys()):
            placeholder = "{" + nested_name + "}"
            if placeholder in template and nested_name not in seen:
                merged[nested_name] = expand(nested_name, seen | {name_})
        return template.format(**merged)

    return expand(name, set())
