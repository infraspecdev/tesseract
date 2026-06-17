"""Tests for the SonarQube adapter."""

import json
import os
from urllib.parse import parse_qs, urlparse

from shield.adapters.sast.sonarqube import adapter as sonar
from shield.adapters.sast.sonarqube.adapter import (
    SEVERITY_MAP,
    _fetch_via_api,
    _load_credentials,
    _parse_sonar_issues,
    _strip_project_prefix,
)


def test_severity_mapping_complete():
    assert SEVERITY_MAP["BLOCKER"] == "high"
    assert SEVERITY_MAP["CRITICAL"] == "high"
    assert SEVERITY_MAP["MAJOR"] == "medium"
    assert SEVERITY_MAP["MINOR"] == "low"
    assert SEVERITY_MAP["INFO"] == "low"


def test_strip_project_prefix():
    assert _strip_project_prefix("my-project:src/Foo.java") == "src/Foo.java"
    # no prefix → return as-is
    assert _strip_project_prefix("src/Foo.java") == "src/Foo.java"


def test_parse_empty_issues(empty_issues):
    findings = _parse_sonar_issues(empty_issues)
    assert findings == []


def test_parse_sample_issues_count(sample_issues):
    findings = _parse_sonar_issues(sample_issues)
    assert len(findings) == 4


def test_parse_first_finding(sample_issues):
    findings = _parse_sonar_issues(sample_issues)
    f = findings[0]
    assert f.source == "sonarqube"
    assert f.rule_id == "java:S5547"
    assert f.file == "shield/examples/spring-boot-api/src/main/java/com/example/api/config/SecurityConfig.java"
    assert f.lines == "17-21"
    assert f.severity == "high"
    assert f.category == "security"


def test_parse_severity_mapping(sample_issues):
    findings = _parse_sonar_issues(sample_issues)
    severities = [f.severity for f in findings]
    assert severities == ["high", "high", "medium", "low"]  # BLOCKER, CRITICAL, MAJOR, MINOR


def test_parse_category_from_type(sample_issues):
    findings = _parse_sonar_issues(sample_issues)
    categories = [f.category for f in findings]
    # VULNERABILITY/VULNERABILITY/CODE_SMELL/CODE_SMELL
    assert categories == ["security", "security", "code-quality", "code-quality"]


def test_load_credentials_from_env(monkeypatch, tmp_path):
    # Ensure no credentials.json in HOME
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("SHIELD_SONAR_URL", "https://sonar.test")
    monkeypatch.setenv("SHIELD_SONAR_TOKEN", "tok123")
    monkeypatch.setenv("SHIELD_SONAR_PROJECT_KEY", "myproj")

    creds = _load_credentials()
    assert creds["url"] == "https://sonar.test"
    assert creds["token"] == "tok123"
    assert creds["project_key"] == "myproj"


def test_load_credentials_from_file(monkeypatch, tmp_path):
    """Credentials file takes precedence over env vars."""
    home = tmp_path
    monkeypatch.setenv("HOME", str(home))
    shield_dir = home / ".shield"
    shield_dir.mkdir()
    (shield_dir / "credentials.json").write_text(
        '{"sonarqube": {"url": "https://from-file", "token": "filetok", "project_key": "filekey"}}'
    )
    # env vars present too — file should win
    monkeypatch.setenv("SHIELD_SONAR_URL", "https://from-env")

    creds = _load_credentials()
    assert creds["url"] == "https://from-file"
    assert creds["token"] == "filetok"
    assert creds["project_key"] == "filekey"


def test_load_credentials_missing(monkeypatch, tmp_path):
    """No file, no env vars → all None."""
    monkeypatch.setenv("HOME", str(tmp_path))
    for var in ("SHIELD_SONAR_URL", "SHIELD_SONAR_TOKEN", "SHIELD_SONAR_PROJECT_KEY"):
        monkeypatch.delenv(var, raising=False)

    creds = _load_credentials()
    assert creds["url"] is None
    assert creds["token"] is None
    assert creds["project_key"] is None


# --- REST API pagination (regression: first-page-only silently dropped >500 findings) ---

def _fake_issue(i: int) -> dict:
    return {
        "rule": f"java:S{i}",
        "component": f"proj:src/F{i}.java",
        "severity": "MAJOR",
        "type": "CODE_SMELL",
        "message": f"issue {i}",
        "line": i,
    }


class _FakeResp:
    def __init__(self, payload: dict):
        self._data = json.dumps(payload).encode()

    def read(self) -> bytes:
        return self._data

    def __enter__(self) -> "_FakeResp":
        return self

    def __exit__(self, *exc) -> bool:
        return False


def test_fetch_via_api_paginates_until_total_exhausted(monkeypatch):
    """1200 issues across 3 pages (500/500/200) — all must be collected."""
    pages = {
        1: {"issues": [_fake_issue(i) for i in range(0, 500)],
            "paging": {"pageIndex": 1, "pageSize": 500, "total": 1200}},
        2: {"issues": [_fake_issue(i) for i in range(500, 1000)],
            "paging": {"pageIndex": 2, "pageSize": 500, "total": 1200}},
        3: {"issues": [_fake_issue(i) for i in range(1000, 1200)],
            "paging": {"pageIndex": 3, "pageSize": 500, "total": 1200}},
    }
    requested_pages: list[int] = []

    def fake_urlopen(req, timeout=None):
        q = parse_qs(urlparse(req.full_url).query)
        page = int(q["p"][0])
        requested_pages.append(page)
        return _FakeResp(pages[page])

    monkeypatch.setattr(sonar.urllib.request, "urlopen", fake_urlopen)

    findings, err = _fetch_via_api("https://sonar.test", "tok", "proj")

    assert err is None
    assert len(findings) == 1200  # not truncated to the first 500
    assert requested_pages == [1, 2, 3]


def test_fetch_via_api_single_page_no_extra_request(monkeypatch):
    """total <= one page → exactly one request, no needless second fetch."""
    payload = {"issues": [_fake_issue(i) for i in range(10)],
               "paging": {"pageIndex": 1, "pageSize": 500, "total": 10}}
    calls: list[str] = []

    def fake_urlopen(req, timeout=None):
        calls.append(req.full_url)
        return _FakeResp(payload)

    monkeypatch.setattr(sonar.urllib.request, "urlopen", fake_urlopen)

    findings, err = _fetch_via_api("https://sonar.test/", "tok", "proj")

    assert err is None
    assert len(findings) == 10
    assert len(calls) == 1


def test_fetch_via_api_propagates_fetch_error(monkeypatch):
    """A network error still surfaces as the err string (drives scanner fallback)."""
    import urllib.error

    def boom(req, timeout=None):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr(sonar.urllib.request, "urlopen", boom)

    findings, err = _fetch_via_api("https://sonar.test", "tok", "proj")

    assert findings == []
    assert err is not None and "API fetch failed" in err
