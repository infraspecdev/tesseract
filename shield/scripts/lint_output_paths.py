# shield/scripts/lint_output_paths.py
"""Lint shield assets and the path registry for consistency.

Runnable: `uv run --with pyyaml shield/scripts/lint_output_paths.py [--root .]`
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

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
    """Return the `outputs:` list from an asset's frontmatter, or [] if absent.

    Raises:
        yaml.YAMLError: if the frontmatter is unparseable. Caller (validate_asset)
            converts this into a lint error so the asset gets fixed; silently
            swallowing YAML errors lets coverage drift sneak in (e.g. an asset
            with `outputs: [foo]` whose frontmatter fails to parse for an
            unrelated reason has the same coverage signature as no declaration).
    """
    text = asset_path.read_text()
    match = FRONTMATTER_RE.match(text)
    if not match:
        return []
    front = yaml.safe_load(match.group(1)) or {}
    raw = front.get("outputs", [])
    if not isinstance(raw, list):
        return []
    return [str(x) for x in raw]


def validate_asset(asset_path: Path, registry_names: set[str]) -> list[str]:
    """Return a list of human-readable error messages for an asset's outputs declarations.

    Empty list means the asset is clean (including the case where it declares no outputs).
    """
    errors: list[str] = []
    try:
        declared = parse_outputs_block(asset_path)
    except yaml.YAMLError as exc:
        first_line = str(exc).splitlines()[0]
        return [f"{asset_path.name}: frontmatter does not parse ({first_line})"]
    for name in declared:
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


def validate_coverage(registry: dict, referenced: set[str]) -> list[str]:
    """Check that every registry path entry is either declared by an asset's
    `outputs:` block or explicitly listed under `derived:` (for parent-directory
    or computed-global entries that no single asset owns).

    Args:
        registry: parsed output-paths.yaml content.
        referenced: set of registry names declared by at least one asset's `outputs:`.

    Returns:
        Human-readable error messages. Empty list means coverage is clean.

    This catches the failure mode where a registry entry is added (e.g. in a
    schema-amendment commit) but never wired into an owning command — invisible
    to per-asset lint and (without the bidirectional eval check) invisible to
    the eval suite.
    """
    errors: list[str] = []
    path_names = set(registry.get("paths", {}).keys())
    derived = set(registry.get("derived", []) or [])
    deprecated = set(registry.get("deprecated", []) or [])

    # 1. Every derived entry must actually exist in `paths` (typo protection).
    for name in sorted(derived):
        if name not in path_names:
            errors.append(
                f"derived entry '{name}' is not in `paths:` — fix the typo or remove from `derived:`"
            )

    # 1b. Every deprecated entry must also exist in `paths` (typo protection).
    for name in sorted(deprecated):
        if name not in path_names:
            errors.append(
                f"deprecated entry '{name}' is not in `paths:` — fix the typo or remove from `deprecated:`"
            )

    # 2. Every path entry must be referenced, derived, OR deprecated.
    for name in sorted(path_names):
        if name in derived or name in deprecated:
            continue
        if name not in referenced:
            errors.append(
                f"registry path '{name}' is declared but no asset declares it in `outputs:` "
                f"(add it to a command/skill/agent, or mark as `derived:`/`deprecated:` "
                f"if it's a parent-directory, computed-global, or sunset entry)"
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
    assets = discover_assets(root / "shield")
    referenced: set[str] = set()
    for asset in assets:
        errors.extend(validate_asset(asset, registry_names))
        try:
            declared = parse_outputs_block(asset)
        except yaml.YAMLError:
            # validate_asset already surfaced the parse error; skip coverage harvest.
            continue
        for name in declared:
            if name in registry_names:
                referenced.add(name)
    errors.extend(validate_coverage(registry, referenced))

    if errors:
        print("Lint failed:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        return 1
    print(f"Lint clean: registry + {len(assets)} assets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
