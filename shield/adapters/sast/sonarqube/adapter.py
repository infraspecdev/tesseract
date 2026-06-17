"""SonarQube Community SAST adapter for shield's backend-reviewer.

Default mode: consume existing output. SonarQube full scans take minutes,
so the adapter prefers reading pre-existing reports over invoking locally.

Layered fallback:
  1. Read SARIF / REST output at known/configured paths
  2. Fetch issues via REST API using credentials
  3. (Last resort) Invoke `sonar-scanner` locally
  4. Best-effort skip
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from shield.adapters.sast.common import (
    AdapterResult,
    Category,
    Finding,
    Severity,
)


SEVERITY_MAP: dict[str, Severity] = {
    "BLOCKER": "high",
    "CRITICAL": "high",
    "MAJOR": "medium",
    "MINOR": "low",
    "INFO": "low",
}


# SonarQube /api/issues/search page size cap and the server-side ceiling on
# total issues returnable via this endpoint (page * pageSize ≤ 10 000).
_SONAR_PAGE_SIZE = 500
_SONAR_MAX_ISSUES = 10000


TYPE_TO_CATEGORY: dict[str, Category] = {
    "VULNERABILITY": "security",
    "SECURITY_HOTSPOT": "security",
    "BUG": "reliability",
    "CODE_SMELL": "code-quality",
}


def _load_credentials() -> dict[str, str | None]:
    """Resolve SonarQube credentials.

    Order:
      1. ~/.shield/credentials.json → "sonarqube" block
      2. Env vars: SHIELD_SONAR_URL, SHIELD_SONAR_TOKEN, SHIELD_SONAR_PROJECT_KEY
    """
    home = Path(os.environ.get("HOME", str(Path.home())))
    creds_path = home / ".shield" / "credentials.json"

    file_creds: dict[str, Any] = {}
    if creds_path.exists():
        try:
            data = json.loads(creds_path.read_text())
            file_creds = data.get("sonarqube", {}) or {}
        except (json.JSONDecodeError, OSError):
            file_creds = {}

    return {
        "url": file_creds.get("url") or os.environ.get("SHIELD_SONAR_URL"),
        "token": file_creds.get("token") or os.environ.get("SHIELD_SONAR_TOKEN"),
        "project_key": file_creds.get("project_key") or os.environ.get("SHIELD_SONAR_PROJECT_KEY"),
    }


def _strip_project_prefix(component: str) -> str:
    """SonarQube prefixes file paths with `project_key:` — strip it."""
    if ":" in component:
        return component.split(":", 1)[1]
    return component


def _parse_sonar_issues(payload: dict[str, Any]) -> list[Finding]:
    """Convert SonarQube /api/issues/search response to normalized findings."""
    findings: list[Finding] = []
    for issue in payload.get("issues", []):
        rule = issue.get("rule", "")
        component = issue.get("component", "")
        path = _strip_project_prefix(component)

        text_range = issue.get("textRange") or {}
        line = issue.get("line", 0)
        start_line = text_range.get("startLine", line)
        end_line = text_range.get("endLine", start_line)
        lines = f"{start_line}" if start_line == end_line else f"{start_line}-{end_line}"

        severity_native = issue.get("severity", "MAJOR")
        severity: Severity = SEVERITY_MAP.get(severity_native, "medium")

        finding_type = issue.get("type", "CODE_SMELL")
        category: Category = TYPE_TO_CATEGORY.get(finding_type, "code-quality")

        findings.append(
            Finding(
                source="sonarqube",
                rule_id=rule,
                file=path,
                lines=lines,
                severity=severity,
                category=category,
                message=issue.get("message", ""),
            )
        )
    return findings


def _consume_existing(output_path: Path, head_commit_time: float) -> list[Finding] | None:
    """Read pre-existing SonarQube output if fresh."""
    if not output_path.exists():
        return None
    if output_path.stat().st_mtime < head_commit_time:
        return None
    try:
        payload = json.loads(output_path.read_text())
    except (json.JSONDecodeError, OSError):
        return None
    return _parse_sonar_issues(payload)


def _fetch_via_api(url: str, token: str, project_key: str) -> tuple[list[Finding], str | None]:
    """Fetch issues via SonarQube REST API, paginating until all issues are read.

    /api/issues/search caps the page size at 500 (``ps``) and returns a
    ``paging`` block; requesting only the first page silently drops every
    finding past the first 500. We loop on ``p`` until the reported ``total``
    is exhausted, bounded by SonarQube's own ceiling of 10 000 issues for this
    endpoint (page * pageSize ≤ 10 000) — beyond that the server itself refuses
    to paginate further.
    """
    api_url = url.rstrip("/") + "/api/issues/search"
    encoded = base64.b64encode((token + ":").encode()).decode()

    findings: list[Finding] = []
    page = 1
    while page * _SONAR_PAGE_SIZE <= _SONAR_MAX_ISSUES:
        params = urllib.parse.urlencode({
            "componentKeys": project_key,
            "ps": _SONAR_PAGE_SIZE,
            "p": page,
            "statuses": "OPEN,REOPENED,CONFIRMED",
        })
        req = urllib.request.Request(f"{api_url}?{params}")
        req.add_header("Authorization", f"Basic {encoded}")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.loads(resp.read().decode())
        except (urllib.error.URLError, json.JSONDecodeError, OSError) as e:
            return [], f"sonarqube adapter — API fetch failed: {e}"

        findings.extend(_parse_sonar_issues(payload))

        paging = payload.get("paging") or {}
        total = paging.get("total", 0)
        page_size = paging.get("pageSize") or _SONAR_PAGE_SIZE
        if not total or page * page_size >= total:
            break
        page += 1

    return findings, None


def _invoke_scanner(target_path: str, creds: dict[str, str | None]) -> tuple[list[Finding], str | None]:
    """Run `sonar-scanner` locally as last resort. Slow."""
    if shutil.which("sonar-scanner") is None:
        return [], "sonarqube adapter — sonar-scanner not on PATH"
    if not (creds["url"] and creds["token"] and creds["project_key"]):
        return [], "sonarqube adapter — credentials missing for local invocation"

    cmd = [
        "sonar-scanner",
        f"-Dsonar.host.url={creds['url']}",
        f"-Dsonar.login={creds['token']}",
        f"-Dsonar.projectKey={creds['project_key']}",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600, cwd=target_path)
    except subprocess.TimeoutExpired:
        return [], "sonarqube adapter — sonar-scanner timed out after 600s"
    except OSError as e:
        return [], f"sonarqube adapter — sonar-scanner error: {e}"

    if result.returncode != 0:
        return [], f"sonarqube adapter — sonar-scanner exit {result.returncode}: {result.stderr[:200]}"

    # After scan, fetch via API
    return _fetch_via_api(creds["url"], creds["token"], creds["project_key"])


def run(
    target_path: str,
    config: dict[str, Any] | None = None,
    head_commit_time: float | None = None,
) -> AdapterResult:
    """Entry point for the SonarQube adapter."""
    config = config or {}
    start = time.time()

    # Mode 1: consume existing output file
    output_path_str = config.get("consume_path")
    if output_path_str and head_commit_time is not None:
        output_path = Path(output_path_str)
        consumed = _consume_existing(output_path, head_commit_time)
        if consumed is not None:
            return AdapterResult(
                source="sonarqube",
                mode="consumed",
                runtime_seconds=time.time() - start,
                findings=consumed,
            )

    # Mode 2: fetch via REST API
    creds = _load_credentials()
    if creds["url"] and creds["token"] and creds["project_key"]:
        findings, err = _fetch_via_api(creds["url"], creds["token"], creds["project_key"])
        if err is None:
            return AdapterResult(
                source="sonarqube",
                mode="consumed",
                runtime_seconds=time.time() - start,
                findings=findings,
            )
        # API failed — try local scan as last resort
        findings, scan_err = _invoke_scanner(target_path, creds)
        if scan_err is None:
            return AdapterResult(
                source="sonarqube",
                mode="invoked",
                runtime_seconds=time.time() - start,
                findings=findings,
            )
        # Both failed
        return AdapterResult(
            source="sonarqube",
            mode="unavailable",
            runtime_seconds=time.time() - start,
            findings=[],
            note=f"{err}; {scan_err}",
        )

    # Mode 3: best-effort skip — credentials missing
    return AdapterResult(
        source="sonarqube",
        mode="unavailable",
        runtime_seconds=time.time() - start,
        findings=[],
        note=(
            "sonarqube adapter — credentials missing; SAST coverage best-effort. "
            "Configure ~/.shield/credentials.json (sonarqube block) or "
            "SHIELD_SONAR_{URL,TOKEN,PROJECT_KEY} env vars to enable."
        ),
    )
