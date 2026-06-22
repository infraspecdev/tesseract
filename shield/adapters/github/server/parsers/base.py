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
    def write_issue_number(
        self, file_path: str | Path, story_index: int, issue_number: int, issue_url: str
    ) -> None:
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
