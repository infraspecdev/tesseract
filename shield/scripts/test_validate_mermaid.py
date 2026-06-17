"""Eval for validate_mermaid.py.

RED cases reproduce the exact syntax errors that shipped in the component
LLDs (verified against mermaid-cli 10.9.1); GREEN cases confirm valid diagrams
and non-mermaid markdown pass clean.
"""

from __future__ import annotations

import validate_mermaid as vm
from validate_mermaid import validate_text, _parse_node_error


def _block(body: str) -> str:
    return f"# doc\n\n```mermaid\n{body}\n```\n"


# --- GREEN: valid diagrams produce no findings ---

def test_valid_sequence_diagram_passes():
    md = _block(
        "sequenceDiagram\n"
        "    participant A as Caller\n"
        "    participant B as Service\n"
        "    A->>B: do(x, y)\n"
        "    alt ok\n"
        "        B-->>A: result\n"
        "    else fail\n"
        "        B-->>A: error\n"
        "    end\n"
    )
    assert validate_text(md) == []


def test_markdown_without_mermaid_passes():
    assert validate_text("# title\n\nSome prose; with a semicolon.\n") == []


def test_non_sequence_diagram_semicolon_not_flagged():
    # Flowcharts legitimately allow ';' — we must not false-positive.
    md = _block("flowchart TD\n    A-->B;\n    B-->C;\n")
    assert validate_text(md) == []


# --- RED: the failure modes that actually shipped ---

def test_semicolon_in_message_flagged():
    md = _block(
        "sequenceDiagram\n"
        "    A->>B: skipped += 1; log outcome=skipped\n"
    )
    findings = validate_text(md)
    assert len(findings) == 1
    assert "statement separator" in findings[0][1]


def test_semicolon_inside_quotes_still_flagged():
    # sast.md case: ';' inside a double-quoted note still breaks mermaid.
    md = _block(
        "sequenceDiagram\n"
        '    A-->>B: Result(note="api err; scan err")\n'
    )
    assert len(validate_text(md)) == 1


def test_reserved_word_participant_flagged():
    # clickup.md case: a participant literally named `Create`.
    md = _block(
        "sequenceDiagram\n"
        "    participant Create as pm_bulk_create\n"
        "    Skill->>Create: stories\n"
    )
    findings = validate_text(md)
    msgs = " ".join(m for _, m in findings)
    assert "reserved mermaid keyword" in msgs


def test_unbalanced_blocks_flagged():
    md = _block(
        "sequenceDiagram\n"
        "    A->>B: go\n"
        "    alt yes\n"
        "        B-->>A: ok\n"  # missing 'end'
    )
    findings = validate_text(md)
    assert any("unbalanced blocks" in m for _, m in findings)


def test_multiple_semicolons_each_flagged():
    md = _block(
        "sequenceDiagram\n"
        "    A->>B: one; two\n"
        "    A->>B: three; four\n"
    )
    assert len(validate_text(md)) == 2


def test_line_numbers_are_document_relative():
    # Findings must point at the real line in the file, not block-relative.
    md = "# heading\n\nintro\n\n" + _block("sequenceDiagram\n    A->>B: x; y\n")
    findings = validate_text(md)
    assert len(findings) == 1
    line, _ = findings[0]
    # lines 1-4 preamble, 5 '# doc', 6 blank, 7 fence, 8 'sequenceDiagram',
    # 9 the message — findings are document-relative, not block-relative.
    assert line == 9


# --- TASK 3: parse mermaid backend error string ---

def test_parse_node_error_extracts_block_line():
    stderr = "Parse error on line 3:\n... -->> ...\nExpecting 'X', got ';'"
    line, msg = _parse_node_error(stderr)
    assert line == 3
    assert "Parse error" in msg


def test_parse_node_error_defaults_line_to_one():
    line, msg = _parse_node_error("Lexical error: something")
    assert line == 1
    assert "Lexical error" in msg


# --- TASK 4: per-block backend call ---

def test_validate_block_uses_backend_when_available(monkeypatch):
    monkeypatch.setattr(vm, "_node_available", lambda: True)
    monkeypatch.setattr(vm, "_run_node_backend", lambda body: (1, "Parse error on line 2:\n..."))
    findings = vm._validate_block_via_backend(start_line=10, body=["sequenceDiagram", "A->>B: a; b"])
    assert findings == [(11, "Parse error on line 2:")]


def test_validate_block_backend_ok_returns_no_findings(monkeypatch):
    monkeypatch.setattr(vm, "_node_available", lambda: True)
    monkeypatch.setattr(vm, "_run_node_backend", lambda body: (0, ""))
    assert vm._validate_block_via_backend(10, ["sequenceDiagram", "A->>B: ok"]) == []


def test_validate_block_backend_setup_failure_returns_none(monkeypatch):
    monkeypatch.setattr(vm, "_node_available", lambda: True)
    monkeypatch.setattr(vm, "_run_node_backend", lambda body: (2, "backend-setup-failure: x"))
    assert vm._validate_block_via_backend(10, ["sequenceDiagram"]) is None
