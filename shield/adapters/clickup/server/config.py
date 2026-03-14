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


def _find_tesseract_marker() -> Path | None:
    """Walk up from cwd to find .tesseract.json."""
    current = Path.cwd()
    while current != current.parent:
        marker = current / ".tesseract.json"
        if marker.exists():
            return marker
        current = current.parent
    return None


def load_shield_config() -> SprintPlannerConfig | None:
    """Load config from ~/.tesseract/ paths (Shield native mode).

    Returns None if .tesseract.json is not found, falling back to legacy mode.
    """
    # Find .tesseract.json
    marker_path = _find_tesseract_marker()
    if not marker_path:
        return None

    with open(marker_path) as f:
        marker = json.load(f)

    project_name = marker["project"]
    tesseract_home = Path.home() / ".tesseract"
    project_dir = tesseract_home / "projects" / project_name

    # Load PM config
    pm_config_path = project_dir / "pm.json"
    if not pm_config_path.exists():
        return None

    with open(pm_config_path) as f:
        pm_config = json.load(f)

    # Load credentials
    creds_path = tesseract_home / "credentials.json"
    api_token = None
    if creds_path.exists():
        with open(creds_path) as f:
            creds = json.load(f)
        adapter_name = pm_config.get("adapter", "clickup")
        api_token = creds.get(adapter_name, {}).get("api_token")

    # Also check env var as fallback
    if not api_token:
        api_token = os.environ.get("CLICKUP_API_TOKEN")

    if not api_token:
        raise ValueError(
            f"No API token found. Add it to {creds_path} or set CLICKUP_API_TOKEN env var."
        )

    # Set the token in env so get_api_token() can find it
    os.environ["CLICKUP_API_TOKEN"] = api_token

    # Build SprintPlannerConfig from Shield config sources
    naming = pm_config.get("naming", {})
    lists_cfg = pm_config.get("lists", {})
    space_cfg = pm_config.get("space", {})
    folder_cfg = pm_config.get("folder", {})
    relationship_cfg = pm_config.get("relationship_field", {})

    # Build epic configs from pm.json
    epic_entries = pm_config.get("epics", [])
    epics = [
        EpicConfig(
            id=e.get("id", ""),
            name=e.get("name", ""),
            plan_doc=e.get("plan_doc", ""),
            epic_id=e.get("epic_id", ""),
        )
        for e in epic_entries
    ]

    return SprintPlannerConfig(
        clickup=ClickUpConfig(
            api_token_env="CLICKUP_API_TOKEN",
            workspace_id=pm_config.get("workspace_id", "auto"),
            space=SpaceConfig(
                name=space_cfg.get("name", ""),
                id=space_cfg.get("id", ""),
            ),
            folder=SpaceConfig(
                name=folder_cfg.get("name", ""),
                id=folder_cfg.get("id", ""),
            ),
            lists=ListsConfig(
                epics=SpaceConfig(
                    name=lists_cfg.get("epics", {}).get("name", ""),
                    id=lists_cfg.get("epics", {}).get("id", ""),
                ),
                backlog=SpaceConfig(
                    name=lists_cfg.get("backlog", {}).get("name", ""),
                    id=lists_cfg.get("backlog", {}).get("id", ""),
                ),
            ),
            relationship_field=RelationshipFieldConfig(
                id=relationship_cfg.get("id", ""),
                type=relationship_cfg.get("type", "list_relationship"),
            ),
        ),
        naming=NamingConfig(
            story_format=naming.get("story_format", "[{epic_id}] {name}"),
            epic_format=naming.get("epic_format", "[EPIC] {name} | [{epic_id}]"),
        ),
        plan_docs=PlanDocsConfig(
            format=pm_config.get("plan_docs", {}).get("format", "json"),
            base_path=pm_config.get("plan_docs", {}).get("base_path", "./phases"),
            epics=epics,
        ),
    )


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
