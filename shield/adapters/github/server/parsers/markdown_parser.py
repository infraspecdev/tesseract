"""Markdown plan document parser — stub."""

from __future__ import annotations

from pathlib import Path

from server.parsers.base import PlanParser, Story


class MarkdownPlanParser(PlanParser):
    def extract_stories(self, file_path: str | Path, extraction_config: dict) -> list[Story]:
        raise NotImplementedError(
            "Markdown parser is not yet implemented. Use HTML format plan docs."
        )

    def write_issue_number(
        self, file_path: str | Path, story_index: int, issue_number: int, issue_url: str
    ) -> None:
        raise NotImplementedError("Markdown parser is not yet implemented.")
