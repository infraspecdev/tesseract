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
PLACEHOLDER_RE = re.compile(r"\{([^{}]+)\}")


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


def validate_registry(registry: dict) -> list[str]:
    """Check that every placeholder in a template is either a declared variable
    or another registered path name. Returns a list of human-readable errors.
    """
    errors: list[str] = []
    declared_vars = set(registry.get("variables", {}).keys())
    path_names = set(registry.get("paths", {}).keys())
    known = declared_vars | path_names

    for path_name, template in registry.get("paths", {}).items():
        for placeholder in PLACEHOLDER_RE.findall(template):
            if placeholder not in known:
                errors.append(
                    f"registry path '{path_name}' references undeclared variable '{placeholder}'"
                )
    return errors


def _load_registry_from(root: Path) -> dict:
    schema = root / "shield" / "schema" / "output-paths.yaml"
    with schema.open() as f:
        return yaml.safe_load(f)


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Lint shield asset outputs against path registry.")
    parser.add_argument("--root", default=".", help="Repo root (default: current dir)")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    registry = _load_registry_from(root)

    errors: list[str] = []
    errors.extend(validate_registry(registry))
    registry_names = set(registry.get("paths", {}).keys())
    for asset in discover_assets(root / "shield"):
        errors.extend(validate_asset(asset, registry_names))

    if errors:
        print("Lint failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"Lint clean: registry + {len(discover_assets(root / 'shield'))} assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
