"""Tests for the shared Finding/AdapterResult dataclasses."""

from shield.adapters.sast.common import Finding, AdapterResult


def test_finding_construction():
    f = Finding(
        source="semgrep",
        rule_id="java.spring.security.noop-encoder",
        file="src/main/java/Foo.java",
        lines="17",
        severity="high",
        category="security",
        message="NoOpPasswordEncoder stores plaintext",
    )
    assert f.source == "semgrep"
    assert f.fix_hint is None


def test_finding_with_fix_hint():
    f = Finding(
        source="semgrep",
        rule_id="x",
        file="x.java",
        lines="1",
        severity="medium",
        category="code-quality",
        message="x",
        fix_hint="Use BCrypt instead",
    )
    assert f.fix_hint == "Use BCrypt instead"


def test_adapter_result_default_findings():
    r = AdapterResult(
        source="semgrep",
        mode="invoked",
        runtime_seconds=1.5,
    )
    assert r.findings == []
    assert r.note is None


def test_adapter_result_unavailable():
    r = AdapterResult(
        source="sonarqube",
        mode="unavailable",
        runtime_seconds=0.0,
        note="sonarqube adapter — credentials missing",
    )
    assert r.mode == "unavailable"
    assert r.findings == []
