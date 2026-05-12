# github-sprint-planner Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `github-sprint-planner` Claude Code plugin that mirrors `clickup-sprint-planner` with a GitHub Issues + Projects v2 backend — plan doc sync, bulk create/update, and sprint status.

**Architecture:** Separate plugin under `github-sprint-planner/` with a `GitHubClient` wrapping GitHub REST + GraphQL APIs. Parsers and action log are adapted copies from the ClickUp plugin. Four MCP tools (`sprint_sync`, `sprint_bulk_create`, `sprint_bulk_update`, `sprint_status`) registered via FastMCP.

**Tech Stack:** Python 3.11+, `mcp[cli]`, `httpx`, `beautifulsoup4`, `pydantic`, `pytest`, `pytest-asyncio`

---

## File Map

| File | Status | Purpose |
|------|--------|---------|
| `github-sprint-planner/.claude-plugin/plugin.json` | Create | Plugin manifest |
| `github-sprint-planner/.mcp.json` | Create | MCP server wiring |
| `github-sprint-planner/pyproject.toml` | Create | Python deps |
| `github-sprint-planner/server/config.py` | Create | Pydantic config models |
| `github-sprint-planner/server/github_client.py` | Create | REST + GraphQL API wrapper |
| `github-sprint-planner/server/action_log.py` | Copy+adapt | Append-only audit log |
| `github-sprint-planner/server/parsers/base.py` | Copy+adapt | Story dataclass (`issue_number` instead of `clickup_id`) |
| `github-sprint-planner/server/parsers/html_parser.py` | Copy+adapt | HTML plan doc parser |
| `github-sprint-planner/server/parsers/markdown_parser.py` | Copy+adapt | Markdown stub |
| `github-sprint-planner/server/parsers/__init__.py` | Create | Empty |
| `github-sprint-planner/server/tools/_helpers.py` | Create | Shared helpers |
| `github-sprint-planner/server/tools/sprint_status.py` | Create | `sprint_status` MCP tool |
| `github-sprint-planner/server/tools/bulk_update.py` | Create | `sprint_bulk_update` MCP tool |
| `github-sprint-planner/server/tools/bulk_create.py` | Create | `sprint_bulk_create` MCP tool |
| `github-sprint-planner/server/tools/sync.py` | Create | `sprint_sync` MCP tool |
| `github-sprint-planner/server/tools/action_log_tool.py` | Create | `sprint_action_log` MCP tool |
| `github-sprint-planner/server/tools/__init__.py` | Create | Empty |
| `github-sprint-planner/server/__init__.py` | Create | Empty |
| `github-sprint-planner/server/main.py` | Create | FastMCP entry point |
| `github-sprint-planner/commands/sprint-sync.md` | Create | `/sprint-sync` command |
| `github-sprint-planner/commands/sprint-plan.md` | Create | `/sprint-plan` command |
| `github-sprint-planner/commands/sprint-status.md` | Create | `/sprint-status` command |
| `github-sprint-planner/skills/sprint-planning/SKILL.md` | Create | Auto-invoked skill |
| `github-sprint-planner/skills/sprint-planning/card-format.md` | Create | Card format reference |
| `github-sprint-planner/examples/sprint-planner.example.json` | Create | Example config |
| `github-sprint-planner/README.md` | Create | Plugin docs |
| `github-sprint-planner/tests/test_config.py` | Create | Config parsing tests |
| `github-sprint-planner/tests/test_github_client.py` | Create | Client tests (httpx mock) |
| `github-sprint-planner/tests/test_sync.py` | Create | Sync diff logic tests |
| `github-sprint-planner/tests/__init__.py` | Create | Empty |
| `.claude-plugin/marketplace.json` | Modify | Register new plugin + bump version |

---

## Task 1: Plugin scaffold

**Files:**
- Create: `github-sprint-planner/.claude-plugin/plugin.json`
- Create: `github-sprint-planner/.mcp.json`
- Create: `github-sprint-planner/pyproject.toml`
- Create: `github-sprint-planner/server/__init__.py`
- Create: `github-sprint-planner/server/parsers/__init__.py`
- Create: `github-sprint-planner/server/tools/__init__.py`
- Create: `github-sprint-planner/tests/__init__.py`

- [ ] **Step 1: Create plugin manifest**

Create `github-sprint-planner/.claude-plugin/plugin.json`:
```json
{
  "name": "github-sprint-planner",
  "description": "Sprint planning tools for GitHub Issues + Projects v2 — bulk operations, sub-issue linking, plan doc sync, and action logging.",
  "author": {
    "name": "infraspecdev"
  },
  "repository": "https://github.com/infraspecdev/tesseract",
  "license": "MIT",
  "keywords": ["github", "sprint", "planning", "bulk-ops", "mcp", "projects"]
}
```

- [ ] **Step 2: Create MCP server config**

Create `github-sprint-planner/.mcp.json`:
```json
{
  "mcpServers": {
    "github-sprint-planner": {
      "command": "uv",
      "args": ["run", "--directory", "${CLAUDE_PLUGIN_ROOT}", "python", "server/main.py"]
    }
  }
}
```

- [ ] **Step 3: Create pyproject.toml**

Create `github-sprint-planner/pyproject.toml`:
```toml
[project]
name = "github-sprint-planner"
version = "1.0.0"
description = "MCP server for GitHub sprint planning — bulk ops, sub-issues, plan doc sync"
requires-python = ">=3.11"
dependencies = [
    "mcp[cli]>=1.12",
    "httpx>=0.27",
    "beautifulsoup4>=4.12",
    "pydantic>=2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "respx>=0.21",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["server"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

- [ ] **Step 4: Create empty `__init__.py` files**

Create `github-sprint-planner/server/__init__.py` — empty file.
Create `github-sprint-planner/server/parsers/__init__.py` — empty file.
Create `github-sprint-planner/server/tools/__init__.py` — empty file.
Create `github-sprint-planner/tests/__init__.py` — empty file.

- [ ] **Step 5: Install dependencies**

```bash
cd github-sprint-planner && uv sync --extra dev
```

Expected: lock file created, packages installed with no errors.

---

## Task 2: Config layer

**Files:**
- Create: `github-sprint-planner/server/config.py`
- Create: `github-sprint-planner/tests/test_config.py`

- [ ] **Step 1: Write failing tests**

Create `github-sprint-planner/tests/test_config.py`:
```python
import json
import pytest
from pathlib import Path
from server.config import load_config, get_github_token, SprintPlannerConfig


MINIMAL_CONFIG = {
    "version": "1",
    "github": {
        "token_env": "GITHUB_TOKEN",
        "owner": "infraspecdev",
        "repo": "my-repo",
        "project_number": 5
    },
    "team": [
        {"name": "Alice", "github_login": "alice"}
    ],
    "plan_docs": {
        "format": "html",
        "base_path": "./epics",
        "epics": [
            {
                "id": "P1",
                "name": "Epic 1",
                "plan_doc": "01-epic/plan.html",
                "epic_issue_number": 42
            }
        ]
    }
}


def test_load_config_from_file(tmp_path):
    config_file = tmp_path / "sprint-planner.json"
    config_file.write_text(json.dumps(MINIMAL_CONFIG))
    config = load_config(config_file)
    assert config.github.owner == "infraspecdev"
    assert config.github.repo == "my-repo"
    assert config.github.project_number == 5
    assert config.team[0].github_login == "alice"
    assert config.plan_docs.epics[0].epic_issue_number == 42


def test_load_config_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(tmp_path / "nonexistent.json")


def test_get_github_token_from_env(monkeypatch, tmp_path):
    config_file = tmp_path / "sprint-planner.json"
    config_file.write_text(json.dumps(MINIMAL_CONFIG))
    config = load_config(config_file)
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test123")
    token = get_github_token(config)
    assert token == "ghp_test123"


def test_get_github_token_missing_raises(monkeypatch, tmp_path):
    config_file = tmp_path / "sprint-planner.json"
    config_file.write_text(json.dumps(MINIMAL_CONFIG))
    config = load_config(config_file)
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    monkeypatch.setattr("server.config._get_gh_cli_token", lambda: None)
    with pytest.raises(RuntimeError, match="GITHUB_TOKEN"):
        get_github_token(config)


