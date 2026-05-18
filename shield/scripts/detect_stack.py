# shield/scripts/detect_stack.py
"""Detect a project's tech stack from filesystem markers.

Mirrors the marker rules in shield/skills/general/research/repo-scan.md so
the devcontainer scaffolder and the research repo-scan stay in sync.

Public API:
    detect_stack(root: Path) -> list[str]

Returns a sorted list of stack tags. Multiple tags are returned for polyglot
repos. Unknown markers are silently ignored; absent markers produce an empty
list.
"""
from __future__ import annotations

from pathlib import Path


def detect_stack(root: Path) -> list[str]:
    root = Path(root)
    tags: set[str] = set()

    # Python
    if (root / "pyproject.toml").exists() or (root / "requirements.txt").exists():
        tags.add("python")

    # Node (+ node-ts if tsconfig.json is present)
    if (root / "package.json").exists():
        tags.add("node")
        if (root / "tsconfig.json").exists():
            tags.add("node-ts")

    # Go
    if (root / "go.mod").exists():
        tags.add("go")

    # Java
    if (root / "pom.xml").exists() \
       or (root / "build.gradle").exists() \
       or (root / "build.gradle.kts").exists():
        tags.add("java")

    # Terraform — recursive
    if _has_recursive(root, "*.tf"):
        tags.add("terraform")

    # Rust
    if (root / "Cargo.toml").exists():
        tags.add("rust")

    # Ruby
    if (root / "Gemfile").exists():
        tags.add("ruby")

    # Docker (flag)
    if (root / "Dockerfile").exists() or (root / "docker-compose.yml").exists():
        tags.add("docker-in-docker")

    # Kubernetes (flag)
    if (root / "helm").is_dir() or (root / "kustomization.yaml").exists():
        tags.add("kubernetes")

    return sorted(tags)


def _has_recursive(root: Path, pattern: str) -> bool:
    """True if any file matching pattern exists at or below root.

    Skips hidden dirs (.git, .venv, etc.) and node_modules to stay fast.
    """
    SKIP = {".git", ".venv", "node_modules", "__pycache__", ".worktrees"}
    for p in root.rglob(pattern):
        parts = set(p.relative_to(root).parts)
        if parts & SKIP:
            continue
        return True
    return False
