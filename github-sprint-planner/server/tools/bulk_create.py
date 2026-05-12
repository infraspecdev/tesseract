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

                try:
                    await client.add_sub_issue(epic_issue_number, issue_number)
                    linked = True
                except GitHubAPIError as e:
                    linked = False
                    format_warnings.append({"name": title, "sub_issue_error": str(e)})

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