def test_story_extraction_defaults(tmp_path):
    config_file = tmp_path / "sprint-planner.json"
    config_file.write_text(json.dumps(MINIMAL_CONFIG))
    config = load_config(config_file)
    assert config.story_extraction.html.story_selector == "div.story[id^='story-']"
    assert config.story_extraction.html.issue_selector == "a.badge-github"
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd github-sprint-planner && uv run pytest tests/test_config.py -v
```

Expected: `ImportError: No module named 'server.config'`

- [ ] **Step 3: Create config.py**

Create `github-sprint-planner/server/config.py`:
```python
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
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd github-sprint-planner && uv run pytest tests/test_config.py -v
```

Expected: 5 tests pass.

---

## Task 3: GitHub client (REST)

**Files:**
- Create: `github-sprint-planner/server/github_client.py`
- Create: `github-sprint-planner/tests/test_github_client.py`

- [ ] **Step 1: Write failing tests**

Create `github-sprint-planner/tests/test_github_client.py`:
```python
import pytest
import httpx
import respx
from server.github_client import GitHubClient, GitHubAPIError


BASE = "https://api.github.com"


@pytest.fixture
def client():
    return GitHubClient("ghp_test", "infraspecdev", "my-repo")


@respx.mock
async def test_get_sub_issues(client):
    respx.get(f"{BASE}/repos/infraspecdev/my-repo/issues/42/sub_issues").mock(
        return_value=httpx.Response(200, json=[
            {"number": 10, "title": "Story 1: Setup VPC", "state": "open",
             "assignees": [], "node_id": "I_abc"},
            {"number": 11, "title": "Story 2: NAT Gateway", "state": "closed",
             "assignees": [], "node_id": "I_def"},
        ])
    )
    issues = await client.get_sub_issues(42)
    assert len(issues) == 2
    assert issues[0]["number"] == 10


@respx.mock
async def test_create_issue(client):
    respx.post(f"{BASE}/repos/infraspecdev/my-repo/issues").mock(
        return_value=httpx.Response(201, json={
            "number": 99, "title": "P1 - Setup VPC", "node_id": "I_new",
            "html_url": "https://github.com/infraspecdev/my-repo/issues/99"
        })
    )
    issue = await client.create_issue("P1 - Setup VPC", body="description")
    assert issue["number"] == 99


@respx.mock
async def test_add_sub_issue(client):
    respx.post(f"{BASE}/repos/infraspecdev/my-repo/issues/42/sub_issues").mock(
        return_value=httpx.Response(201, json={"number": 99})
    )
    result = await client.add_sub_issue(parent_number=42, sub_issue_number=99)
    assert result["number"] == 99


@respx.mock
async def test_update_issue(client):
    respx.patch(f"{BASE}/repos/infraspecdev/my-repo/issues/99").mock(
        return_value=httpx.Response(200, json={"number": 99, "state": "closed"})
    )
    result = await client.update_issue(99, {"state": "closed"})
    assert result["state"] == "closed"


@respx.mock
async def test_api_error_raises(client):
    respx.get(f"{BASE}/repos/infraspecdev/my-repo/issues/42/sub_issues").mock(
        return_value=httpx.Response(404, json={"message": "Not Found"})
    )
    with pytest.raises(GitHubAPIError) as exc:
        await client.get_sub_issues(42)
    assert exc.value.status_code == 404


@respx.mock
async def test_get_repo_issues_paginated(client):
    respx.get(f"{BASE}/repos/infraspecdev/my-repo/issues").mock(
        return_value=httpx.Response(200, json=[
            {"number": 1, "title": "Issue 1", "state": "open", "assignees": [], "node_id": "I_1"}
        ])
    )
    issues = await client.get_repo_issues(state="open")
    assert len(issues) == 1
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd github-sprint-planner && uv run pytest tests/test_github_client.py -v
```

Expected: `ImportError: No module named 'server.github_client'`

- [ ] **Step 3: Create github_client.py**

Create `github-sprint-planner/server/github_client.py`:
```python
"""GitHub REST + GraphQL API wrapper using httpx.AsyncClient."""

from __future__ import annotations

from typing import Any

import httpx


class GitHubAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(f"GitHub API {status_code}: {message}")


class GitHubClient:
    """Async wrapper around GitHub REST v3 and GraphQL v4 APIs."""

    REST_BASE = "https://api.github.com"
    GRAPHQL_URL = "https://api.github.com/graphql"

    def __init__(self, token: str, owner: str, repo: str):
        self.owner = owner
        self.repo = repo
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        self._client = httpx.AsyncClient(
            base_url=self.REST_BASE,
            headers=headers,
            timeout=30.0,
        )

    async def close(self):
        await self._client.aclose()

    # -- low-level REST -------------------------------------------------------

    async def _rest(
        self, method: str, path: str, json: dict | None = None, params: dict | None = None
    ) -> Any:
        resp = await self._client.request(method, path, json=json, params=params)
        if resp.status_code >= 400:
            body = resp.json() if "application/json" in resp.headers.get("content-type", "") else {}
            raise GitHubAPIError(resp.status_code, body.get("message", resp.text[:200]))
        return resp.json() if resp.content else {}

    # -- low-level GraphQL ----------------------------------------------------

    async def _graphql(self, query: str, variables: dict | None = None) -> dict:
        payload: dict = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = await self._client.post(self.GRAPHQL_URL, json=payload)
        if resp.status_code >= 400:
            raise GitHubAPIError(resp.status_code, resp.text[:200])
        data = resp.json()
        if "errors" in data:
            raise GitHubAPIError(422, str(data["errors"]))
        return data.get("data", {})

    # -- issues ---------------------------------------------------------------

    async def get_repo_issues(self, *, state: str = "open", per_page: int = 100) -> list[dict]:
        """Fetch all issues in the repo (auto-paginated)."""
        all_issues: list[dict] = []
        page = 1
        while True:
            batch = await self._rest(
                "GET",
                f"/repos/{self.owner}/{self.repo}/issues",
                params={"state": state, "per_page": per_page, "page": page},
            )
            all_issues.extend(batch)
            if len(batch) < per_page:
                break
            page += 1
        return all_issues

    async def get_sub_issues(self, parent_number: int) -> list[dict]:
        """Fetch all sub-issues of an issue."""
        return await self._rest(
            "GET", f"/repos/{self.owner}/{self.repo}/issues/{parent_number}/sub_issues"
        )

    async def create_issue(
        self,
        title: str,
        body: str = "",
        assignees: list[str] | None = None,
        labels: list[str] | None = None,
    ) -> dict:
        """Create a GitHub issue. Returns the created issue object."""
        payload: dict = {"title": title, "body": body}
        if assignees:
            payload["assignees"] = assignees
        if labels:
            payload["labels"] = labels
        return await self._rest("POST", f"/repos/{self.owner}/{self.repo}/issues", json=payload)

    async def update_issue(self, issue_number: int, updates: dict) -> dict:
        """Update a GitHub issue."""
        return await self._rest(
            "PATCH", f"/repos/{self.owner}/{self.repo}/issues/{issue_number}", json=updates
        )

    async def add_sub_issue(self, parent_number: int, sub_issue_number: int) -> dict:
        """Link an issue as a sub-issue of a parent."""
        return await self._rest(
            "POST",
            f"/repos/{self.owner}/{self.repo}/issues/{parent_number}/sub_issues",
            json={"sub_issue_id": sub_issue_number},
        )

    # -- Projects v2 (GraphQL) ------------------------------------------------

    async def get_project_id(self, project_number: int) -> tuple[str, str]:
        """Get the node ID and owner type ('org' or 'user') of a Projects v2 project.

        Returns (project_node_id, owner_type).
        """
        query = """
        query($owner: String!, $number: Int!) {
          organization(login: $owner) {
            projectV2(number: $number) { id }
          }
        }
        """
        try:
            data = await self._graphql(query, {"owner": self.owner, "number": project_number})
            project_id = data["organization"]["projectV2"]["id"]
            return project_id, "org"
        except (GitHubAPIError, KeyError, TypeError):
            pass

        query_user = """
        query($owner: String!, $number: Int!) {
          user(login: $owner) {
            projectV2(number: $number) { id }
          }
        }
        """
        data = await self._graphql(query_user, {"owner": self.owner, "number": project_number})
        project_id = data["user"]["projectV2"]["id"]
        return project_id, "user"

    async def get_project_iteration_field(
        self, project_id: str
    ) -> tuple[str, list[dict]]:
        """Get the iteration field ID and available iterations for a project.

        Returns (field_id, [{"id": ..., "title": ..., "startDate": ...}]).
        """
        query = """
        query($projectId: ID!) {
          node(id: $projectId) {
            ... on ProjectV2 {
              fields(first: 20) {
                nodes {
                  ... on ProjectV2IterationField {
                    id
                    name
                    configuration {
                      iterations { id title startDate }
                    }
                  }
                }
              }
            }
          }
        }
        """
        data = await self._graphql(query, {"projectId": project_id})
        fields = data.get("node", {}).get("fields", {}).get("nodes", [])
        for field in fields:
            if field and "configuration" in field:
                iterations = field["configuration"].get("iterations", [])
                return field["id"], iterations
        return "", []

    async def add_issue_to_project(self, project_id: str, issue_node_id: str) -> str:
        """Add an issue to a Projects v2 project. Returns the project item ID."""
        mutation = """
        mutation($projectId: ID!, $contentId: ID!) {
          addProjectV2ItemById(input: {projectId: $projectId, contentId: $contentId}) {
            item { id }
          }
        }
        """
        data = await self._graphql(
            mutation, {"projectId": project_id, "contentId": issue_node_id}
        )
        return data["addProjectV2ItemById"]["item"]["id"]

    async def set_project_item_iteration(
        self, project_id: str, item_id: str, field_id: str, iteration_id: str
    ) -> None:
        """Set the iteration field on a project item."""
        mutation = """
        mutation($projectId: ID!, $itemId: ID!, $fieldId: ID!, $iterationId: String!) {
          updateProjectV2ItemFieldValue(input: {
            projectId: $projectId,
            itemId: $itemId,
            fieldId: $fieldId,
            value: { iterationId: $iterationId }
          }) {
            projectV2Item { id }
          }
        }
        """
        await self._graphql(
            mutation,
            {
                "projectId": project_id,
                "itemId": item_id,
                "fieldId": field_id,
                "iterationId": iteration_id,
            },
        )

    async def get_project_items(self, project_id: str) -> list[dict]:
        """Fetch all items in a Projects v2 project with issue details."""
        query = """
        query($projectId: ID!, $cursor: String) {
          node(id: $projectId) {
            ... on ProjectV2 {
              items(first: 100, after: $cursor) {
                pageInfo { hasNextPage endCursor }
                nodes {
                  id
                  content {
                    ... on Issue {
                      number title state
                      assignees(first: 5) { nodes { login } }
                      parent { number }
                    }
                  }
                  fieldValues(first: 10) {
                    nodes {
                      ... on ProjectV2ItemFieldIterationValue {
                        iterationId title
                        field { ... on ProjectV2IterationField { name } }
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """
        all_items: list[dict] = []
        cursor = None
        while True:
            data = await self._graphql(query, {"projectId": project_id, "cursor": cursor})
            page = data.get("node", {}).get("items", {})
            nodes = page.get("nodes", [])
            all_items.extend(n for n in nodes if n and n.get("content"))
            page_info = page.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info["endCursor"]
        return all_items
