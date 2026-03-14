"""Story data model and abstract parser interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from server.config import StoryExtractionConfig


@dataclass
class Story:
    """A single user story extracted from a plan document."""

    index: int
    name: str
    description: str = ""
    clickup_id: str | None = None
    status: str | None = None
    assignee: str | None = None
    tasks: list[str] = field(default_factory=list)
    acceptance_criteria: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "name": self.name,
            "description": self.description,
            "clickup_id": self.clickup_id,
            "status": self.status,
            "assignee": self.assignee,
            "tasks": self.tasks,
            "acceptance_criteria": self.acceptance_criteria,
        }


class PlanParser(ABC):
    """Abstract base class for plan document parsers."""

    @abstractmethod
    def extract_stories(self, file_path: str | Path, extraction_config: dict) -> list[Story]:
        """Extract stories from a plan document.

        Args:
            file_path: Path to the plan document.
            extraction_config: Format-specific extraction config (e.g. CSS selectors for HTML).

        Returns:
            List of Story objects extracted from the document.
        """

    @abstractmethod
    def write_clickup_id(self, file_path: str | Path, story_index: int, clickup_id: str) -> None:
        """Write a ClickUp ID back into the plan doc after task creation.

        Replaces "to create" badges with linked ClickUp ID badges.
        """


def get_parser(format: str) -> PlanParser:
    """Factory function to get a parser by format name."""
    if format == "html":
        from server.parsers.html_parser import HtmlPlanParser
        return HtmlPlanParser()
    elif format == "markdown":
        from server.parsers.markdown_parser import MarkdownPlanParser
        return MarkdownPlanParser()
    else:
        raise ValueError(f"Unknown plan doc format: {format!r}. Supported: html, markdown")
