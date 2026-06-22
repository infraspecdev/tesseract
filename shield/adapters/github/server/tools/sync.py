"""MCP tool: pm_sync — diff plan documents against GitHub Issues."""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from pathlib import Path

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.config import SprintPlannerConfig
from server.github_client import GitHubClient, GitHubAPIError
from server.parsers.base import get_parser

FUZZY_THRESHOLD = 0.8
FUZZY_LINK_THRESHOLD = 0.6

_EPIC_PREFIX_RE = re.compile(r"^(?:\[[^\]]+\]\s*)?[A-Z]\d+[a-z]?\s*[-–]\s*")


def _strip_prefix(title: str) -> str:
    if ": " in title:
        return title.split(": ", 1)[-1]
    return _EPIC_PREFIX_RE.sub("", title)


def _fuzzy_match(name: str, candidates: list[dict]) -> tuple[dict | None, float]:
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


def _determine_diff(story, issue: dict | None) -> str:
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
    async def pm_sync(
        epic: str | None = None,
        apply_links: bool = False,
    ) -> dict:
        """Diff plan documents against GitHub Issues.

        Matches stories to sub-issues of each epic issue. Stories with no linked
        issue but a fuzzy-matched GitHub issue are flagged as "to_link".

        When apply_links=True, auto-links unlinked issues to their epic via the sub-issues API.

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
                if story.issue_number:
                    issue = next(
                        (i for i in all_repo_issues if i["number"] == story.issue_number), None
                    )
                    if issue:
                        matched_numbers.add(issue["number"])
                        story_results.append({
                            "index": story.index,
                            "name": story.name,
                            "plan_status": story.status,
                            "issue_number": story.issue_number,
                            "github_state": issue.get("state"),
                            "github_title": issue.get("title"),
                            "diff": _determine_diff(story, issue),
                        })
                        continue

                unmatched_sub = [i for i in sub_issues if i["number"] not in matched_numbers]
                match, ratio = _fuzzy_match(story.name, unmatched_sub)
                if match and ratio >= FUZZY_THRESHOLD:
                    matched_numbers.add(match["number"])
                    story_results.append({
                        "index": story.index,
                        "name": story.name,
                        "plan_status": story.status,
                        "issue_number": match["number"],
                        "github_state": match.get("state"),
                        "github_title": match.get("title"),
                        "diff": _determine_diff(story, match),
                    })
                    continue

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
                    story_results.append({
                        "index": story.index,
                        "name": story.name,
                        "plan_status": story.status,
                        "issue_number": None,
                        "diff": "to_create",
                    })

            orphaned_count = sum(1 for i in sub_issues if i["number"] not in matched_numbers)
            results.append({
                "epic": epic_cfg.id,
                "name": epic_cfg.name,
                "summary": {
                    "match": sum(1 for s in story_results if s["diff"] == "match"),
                    "to_create": sum(1 for s in story_results if s["diff"] == "to_create"),
                    "to_update": sum(1 for s in story_results if s["diff"] == "to_update"),
                    "to_link": sum(1 for s in story_results if s["diff"] == "to_link"),
                    "orphaned": orphaned_count,
                },
                "stories": story_results,
            })

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