```

- [ ] **Step 4: Run tests — verify they pass**

```bash
cd github-sprint-planner && uv run pytest tests/test_github_client.py -v
```

Expected: 6 tests pass.

---

## Task 4: Parsers + action log

**Files:**
- Create: `github-sprint-planner/server/action_log.py`
- Create: `github-sprint-planner/server/parsers/base.py`
- Create: `github-sprint-planner/server/parsers/html_parser.py`
- Create: `github-sprint-planner/server/parsers/markdown_parser.py`

> These are adapted from `clickup-sprint-planner/server/`. Key changes:
> - `Story.clickup_id: str | None` → `Story.issue_number: int | None`
> - `write_clickup_id` → `write_issue_number`
> - HTML badge selector: `a.badge-clickup` → `a.badge-github`
> - Badge class exclusion: `badge-clickup` → `badge-github`

- [ ] **Step 1: Create action_log.py**

Copy `clickup-sprint-planner/server/action_log.py` verbatim — no changes needed.

Create `github-sprint-planner/server/action_log.py` with identical content:
```python
"""Append-only JSON action log for audit and undo support."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ActionLog:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._ensure_file()

    def _ensure_file(self):
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"metadata": {}, "actions": []}, indent=2))

    def _read(self) -> dict:
        return json.loads(self.path.read_text())

    def _write(self, data: dict):
        self.path.write_text(json.dumps(data, indent=2, default=str))

    def _next_seq(self, data: dict) -> int:
        actions = data.get("actions", [])
        if not actions:
            return 1
        return max(a.get("seq", 0) for a in actions) + 1

    def log_action(
        self,
        action: str,
        status: str,
        summary: str,
        results: list[dict] | None = None,
        undo: dict | None = None,
        **extra: Any,
    ) -> dict:
        data = self._read()
        entry = {
            "seq": self._next_seq(data),
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "summary": summary,
        }
        if results is not None:
            entry["results"] = results
        if undo is not None:
            entry["undo"] = undo
        entry.update(extra)
        data["actions"].append(entry)
        self._write(data)
        return entry

    def get_actions(
        self,
        *,
        epic: str | None = None,
        action: str | None = None,
        since: str | None = None,
        last_n: int | None = None,
    ) -> list[dict]:
        data = self._read()
        actions = data.get("actions", [])
        if epic:
            actions = [a for a in actions if a.get("epic") == epic]
        if action:
            actions = [a for a in actions if a.get("action") == action]
        if since:
            actions = [a for a in actions if a.get("timestamp", "") >= since]
        if last_n:
            actions = actions[-last_n:]
        return actions
```

- [ ] **Step 2: Create parsers/base.py**

Create `github-sprint-planner/server/parsers/base.py`:
```python
"""Story data model and abstract parser interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Story:
    """A single user story extracted from a plan document."""

    index: int
    name: str
    description: str = ""
    issue_number: int | None = None
    status: str | None = None
    assignee: str | None = None
    tasks: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "name": self.name,
            "description": self.description,
            "issue_number": self.issue_number,
            "status": self.status,
            "assignee": self.assignee,
            "tasks": self.tasks,
            "acceptance_criteria": self.acceptance_criteria,
        }


class PlanParser(ABC):
    @abstractmethod
    def extract_stories(self, file_path: str | Path, extraction_config: dict) -> list[Story]:
        """Extract stories from a plan document."""

    @abstractmethod
    def write_issue_number(self, file_path: str | Path, story_index: int, issue_number: int, issue_url: str) -> None:
        """Write a GitHub issue number back into the plan doc after creation."""


def get_parser(format: str) -> PlanParser:
    if format == "html":
        from server.parsers.html_parser import HtmlPlanParser
        return HtmlPlanParser()
    elif format == "markdown":
        from server.parsers.markdown_parser import MarkdownPlanParser
        return MarkdownPlanParser()
    else:
        raise ValueError(f"Unknown plan doc format: {format!r}. Supported: html, markdown")
```

- [ ] **Step 3: Create parsers/html_parser.py**

Create `github-sprint-planner/server/parsers/html_parser.py`:
```python
"""HTML plan document parser using BeautifulSoup."""

from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from server.parsers.base import PlanParser, Story


class HtmlPlanParser(PlanParser):
    def extract_stories(self, file_path: str | Path, extraction_config: dict) -> list[Story]:
        file_path = Path(file_path)
        html = file_path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")

        story_selector = extraction_config.get("story_selector", "div.story[id^='story-']")
        name_pattern = extraction_config.get("name_pattern", r"Story \d+: (.+)")
        issue_selector = extraction_config.get("issue_selector", "a.badge-github")

        stories: list[Story] = []

        for story_div in soup.select(story_selector):
            if not isinstance(story_div, Tag):
                continue

            story_id_attr = story_div.get("id", "")
            index_match = re.search(r"story-(\d+)", str(story_id_attr))
            index = int(index_match.group(1)) if index_match else len(stories) + 1

            h3 = story_div.select_one(".story-header h3") or story_div.select_one("h3")
            raw_name = h3.get_text(strip=True) if h3 else f"Story {index}"
            name_match = re.search(name_pattern, raw_name)
            name = name_match.group(1) if name_match else raw_name

            issue_link = story_div.select_one(issue_selector)
            issue_number: int | None = None
            if issue_link:
                try:
                    issue_number = int(issue_link.get_text(strip=True).lstrip("#"))
                except ValueError:
                    issue_number = None

            status = self._extract_status(story_div)

            desc_div = story_div.select_one(".story-description")
            description = desc_div.get_text(strip=True) if desc_div else ""

            tasks: list[str] = []
            checklist = story_div.select_one("ul.checklist")
            if checklist:
                tasks = [li.get_text(strip=True) for li in checklist.find_all("li")]

            acceptance: list[str] = []
            acc_div = story_div.select_one(".acceptance")
            if acc_div:
                acceptance = [li.get_text(strip=True) for li in acc_div.find_all("li")]

            stories.append(
                Story(
                    index=index,
                    name=name,
                    description=description,
                    issue_number=issue_number,
                    status=status,
                    tasks=tasks,
                    acceptance_criteria=acceptance,
                )
            )

        return stories

    def write_issue_number(
        self, file_path: str | Path, story_index: int, issue_number: int, issue_url: str
    ) -> None:
        file_path = Path(file_path)
        html = file_path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")

        story_div = soup.select_one(f"div.story#story-{story_index}")
        if not story_div:
            raise ValueError(f"Story {story_index} not found in {file_path}")

        to_create_badge = story_div.select_one(".badge-to-create")
        if to_create_badge:
            new_tag = soup.new_tag(
                "a",
                attrs={
                    "class": "badge badge-github",
                    "href": issue_url,
                    "target": "_blank",
                },
            )
            new_tag.string = f"#{issue_number}"
            to_create_badge.replace_with(new_tag)
            file_path.write_text(str(soup), encoding="utf-8")

    def _extract_status(self, story_div: Tag) -> str | None:
        header = story_div.select_one(".story-header")
        if not header:
            return None
        for badge in header.select(".badge"):
            classes = badge.get("class", [])
            if "badge-github" in classes or "badge-to-create" in classes:
                continue
            text = badge.get_text(strip=True).lower()
            if text:
                return text.replace(" ", "_")
        return None
