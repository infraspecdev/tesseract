"""Tests for shield_backlog.view — render entries by order + pipeline status badges
(EPIC-1-S3 + EPIC-2-S1)."""
import json
from pathlib import Path

from shield_backlog.view import render


def _entry(idx, feature="auth", epic="Session mgmt", order=None, text="idea", source="user"):
    return {
        "id": f"{idx:08x}-0000-4000-8000-000000000001",
        "order": idx if order is None else order,
        "kind": "task",
        "source": source,
        "feature": feature,
        "epic": epic,
        "text": text,
    }


def test_render_empty_backlog():
    out = render({"schema_version": 1, "entries": []})
    assert "no entries" in out.lower()
    assert "Error" not in out


def test_render_entries_sorted_by_order():
    """Even when entries are stored out-of-order, view renders ascending."""
    doc = {
        "schema_version": 1,
        "entries": [
            _entry(3, text="third"),
            _entry(1, text="first"),
            _entry(2, text="second"),
        ],
    }
    out = render(doc)
    # First non-empty data line should reference order=1.
    lines = [l for l in out.splitlines() if l.strip() and not l.startswith(" ")]
    assert lines[0].startswith("1. ")
    assert lines[1].startswith("2. ")
    assert lines[2].startswith("3. ")


def test_render_line_format_pinned():
    """The pinned per-entry render line includes order, id-short, feature, epic, source, text."""
    doc = {"schema_version": 1, "entries": [_entry(5, feature="billing", epic="Invoice", text="PDF polish", source="agent")]}
    out = render(doc).splitlines()[0]
    assert "5. " in out
    assert "[00000005]" in out  # id-short = first segment
    assert "(billing / Invoice, agent)" in out
    assert "PDF polish" in out


def test_render_status_badges_present_feature():
    """A feature present in manifest renders the artifact flags as badges."""
    manifest = {
        "schema_version": 2,
        "features": [
            {"name": "auth", "artifacts": {"research": False, "prd": True, "plan_json": False}}
        ],
    }
    doc = {"schema_version": 1, "entries": [_entry(1, feature="auth")]}
    out = render(doc, manifest=manifest)
    assert "research –" in out
    assert "prd ✓" in out
    assert "plan –" in out


def test_render_status_badges_prd_yes_plan_no_stays():
    """An entry whose feature has prd but no plan shows 'prd ✓ plan –' (and is not pruned by view)."""
    manifest = {
        "schema_version": 2,
        "features": [
            {"name": "auth", "artifacts": {"research": True, "prd": True, "plan_json": False}}
        ],
    }
    doc = {"schema_version": 1, "entries": [_entry(1, feature="auth", text="prd-but-no-plan idea")]}
    out = render(doc, manifest=manifest)
    assert "prd ✓" in out
    assert "plan –" in out
    assert "prd-but-no-plan idea" in out


def test_render_status_badges_missing_feature_renders_not_started():
    """A feature absent from the manifest renders 'not started' badge."""
    manifest = {"schema_version": 2, "features": [{"name": "billing", "artifacts": {}}]}
    doc = {"schema_version": 1, "entries": [_entry(1, feature="auth")]}
    out = render(doc, manifest=manifest)
    assert "not started" in out


def test_render_without_manifest_omits_badges():
    """When no manifest is supplied, no badge line is rendered."""
    doc = {"schema_version": 1, "entries": [_entry(1)]}
    out = render(doc)
    assert "research" not in out
    assert "not started" not in out


def test_render_handles_unrecognized_manifest_shape_gracefully():
    """A malformed manifest shape → no badge string, no crash."""
    doc = {"schema_version": 1, "entries": [_entry(1)]}
    out = render(doc, manifest={"unexpected": True})  # no 'features' key
    assert "1. " in out  # still rendered
    assert "research" not in out  # no badges
