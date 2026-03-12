"""Load and validate sprint-planner.json configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path

from pydantic import BaseModel, Field


class SpaceConfig(BaseModel):
    name: str
    id: str


class ListsConfig(BaseModel):
    epics: SpaceConfig
    backlog: SpaceConfig


class RelationshipFieldConfig(BaseModel):
    id: str
    type: str = "list_relationship"


class ClickUpConfig(BaseModel):
    api_token_env: str = "CLICKUP_API_TOKEN"
    workspace_id: str = "auto"
    space: SpaceConfig
    folder: SpaceConfig
    lists: ListsConfig
    relationship_field: RelationshipFieldConfig
    custom_fields: dict = Field(default_factory=dict)


class TeamMember(BaseModel):
    name: str
    id: str


class NamingConfig(BaseModel):
    story_format: str = "[{epic_id}] {name}"
    epic_format: str = "[EPIC] {name} | [{epic_id}]"


class EpicConfig(BaseModel):
    id: str
    name: str
    plan_doc: str
    epic_id: str
    naming: NamingConfig | None = None


class PlanDocsConfig(BaseModel):
    format: str = "html"
    base_path: str = "./phases"
    epics: list[EpicConfig]


class HtmlExtractionConfig(BaseModel):
    story_selector: str = "div.story[id^='story-']"
    name_pattern: str = r"Story \d+: (.+)"
    clickup_id_selector: str = "a.badge-clickup"
    status_selector: str = ".badge:not(.badge-clickup):not(.badge-to-create)"


class StoryExtractionConfig(BaseModel):
    html: HtmlExtractionConfig = Field(default_factory=HtmlExtractionConfig)


class ActionLogConfig(BaseModel):
    path: str = "./clickup_actions.json"


class SprintPlannerConfig(BaseModel):
    version: str = "1"
    clickup: ClickUpConfig
    team: list[TeamMember] = Field(default_factory=list)
    plan_docs: PlanDocsConfig
    story_extraction: StoryExtractionConfig = Field(default_factory=StoryExtractionConfig)
    naming: NamingConfig = Field(default_factory=NamingConfig)
    action_log: ActionLogConfig = Field(default_factory=ActionLogConfig)


def load_config(path: str | Path | None = None) -> SprintPlannerConfig:
    """Load sprint-planner.json from path, env var, or default location."""
    if path is None:
        path = os.environ.get("SPRINT_PLANNER_CONFIG", "./sprint-planner.json")
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with open(path) as f:
        data = json.load(f)
    return SprintPlannerConfig(**data)


def get_api_token(config: SprintPlannerConfig) -> str:
    """Read ClickUp API token from the env var named in config."""
    env_var = config.clickup.api_token_env
    token = os.environ.get(env_var)
    if not token:
        raise RuntimeError(
            f"Set {env_var} environment variable with your ClickUp personal API token"
        )
    return token