```

- [ ] **Step 4: Create parsers/markdown_parser.py**

Create `github-sprint-planner/server/parsers/markdown_parser.py`:
```python
"""Markdown plan document parser — stub."""

from __future__ import annotations

from pathlib import Path

from server.parsers.base import PlanParser, Story


class MarkdownPlanParser(PlanParser):
    def extract_stories(self, file_path: str | Path, extraction_config: dict) -> list[Story]:
        raise NotImplementedError(
            "Markdown parser is not yet implemented. Use HTML format plan docs."
        )

    def write_issue_number(self, file_path: str | Path, story_index: int, issue_number: int, issue_url: str) -> None:
        raise NotImplementedError("Markdown parser is not yet implemented.")
```

- [ ] **Step 5: Smoke-test parsers**

```bash
cd github-sprint-planner && uv run python -c "
from server.parsers.base import get_parser, Story
p = get_parser('html')
print('Parser loaded:', type(p).__name__)
s = Story(index=1, name='Test')
print('Story:', s.to_dict())
"
```

Expected:
```
Parser loaded: HtmlPlanParser
Story: {'index': 1, 'name': 'Test', 'description': '', 'issue_number': None, ...}
```

---

## Task 5: Tool — `sprint_status`

**Files:**
- Create: `github-sprint-planner/server/tools/_helpers.py`
- Create: `github-sprint-planner/server/tools/sprint_status.py`

- [ ] **Step 1: Create _helpers.py**

Create `github-sprint-planner/server/tools/_helpers.py`:
```python
"""Shared helpers for github-sprint-planner MCP tools."""

from __future__ import annotations


def normalize_status(state: str, labels: list[str]) -> str:
    """Map GitHub issue state + labels to a sprint status category."""
    if state == "closed":
        return "done"
    label_lower = [l.lower() for l in labels]
    if any(l in label_lower for l in ("in progress", "in-progress", "in dev", "in-dev")):
        return "in_progress"
    if any(l in label_lower for l in ("blocked",)):
        return "blocked"
    return "ready"
```

- [ ] **Step 2: Create tools/sprint_status.py**

Create `github-sprint-planner/server/tools/sprint_status.py`:
```python
"""MCP tool: sprint_status — sprint/epic overview via GitHub sub-issues."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from server.config import SprintPlannerConfig
from server.github_client import GitHubClient, GitHubAPIError
from server.tools._helpers import normalize_status


def _extract_labels(issue: dict) -> list[str]:
    return [lbl.get("name", "") for lbl in issue.get("labels", [])]


def _story_row(issue: dict, team_by_login: dict) -> dict:
    assignees = issue.get("assignees", [])
    assignee_login = assignees[0].get("login") if assignees else None
    assignee_name = team_by_login.get(assignee_login, assignee_login) if assignee_login else None
    labels = _extract_labels(issue)
    return {
        "issue_number": issue["number"],
        "name": issue.get("title", ""),
        "status": normalize_status(issue.get("state", "open"), labels),
        "assignee": assignee_name,
        "url": issue.get("html_url", f"https://github.com/issues/{issue['number']}"),
    }


def _compute_stats(stories: list[dict]) -> dict:
    stats = {"total": len(stories), "done": 0, "in_progress": 0, "ready": 0, "blocked": 0}
    for s in stories:
        cat = s.get("status", "ready")
        if cat in stats:
            stats[cat] += 1
    return stats


def register(mcp: FastMCP, client: GitHubClient, config: SprintPlannerConfig):
    @mcp.tool()
    async def sprint_status(
        epic: str | None = None,
        group_by: str = "epic",
    ) -> dict:
        """Get sprint/epic overview with story states from GitHub Issues.

        Fetches sub-issues of each epic issue and aggregates stats.

        Args:
            epic: Epic ID to filter (e.g. "P1a"). Omit for all epics.
            group_by: Grouping: "epic" (default), "status", or "assignee".
        """
        epics_to_check = config.plan_docs.epics
        if epic:
            epics_to_check = [e for e in epics_to_check if e.id == epic]
            if not epics_to_check:
                available = [e.id for e in config.plan_docs.epics]
                return {"error": f"Epic {epic!r} not found. Available: {available}"}

        team_by_login = {m.github_login: m.name for m in config.team}

        if group_by == "epic":
            result_epics = []
            for epic_cfg in epics_to_check:
                try:
                    issues = await client.get_sub_issues(epic_cfg.epic_issue_number)
                except GitHubAPIError as e:
                    result_epics.append({
                        "id": epic_cfg.id,
                        "name": epic_cfg.name,
                        "error": str(e),
                    })
                    continue
                stories = [_story_row(i, team_by_login) for i in issues]
                result_epics.append({
                    "id": epic_cfg.id,
                    "name": epic_cfg.name,
                    "epic_issue_number": epic_cfg.epic_issue_number,
                    "stats": _compute_stats(stories),
                    "stories": stories,
                })
            return {"epics": result_epics}

        # Collect all sub-issues across epics for status/assignee grouping
        all_stories: list[dict] = []
        for epic_cfg in epics_to_check:
            try:
                issues = await client.get_sub_issues(epic_cfg.epic_issue_number)
                all_stories.extend(_story_row(i, team_by_login) for i in issues)
            except GitHubAPIError:
                continue

        if group_by == "status":
            groups: dict[str, list] = {"done": [], "in_progress": [], "ready": [], "blocked": []}
            for s in all_stories:
                cat = s.get("status", "ready")
                groups.setdefault(cat, []).append(s)
            return {"groups": {k: {"count": len(v), "stories": v} for k, v in groups.items()}}

        if group_by == "assignee":
            groups = {}
            for s in all_stories:
                key = s.get("assignee") or "Unassigned"
                groups.setdefault(key, []).append(s)
            return {
                "groups": {
                    k: {"count": len(v), "stats": _compute_stats(v), "stories": v}
                    for k, v in groups.items()
                }
            }

        return {"error": f"Invalid group_by: {group_by!r}. Use 'epic', 'status', or 'assignee'."}
```

- [ ] **Step 3: Smoke-test import**

```bash
cd github-sprint-planner && uv run python -c "
from server.tools.sprint_status import register
from server.tools._helpers import normalize_status
print(normalize_status('open', ['in-progress']))   # in_progress
print(normalize_status('closed', []))              # done
print(normalize_status('open', []))                # ready
"
```

Expected:
```
in_progress
done
ready
```

---

## Task 6: Tool — `sprint_bulk_update`

**Files:**
- Create: `github-sprint-planner/server/tools/bulk_update.py`

- [ ] **Step 1: Create tools/bulk_update.py**

Create `github-sprint-planner/server/tools/bulk_update.py`:
```python
"""MCP tool: sprint_bulk_update — batch issue updates."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.github_client import GitHubClient, GitHubAPIError


