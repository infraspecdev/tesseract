"""Shared types for shield SAST adapters.

Each adapter normalizes its tool's output to the dataclasses defined here.
The normalized findings flow into backend-reviewer's aggregation step,
which dedups by file + overlapping line range.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


Severity = Literal["high", "medium", "low"]
Category = Literal["security", "code-quality", "performance", "reliability", "style"]


@dataclass
class Finding:
    """A single normalized SAST finding."""
    source: str          # adapter name, e.g., "semgrep"
    rule_id: str         # tool-native rule ID
    file: str            # path relative to repo root
    lines: str           # "27" or "27-29"
    severity: Severity
    category: Category
    message: str
    fix_hint: str | None = None


@dataclass
class AdapterResult:
    """Result of a single adapter run."""
    source: str
    mode: Literal["consumed", "invoked", "unavailable"]
    runtime_seconds: float
    findings: list[Finding] = field(default_factory=list)
    note: str | None = None  # for "best-effort" messages or invocation errors
