# shield/scripts/test_detect_stack.py
"""Tests for detect_stack.py.

Runnable: `cd shield/scripts && uv run --with pytest pytest test_detect_stack.py -v`
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from detect_stack import detect_stack  # type: ignore[import-not-found]


def _make(tmp_path: Path, files: dict[str, str]) -> Path:
    for relpath, content in files.items():
        target = tmp_path / relpath
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
    return tmp_path


@pytest.mark.parametrize(
    "files,expected",
    [
        ({"pyproject.toml": "[project]\nname='x'\n"}, {"python"}),
        ({"requirements.txt": "requests==2.0\n"}, {"python"}),
        ({"package.json": "{}"}, {"node"}),
        ({"package.json": "{}", "tsconfig.json": "{}"}, {"node", "node-ts"}),
        ({"go.mod": "module x\n"}, {"go"}),
        ({"pom.xml": "<project/>"}, {"java"}),
        ({"build.gradle": ""}, {"java"}),
        ({"build.gradle.kts": ""}, {"java"}),
        ({"main.tf": "resource {}\n"}, {"terraform"}),
        ({"infra/sub/aws.tf": "resource {}\n"}, {"terraform"}),
        ({"Cargo.toml": "[package]\n"}, {"rust"}),
        ({"Gemfile": ""}, {"ruby"}),
        ({"Dockerfile": "FROM scratch\n"}, {"docker-in-docker"}),
        ({"docker-compose.yml": "services: {}\n"}, {"docker-in-docker"}),
        ({"helm/values.yaml": ""}, {"kubernetes"}),
        ({"kustomization.yaml": ""}, {"kubernetes"}),
        ({"pyproject.toml": "", "package.json": "{}"}, {"python", "node"}),
        ({}, set()),
    ],
)
def test_detect_stack(tmp_path: Path, files: dict[str, str], expected: set[str]) -> None:
    repo = _make(tmp_path, files)
    assert set(detect_stack(repo)) == expected


def test_detect_stack_returns_sorted_list(tmp_path: Path) -> None:
    """Output is deterministic — caller can use it in a stable composition."""
    _make(tmp_path, {"pyproject.toml": "", "package.json": "{}", "go.mod": "module x"})
    assert detect_stack(tmp_path) == sorted(detect_stack(tmp_path))