def register(mcp: FastMCP, client: GitHubClient, action_log: ActionLog):
    @mcp.tool()
    async def sprint_bulk_update(
        updates: list[dict],
    ) -> dict:
        """Batch update assignee, labels, or state across multiple GitHub issues.

        Each update dict should have:
          - issue_number (required): The issue to update
          - assignees: List of GitHub logins to assign
          - labels: List of label names to set
          - state: "open" or "closed"
          - title: New issue title
          - body: New issue body (markdown)

        Args:
            updates: Array of update objects with issue_number and fields to change.
        """
        updated = []
        failed = []

        for update in updates:
            issue_number = update.get("issue_number")
            if not issue_number:
                failed.append({"error": "Missing issue_number", "update": update})
                continue

            payload: dict = {}
            changes = []

            if "assignees" in update:
                payload["assignees"] = update["assignees"]
                changes.append("assignees")
            if "labels" in update:
                payload["labels"] = update["labels"]
                changes.append("labels")
            if "state" in update:
                payload["state"] = update["state"]
                changes.append("state")
            if "title" in update:
                payload["title"] = update["title"]
                changes.append("title")
            if "body" in update:
                payload["body"] = update["body"]
                changes.append("body")

            if not payload:
                failed.append({"issue_number": issue_number, "error": "No fields to update"})
                continue

            try:
                await client.update_issue(issue_number, payload)
                updated.append({
                    "issue_number": issue_number,
                    "status": "success",
                    "changes": changes,
                })
            except GitHubAPIError as e:
                failed.append({
                    "issue_number": issue_number,
                    "status": "failed",
                    "error": str(e),
                })

        log_warning = None
        try:
            action_log.log_action(
                action="bulk_update",
                status="success" if not failed else "partial",
                summary=f"Updated {len(updated)}/{len(updates)} issues",
                results=updated + failed,
            )
        except Exception as e:
            log_warning = f"Action logging failed: {e}"

        result = {"updated": updated, "failed": failed}
        if log_warning:
            result["log_warning"] = log_warning
        return result
```

- [ ] **Step 2: Smoke-test import**

```bash
cd github-sprint-planner && uv run python -c "from server.tools.bulk_update import register; print('OK')"
```

Expected: `OK`

---

## Task 7: Tool — `sprint_bulk_create`

**Files:**
- Create: `github-sprint-planner/server/tools/bulk_create.py`

- [ ] **Step 1: Create tools/bulk_create.py**

Create `github-sprint-planner/server/tools/bulk_create.py`:
```python
"""MCP tool: sprint_bulk_create — batch issue creation with sub-issue + project linking."""

from __future__ import annotations

import re

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.config import SprintPlannerConfig
from server.github_client import GitHubClient, GitHubAPIError

_EPIC_PREFIX_RE = re.compile(r"^[A-Z]\d+[a-z]?\s*[-–]\s*")
_REQUIRED_SECTIONS = ["Summary", "Tasks", "Context", "Acceptance Criteria"]


def _auto_format_title(story: dict) -> str:
    name = story["name"]
    epic_id = story.get("epic_id")
    if epic_id and not _EPIC_PREFIX_RE.match(name):
        return f"{epic_id} - {name}"
    return name


def _check_description_sections(description: str | None) -> list[str]:
    if not description:
        return list(_REQUIRED_SECTIONS)
    desc_lower = description.lower()
    return [s for s in _REQUIRED_SECTIONS if s.lower() not in desc_lower]


def register(
    mcp: FastMCP,
    client: GitHubClient,
    action_log: ActionLog,
    config: SprintPlannerConfig,
):
    @mcp.tool()
    async def sprint_bulk_create(
        epic_issue_number: int,
        stories: list[dict],
        add_to_project: bool = True,
        iteration_id: str | None = None,
    ) -> dict:
        """Create multiple GitHub issues and link them as sub-issues of an epic.

        Each story dict should have:
          - name (required): Issue title
          - body: Issue body (markdown with Summary, Tasks, Context, AC sections)
          - assignees: List of GitHub logins
          - labels: List of label names
          - epic_id: Epic prefix for auto-formatting name (e.g. "P1a")

        Args:
            epic_issue_number: Parent epic issue number to link stories under.
            stories: Array of story objects to create.
            add_to_project: If true, add each issue to the configured project.
            iteration_id: Projects v2 iteration ID to assign. Requires add_to_project=True.
        """
        created = []
        failed = []
        format_warnings = []

        # Resolve project ID once if needed
        project_id: str | None = None
        iteration_field_id: str | None = None
        if add_to_project:
            try:
                project_id, _ = await client.get_project_id(config.github.project_number)
                if iteration_id:
                    iteration_field_id, _ = await client.get_project_iteration_field(project_id)
            except GitHubAPIError as e:
                return {"error": f"Failed to resolve project: {e}"}

        for story in stories:
            title = _auto_format_title(story)
            body = story.get("body", "")

            missing = _check_description_sections(body)
            if missing:
                format_warnings.append({"name": title, "missing_sections": missing})

            assignees = story.get("assignees", [])
            labels = story.get("labels", [])

            try:
                issue = await client.create_issue(title, body=body, assignees=assignees, labels=labels)
                issue_number = issue["number"]
                issue_url = issue.get("html_url", f"https://github.com/{client.owner}/{client.repo}/issues/{issue_number}")
                issue_node_id = issue.get("node_id", "")

                # Link as sub-issue of epic
                try:
                    await client.add_sub_issue(epic_issue_number, issue_number)
                    linked = True
                except GitHubAPIError as e:
                    linked = False
                    format_warnings.append({"name": title, "sub_issue_error": str(e)})

                # Add to project + set iteration
                project_item_id: str | None = None
                if add_to_project and project_id and issue_node_id:
                    try:
                        project_item_id = await client.add_issue_to_project(project_id, issue_node_id)
                        if iteration_id and iteration_field_id and project_item_id:
                            await client.set_project_item_iteration(
                                project_id, project_item_id, iteration_field_id, iteration_id
                            )
                    except GitHubAPIError as e:
                        format_warnings.append({"name": title, "project_error": str(e)})

                created.append({
                    "issue_number": issue_number,
                    "issue_url": issue_url,
                    "name": title,
                    "linked_to_epic": linked,
                    "added_to_project": project_item_id is not None,
                    "status": "success",
                })

            except GitHubAPIError as e:
                failed.append({"name": title, "status": "failed", "error": str(e)})

        log_warning = None
        try:
            action_log.log_action(
                action="bulk_create",
                status="success" if not failed else "partial",
                summary=f"Created {len(created)}/{len(stories)} issues under epic #{epic_issue_number}",
                results=created + failed,
                undo={
                    "type": "close_issues",
                    "issue_numbers": [c["issue_number"] for c in created],
                },
            )
        except Exception as e:
            log_warning = f"Action logging failed: {e}"

        result = {"created": created, "failed": failed}
        if format_warnings:
            result["format_warnings"] = format_warnings
        if log_warning:
            result["log_warning"] = log_warning
        return result
```

- [ ] **Step 2: Smoke-test import**

```bash
cd github-sprint-planner && uv run python -c "from server.tools.bulk_create import register; print('OK')"
```

Expected: `OK`

---

## Task 8: Tool — `sprint_sync`

**Files:**
- Create: `github-sprint-planner/server/tools/sync.py`
- Create: `github-sprint-planner/tests/test_sync.py`

- [ ] **Step 1: Write failing tests for sync diff logic**

Create `github-sprint-planner/tests/test_sync.py`:
```python
import pytest
from server.parsers.base import Story
from server.tools.sync import _fuzzy_match, _determine_diff, FUZZY_THRESHOLD


def make_issue(number: int, title: str, state: str = "open") -> dict:
    return {"number": number, "title": title, "state": state, "assignees": [], "labels": []}


def test_fuzzy_match_exact():
    stories = [make_issue(10, "P1 - Create VPC")]
    match, ratio = _fuzzy_match("Create VPC", stories)
    assert match is not None
    assert match["number"] == 10
    assert ratio >= FUZZY_THRESHOLD


def test_fuzzy_match_no_match():
    stories = [make_issue(10, "P1 - Completely Different Thing")]
    match, ratio = _fuzzy_match("Create VPC", stories)
    assert match is None


def test_determine_diff_no_task():
    story = Story(index=1, name="Create VPC")
    result = _determine_diff(story, None)
    assert result == "to_create"


def test_determine_diff_match():
    story = Story(index=1, name="Create VPC")
    issue = make_issue(10, "P1 - Create VPC")
    result = _determine_diff(story, issue)
    assert result == "match"


def test_determine_diff_to_update():
    story = Story(index=1, name="Create VPC with Subnets")
    issue = make_issue(10, "P1 - Something Completely Different")
    result = _determine_diff(story, issue)
    assert result == "to_update"


def test_fuzzy_match_strips_prefix():
    stories = [make_issue(10, "[P1] Create VPC")]
    match, ratio = _fuzzy_match("Create VPC", stories)
    assert match is not None
    assert ratio >= FUZZY_THRESHOLD
