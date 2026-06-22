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
