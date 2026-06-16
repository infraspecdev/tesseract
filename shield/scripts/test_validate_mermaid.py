"""Eval for validate_mermaid.py.

RED cases reproduce the exact syntax errors that shipped in the component
LLDs (verified against mermaid-cli 10.9.1); GREEN cases confirm valid diagrams
and non-mermaid markdown pass clean.
"""

from __future__ import annotations

from validate_mermaid import validate_text


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
