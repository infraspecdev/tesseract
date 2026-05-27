"""Canonical task-name formatting shared by pm_bulk_create and pm_bulk_rename.

One formatter for both tools means they can never drift on what a "compliant"
name looks like, and a format string that references an unsupported placeholder
fails with a clear, named error instead of a bare KeyError.
"""

from __future__ import annotations

import re
import string

_STORY_PLACEHOLDERS = {"prefix", "epic_id", "index", "name"}
_EPIC_PLACEHOLDERS = {"prefix", "epic_id", "name", "epic_name"}

_STORY_INDEX_RE = re.compile(r"-S(\d+)$")


def _placeholders_used(fmt: str) -> set[str]:
    """Root field names referenced by a str.format template."""
    used: set[str] = set()
    for _literal, field_name, _spec, _conv in string.Formatter().parse(fmt):
        if field_name:
            # Strip attribute/index access: "name.upper" / "name[0]" -> "name".
            root = field_name.split(".")[0].split("[")[0]
            if root:
                used.add(root)
    return used


def _check_placeholders(fmt: str, allowed: set[str], kind: str) -> None:
    unknown = _placeholders_used(fmt) - allowed
    if unknown:
        unknown_str = ", ".join("{" + u + "}" for u in sorted(unknown))
        allowed_str = ", ".join("{" + a + "}" for a in sorted(allowed))
        raise ValueError(
            f"{kind} references unknown placeholder(s) {unknown_str}; "
            f"allowed: {allowed_str}"
        )


def format_story_name(
    fmt: str, *, prefix: str, epic_id: str, index: int | str, name: str
) -> str:
    """Render a story task name from the configured story_format."""
    _check_placeholders(fmt, _STORY_PLACEHOLDERS, "story_format")
    return fmt.format(prefix=prefix, epic_id=epic_id, index=index, name=name)


def format_epic_name(
    fmt: str, *, prefix: str, epic_id: str, name: str, epic_name: str
) -> str:
    """Render an epic card name from the configured epic_format."""
    _check_placeholders(fmt, _EPIC_PLACEHOLDERS, "epic_format")
    return fmt.format(prefix=prefix, epic_id=epic_id, name=name, epic_name=epic_name)


def story_index(story_id: str) -> str:
    """Extract the S-index from a plan story id (e.g. 'EPIC-4-S0' -> '0').

    Returns '' when the id carries no '-S<n>' suffix.
    """
    m = _STORY_INDEX_RE.search(story_id)
    return m.group(1) if m else ""
