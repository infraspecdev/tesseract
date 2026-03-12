"""MCP tool: sprint_bulk_rename — prepend epic prefix to non-compliant task names."""

from __future__ import annotations

import re

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.clickup_client import ClickUpClient, ClickUpAPIError
from server.config import SprintPlannerConfig
from server.tools._helpers import _get_linked_epic_ids


def register(
    mcp: FastMCP,
    client: ClickUpClient,
    action_log: ActionLog,
    config: SprintPlannerConfig,
):
    @mcp.tool()
    async def sprint_bulk_rename(
        epic: str | None = None,
        apply: bool = False,
        strip_prefix: str | None = None,
        story_format: str = "[{epic_id}] {name}",
        epic_format: str = "[EPIC] {name} | [{epic_id}]",
    ) -> dict:
        """Preview or apply prefix renames on non-compliant task names.

        Scans story tasks linked to epics via the relationship field and epic
        cards themselves. Identifies names missing the expected format and
        proposes renames. Set apply=True to execute.

        Args:
            epic: Epic ID to scope (e.g. "P3"). Omit for all epics.
            apply: If true, rename the tasks. If false (default), preview only.
            strip_prefix: Regex pattern to strip from existing names before
                reformatting. E.g. r"\\[K8S Migration\\] Phase \\d+ \\|\\s*"
                to remove "[K8S Migration] Phase 2 | " from names.
            story_format: Format string for story task names. Placeholders:
                {epic_id}, {name}. Default: "[{epic_id}] {name}".
            epic_format: Format string for epic card names. Placeholders:
                {epic_id}, {name}, {epic_name} (from config). Default:
                "[EPIC] {name} | [{epic_id}]".
        """
        epics_to_check = config.plan_docs.epics
        if epic:
            epics_to_check = [e for e in epics_to_check if e.id == epic]
            if not epics_to_check:
                available = [e.id for e in config.plan_docs.epics]
                return {"error": f"Epic {epic!r} not found. Available: {available}"}

        strip_re = re.compile(strip_prefix) if strip_prefix else None
        relationship_field_id = config.clickup.relationship_field.id

        # Fetch backlog (story) tasks
        try:
            all_tasks = await client.get_tasks_by_list(
                config.clickup.lists.backlog.id, include_closed=True
            )
        except ClickUpAPIError as e:
            return {"error": f"Failed to fetch backlog tasks: {e}"}

        # Fetch epic cards
        try:
            epic_tasks = await client.get_tasks_by_list(
                config.clickup.lists.epics.id, include_closed=True
            )
        except ClickUpAPIError as e:
            return {"error": f"Failed to fetch epic tasks: {e}"}

        epic_tasks_by_id = {t["id"]: t for t in epic_tasks}

        renames = []
        for epic_cfg in epics_to_check:
            # 1. Check the epic card itself
            epic_task = epic_tasks_by_id.get(epic_cfg.epic_id)
            if epic_task:
                name = epic_task.get("name", "")
                clean_name = strip_re.sub("", name).strip() if strip_re else name
                new_name = epic_format.format(
                    epic_id=epic_cfg.id,
                    name=clean_name,
                    epic_name=epic_cfg.name,
                )
                if name != new_name:
                    renames.append({
                        "task_id": epic_task["id"],
                        "epic": epic_cfg.id,
                        "type": "epic",
                        "current_name": name,
                        "new_name": new_name,
                    })

            # 2. Check story tasks linked to this epic
            linked_tasks = [
                t for t in all_tasks
                if epic_cfg.epic_id in _get_linked_epic_ids(t, relationship_field_id)
            ]
            for task in linked_tasks:
                name = task.get("name", "")
                clean_name = strip_re.sub("", name).strip() if strip_re else name
                new_name = story_format.format(
                    epic_id=epic_cfg.id,
                    name=clean_name,
                )
                if name != new_name:
                    renames.append({
                        "task_id": task["id"],
                        "epic": epic_cfg.id,
                        "type": "story",
                        "current_name": name,
                        "new_name": new_name,
                    })

        if not renames:
            return {"message": "All task names are compliant.", "renames": []}

        if not apply:
            epic_count = sum(1 for r in renames if r["type"] == "epic")
            story_count = sum(1 for r in renames if r["type"] == "story")
            return {
                "message": f"Found {len(renames)} tasks to rename ({epic_count} epics, {story_count} stories). Set apply=True to execute.",
                "mode": "preview",
                "renames": renames,
            }

        # Apply renames
        renamed = []
        failed = []
        for r in renames:
            try:
                await client.update_task(r["task_id"], {"name": r["new_name"]})
                renamed.append({**r, "status": "success"})
            except ClickUpAPIError as e:
                failed.append({**r, "status": "failed", "error": str(e)})

        # Log action
        log_warning = None
        try:
            action_log.log_action(
                action="bulk_rename",
                status="success" if not failed else "partial",
                summary=f"Renamed {len(renamed)}/{len(renames)} tasks with epic prefix",
                results=renamed + failed,
                undo={
                    "type": "bulk_rename",
                    "rollback": [
                        {"task_id": r["task_id"], "name": r["current_name"]}
                        for r in renamed
                    ],
                },
            )
        except Exception as e:
            log_warning = f"Action logging failed: {e}"

        result = {
            "message": f"Renamed {len(renamed)}/{len(renames)} tasks.",
            "mode": "applied",
            "renamed": renamed,
            "failed": failed,
        }
        if log_warning:
            result["log_warning"] = log_warning
        return result
