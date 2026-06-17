from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]  # repo root from shield/scripts/

def test_style_guide_exists():
    assert (ROOT / "shield/skills/general/mermaid-authoring.md").is_file()

def test_renderer_and_validator_pin_same_major():
    shell = (ROOT / "shield/templates/shell.html").read_text()
    validator = (ROOT / "shield/scripts/validate_mermaid.py").read_text()
    assert "mermaid@10" in shell        # renderer CDN pin
    assert 'mermaid@10' in validator    # _NODE_MERMAID_PKG pin

def test_emitting_skills_reference_style_guide():
    for rel in [
        "shield/skills/general/lld-docs/SKILL.md",
        "shield/skills/general/prd-docs/SKILL.md",
        "shield/skills/general/plan-docs/SKILL.md",
        "shield/agents/architect.md",
    ]:
        assert "mermaid-authoring" in (ROOT / rel).read_text(), rel

def test_lld_docs_has_validate_before_write_contract():
    text = (ROOT / "shield/skills/general/lld-docs/SKILL.md").read_text()
    assert "validate_mermaid.py" in text
    # The contract must require validate → fix → agent-repair before the write.
    assert "before" in text.lower() and "write" in text.lower()
    assert "--fix" in text
