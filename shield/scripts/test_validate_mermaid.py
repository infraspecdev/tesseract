"""Eval for validate_mermaid.py.

RED cases reproduce the exact syntax errors that shipped in the component
LLDs (verified against mermaid-cli 10.9.1); GREEN cases confirm valid diagrams
and non-mermaid markdown pass clean.
"""

from __future__ import annotations

import pytest

import validate_mermaid as vm
from validate_mermaid import validate_text, _parse_node_error


@pytest.fixture(autouse=True)
def _force_heuristic(monkeypatch, request):
    # Tests tagged @pytest.mark.backend opt back into the real backend.
    if "backend" not in request.keywords:
        monkeypatch.setattr(vm, "_node_available", lambda: False)


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


# --- TASK 5: validate_text backend wiring + heuristic fallback ---

def _doc(body):
    return "# d\n\n```mermaid\n" + body + "\n```\n"


@pytest.mark.backend
def test_validate_text_prefers_backend_when_available(monkeypatch):
    monkeypatch.setattr(vm, "_node_available", lambda: True)
    monkeypatch.setattr(vm, "_validate_block_via_backend",
                        lambda start, body: [(start + 1, "Parse error on line 2:")])
    findings = vm.validate_text(_doc("sequenceDiagram\n    A->>B: whatever"))
    assert findings and "Parse error" in findings[0][1]


def test_validate_text_falls_back_to_heuristic_without_node():
    findings = vm.validate_text(_doc("sequenceDiagram\n    A->>B: a; b"))
    assert len(findings) == 1
    assert "statement separator" in findings[0][1]


def test_validate_text_backend_none_falls_back(monkeypatch):
    monkeypatch.setattr(vm, "_node_available", lambda: True)
    monkeypatch.setattr(vm, "_validate_block_via_backend", lambda start, body: None)
    findings = vm.validate_text(_doc("sequenceDiagram\n    A->>B: a; b"))
    assert any("statement separator" in m for _, m in findings)


# --- TASK 6: live Node backend integration (skip-guarded) ---

def _backend_smoke_ok() -> bool:
    if not vm._node_available():
        return False
    code, _ = vm._run_node_backend("sequenceDiagram\n  A->>B: ok\n")
    return code == 0


@pytest.mark.backend
@pytest.mark.skipif(not _backend_smoke_ok(), reason="node/mermaid backend unavailable")
def test_real_backend_catches_semicolon():
    findings = vm.validate_text("```mermaid\nsequenceDiagram\n  A->>B: a; b\n```\n")
    assert findings, "real parser should reject ';' in a sequence message"


@pytest.mark.backend
@pytest.mark.skipif(not _backend_smoke_ok(), reason="node/mermaid backend unavailable")
def test_real_backend_accepts_valid():
    assert vm.validate_text("```mermaid\nsequenceDiagram\n  A->>B: ok\n```\n") == []


# --- TASK 8: --fix transforms for known classes ---

def test_fix_replaces_semicolon_with_dash():
    block = "sequenceDiagram\n    A->>B: a; b"
    fixed = vm._fix_block(block)
    assert ";" not in fixed
    assert "a — b" in fixed

def test_fix_semicolon_inside_parens_uses_comma():
    block = 'sequenceDiagram\n    A->>B: f(x; y)'
    fixed = vm._fix_block(block)
    assert "f(x, y)" in fixed

def test_fix_semicolon_inside_quotes_uses_comma():
    block = 'sequenceDiagram\n    A-->>B: note="a; b"'
    fixed = vm._fix_block(block)
    assert 'note="a, b"' in fixed

def test_fix_renames_reserved_actor_consistently():
    block = ("sequenceDiagram\n"
             "    participant Create as pm_bulk_create\n"
             "    Skill->>Create: stories\n"
             "    Create-->>Skill: done")
    fixed = vm._fix_block(block)
    assert "participant CreateActor as pm_bulk_create" in fixed
    assert "Skill->>CreateActor:" in fixed
    assert "CreateActor-->>Skill:" in fixed
    # the prose alias after `as` is untouched; only the identifier changed
    assert "pm_bulk_create" in fixed

def test_fix_leaves_valid_flowchart_untouched():
    # ';' is legal in a flowchart — --fix must not turn a valid diagram invalid.
    block = "flowchart TD\n    A-->B;\n    B-->C;"
    assert vm._fix_block(block) == block

def test_fix_text_does_not_corrupt_flowchart(monkeypatch):
    monkeypatch.setattr(vm, "_node_available", lambda: False)
    src = "# d\n\n```mermaid\nflowchart TD\n    A-->B;\n    B-->C;\n```\n"
    new_text, _ = vm.fix_text(src)
    assert "A-->B;" in new_text and "B-->C;" in new_text

def test_fix_preserves_alias_reusing_reserved_word():
    # The free-form `as <alias>` text may legitimately reuse a reserved word;
    # only the identifier is renamed, never the alias.
    block = ("sequenceDiagram\n"
             "    participant create as create handler\n"
             "    A->>create: x")
    fixed = vm._fix_block(block)
    assert "participant createActor as create handler" in fixed
    assert "A->>createActor: x" in fixed


# --- TASK 9: --fix file rewrite + re-validate + CLI flag ---

def test_fix_text_repairs_and_clears_findings(monkeypatch):
    monkeypatch.setattr(vm, "_node_available", lambda: False)  # heuristic check
    src = "# d\n\n```mermaid\nsequenceDiagram\n    A->>B: a; b\n```\n"
    new_text, remaining = vm.fix_text(src)
    assert ";" not in new_text
    assert remaining == []

def test_fix_text_leaves_unfixable_and_reports(monkeypatch):
    monkeypatch.setattr(vm, "_node_available", lambda: False)
    # unbalanced alt is not a deterministic-fix class
    src = "# d\n\n```mermaid\nsequenceDiagram\n    alt x\n    A->>B: ok\n```\n"
    new_text, remaining = vm.fix_text(src)
    assert any("unbalanced" in m for _, m in remaining)

def test_main_fix_writes_file(tmp_path, monkeypatch):
    monkeypatch.setattr(vm, "_node_available", lambda: False)
    p = tmp_path / "d.md"
    p.write_text("# d\n\n```mermaid\nsequenceDiagram\n    A->>B: a; b\n```\n")
    rc = vm.main(["--fix", str(p)])
    assert ";" not in p.read_text()
    assert rc == 0  # all clean after fix
