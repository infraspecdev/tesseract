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

    Raises:
        KeyError: if `name` is not in the registry, or a required template
            variable is not supplied in `bindings`.
        ValueError: on circular references in the registry.
    """
    registry = _load_registry()
    paths = registry["paths"]
    if name not in paths:
        raise KeyError(f"Path '{name}' is not in the registry (shield/schema/output-paths.yaml)")

    def expand(name_: str, seen: set[str]) -> str:
        if name_ in seen:
            raise ValueError(f"Circular reference detected for path '{name_}'")
        template = paths[name_]
        merged: dict[str, str] = dict(bindings)
        for nested_name in list(paths.keys()):
            placeholder = "{" + nested_name + "}"
            if placeholder in template:
                merged[nested_name] = expand(nested_name, seen | {name_})
        try:
            return template.format(**merged)
        except KeyError as exc:
            missing = exc.args[0]
            raise KeyError(
                f"Path '{name_}' requires variable '{missing}' but it was not supplied"
            ) from exc

    return expand(name, set())
