"""plan.json sidecar reader/writer with typed dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

CURRENT_SCHEMA_VERSION = "1.4"
MIN_SUPPORTED_VERSION = "1.0"


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
