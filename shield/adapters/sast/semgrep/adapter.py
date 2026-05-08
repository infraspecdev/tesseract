"""Semgrep SAST adapter for shield's backend-reviewer.

Default mode: invoke locally. Semgrep is fast (seconds for typical repos)
and parses to deterministic JSON. Custom shield rule packs ship under
`./rules/` and target Spring Boot 3.x patterns.

Layered fallback:
  1. Consume existing output (if --output path configured and mtime fresh)
  2. Invoke `semgrep --config <rules> --json <target_path>`
  3. Best-effort skip with note
"""

from __future__ import annotations

import json
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from shield.adapters.sast.common import (
    AdapterResult,
    Category,
    Finding,
    Severity,
)


SEVERITY_MAP: dict[str, Severity] = {
    "ERROR": "high",
    "WARNING": "medium",
    "INFO": "low",
}


VALID_CATEGORIES: set[Category] = {
    "security",
    "code-quality",
    "performance",
    "reliability",
    "style",
}


def _parse_semgrep_json(payload: dict[str, Any]) -> list[Finding]:
    """Convert Semgrep `--json` output to normalized findings.

    Semgrep result schema (relevant fields):
      results: [
        {
          check_id: str,
          path: str,
          start: { line: int, ... },
          end: { line: int, ... },
          extra: {
            severity: "ERROR" | "WARNING" | "INFO",
            message: str,
            metadata: { category: str, ... }
          }
        }
      ]
    """
    findings: list[Finding] = []
    for result in payload.get("results", []):
        check_id = result.get("check_id", "")
        path = result.get("path", "")
        start_line = result.get("start", {}).get("line", 0)
        end_line = result.get("end", {}).get("line", start_line)
        lines = f"{start_line}" if start_line == end_line else f"{start_line}-{end_line}"

        extra = result.get("extra", {})
        severity_native = extra.get("severity", "INFO")
        severity: Severity = SEVERITY_MAP.get(severity_native, "medium")
        message = extra.get("message", "")

        category_raw = extra.get("metadata", {}).get("category", "code-quality")
        category: Category = (
            category_raw if category_raw in VALID_CATEGORIES else "code-quality"
        )

        findings.append(
            Finding(
                source="semgrep",
                rule_id=check_id,
                file=path,
                lines=lines,
                severity=severity,
                category=category,
                message=message,
            )
        )
    return findings


def _tool_available() -> bool:
    """Check `semgrep` is on PATH and runnable."""
    return shutil.which("semgrep") is not None


def _default_rules_path() -> str:
    """Path to shield's bundled rule packs."""
    return str(Path(__file__).parent / "rules")


def _consume_existing(output_path: Path, head_commit_time: float) -> list[Finding] | None:
    """Read pre-existing Semgrep output if fresh.

    Returns None if no output, output is stale, or output is unparseable.
    """
    if not output_path.exists():
        return None
    if output_path.stat().st_mtime < head_commit_time:
        return None
    try:
        payload = json.loads(output_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    return _parse_semgrep_json(payload)


def _invoke_semgrep(target_path: str, rules_config: str) -> tuple[list[Finding], str | None]:
    """Run `semgrep` against `target_path` using `rules_config`.

    Returns (findings, error_note). `error_note` is None on success.
    """
    cmd = [
        "semgrep",
        "--config",
        rules_config,
        "--json",
        "--quiet",
        target_path,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    except subprocess.TimeoutExpired:
        return [], "semgrep adapter — invocation timed out after 120s"
    except OSError as e:
        return [], f"semgrep adapter — invocation error: {e}"

    # Semgrep returns 0 (clean) or 1 (findings present). Anything else is failure.
    if result.returncode not in (0, 1):
        return [], f"semgrep adapter — exit code {result.returncode}: {result.stderr[:200]}"

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return [], f"semgrep adapter — could not parse JSON output: {e}"

    return _parse_semgrep_json(payload), None


def run(
    target_path: str,
    config: dict[str, Any] | None = None,
    head_commit_time: float | None = None,
) -> AdapterResult:
    """Entry point for the Semgrep adapter.

    Layered fallback:
      1. If `config["output_path"]` is set, try to consume it (if mtime fresh).
      2. If semgrep is installed, invoke it locally.
      3. Otherwise, return AdapterResult with mode="unavailable".
    """
    config = config or {}
    start = time.time()

    # Mode 1: consume existing output
    output_path_str = config.get("output_path")
    if output_path_str and head_commit_time is not None:
        output_path = Path(output_path_str)
        consumed = _consume_existing(output_path, head_commit_time)
        if consumed is not None:
            return AdapterResult(
                source="semgrep",
                mode="consumed",
                runtime_seconds=time.time() - start,
                findings=consumed,
            )

    # Mode 2: invoke locally
    if _tool_available():
        rules = config.get("config") or _default_rules_path()
        findings, err = _invoke_semgrep(target_path, rules)
        return AdapterResult(
            source="semgrep",
            mode="invoked",
            runtime_seconds=time.time() - start,
            findings=findings,
            note=err,
        )

    # Mode 3: best-effort skip
    return AdapterResult(
        source="semgrep",
        mode="unavailable",
        runtime_seconds=time.time() - start,
        findings=[],
        note=(
            "semgrep adapter — tool not available; SAST coverage best-effort. "
            "Install with `pip install semgrep` to enable."
        ),
    )
