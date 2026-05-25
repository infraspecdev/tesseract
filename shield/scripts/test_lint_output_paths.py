# shield/scripts/test_lint_output_paths.py
"""Tests for lint_output_paths.py.

Runnable: `cd shield/scripts && uv run --with pyyaml --with pytest pytest test_lint_output_paths.py -v`
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from lint_output_paths import discover_assets, parse_outputs_block, validate_asset, validate_coverage, validate_registry  # type: ignore[import-not-found]


def _write_asset(path: Path, frontmatter: str, body: str = "Body.\n") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}---\n{body}")


def test_discover_finds_md_files(tmp_path: Path) -> None:
    _write_asset(tmp_path / "commands" / "plan.md", "name: plan\n")
    _write_asset(tmp_path / "skills" / "x" / "SKILL.md", "name: x\n")
    (tmp_path / "README.md").write_text("not an asset\n")
    found = discover_assets(tmp_path)
    rels = sorted(p.relative_to(tmp_path).as_posix() for p in found)
    assert rels == ["commands/plan.md", "skills/x/SKILL.md"]


def test_parse_outputs_block_present(tmp_path: Path) -> None:
    asset = tmp_path / "commands" / "plan.md"
    _write_asset(asset, "name: plan\noutputs:\n  - plan_md\n  - plan_json\n")
    assert parse_outputs_block(asset) == ["plan_md", "plan_json"]


def test_parse_outputs_block_absent(tmp_path: Path) -> None:
    asset = tmp_path / "commands" / "plan.md"
    _write_asset(asset, "name: plan\n")
    assert parse_outputs_block(asset) == []


def test_validate_asset_passes_when_outputs_in_registry(tmp_path: Path) -> None:
    asset = tmp_path / "commands" / "plan.md"
    _write_asset(asset, "name: plan\noutputs:\n  - plan_md\n  - plan_json\n")
    errors = validate_asset(asset, registry_names={"plan_md", "plan_json", "research"})
    assert errors == []


def test_validate_asset_fails_on_unknown_name(tmp_path: Path) -> None:
    asset = tmp_path / "commands" / "plan.md"
    _write_asset(asset, "name: plan\noutputs:\n  - plan_md\n  - not_in_registry\n")
    errors = validate_asset(asset, registry_names={"plan_md"})
    assert len(errors) == 1
    assert "not_in_registry" in errors[0]
    assert asset.name in errors[0]


def test_validate_asset_no_outputs_is_ok(tmp_path: Path) -> None:
    asset = tmp_path / "commands" / "plan.md"
    _write_asset(asset, "name: plan\n")
    errors = validate_asset(asset, registry_names={"plan_md"})
    assert errors == []


def test_validate_registry_passes_clean_registry() -> None:
    registry = {
        "variables": {"output_dir": "", "feature": ""},
        "paths": {
            "feature_dir": "{output_dir}/{feature}",
            "research":    "{feature_dir}/research.md",
        },
    }
    assert validate_registry(registry) == []


def test_validate_registry_flags_unknown_variable() -> None:
    registry = {
        "variables": {"output_dir": ""},
        "paths": {
            "research": "{output_dir}/{nonexistent}/research.md",
        },
    }
    errors = validate_registry(registry)
    assert len(errors) == 1
    assert "nonexistent" in errors[0]
    assert "research" in errors[0]


def test_validate_coverage_clean_all_declared() -> None:
    registry = {
        "paths": {"plan_md": "...", "research": "..."},
        "derived": [],
    }
    referenced = {"plan_md", "research"}
    assert validate_coverage(registry, referenced) == []


def test_validate_coverage_flags_orphan_registry_entry() -> None:
    registry = {
        "paths": {"plan_md": "...", "ghost_path": "..."},
        "derived": [],
    }
    referenced = {"plan_md"}
    errors = validate_coverage(registry, referenced)
    assert len(errors) == 1
    assert "ghost_path" in errors[0]
    assert "no asset declares it" in errors[0] or "no asset" in errors[0]


def test_validate_coverage_derived_entry_is_exempt() -> None:
    registry = {
        "paths": {
            "plan_md": "...",
            "global_index_html": "...",
            "review_outputs_dir": "...",
        },
        "derived": ["global_index_html", "review_outputs_dir"],
    }
    referenced = {"plan_md"}
    assert validate_coverage(registry, referenced) == []


def test_validate_coverage_derived_entry_must_exist_in_paths() -> None:
    registry = {
        "paths": {"plan_md": "..."},
        "derived": ["nonexistent_entry"],
    }
    referenced = {"plan_md"}
    errors = validate_coverage(registry, referenced)
    assert len(errors) == 1
    assert "nonexistent_entry" in errors[0]


def test_cli_fails_on_orphaned_registry_entry(tmp_path: Path) -> None:
    schema_dir = tmp_path / "shield" / "schema"
    schema_dir.mkdir(parents=True)
    (schema_dir / "output-paths.yaml").write_text(
        "variables:\n  output_dir: ''\n"
        "paths:\n"
        "  feature_dir: '{output_dir}/x'\n"
        "  declared_path: '{feature_dir}/declared.md'\n"
        "  orphan_path:   '{feature_dir}/orphan.md'\n"
    )
    asset = tmp_path / "shield" / "commands" / "plan.md"
    asset.parent.mkdir(parents=True)
    _write_asset(asset, "name: plan\noutputs:\n  - declared_path\n")

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "lint_output_paths.py"), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "orphan_path" in result.stdout + result.stderr


import subprocess


def test_cli_passes_clean_tree(tmp_path: Path) -> None:
    # Build a minimal repo: registry with one path declared by an asset, plus
    # a parent-directory entry marked as `derived:`.
    schema_dir = tmp_path / "shield" / "schema"
    schema_dir.mkdir(parents=True)
    (schema_dir / "output-paths.yaml").write_text(
        "variables:\n  output_dir: ''\n"
        "paths:\n"
        "  feature_dir: '{output_dir}/x'\n"
        "  plan_md:     '{feature_dir}/plan.md'\n"
        "derived:\n"
        "  - feature_dir\n"
    )
    asset = tmp_path / "shield" / "commands" / "plan.md"
    asset.parent.mkdir(parents=True)
    _write_asset(asset, "name: plan\noutputs:\n  - plan_md\n")

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "lint_output_paths.py"), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_cli_fails_on_unknown_output_name(tmp_path: Path) -> None:
    schema_dir = tmp_path / "shield" / "schema"
    schema_dir.mkdir(parents=True)
    (schema_dir / "output-paths.yaml").write_text(
        "variables:\n  output_dir: ''\n"
        "paths:\n  feature_dir: '{output_dir}/x'\n"
    )
    asset = tmp_path / "shield" / "commands" / "plan.md"
    asset.parent.mkdir(parents=True)
    _write_asset(asset, "name: plan\noutputs:\n  - ghost_path\n")

    result = subprocess.run(
        ["python3", str(SCRIPT_DIR / "lint_output_paths.py"), "--root", str(tmp_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0
    assert "ghost_path" in result.stdout + result.stderr
