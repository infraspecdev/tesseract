"""HTML plan document parser using BeautifulSoup.

Parses structured HTML plan documents with story sections.
"""

from __future__ import annotations

import re
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from server.parsers.base import PlanParser, Story


class HtmlPlanParser(PlanParser):
    """Parses HTML plan documents with div.story sections.

    Expected HTML structure per story:

        <div class="story" id="story-1">
          <div class="story-header">
            <h3>Story 1: Create new ECS infrastructure in Production VPC</h3>
            <span class="badge badge-to-create">to create</span>
            <!-- or: <a class="badge badge-clickup" href="...">86d25arth</a> -->
            <span class="badge badge-ready">ready for dev</span>
          </div>
          <div class="story-description">
            <p>Description text...</p>
          </div>
          <h4>Tasks</h4>
          <ul class="checklist">
            <li>Task item 1</li>
            <li>Task item 2</li>
          </ul>
          <div class="acceptance">
            <h4>Acceptance Criteria</h4>
            <ul>
              <li>Criterion 1</li>
              <li>Criterion 2</li>
            </ul>
          </div>
        </div>
    """

    def extract_stories(self, file_path: str | Path, extraction_config: dict) -> list[Story]:
        file_path = Path(file_path)
        html = file_path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")

        story_selector = extraction_config.get("story_selector", "div.story[id^='story-']")
        name_pattern = extraction_config.get("name_pattern", r"Story \d+: (.+)")
        clickup_id_selector = extraction_config.get("clickup_id_selector", "a.badge-clickup")

        stories: list[Story] = []

        for story_div in soup.select(story_selector):
            if not isinstance(story_div, Tag):
                continue

            story_id_attr = story_div.get("id", "")
            index_match = re.search(r"story-(\d+)", str(story_id_attr))
            index = int(index_match.group(1)) if index_match else len(stories) + 1

            # Name from h3
            h3 = story_div.select_one(".story-header h3") or story_div.select_one("h3")
            raw_name = h3.get_text(strip=True) if h3 else f"Story {index}"
            name_match = re.search(name_pattern, raw_name)
            name = name_match.group(1) if name_match else raw_name

            # ClickUp ID from badge link
            clickup_link = story_div.select_one(clickup_id_selector)
            clickup_id = clickup_link.get_text(strip=True) if clickup_link else None

            # Status from non-clickup, non-to-create badge
            status = self._extract_status(story_div)

            # Description
            desc_div = story_div.select_one(".story-description")
            description = desc_div.get_text(strip=True) if desc_div else ""

            # Tasks from checklist
            tasks: list[str] = []
            checklist = story_div.select_one("ul.checklist")
            if checklist:
                tasks = [li.get_text(strip=True) for li in checklist.find_all("li")]

            # Acceptance criteria
            acceptance: list[str] = []
            acc_div = story_div.select_one(".acceptance")
            if acc_div:
                acceptance = [li.get_text(strip=True) for li in acc_div.find_all("li")]

            stories.append(
                Story(
                    index=index,
                    name=name,
                    description=description,
                    clickup_id=clickup_id,
                    status=status,
                    tasks=tasks,
                    acceptance_criteria=acceptance,
                )
            )

        return stories

    def write_clickup_id(self, file_path: str | Path, story_index: int, clickup_id: str) -> None:
        file_path = Path(file_path)
        html = file_path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")

        story_div = soup.select_one(f"div.story#story-{story_index}")
        if not story_div:
            raise ValueError(f"Story {story_index} not found in {file_path}")

        # Find the "to create" badge and replace it
        to_create_badge = story_div.select_one(".badge-to-create")
        if to_create_badge:
            new_tag = soup.new_tag(
                "a",
                attrs={
                    "class": "badge badge-clickup",
                    "href": f"https://app.clickup.com/t/{clickup_id}",
                    "target": "_blank",
                },
            )
            new_tag.string = clickup_id
            to_create_badge.replace_with(new_tag)
            file_path.write_text(str(soup), encoding="utf-8")
        else:
            # Already has a clickup badge or no badge — skip
            pass

    def _extract_status(self, story_div: Tag) -> str | None:
        """Extract status from badge spans, excluding clickup and to-create badges."""
        header = story_div.select_one(".story-header")
        if not header:
            return None

        for badge in header.select(".badge"):
            classes = badge.get("class", [])
            if "badge-clickup" in classes or "badge-to-create" in classes:
                continue
            text = badge.get_text(strip=True).lower()
            if text:
                return text.replace(" ", "_")
        return None