```

- [ ] **Step 2: Run tests — verify they fail**

```bash
cd github-sprint-planner && uv run pytest tests/test_sync.py -v
```

Expected: `ImportError: cannot import name '_fuzzy_match' from 'server.tools.sync'`

- [ ] **Step 3: Create tools/sync.py**

Create `github-sprint-planner/server/tools/sync.py`:
```python
"""MCP tool: sprint_sync — diff plan documents against GitHub Issues."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.config import SprintPlannerConfig
from server.github_client import GitHubClient, GitHubAPIError
from server.parsers.base import Story, get_parser

FUZZY_THRESHOLD = 0.8
FUZZY_LINK_THRESHOLD = 0.6

_EPIC_PREFIX_RE = re.compile(r"^(?:\[[^\]]+\]\s*)?[A-Z]\d+[a-z]?\s*[-–]\s*")


def _strip_prefix(title: str) -> str:
    """Strip epic prefix like 'P1 - ' or '[Project] P1a - ' from a title."""
    if ": " in title:
        return title.split(": ", 1)[-1]
    return _EPIC_PREFIX_RE.sub("", title)


def _fuzzy_match(name: str, candidates: list[dict]) -> tuple[dict | None, float]:
    """Find the best fuzzy match for a story name among GitHub issues."""
    best_match = None
    best_ratio = 0.0
    name_lower = name.lower().strip()
    for issue in candidates:
        clean = _strip_prefix(issue.get("title", ""))
        ratio = SequenceMatcher(None, name_lower, clean.lower().strip()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = issue
    if best_ratio >= FUZZY_LINK_THRESHOLD:
        return best_match, best_ratio
    return None, best_ratio


def _determine_diff(story: Story, issue: dict | None) -> str:
    if issue is None:
        return "to_create"
    clean = _strip_prefix(issue.get("title", ""))
    ratio = SequenceMatcher(None, story.name.lower(), clean.lower()).ratio()
    return "match" if ratio >= 0.8 else "to_update"


def register(
    mcp: FastMCP,
    client: GitHubClient,
    config: SprintPlannerConfig,
    base_path: Path,
    action_log: ActionLog | None = None,
):
    @mcp.tool()
    async def sprint_sync(
        epic: str | None = None,
        apply_links: bool = False,
    ) -> dict:
        """Diff plan documents against GitHub Issues.

        Matches stories to sub-issues of each epic. Stories with no linked issue
        but a fuzzy-matched GitHub issue are flagged as "to_link".

        When apply_links=True, auto-links unlinked issues to their epic via sub-issues API.

        Args:
            epic: Epic ID to sync (e.g. "P1a"). If omitted, syncs all epics.
            apply_links: If true, add "to_link" issues as sub-issues of the epic.
        """
        epics_to_sync = config.plan_docs.epics
        if epic:
            epics_to_sync = [e for e in epics_to_sync if e.id == epic]
            if not epics_to_sync:
                available = [e.id for e in config.plan_docs.epics]
                return {"error": f"Epic {epic!r} not found. Available: {available}"}

        parser = get_parser(config.plan_docs.format)
        extraction_config = config.story_extraction.html.model_dump()

        # Fetch all open repo issues for fuzzy matching unlinked ones
        try:
            all_repo_issues = await client.get_repo_issues(state="all")
        except GitHubAPIError as e:
            return {"error": f"Failed to fetch GitHub issues: {e}"}

        results = []
        link_operations = []

        for epic_cfg in epics_to_sync:
            plan_doc_path = base_path / epic_cfg.plan_doc
            if not plan_doc_path.exists():
                results.append({
                    "epic": epic_cfg.id,
                    "name": epic_cfg.name,
                    "error": f"Plan doc not found: {plan_doc_path}",
                })
                continue

            try:
                stories = parser.extract_stories(plan_doc_path, extraction_config)
            except Exception as e:
                results.append({
                    "epic": epic_cfg.id,
                    "name": epic_cfg.name,
                    "error": f"Failed to parse plan doc: {e}",
                })
                continue

            # Sub-issues already linked to this epic
            try:
                sub_issues = await client.get_sub_issues(epic_cfg.epic_issue_number)
            except GitHubAPIError as e:
                results.append({
                    "epic": epic_cfg.id,
                    "name": epic_cfg.name,
                    "error": f"Failed to fetch sub-issues: {e}",
                })
                continue

            sub_issue_numbers = {i["number"] for i in sub_issues}
            matched_numbers: set[int] = set()
            story_results = []

            for story in stories:
                # 1. Exact match by issue_number in plan doc
                if story.issue_number:
                    issue = next(
                        (i for i in all_repo_issues if i["number"] == story.issue_number), None
                    )
                    if issue:
                        matched_numbers.add(issue["number"])
                        diff = _determine_diff(story, issue)
                        story_results.append({
                            "index": story.index,
                            "name": story.name,
                            "plan_status": story.status,
                            "issue_number": story.issue_number,
                            "github_state": issue.get("state"),
                            "github_title": issue.get("title"),
                            "diff": diff,
                        })
                        continue

                # 2. Fuzzy match against linked sub-issues
                unmatched_sub = [i for i in sub_issues if i["number"] not in matched_numbers]
                match, ratio = _fuzzy_match(story.name, unmatched_sub)
                if match and ratio >= FUZZY_THRESHOLD:
                    matched_numbers.add(match["number"])
                    diff = _determine_diff(story, match)
                    story_results.append({
                        "index": story.index,
                        "name": story.name,
                        "plan_status": story.status,
                        "issue_number": match["number"],
                        "github_state": match.get("state"),
                        "github_title": match.get("title"),
                        "diff": diff,
                    })
                    continue

                # 3. Fuzzy match against unlinked repo issues
                unlinked = [
                    i for i in all_repo_issues
                    if i["number"] not in sub_issue_numbers
                    and i["number"] not in matched_numbers
                ]
                match, ratio = _fuzzy_match(story.name, unlinked)
                if match and ratio >= FUZZY_LINK_THRESHOLD:
                    matched_numbers.add(match["number"])
                    story_results.append({
                        "index": story.index,
                        "name": story.name,
                        "plan_status": story.status,
                        "issue_number": None,
                        "diff": "to_link",
                        "candidate": {
                            "issue_number": match["number"],
                            "github_title": match.get("title"),
                            "github_state": match.get("state"),
                            "fuzzy_ratio": round(ratio, 3),
                        },
                    })
                    link_operations.append({
                        "issue_number": match["number"],
                        "epic_issue_number": epic_cfg.epic_issue_number,
                        "epic_label": epic_cfg.id,
                        "story_name": story.name,
                    })
                else:
                    # 4. No match — needs creating
                    story_results.append({
                        "index": story.index,
                        "name": story.name,
                        "plan_status": story.status,
                        "issue_number": None,
                        "diff": "to_create",
                    })

            orphaned_count = sum(1 for i in sub_issues if i["number"] not in matched_numbers)

            summary = {
                "match": sum(1 for s in story_results if s["diff"] == "match"),
                "to_create": sum(1 for s in story_results if s["diff"] == "to_create"),
                "to_update": sum(1 for s in story_results if s["diff"] == "to_update"),
                "to_link": sum(1 for s in story_results if s["diff"] == "to_link"),
                "orphaned": orphaned_count,
            }

            results.append({
                "epic": epic_cfg.id,
                "name": epic_cfg.name,
                "summary": summary,
                "stories": story_results,
            })

        # Apply links if requested
        linked = []
        link_failed = []
        if apply_links and link_operations:
            for op in link_operations:
                try:
                    await client.add_sub_issue(op["epic_issue_number"], op["issue_number"])
                    linked.append({
                        "issue_number": op["issue_number"],
                        "epic_issue_number": op["epic_issue_number"],
                        "epic_label": op["epic_label"],
                        "story_name": op["story_name"],
                        "status": "success",
                    })
                except GitHubAPIError as e:
                    link_failed.append({
                        "issue_number": op["issue_number"],
                        "story_name": op["story_name"],
                        "status": "failed",
                        "error": str(e),
                    })

            if action_log and (linked or link_failed):
                try:
                    action_log.log_action(
                        action="sync_auto_link",
                        status="success" if not link_failed else "partial",
                        summary=f"Auto-linked {len(linked)}/{len(link_operations)} issues to epics",
                        results=linked + link_failed,
                    )
                except Exception:
                    pass

        output = results[0] if len(results) == 1 else {"epics": results}
        if apply_links and link_operations:
            output["link_results"] = {"linked": linked, "failed": link_failed}
        return output
```

- [ ] **Step 4: Run sync tests — verify they pass**

```bash
cd github-sprint-planner && uv run pytest tests/test_sync.py -v
```

Expected: 6 tests pass.

---

## Task 9: Action log tool + main.py

**Files:**
- Create: `github-sprint-planner/server/tools/action_log_tool.py`
- Create: `github-sprint-planner/server/main.py`

- [ ] **Step 1: Create action_log_tool.py**

Create `github-sprint-planner/server/tools/action_log_tool.py`:
```python
"""MCP tool: sprint_action_log — query the action log."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog


