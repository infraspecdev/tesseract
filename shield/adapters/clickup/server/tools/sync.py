"""MCP tool: pm_sync — diff plan documents against ClickUp state."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.clickup_client import ClickUpClient, ClickUpAPIError
from server.config import SprintPlannerConfig
from server.parsers.base import Story, get_parser
from server.tools._helpers import _get_linked_epic_ids


FUZZY_THRESHOLD = 0.8
FUZZY_LINK_THRESHOLD = 0.6

# Fallback: matches names like "P3 - Install Istio" or "[Project] P1a-S1: ..."
_EPIC_PREFIX_RE = re.compile(r"^[A-Z]\d+[a-z]?\s*-\s*")


def _build_naming_regex(story_format: str) -> re.Pattern:
    """Build a compliance regex from a story_format string.

    Converts a format like "[{epic_id}] K8S Migration | {name}" into a regex
    that matches task names following that pattern. {epic_id} becomes a capture
    group for the epic ID, {name} becomes a wildcard match.
    """
    # Escape everything except our placeholders
    escaped = re.escape(story_format)
    # Replace escaped placeholders with regex groups
    escaped = escaped.replace(re.escape("{epic_id}"), r"[A-Z]\d+[a-z]?")
    escaped = escaped.replace(re.escape("{name}"), r".+")
    return re.compile(f"^{escaped}$")


def _fuzzy_match(name: str, candidates: list[dict]) -> tuple[dict | None, float]:
    """Find the best fuzzy match for a story name among ClickUp tasks.

    Returns a tuple of (best_match, best_ratio) so callers can distinguish
    between strong matches (>= FUZZY_THRESHOLD) and ambiguous ones
    (>= FUZZY_LINK_THRESHOLD).
    """
    best_match = None
    best_ratio = 0.0
    name_lower = name.lower().strip()
    for task in candidates:
        task_name = task.get("name", "")
        # Strip common prefixes like "[Project] P1a-S1: " or "P3 - "
        clean_name = task_name
        if ": " in clean_name:
            clean_name = clean_name.split(": ", 1)[-1]
        elif _EPIC_PREFIX_RE.match(clean_name):
            clean_name = _EPIC_PREFIX_RE.sub("", clean_name)
        ratio = SequenceMatcher(None, name_lower, clean_name.lower().strip()).ratio()
        if ratio > best_ratio:
            best_ratio = ratio
            best_match = task
    if best_ratio >= FUZZY_LINK_THRESHOLD:
        return best_match, best_ratio
    return None, best_ratio


def _determine_diff(story: Story, clickup_task: dict | None) -> str:
    """Determine the diff status between a plan story and its ClickUp match."""
    if clickup_task is None:
        return "to_create"
    task_name = clickup_task.get("name", "")
    clean_name = task_name
    if ": " in clean_name:
        clean_name = clean_name.split(": ", 1)[-1]
    elif _EPIC_PREFIX_RE.match(clean_name):
        clean_name = _EPIC_PREFIX_RE.sub("", clean_name)
    ratio = SequenceMatcher(None, story.name.lower(), clean_name.lower()).ratio()
    if ratio >= 0.8:
        return "match"
    return "to_update"


def _check_naming_compliance(task_name: str, naming_re: re.Pattern | None = None) -> bool:
    """Check if a task name follows the configured naming convention."""
    pattern = naming_re or _EPIC_PREFIX_RE
    return bool(pattern.match(task_name))


def _filter_tasks_by_relationship(
    tasks: list[dict], epic_task_id: str, relationship_field_id: str
) -> list[dict]:
    """Filter tasks linked to a specific epic via the relationship custom field."""
    return [
        t for t in tasks
        if epic_task_id in _get_linked_epic_ids(t, relationship_field_id)
    ]


def _get_unlinked_tasks(tasks: list[dict], relationship_field_id: str) -> list[dict]:
    """Get tasks that have no epic relationship set."""
    return [
        t for t in tasks
        if not _get_linked_epic_ids(t, relationship_field_id)
    ]


def register(
    mcp: FastMCP,
    client: ClickUpClient,
    config: SprintPlannerConfig,
    base_path: Path,
    action_log: ActionLog | None = None,
):
    @mcp.tool()
    async def pm_sync(
        epic: str | None = None,
        apply_links: bool = False,
    ) -> dict:
        """Diff plan documents against ClickUp state.

        Matches tasks to epics via the relationship custom field. Tasks without
        a relationship field set are detected via fuzzy name matching and flagged
        as "to_link".

        When apply_links=True, auto-sets the relationship field on flagged tasks
        and logs the action.

        Args:
            epic: Epic ID to sync (e.g. "P1a"). If omitted, syncs all epics.
            apply_links: If true, auto-link "to_link" tasks by setting their relationship field.
        """
        epics_to_sync = config.plan_docs.epics
        if epic:
            epics_to_sync = [p for p in epics_to_sync if p.id == epic]
            if not epics_to_sync:
                available = [p.id for p in config.plan_docs.epics]
                return {"error": f"Epic {epic!r} not found. Available: {available}"}

        parser = get_parser(config.plan_docs.format)
        extraction_config = config.story_extraction.html.model_dump()
        relationship_field_id = config.clickup.relationship_field.id
        default_naming_re = _build_naming_regex(config.naming.story_format)

        # Fetch all backlog tasks including closed (needed to match done stories)
        try:
            all_clickup_tasks = await client.get_tasks_by_list(
                config.clickup.lists.backlog.id, include_closed=True
            )
        except ClickUpAPIError as e:
            return {"error": f"Failed to fetch ClickUp tasks: {e}"}

        # Pre-compute unlinked tasks (no relationship field set)
        unlinked_tasks = _get_unlinked_tasks(all_clickup_tasks, relationship_field_id)

        results = []
        link_operations = []  # Collect link ops for apply_links mode

        for epic_cfg in epics_to_sync:
            # Resolve per-epic naming override, fall back to default
            if epic_cfg.naming and epic_cfg.naming.story_format:
                naming_re = _build_naming_regex(epic_cfg.naming.story_format)
            else:
                naming_re = default_naming_re

            plan_doc_path = base_path / epic_cfg.plan_doc
            if not plan_doc_path.exists():
                results.append({
                    "epic": epic_cfg.id,
                    "name": epic_cfg.name,
                    "error": f"Plan doc not found: {plan_doc_path}",
                })
                continue

            # Parse stories from plan doc
            try:
                stories = parser.extract_stories(plan_doc_path, extraction_config)
            except Exception as e:
                results.append({
                    "epic": epic_cfg.id,
                    "name": epic_cfg.name,
                    "error": f"Failed to parse plan doc: {e}",
                })
                continue

            # Filter ClickUp tasks linked to this epic via relationship field
            clickup_tasks = _filter_tasks_by_relationship(
                all_clickup_tasks, epic_cfg.epic_id, relationship_field_id
            )

            # Match stories to ClickUp tasks
            matched_task_ids = set()
            story_results = []

            for story in stories:
                # 1. Try exact match by clickup_id
                if story.clickup_id:
                    task = next(
                        (t for t in all_clickup_tasks if t["id"] == story.clickup_id), None
                    )
                    if task:
                        matched_task_ids.add(task["id"])
                        diff = _determine_diff(story, task)
                        story_results.append({
                            "index": story.index,
                            "name": story.name,
                            "plan_status": story.status,
                            "clickup_id": story.clickup_id,
                            "clickup_status": task.get("status", {}).get("status"),
                            "naming_compliant": _check_naming_compliance(task.get("name", ""), naming_re),
                            "diff": diff,
                        })
                        continue

                # 2. Try fuzzy name match against relationship-linked tasks
                unmatched = [t for t in clickup_tasks if t["id"] not in matched_task_ids]
                match, ratio = _fuzzy_match(story.name, unmatched)
                if match and ratio >= FUZZY_THRESHOLD:
                    # Strong match — auto-link
                    matched_task_ids.add(match["id"])
                    diff = _determine_diff(story, match)
                    story_results.append({
                        "index": story.index,
                        "name": story.name,
                        "plan_status": story.status,
                        "clickup_id": match["id"],
                        "clickup_status": match.get("status", {}).get("status"),
                        "naming_compliant": _check_naming_compliance(match.get("name", ""), naming_re),
                        "diff": diff,
                    })
                    continue

                # 3. Try fuzzy match against ALL unlinked tasks (no relationship set)
                unmatched_unlinked = [t for t in unlinked_tasks if t["id"] not in matched_task_ids]
                match, ratio = _fuzzy_match(story.name, unmatched_unlinked)
                if match and ratio >= FUZZY_LINK_THRESHOLD:
                    # Found unlinked task — flag as to_link
                    matched_task_ids.add(match["id"])
                    story_results.append({
                        "index": story.index,
                        "name": story.name,
                        "plan_status": story.status,
                        "clickup_id": None,
                        "diff": "to_link",
                        "naming_compliant": _check_naming_compliance(match.get("name", ""), naming_re),
                        "candidate": {
                            "clickup_id": match["id"],
                            "clickup_name": match.get("name"),
                            "clickup_status": match.get("status", {}).get("status"),
                            "fuzzy_ratio": round(ratio, 3),
                        },
                    })
                    # Collect for apply_links
                    link_operations.append({
                        "task_id": match["id"],
                        "epic_id": epic_cfg.epic_id,
                        "epic_label": epic_cfg.id,
                        "story_name": story.name,
                        "clickup_name": match.get("name"),
                    })
                else:
                    # 4. No match — to_create
                    story_results.append({
                        "index": story.index,
                        "name": story.name,
                        "plan_status": story.status,
                        "clickup_id": None,
                        "diff": "to_create",
                    })

            # Orphaned: ClickUp tasks for this epic with no matching plan story
            orphaned_count = sum(
                1 for t in clickup_tasks if t["id"] not in matched_task_ids
            )

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
                    await client.set_relationship_field(
                        op["task_id"], relationship_field_id, [op["epic_id"]]
                    )
                    linked.append({
                        "task_id": op["task_id"],
                        "epic_id": op["epic_id"],
                        "epic_label": op["epic_label"],
                        "story_name": op["story_name"],
                        "status": "success",
                    })
                except ClickUpAPIError as e:
                    link_failed.append({
                        "task_id": op["task_id"],
                        "epic_id": op["epic_id"],
                        "story_name": op["story_name"],
                        "status": "failed",
                        "error": str(e),
                    })

            # Log to action log
            if action_log and (linked or link_failed):
                try:
                    action_log.log_action(
                        action="sync_auto_link",
                        status="success" if not link_failed else "partial",
                        summary=f"Auto-linked {len(linked)}/{len(link_operations)} tasks to epics",
                        results=linked + link_failed,
                    )
                except Exception:
                    pass  # Don't fail sync due to logging errors

        output = results[0] if len(results) == 1 else {"epics": results}

        if apply_links and link_operations:
            output["link_results"] = {
                "linked": linked,
                "failed": link_failed,
            }

        return output
