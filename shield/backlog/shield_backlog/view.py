"""Backlog view rendering — ordered list with pipeline status badges.

The canonical badge string is pinned here so every view path (CLI, command,
skill-internal) renders identically (EPIC-2-S1 / EPIC-1-S3 AC).

Badge string format (PINNED, per backlog SKILL.md):

    research ✓  prd ✓  plan –       # mix of present/absent flags
    not started                      # feature absent from manifest.json
"""
from __future__ import annotations

from typing import Any


def _status_badges(feature: str, manifest: dict[str, Any] | None) -> str:
    """Compute the per-entry pipeline status badge string.

    - When `manifest` is None or shape unknown → "" (no badges).
    - When `feature` is absent from manifest.features[] → "not started".
    - When present → "research ✓|–  prd ✓|–  plan ✓|–" derived from
      artifacts.{research, prd, plan_json} flags.
    """
    if not isinstance(manifest, dict):
        return ""
    features = manifest.get("features")
    if not isinstance(features, list):
        return ""

    match = next((f for f in features if isinstance(f, dict) and f.get("name") == feature), None)
    if match is None:
        return "not started"

    artifacts = match.get("artifacts") or {}
    def flag(k: str) -> str:
        return "✓" if artifacts.get(k) else "–"

    return f"research {flag('research')}  prd {flag('prd')}  plan {flag('plan_json')}"


def render(doc: dict[str, Any], *, manifest: dict[str, Any] | None = None) -> str:
    """Render the backlog as a plain-text list ordered by entries[].order.

    Per-entry line format (PINNED in SKILL.md):

        <order>. [<id-short>] (<feature> / <epic>, <source>) <text>
                <status-badges>

    Empty backlog returns a single 'no entries' line (not an error).
    """
    entries = sorted(
        doc.get("entries") or [],
        key=lambda e: (e.get("order"), e.get("id") or ""),
    )
    if not entries:
        return "Backlog is empty — no entries.\n"

    lines: list[str] = []
    for entry in entries:
        eid = (entry.get("id") or "")
        id_short = eid.split("-", 1)[0] if eid else "???"
        feature = entry.get("feature") or "?"
        epic = entry.get("epic") or "?"
        source = entry.get("source") or "?"
        text = entry.get("text") or ""
        order = entry.get("order")

        lines.append(f"{order}. [{id_short}] ({feature} / {epic}, {source}) {text}")

        badges = _status_badges(feature, manifest)
        if badges:
            lines.append(f"        {badges}")

    return "\n".join(lines) + "\n"
