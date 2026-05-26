"""plan.json sidecar reader/writer with typed dataclasses."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import jsonschema

CURRENT_SCHEMA_VERSION = "1.4"
MIN_SUPPORTED_VERSION = "1.0"


class PlanSchemaError(ValueError):
    """Raised when a plan.json file fails JSON Schema validation."""


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
