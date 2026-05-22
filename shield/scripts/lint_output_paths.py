# shield/scripts/lint_output_paths.py
"""Lint shield assets and the path registry for consistency.

Runnable: `uv run --with pyyaml shield/scripts/lint_output_paths.py [--root .] [--strict]`
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Iterator

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

ASSET_DIRS = ("commands", "skills", "agents")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n", re.DOTALL)


def discover_assets(root: Path) -> list[Path]:
    """Find all asset markdown files under any `commands/`, `skills/`, or `agents/` directory."""
    found: list[Path] = []
    for asset_dir in ASSET_DIRS:
        for path in root.rglob(f"{asset_dir}/**/*.md"):
            if path.is_file():
                found.append(path)
    return sorted(found)


def parse_outputs_block(asset_path: Path) -> list[str]:
    """Return the `outputs:` list from an asset's frontmatter, or [] if absent."""
    text = asset_path.read_text()
    match = FRONTMATTER_RE.match(text)
    if not match:
        return []
    try:
        front = yaml.safe_load(match.group(1)) or {}
    except yaml.YAMLError:
        return []
    raw = front.get("outputs", [])
    if not isinstance(raw, list):
        return []
    return [str(x) for x in raw]


def validate_asset(asset_path: Path, registry_names: set[str]) -> list[str]:
    """Return a list of human-readable error messages for an asset's outputs declarations.

    Empty list means the asset is clean (including the case where it declares no outputs).
    """
    errors: list[str] = []
    for name in parse_outputs_block(asset_path):
        if name not in registry_names:
            errors.append(
                f"{asset_path.name}: declared output '{name}' is not in the path registry"
            )
    return errors
