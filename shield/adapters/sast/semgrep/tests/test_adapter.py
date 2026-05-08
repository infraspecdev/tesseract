"""Tests for the Semgrep adapter."""

from shield.adapters.sast.semgrep.adapter import (
    SEVERITY_MAP,
    _parse_semgrep_json,
)


def test_severity_mapping_complete():
    assert SEVERITY_MAP["ERROR"] == "high"
    assert SEVERITY_MAP["WARNING"] == "medium"
    assert SEVERITY_MAP["INFO"] == "low"


def test_parse_empty_output(empty_output):
    findings = _parse_semgrep_json(empty_output)
    assert findings == []


def test_parse_spring_boot_api_output(spring_boot_api_output):
    findings = _parse_semgrep_json(spring_boot_api_output)
    assert len(findings) == 3


def test_parse_finding_fields(spring_boot_api_output):
    findings = _parse_semgrep_json(spring_boot_api_output)
    f = findings[0]
    assert f.source == "semgrep"
    assert f.rule_id == "java.spring.security.noop-encoder"
    assert f.file == "shield/examples/spring-boot-api/src/main/java/com/example/api/config/SecurityConfig.java"
    assert f.lines == "17"
    assert f.severity == "high"
    assert f.category == "security"
    assert "NoOpPasswordEncoder" in f.message


def test_parse_multiline_range(spring_boot_api_output):
    """The third fixture finding spans lines 27-28."""
    findings = _parse_semgrep_json(spring_boot_api_output)
    multi = findings[2]
    assert multi.lines == "27-28"


def test_parse_severity_mapping(spring_boot_api_output):
    findings = _parse_semgrep_json(spring_boot_api_output)
    assert findings[0].severity == "high"  # ERROR
    assert findings[2].severity == "medium"  # WARNING


def test_parse_default_category_when_missing():
    payload = {
        "results": [
            {
                "check_id": "x",
                "path": "x.java",
                "start": {"line": 1},
                "end": {"line": 1},
                "extra": {"severity": "ERROR", "message": "x"}
            }
        ]
    }
    findings = _parse_semgrep_json(payload)
    assert findings[0].category == "code-quality"  # default


def test_parse_unknown_severity_defaults_medium():
    payload = {
        "results": [
            {
                "check_id": "x",
                "path": "x.java",
                "start": {"line": 1},
                "end": {"line": 1},
                "extra": {"severity": "FATAL_UNKNOWN", "message": "x"}
            }
        ]
    }
    findings = _parse_semgrep_json(payload)
    assert findings[0].severity == "medium"
