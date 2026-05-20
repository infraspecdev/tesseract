"""Load and validate GitHub sprint-planner configuration."""

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
    project_number: int = 0


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


def _find_shield_marker() -> Path | None:
    """Walk up from cwd to find .shield.json.

    Also checks CLAUDE_PROJECT_ROOT env var — Claude Code sets this when
    launching MCP servers so the server's cwd may differ from the project root.
    """
    search_roots = []
    if project_root := os.environ.get("CLAUDE_PROJECT_ROOT"):
        search_roots.append(Path(project_root))
    search_roots.append(Path.cwd())

    for start in search_roots:
        current = start
        while current != current.parent:
            marker = current / ".shield.json"
            if marker.exists():
                return marker
            current = current.parent
    return None


def _get_gh_cli_token() -> str | None:
    try:
        result = subprocess.run(
            ["gh", "auth", "token"], capture_output=True, text=True, timeout=5
        )
        token = result.stdout.strip()
        return token if token else None
    except Exception:
        return None


def load_shield_config() -> SprintPlannerConfig | None:
    """Load config from ~/.shield/ paths (Shield native mode).

    Returns None if .shield.json is not found, falling back to legacy mode.
    """
    marker_path = _find_shield_marker()
    if not marker_path:
        return None

    with open(marker_path) as f:
        marker = json.load(f)

    project_name = marker["project"]
    shield_home = Path.home() / ".shield"
    project_dir = shield_home / "projects" / project_name

    pm_config_path = project_dir / "pm.json"
    if not pm_config_path.exists():
        return None

    with open(pm_config_path) as f:
        pm_config = json.load(f)

    creds_path = shield_home / "credentials.json"
    api_token = None
    if creds_path.exists():
        with open(creds_path) as f:
            creds = json.load(f)
        api_token = creds.get("github", {}).get("api_token")

    if not api_token:
        api_token = os.environ.get("GITHUB_TOKEN")
    if not api_token:
        api_token = _get_gh_cli_token()
    if not api_token:
        raise ValueError(
            f"No GitHub token found. Add it to {creds_path} under 'github.api_token', "
            "set GITHUB_TOKEN env var, or run `gh auth login`."
        )

    os.environ["GITHUB_TOKEN"] = api_token

    naming = pm_config.get("naming", {})
    plan_docs_cfg = pm_config.get("plan_docs", {})
    epic_entries = pm_config.get("epics", [])
    epics = [
        EpicConfig(
            id=e["id"],
            name=e.get("name", ""),
            plan_doc=e.get("plan_doc", ""),
            epic_issue_number=e["epic_issue_number"],
        )
        for e in epic_entries
    ]

    team_entries = pm_config.get("team", [])
    team = [TeamMember(name=m["name"], github_login=m["github_login"]) for m in team_entries]

    return SprintPlannerConfig(
        github=GitHubConfig(
            token_env="GITHUB_TOKEN",
            owner=pm_config["owner"],
            repo=pm_config["repo"],
            project_number=pm_config.get("project_number", 0),
        ),
        team=team,
        naming=NamingConfig(
            story_format=naming.get("story_format", "[{epic_id}] {name}"),
        ),
        plan_docs=PlanDocsConfig(
            format=plan_docs_cfg.get("format", "html"),
            base_path=plan_docs_cfg.get("base_path", "./epics"),
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


def get_github_token(config: SprintPlannerConfig) -> str:
    token = os.environ.get(config.github.token_env) or _get_gh_cli_token()
    if not token:
        raise RuntimeError(
            f"GitHub token not found. Set {config.github.token_env} env var or run `gh auth login`."
        )
    return token