def register(mcp: FastMCP, action_log: ActionLog):
    @mcp.tool()
    async def sprint_action_log(
        epic: str | None = None,
        action: str | None = None,
        since: str | None = None,
        last_n: int | None = None,
    ) -> dict:
        """Query the action log for past sprint planning operations.

        Args:
            epic: Filter by epic ID (e.g. "P1a").
            action: Filter by action type (e.g. "bulk_create").
            since: ISO date string — only return entries after this timestamp.
            last_n: Return only the last N entries (after other filters).
        """
        actions = action_log.get_actions(
            epic=epic, action=action, since=since, last_n=last_n
        )
        return {"actions": actions, "total": len(actions)}
```

- [ ] **Step 2: Create main.py**

Create `github-sprint-planner/server/main.py`:
```python
"""github-sprint-planner MCP server entry point."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.config import load_config, get_github_token
from server.github_client import GitHubClient
from server.tools import (
    sync,
    bulk_create,
    bulk_update,
    sprint_status,
    action_log_tool,
)

mcp = FastMCP(
    "github-sprint-planner",
    instructions="Sprint planning tools for GitHub Issues + Projects v2 — bulk operations, sub-issue linking, plan doc sync.",
)


def _resolve_relative(path_str: str, config_path: Path) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (config_path.parent / p).resolve()


def _register_tools():
    import os

    config_path = Path(
        os.environ.get("SPRINT_PLANNER_CONFIG", "./sprint-planner.json")
    ).resolve()
    config = load_config(config_path)
    token = get_github_token(config)
    client = GitHubClient(token, config.github.owner, config.github.repo)

    log_path = _resolve_relative(config.action_log.path, config_path)
    base_path = _resolve_relative(config.plan_docs.base_path, config_path)
    action_log = ActionLog(log_path)

    sync.register(mcp, client, config, base_path, action_log)
    bulk_create.register(mcp, client, action_log, config)
    bulk_update.register(mcp, client, action_log)
    sprint_status.register(mcp, client, config)
    action_log_tool.register(mcp, action_log)


_register_tools()

if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 3: Run all tests**

```bash
cd github-sprint-planner && uv run pytest tests/ -v
```

Expected: All tests pass (config + client + sync tests).

---

## Task 10: Commands + skills

**Files:**
- Create: `github-sprint-planner/commands/sprint-sync.md`
- Create: `github-sprint-planner/commands/sprint-plan.md`
- Create: `github-sprint-planner/commands/sprint-status.md`
- Create: `github-sprint-planner/skills/sprint-planning/SKILL.md`
- Create: `github-sprint-planner/skills/sprint-planning/card-format.md`

- [ ] **Step 1: Create commands/sprint-sync.md**

Create `github-sprint-planner/commands/sprint-sync.md`:
```markdown
---
name: sprint-sync
description: Sync plan documents against GitHub Issues state, showing diffs and optionally creating/linking issues.
user_invocable: true
---

# /sprint-sync [epic]

Sync plan documents against GitHub Issues, then optionally apply changes.

**IMPORTANT:** Always use `sprint_*` tools — never create GitHub issues manually outside these tools, as they bypass action logging and sub-issue linking.

## Steps

1. Load `sprint-planner.json` config
2. Call `sprint_sync` for the specified epic (or all epics if none given)
3. Present the diff as a table:

```
┌──────────┬─────────────────────────────────────────┬──────────┐
│ Status   │ Story                                   │ Action   │
├──────────┼─────────────────────────────────────────┼──────────┤
│ ✅ match  │ S1: Create new ECS infrastructure       │ none     │
│ ⚠️ diff   │ S3: Create new ALB — title diverged     │ update   │
│ 🔗 link   │ S4: Set up monitoring — unlinked issue  │ link     │
│ 🆕 new    │ S6: Configure CloudWatch alarms         │ create   │
└──────────┴─────────────────────────────────────────┴──────────┘
```

4. Ask the user: **apply all** / **pick which** / **cancel**
5. For "to_create" stories: call `sprint_bulk_create` with the epic issue number
6. For "to_update" stories: call `sprint_bulk_update` with the relevant changes
7. For "to_link" stories:
   - Show candidates with match confidence
   - If user approves: call `sprint_sync(apply_links=true)`
8. Show results + any failures

## Arguments

- `epic` (optional): Epic ID like "P1a", "P2". Omit for all epics.

## Examples

```
/sprint-sync P1a       # Sync epic P1a only
/sprint-sync            # Sync all epics
```
```

- [ ] **Step 2: Create commands/sprint-plan.md**

Create `github-sprint-planner/commands/sprint-plan.md`:
```markdown
---
name: sprint-plan
description: Interactive sprint planning — assign stories to team members, set labels, and push to GitHub.
user_invocable: true
---

# /sprint-plan

Interactive sprint planning workflow.

## Steps

1. Call `sprint_status` grouped by epic to see the current state
2. Show overview: which epics have stories ready, in progress, done
3. Ask the user: **Which epic/stories to include in the next sprint?**
4. For selected stories, let the user:
   - Assign to team members (show team from config)
   - Set labels (e.g. "in-progress", "high-priority")
   - Set iteration (ask for iteration ID from Projects v2)
5. Apply changes via `sprint_bulk_update`
6. Show confirmation table with all changes applied

## Notes

- Always show current state before asking for changes
- Validate assignee logins against the team list in config
- Group changes by type (assignees, labels, state) in the confirmation
```

- [ ] **Step 3: Create commands/sprint-status.md**

Create `github-sprint-planner/commands/sprint-status.md`:
```markdown
---
name: sprint-status
description: Show sprint/epic status overview from GitHub Issues with story-level detail.
user_invocable: true
---

# /sprint-status [epic] [--by status|assignee]

Show sprint status from GitHub Issues.

## Steps

1. Call `sprint_status` with the requested grouping
2. Render summary table:

```
Epic   │ Total │ Done │ In Progress │ Ready │ Blocked
───────┼───────┼──────┼─────────────┼───────┼────────
P1     │ 12    │ 8    │ 2           │ 2     │ 0
P1a    │ 5     │ 0    │ 2           │ 3     │ 0
```

3. If a specific epic was requested, also show story-level detail:

```
# P1a: ECS VPC Migration (2/5 in progress)

│ Status       │ Story                                  │ Assignee       │
│ 🔵 in progress│ S1: Create new Launch Template         │ alice          │
│ 🔵 in progress│ S2: Create new ALB                     │ bob            │
│ ⚪ ready      │ S3: Migrate ECS services               │ —              │
```

## Arguments

- `epic` (optional): Epic ID like "P1a" for detailed view
- `--by status`: Group by status instead of epic
- `--by assignee`: Group by assignee instead of epic
```

- [ ] **Step 4: Create skills/sprint-planning/SKILL.md**

Create `github-sprint-planner/skills/sprint-planning/SKILL.md`:
```markdown
---
name: sprint-planning
description: Use when the user asks about sprint planning, syncing plan docs to GitHub, managing issues in bulk, or checking sprint status. Triggers on mentions of sprint, sync, stories, GitHub Issues, bulk operations, or epic planning.
---

# Sprint Planning Skill (GitHub)

## Overview

Orchestrate GitHub sprint operations through the github-sprint-planner MCP server — sync plan documents, create story issues in bulk, and track sprint progress.

**Core principle:** Always sync before mutating. Show the user the diff, get confirmation, then execute.

## When to Use

- Syncing plan docs to GitHub Issues (creating/updating stories)
- Bulk operations on GitHub Issues (create, update, assign)
- Sprint status checks and epic progress tracking
- Linking issues as sub-issues of epics

## When NOT to Use

- Individual issue updates — use GitHub UI directly
- Creating plan documents — use `dev-workflow:plan-docs` skill
- ClickUp-based project management — use `clickup-sprint-planner`

## Available Tools

| Tool | Purpose |
|------|---------|
| `sprint_sync` | Diff plan docs against GitHub Issues (read-only) |
| `sprint_bulk_create` | Create multiple issues + link as sub-issues + add to project |
| `sprint_bulk_update` | Batch update assignees/labels/state |
| `sprint_status` | Get epic overview with stats |
| `sprint_action_log` | Query past operations |

## Rules

1. **Sync before mutating.** Always call `sprint_sync` first. Present the diff and get confirmation.
2. **Use bulk operations.** Never create issues one-by-one. Use `sprint_bulk_create`.
3. **Read config, don't hardcode.** All IDs come from `sprint-planner.json`. Never hardcode issue numbers or project IDs.
4. **Confirm before mutating.** Show the user exactly what will happen and ask for confirmation.
5. **Surface errors clearly.** Show which operations succeeded vs failed.
6. **Present results as tables.** After any operation, show issue numbers, titles, URLs, and any failures.

## Workflows

### Creating Stories

```
1. sprint_sync(epic="P1a")            → see what exists vs plan doc
2. Present diff table to user         → match / to_create / to_update / to_link
3. User confirms which to create
4. sprint_bulk_create(epic_issue_number=42, stories=[...], add_to_project=true)
   - Titles auto-formatted as "{epic_id} - {name}" (e.g. "P1a - Create VPC")
   - Include full issue body with all required sections
5. Show results table                 → created issues with numbers and URLs
```

### Updating Stories

```
1. sprint_sync(epic="P1")             → identify stale stories
2. Present diff to user
3. User confirms which to update
4. sprint_bulk_update(updates=[{"issue_number": 99, "title": "...", "body": "..."}])
5. Show results table
```

### Sprint Status Check

```
1. sprint_status(group_by="epic"|"status"|"assignee")
2. Present summary table
3. User drills into specific epic for story-level detail
```

## Card Format

Issue title: `{EpicID} - {StoryName}` (e.g. `P1a - Create new ECS infrastructure`)

Every issue body MUST include: Summary, Tasks checklist, Context/Notes, Acceptance Criteria. See `card-format.md` for full requirements.

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Creating issues one-by-one | Use `sprint_bulk_create` for all stories in one call |
| Not syncing before creating | Always `sprint_sync` first — avoids duplicating existing issues |
| One-line issue bodies | Include all 4 required sections (see `card-format.md`) |
| Hardcoding issue numbers | Read epic_issue_number from `sprint-planner.json` config |
```

- [ ] **Step 5: Create skills/sprint-planning/card-format.md**

Create `github-sprint-planner/skills/sprint-planning/card-format.md`:
```markdown
# Card Content Reference (GitHub Issues)

## Issue Title Convention

```
{EpicID} - {StoryName}
```
Example: `P1a - Create new ECS infrastructure in Production VPC`

## Required Sections

Every issue body MUST include these sections. Never create issues with one-line bodies.

1. **Summary paragraph** — What this story does and why (2-3 sentences)
2. **## Tasks** — Checklist using `- [ ]` markdown. Each task specific enough to execute.
3. **## Context / Notes** — Key decisions, existing resource IDs, dependencies, gotchas.
4. **## Acceptance Criteria** — Verifiable outcomes using `- [ ]` markdown.

## Example Issue Body

```markdown
Create two new private subnets in the default VPC for us-east-1b and us-east-1c.
Associate them with the existing production-private-route-table so they route outbound
traffic through the same NAT Gateway in us-east-1a (Elastic IP 203.0.113.10).

## Tasks
- [ ] Allocate CIDR blocks for new subnets from available ranges in 10.0.0.0/16
- [ ] Create production-private-subnet-b in us-east-1b with MapPublicIpOnLaunch=false
- [ ] Create production-private-subnet-c in us-east-1c with MapPublicIpOnLaunch=false
- [ ] Associate both subnets with production-private-route-table (rtb-0123456789abcdef0)
- [ ] Verify outbound connectivity (curl ifconfig.me should return 203.0.113.10)

## Context / Notes
- Private Subnet (1a): production-private-subnet-a (subnet-0123456789abcdef0) — EXISTS
- NAT Gateway: nat-0123456789abcdef0 — EXISTS
- Route Table: production-private-route-table (rtb-0123456789abcdef0) — EXISTS

## Acceptance Criteria
- [ ] Two new private subnets created (1b, 1c) with MapPublicIpOnLaunch=false
- [ ] Both subnets associated with production-private-route-table
- [ ] Outbound traffic from both subnets egresses via 203.0.113.10
```
```

---

## Task 11: Example config + README

**Files:**
- Create: `github-sprint-planner/examples/sprint-planner.example.json`
- Create: `github-sprint-planner/README.md`

- [ ] **Step 1: Create example config**

Create `github-sprint-planner/examples/sprint-planner.example.json`:
```json
{
  "version": "1",
  "github": {
    "token_env": "GITHUB_TOKEN",
    "owner": "your-org",
    "repo": "your-repo",
    "project_number": 1
  },
  "team": [
    { "name": "Team Member 1", "github_login": "github-username-1" },
    { "name": "Team Member 2", "github_login": "github-username-2" }
  ],
  "plan_docs": {
    "format": "html",
    "base_path": "./epics",
    "epics": [
      {
        "id": "P1",
        "name": "Epic 1 Name",
        "plan_doc": "01-epic-name/detailed-plan.html",
        "epic_issue_number": 42
      }
    ]
  },
  "story_extraction": {
    "html": {
      "story_selector": "div.story[id^='story-']",
      "name_pattern": "Story \\d+: (.+)",
      "issue_selector": "a.badge-github",
      "status_selector": ".badge:not(.badge-github):not(.badge-to-create)"
    }
  },
  "action_log": {
    "path": "./epics/github_actions.json"
  }
}
```

- [ ] **Step 2: Create README.md**

Create `github-sprint-planner/README.md`:
```markdown
# github-sprint-planner

Claude Code plugin for sprint planning with GitHub Issues + Projects v2. Mirrors the `clickup-sprint-planner` workflow with a GitHub backend — bulk operations, sub-issue linking, plan doc sync, and action logging.

## Prerequisites

- **[uv](https://docs.astral.sh/uv/)** — the MCP server runs via `uv run`.
  ```bash
  brew install uv
  ```
- **GitHub token** — Personal Access Token with `repo` and `project` scopes, or `gh auth login`.

## Install

```bash
claude --plugin-dir ./github-sprint-planner
```

## Setup

1. **Set your GitHub token:**
   ```bash
   export GITHUB_TOKEN=ghp_XXXXXXXXX
   # or: gh auth login
   ```

2. **Copy and edit the config:**
   ```bash
   cp examples/sprint-planner.json ./sprint-planner.json
   # Edit with your org, repo, project number, epics, and team
   ```

3. **Set the config path** (or place at `./sprint-planner.json`):
   ```bash
   export SPRINT_PLANNER_CONFIG=/path/to/sprint-planner.json
   ```

## Commands

| Command | Description |
|---------|-------------|
| `/sprint-sync [epic]` | Diff plan docs against GitHub Issues, optionally create/update |
| `/sprint-plan` | Interactive sprint planning — assign, label, push |
| `/sprint-status [epic]` | Epic overview with story-level detail |

## MCP Tools

| Tool | Description |
|------|-------------|
| `sprint_sync` | Read-only diff of plan docs vs GitHub Issues |
| `sprint_bulk_create` | Create multiple issues + link as sub-issues + add to project |
| `sprint_bulk_update` | Batch update assignees/labels/state |
| `sprint_status` | Aggregated epic/status/assignee overview |
| `sprint_action_log` | Query the append-only action log |

## Config

See `examples/sprint-planner.json` for a complete example. Key sections:

- **github** — repo owner, repo name, Projects v2 project number
- **team** — team members with GitHub logins
- **plan_docs** — format, base path, epic-to-plan-doc mapping with parent issue numbers
- **story_extraction** — CSS selectors/regex for parsing plan documents
- **action_log** — path to the append-only JSON log
```

---

## Task 12: Register in marketplace

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Read current marketplace.json**

```bash
cat .claude-plugin/marketplace.json
```

- [ ] **Step 2: Add github-sprint-planner entry**

In `.claude-plugin/marketplace.json`, add this entry inside the `"plugins"` array, after the `clickup-sprint-planner` entry:

```json
{
  "name": "github-sprint-planner",
  "description": "Sprint planning tools for GitHub Issues + Projects v2 — bulk operations, sub-issue linking, plan doc sync, and action logging.",
  "version": "1.0.0",
  "source": "./github-sprint-planner",
  "category": "productivity"
}
```

- [ ] **Step 3: Run final test suite**

```bash
cd github-sprint-planner && uv run pytest tests/ -v --tb=short
```

Expected: All tests pass.

- [ ] **Step 4: Verify MCP server starts**

```bash
cd github-sprint-planner && SPRINT_PLANNER_CONFIG=examples/sprint-planner.example.json uv run python server/main.py &
sleep 2 && kill %1
```

Expected: Server starts without import errors (will error on missing real config values, that's fine).
