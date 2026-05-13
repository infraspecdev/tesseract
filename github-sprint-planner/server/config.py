"""Load and validate sprint-planner.json configuration."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from pydantic import BaseModel, Field


class GitHubConfig(BaseModel):
    token_env: str = "GITHUB_TOKEN"
    owner: str
    repo: str
    project_number: int


class TeamMember(BaseModel):
    name: str
    github_login: str


class NamingConfig(BaseModel):
    story_format: str = "[{epic_id}] {name}"


class EpicConfig(BaseModel):
    id: str
    name: str
    plan_doc: str
    epic_issue_number: int
    naming: NamingConfig | None = None


class PlanDocsConfig(BaseModel):
    format: str = "html"
    base_path: str = "./epics"
    epics: list[EpicConfig]


class HtmlExtractionConfig(BaseModel):
    story_selector: str = "div.story[id^='story-']"
    name_pattern: str = r"Story \d+: (.+)"
    issue_selector: str = "a.badge-github"
    status_selector: str = ".badge:not(.badge-github):not(.badge-to-create)"


class StoryExtractionConfig(BaseModel):
    html: HtmlExtractionConfig = Field(default_factory=HtmlExtractionConfig)


class ActionLogConfig(BaseModel):
    path: str = "./github_actions.json"


class SprintPlannerConfig(BaseModel):
    version: str = "1"
    github: GitHubConfig
    team: list[TeamMember] = Field(default_factory=list)
    plan_docs: PlanDocsConfig
    story_extraction: StoryExtractionConfig = Field(default_factory=StoryExtractionConfig)
    naming: NamingConfig = Field(default_factory=NamingConfig)
    action_log: ActionLogConfig = Field(default_factory=ActionLogConfig)


def load_config(path: str | Path | None = None) -> SprintPlannerConfig:
    if path is None:
        path = os.environ.get("SPRINT_PLANNER_CONFIG", "./sprint-planner.json")
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Config not found: {path}")
    with open(path) as f:
        data = json.load(f)
    return SprintPlannerConfig(**data)


def _get_gh_cli_token() -> str | None:
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=5
        )
        token = result.stdout.strip()
        return token if token else None
    except Exception:
        return None


def get_github_token(config: SprintPlannerConfig) -> str:
    token = os.environ.get(config.github.token_env) or _get_gh_cli_token()
    if not token:
        raise RuntimeError(
            f"GitHub token not found. Set {config.github.token_env} env var or run `gh auth login`."
        )
    return token
