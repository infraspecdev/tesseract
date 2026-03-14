"""Markdown plan document parser — stub for v0.2."""

from __future__ import annotations

from pathlib import Path

from server.parsers.base import PlanParser, Story


class MarkdownPlanParser(PlanParser):
    """Markdown plan document parser. Not yet implemented."""

    def extract_stories(self, file_path: str | Path, extraction_config: dict) -> list[Story]:
        raise NotImplementedError(
            "Markdown parser is not yet implemented. "
            "Use HTML format plan docs, or contribute a parser."
        )

    def write_clickup_id(self, file_path: str | Path, story_index: int, clickup_id: str) -> None:
        raise NotImplementedError("Markdown parser is not yet implemented.")
