"""plan.json sidecar reader/writer with typed dataclasses."""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

CURRENT_SCHEMA_VERSION = "1.4"
MIN_SUPPORTED_VERSION = "1.0"


class PlanSchemaError(ValueError):
    """Raised when a plan.json file fails JSON Schema validation."""


class SchemaVersionTooNew(ValueError):
    """Raised when a plan.json declares a major version we don't support."""


def _parse_version(v: str) -> tuple[int, int]:
    parts = v.split(".")
    return int(parts[0]), int(parts[1])


def _schema_path() -> Path:
    # shield/parsers/shield_parsers/sidecar.py → shield/schema/plan-sidecar.schema.json
    # parents[0]=shield_parsers/, parents[1]=parsers/, parents[2]=shield/
    return Path(__file__).resolve().parents[2] / "schema" / "plan-sidecar.schema.json"


def _load_schema() -> dict[str, Any]:
    return json.loads(_schema_path().read_text(encoding="utf-8"))


@dataclass
class DesignRef:
    doc: str  # "trd" | "lld" | "prd"
    label: str
    component: str | None = None
    section_id: str | None = None
    anchor_url: str | None = None
    stale: bool = False
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Story:
    id: str
    name: str
    status: str
    description: str
    tasks: list[str]
    acceptance_criteria: list[str]
    assignee: str | None = None
    priority: str | None = None
    week: str | int | None = None
    milestone_id: str | None = None
    design_refs: list[DesignRef] = field(default_factory=list)
    pm_id: str | None = None
    pm_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Epic:
    id: str
    name: str
    stories: list[Story]
    pm_id: str | None = None
    pm_url: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Milestone:
    id: str
    name: str
    outcome: str
    exit_criteria: list[str]
    depends_on: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Plan:
    version: str
    project: str
    name: str
    epics: list[Epic]
    milestones: list[Milestone] = field(default_factory=list)
    phase: str | None = None
    source_research: str | None = None
    source_prd: str | None = None
    prd_rubric_version_at_planning: str | None = None
    last_aligned_with: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)


def _story_from_dict(d: dict[str, Any]) -> Story:
    known = {
        "id", "name", "status", "description", "tasks", "acceptance_criteria",
        "assignee", "priority", "week", "milestone_id", "design_refs",
        "pm_id", "pm_url",
    }
    refs = [_design_ref_from_dict(r) for r in d.get("design_refs", []) or []]
    extra = {k: v for k, v in d.items() if k not in known}
    return Story(
        id=d["id"],
        name=d["name"],
        status=d["status"],
        description=d["description"],
        tasks=list(d.get("tasks", [])),
        acceptance_criteria=list(d.get("acceptance_criteria", [])),
        assignee=d.get("assignee"),
        priority=d.get("priority"),
        week=d.get("week"),
        milestone_id=d.get("milestone_id"),
        design_refs=refs,
        pm_id=d.get("pm_id"),
        pm_url=d.get("pm_url"),
        extra=extra,
    )


def _design_ref_from_dict(d: dict[str, Any]) -> DesignRef:
    known = {"doc", "label", "component", "section_id", "anchor_url", "stale"}
    extra = {k: v for k, v in d.items() if k not in known}
    return DesignRef(
        doc=d["doc"],
        label=d["label"],
        component=d.get("component"),
        section_id=d.get("section_id"),
        anchor_url=d.get("anchor_url"),
        stale=d.get("stale", False),
        extra=extra,
    )


def _epic_from_dict(d: dict[str, Any]) -> Epic:
    known = {"id", "name", "stories", "pm_id", "pm_url"}
    extra = {k: v for k, v in d.items() if k not in known}
    return Epic(
        id=d["id"],
        name=d["name"],
        stories=[_story_from_dict(s) for s in d.get("stories", [])],
        pm_id=d.get("pm_id"),
        pm_url=d.get("pm_url"),
        extra=extra,
    )


def _milestone_from_dict(d: dict[str, Any]) -> Milestone:
    known = {"id", "name", "outcome", "exit_criteria", "depends_on"}
    extra = {k: v for k, v in d.items() if k not in known}
    return Milestone(
        id=d["id"],
        name=d["name"],
        outcome=d["outcome"],
        exit_criteria=list(d["exit_criteria"]),
        depends_on=list(d.get("depends_on", [])),
        extra=extra,
    )


