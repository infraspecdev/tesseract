# shield/scripts/compose_devcontainer.py
"""Compose a devcontainer.json dict from detected stacks + feature-map.

Public API:
    compose_devcontainer(stacks, feature_map_path, user_extra_allowlist=None) -> dict

Pure function. No filesystem writes. The caller serializes the returned dict.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterable

ANTHROPIC_CLAUDE_CODE_FEATURE = (
    "ghcr.io/anthropics/devcontainer-features/claude-code:1"
    "@sha256:cfc2e7d3e9fd3b9b01f8d5cb158508a884c8c0ede2e23ed10f32dea5d4ffe69a"
)


def compose_devcontainer(
    stacks: Iterable[str],
    feature_map_path: Path,
    user_extra_allowlist: list[str] | None = None,
) -> dict:
    feature_map = json.loads(Path(feature_map_path).read_text())

    features: dict[str, dict] = {}
    extra_hosts: list[str] = []
    skipped: list[str] = []

    for stack in stacks:
        entry = feature_map.get(stack)
        if entry is None:
            skipped.append(stack)
            continue
        features[entry["feature"]] = entry.get("default_options", {})
        extra_hosts.extend(entry.get("firewall_allowlist", []))

    if user_extra_allowlist:
        extra_hosts.extend(user_extra_allowlist)

    for stack in skipped:
        print(
            f"warning: stack '{stack}' has no feature-map entry; "
            f"its Feature and postCreate hint will be omitted.",
            file=sys.stderr,
        )

    # Constant layer: Claude Code must be present in every Shield devcontainer,
    # regardless of detected stacks. Set unconditionally after the per-stack loop.
    features[ANTHROPIC_CLAUDE_CODE_FEATURE] = {}

    return {
        "$schema": "https://raw.githubusercontent.com/devcontainers/spec/main/schemas/devContainer.schema.json",
        "name": "shield-implement",
        "build": {"dockerfile": "Dockerfile"},
        "features": features,
        "remoteUser": "dev",
        "capAdd": ["NET_ADMIN", "NET_RAW"],
        "mounts": [
            "source=claude-config-${devcontainerId},target=/home/dev/.claude,type=volume",
        ],
        "containerEnv": {
            "SHIELD_IN_DEVCONTAINER": "true",
            "EXTRA_HOSTS": " ".join(extra_hosts),
        },
        "postCreateCommand": "bash .devcontainer/postCreate.sh",
        "postStartCommand": "sudo /usr/local/bin/shield-firewall.sh",
        "customizations": {
            "vscode": {"extensions": ["anthropic.claude-code"]},
        },
    }