def load_plan(path: Path | str) -> Plan:
    """Load a plan.json sidecar from disk into a typed `Plan` object."""
    p = Path(path)
    raw = json.loads(p.read_text(encoding="utf-8"))

    schema = _load_schema()
    try:
        jsonschema.validate(raw, schema)
    except jsonschema.ValidationError as e:
        # Path is a deque of keys; render it for the error message.
        loc = "/".join(str(seg) for seg in e.absolute_path) or "<root>"
        raise PlanSchemaError(
            f"plan.json at {p} failed schema validation at {loc}: {e.message}"
        ) from e

    declared_major, _ = _parse_version(raw["version"])
    current_major, _ = _parse_version(CURRENT_SCHEMA_VERSION)
    if declared_major > current_major:
        raise SchemaVersionTooNew(
            f"plan.json at {p} declares version {raw['version']!r}, "
            f"newer than supported (max {CURRENT_SCHEMA_VERSION!r})"
        )

    known_top = {
        "version", "project", "name", "phase", "source_research", "source_prd",
        "prd_rubric_version_at_planning", "last_aligned_with", "milestones",
        "epics", "metadata",
    }
    extra = {k: v for k, v in raw.items() if k not in known_top}
    return Plan(
        version=raw["version"],
        project=raw["project"],
        name=raw["name"],
        milestones=[_milestone_from_dict(m) for m in raw.get("milestones", [])],
        epics=[_epic_from_dict(e) for e in raw.get("epics", [])],
        phase=raw.get("phase"),
        source_research=raw.get("source_research"),
        source_prd=raw.get("source_prd"),
        prd_rubric_version_at_planning=raw.get("prd_rubric_version_at_planning"),
        last_aligned_with=raw.get("last_aligned_with"),
        metadata=dict(raw.get("metadata", {})),
        extra=extra,
    )


def _design_ref_to_dict(r: DesignRef) -> dict[str, Any]:
    out = {
        "doc": r.doc,
        "label": r.label,
        "component": r.component,
        "section_id": r.section_id,
        "anchor_url": r.anchor_url,
    }
    if r.stale:
        out["stale"] = True
    out.update(r.extra)
    return out


def _story_to_dict(s: Story) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": s.id,
        "name": s.name,
        "status": s.status,
        "assignee": s.assignee,
        "priority": s.priority,
        "week": s.week,
        "milestone_id": s.milestone_id,
        "description": s.description,
        "tasks": list(s.tasks),
        "acceptance_criteria": list(s.acceptance_criteria),
        "pm_id": s.pm_id,
        "pm_url": s.pm_url,
    }
    if s.design_refs:
        out["design_refs"] = [_design_ref_to_dict(r) for r in s.design_refs]
    out.update(s.extra)
    return out


def _epic_to_dict(e: Epic) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": e.id,
        "name": e.name,
        "pm_id": e.pm_id,
        "pm_url": e.pm_url,
        "stories": [_story_to_dict(s) for s in e.stories],
    }
    out.update(e.extra)
    return out


def _milestone_to_dict(m: Milestone) -> dict[str, Any]:
    out: dict[str, Any] = {
        "id": m.id,
        "name": m.name,
        "outcome": m.outcome,
        "exit_criteria": list(m.exit_criteria),
    }
    if m.depends_on:
        out["depends_on"] = list(m.depends_on)
    out.update(m.extra)
    return out


def _plan_to_dict(plan: Plan) -> dict[str, Any]:
    out: dict[str, Any] = {
        "version": CURRENT_SCHEMA_VERSION,  # always stamp current on save
        "project": plan.project,
        "name": plan.name,
        "phase": plan.phase,
        "source_research": plan.source_research,
        "source_prd": plan.source_prd,
        "prd_rubric_version_at_planning": plan.prd_rubric_version_at_planning,
        "last_aligned_with": plan.last_aligned_with,
        "milestones": [_milestone_to_dict(m) for m in plan.milestones],
        "epics": [_epic_to_dict(e) for e in plan.epics],
    }
    if plan.metadata:
        out["metadata"] = dict(plan.metadata)
    out.update(plan.extra)
    return out


def save_plan(path: Path | str, plan: Plan) -> None:
    """Atomically write a Plan to disk as plan.json, stamping CURRENT_SCHEMA_VERSION."""
    p = Path(path)
    data = _plan_to_dict(plan)
    parent = p.parent
    fd, tmp_path_str = tempfile.mkstemp(
        prefix=p.name + ".", suffix=".tmp", dir=parent
    )
    tmp_path = Path(tmp_path_str)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        os.replace(tmp_path, p)
    except Exception:
        # Clean up the temp file on any failure so we don't leave .tmp orphans.
        if tmp_path.exists():
            tmp_path.unlink()
        raise
