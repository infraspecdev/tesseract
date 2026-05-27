# pm-sync naming-format fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `pm_bulk_create` and `pm_bulk_rename` share one canonical task-naming source so they can't crash on `{prefix}`/`{index}` formats, can't stamp opaque ClickUp ids as display prefixes, and can't disagree on the canonical name.

**Architecture:** Introduce `server/naming.py` as the single source of truth for formatting epic/story names. Both tools call it. `bulk_create` takes structured `epic_label`/`index`/bare-`name` inputs (with `epic_id` reserved for the relationship link); `bulk_rename` correlates ClickUp tasks back to plan stories by `pm_id` to recover the true index and bare name. `config.py` stops dropping `project_prefix`.

**Tech Stack:** Python 3, `uv`, `pytest` (+ `pytest-asyncio`), `unittest.mock`. MCP tools in `shield/adapters/clickup/server/tools/`.

**Test command (run from the adapter dir):** `cd shield/adapters/clickup && uv run pytest <path> -v`

---

## File Structure

- **Create** `shield/adapters/clickup/server/naming.py` — canonical name formatting (`format_story_name`, `format_epic_name`, `story_index`).
- **Create** `shield/adapters/clickup/tests/test_naming.py` — unit tests for the formatter.
- **Create** `shield/adapters/clickup/tests/test_config_naming.py` — `project_prefix` round-trip.
- **Modify** `shield/adapters/clickup/server/config.py` — add `project_prefix` to `NamingConfig`; read it in `load_shield_config`.
- **Modify** `shield/adapters/clickup/server/tools/bulk_create.py` — structured naming via `naming.py`; drop opaque-id prefixing; relax Summary check.
- **Modify** `shield/adapters/clickup/server/tools/rename.py` — use `naming.py`; correlate by `pm_id` for index + bare name.
- **Modify** `shield/adapters/clickup/tests/test_bulk_create.py` — replace the auto-prefix test; fix the format-warnings expectation; add structured-naming cases.
- **Modify** `shield/adapters/clickup/tests/test_rename_sidecar.py` — add `{prefix}`/`{index}` crash-regression + correlation cases.
- **Modify** `shield/adapters/clickup/skills/pm-sync/SKILL.md`, `commands/pm-sync.md`, `skills/pm-sync/card-format.md` — document the new `bulk_create` story-dict shape and the heading-less Summary.

> **Note (out of scope):** `sync.py` has its own `_EPIC_PREFIX_RE`. After backfill, `pm_sync_sidecar` matches by `pm_id`, so that heuristic is secondary and is left unchanged.

---

## Task 1: Shared naming module

**Files:**
- Create: `shield/adapters/clickup/server/naming.py`
- Test: `shield/adapters/clickup/tests/test_naming.py`

- [ ] **Step 1: Write the failing tests**

Create `shield/adapters/clickup/tests/test_naming.py`:

```python
"""Tests for the canonical task-name formatter shared by create + rename."""

from __future__ import annotations

import pytest

from server.naming import format_epic_name, format_story_name, story_index


def test_story_simple_format() -> None:
    out = format_story_name(
        "[{epic_id}] {name}", prefix="", epic_id="EPIC-1", index="1", name="Do X"
    )
    assert out == "[EPIC-1] Do X"


def test_story_full_format_with_prefix_and_index() -> None:
    out = format_story_name(
        "[{prefix}] {epic_id}-S{index}: {name}",
        prefix="SHIELD", epic_id="EPIC-1", index="1", name="Do X",
    )
    assert out == "[SHIELD] EPIC-1-S1: Do X"


def test_story_unknown_placeholder_raises_named_error() -> None:
    with pytest.raises(ValueError) as exc:
        format_story_name(
            "{foo} {name}", prefix="", epic_id="E", index="1", name="n"
        )
    assert "story_format" in str(exc.value)
    assert "{foo}" in str(exc.value)


def test_epic_default_format_uses_name() -> None:
    out = format_epic_name(
        "[EPIC] {name} | [{epic_id}]",
        prefix="", epic_id="EPIC-1", name="First epic", epic_name="First epic",
    )
    assert out == "[EPIC] First epic | [EPIC-1]"


def test_epic_format_with_prefix_and_epic_name() -> None:
    out = format_epic_name(
        "[{prefix}] {epic_id}: {epic_name}",
        prefix="SHIELD", epic_id="EPIC-1", name="ignored", epic_name="First epic",
    )
    assert out == "[SHIELD] EPIC-1: First epic"


def test_epic_unknown_placeholder_raises_named_error() -> None:
    with pytest.raises(ValueError) as exc:
        format_epic_name(
            "{bar}", prefix="", epic_id="E", name="n", epic_name="n"
        )
    assert "epic_format" in str(exc.value)
    assert "{bar}" in str(exc.value)


def test_story_index_parses_trailing_s_number() -> None:
    assert story_index("EPIC-1-S1") == "1"
    assert story_index("EPIC-4-S0") == "0"
    assert story_index("EPIC-12-S37") == "37"


def test_story_index_returns_empty_when_absent() -> None:
    assert story_index("EPIC-1") == ""
    assert story_index("freeform-id") == ""
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd shield/adapters/clickup && uv run pytest tests/test_naming.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'server.naming'`.

- [ ] **Step 3: Write the implementation**

Create `shield/adapters/clickup/server/naming.py`:

```python
"""Canonical task-name formatting shared by pm_bulk_create and pm_bulk_rename.

One formatter for both tools means they can never drift on what a "compliant"
name looks like, and a format string that references an unsupported placeholder
fails with a clear, named error instead of a bare KeyError.
"""

from __future__ import annotations

import re
import string

_STORY_PLACEHOLDERS = {"prefix", "epic_id", "index", "name"}
_EPIC_PLACEHOLDERS = {"prefix", "epic_id", "name", "epic_name"}

_STORY_INDEX_RE = re.compile(r"-S(\d+)$")


def _placeholders_used(fmt: str) -> set[str]:
    """Root field names referenced by a str.format template."""
    used: set[str] = set()
    for _literal, field_name, _spec, _conv in string.Formatter().parse(fmt):
        if field_name:
            # Strip attribute/index access: "name.upper" / "name[0]" -> "name".
            root = field_name.split(".")[0].split("[")[0]
            if root:
                used.add(root)
    return used


def _check_placeholders(fmt: str, allowed: set[str], kind: str) -> None:
    unknown = _placeholders_used(fmt) - allowed
    if unknown:
        unknown_str = ", ".join("{" + u + "}" for u in sorted(unknown))
        allowed_str = ", ".join("{" + a + "}" for a in sorted(allowed))
        raise ValueError(
            f"{kind} references unknown placeholder(s) {unknown_str}; "
            f"allowed: {allowed_str}"
        )


def format_story_name(
    fmt: str, *, prefix: str, epic_id: str, index: int | str, name: str
) -> str:
    """Render a story task name from the configured story_format."""
    _check_placeholders(fmt, _STORY_PLACEHOLDERS, "story_format")
    return fmt.format(prefix=prefix, epic_id=epic_id, index=index, name=name)


def format_epic_name(
    fmt: str, *, prefix: str, epic_id: str, name: str, epic_name: str
) -> str:
    """Render an epic card name from the configured epic_format."""
    _check_placeholders(fmt, _EPIC_PLACEHOLDERS, "epic_format")
    return fmt.format(prefix=prefix, epic_id=epic_id, name=name, epic_name=epic_name)


def story_index(story_id: str) -> str:
    """Extract the S-index from a plan story id (e.g. 'EPIC-4-S0' -> '0').

    Returns '' when the id carries no '-S<n>' suffix.
    """
    m = _STORY_INDEX_RE.search(story_id)
    return m.group(1) if m else ""
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd shield/adapters/clickup && uv run pytest tests/test_naming.py -v`
Expected: PASS (8 passed).

- [ ] **Step 5: Commit**

```bash
git add shield/adapters/clickup/server/naming.py shield/adapters/clickup/tests/test_naming.py
git commit -m "feat(shield/clickup): shared canonical task-name formatter

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: `project_prefix` in config

**Files:**
- Modify: `shield/adapters/clickup/server/config.py:42-44` (NamingConfig) and `:150-153` (load_shield_config)
- Test: `shield/adapters/clickup/tests/test_config_naming.py`

- [ ] **Step 1: Write the failing test**

Create `shield/adapters/clickup/tests/test_config_naming.py`:

```python
"""Tests that NamingConfig carries project_prefix and load_shield_config reads it."""

from __future__ import annotations

from server.config import NamingConfig


def test_naming_config_defaults_project_prefix_empty() -> None:
    assert NamingConfig().project_prefix == ""


def test_naming_config_accepts_project_prefix() -> None:
    nc = NamingConfig(
        project_prefix="SHIELD",
        story_format="[{prefix}] {epic_id}-S{index}: {name}",
    )
    assert nc.project_prefix == "SHIELD"
    assert nc.story_format == "[{prefix}] {epic_id}-S{index}: {name}"
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `cd shield/adapters/clickup && uv run pytest tests/test_config_naming.py -v`
Expected: FAIL — `NamingConfig` rejects the unexpected `project_prefix` kwarg (pydantic) or the attribute is missing.

- [ ] **Step 3: Add the field**

In `shield/adapters/clickup/server/config.py`, change `NamingConfig` (currently lines 42-44):

```python
class NamingConfig(BaseModel):
    project_prefix: str = ""
    story_format: str = "[{epic_id}] {name}"
    epic_format: str = "[EPIC] {name} | [{epic_id}]"
```

- [ ] **Step 4: Read project_prefix in load_shield_config**

In the same file, change the `naming=NamingConfig(...)` block in `load_shield_config` (currently lines 150-153):

```python
        naming=NamingConfig(
            project_prefix=naming.get("project_prefix", ""),
            story_format=naming.get("story_format", "[{epic_id}] {name}"),
            epic_format=naming.get("epic_format", "[EPIC] {name} | [{epic_id}]"),
        ),
```

- [ ] **Step 5: Run the test to verify it passes**

Run: `cd shield/adapters/clickup && uv run pytest tests/test_config_naming.py -v`
Expected: PASS (2 passed).

- [ ] **Step 6: Commit**

```bash
git add shield/adapters/clickup/server/config.py shield/adapters/clickup/tests/test_config_naming.py
git commit -m "fix(shield/clickup): stop dropping naming.project_prefix from config

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: `bulk_create` — structured naming, no opaque prefix, Summary fix

**Files:**
- Modify: `shield/adapters/clickup/server/tools/bulk_create.py`
- Modify: `shield/adapters/clickup/tests/test_bulk_create.py`

- [ ] **Step 1: Write/replace the failing tests**

In `shield/adapters/clickup/tests/test_bulk_create.py`:

(a) **Delete** the test `test_bulk_create_auto_prefixes_name_with_epic_id` (it asserts the removed opaque-prefix behavior).

(b) **Replace** `test_bulk_create_format_warnings_for_missing_sections` body's expected set — Summary is no longer a required heading:

```python
@pytest.mark.asyncio
async def test_bulk_create_format_warnings_for_missing_sections() -> None:
    client, action_log, config = _mocks()
    stories = [
        {"name": "P1 - Incomplete story", "description": "hi"},
        {"name": "P2 - No description"},  # missing description key
    ]

    result = await pm_bulk_create_impl(
        "BACKLOG", stories, False,
        client=client, action_log=action_log, config=config,
    )

    assert "format_warnings" in result
    assert len(result["format_warnings"]) == 2
    for warning in result["format_warnings"]:
        assert set(warning["missing_sections"]) == {
            "Tasks", "Context", "Acceptance Criteria"
        }
```

(c) **Add** new tests at the end of the file:

```python
@pytest.mark.asyncio
async def test_bulk_create_formats_name_from_epic_label_and_index() -> None:
    client, action_log, config = _mocks()
    config.naming.project_prefix = "SHIELD"
    config.naming.story_format = "[{prefix}] {epic_id}-S{index}: {name}"
    stories = [{
        "name": "Install Istio",
        "epic_label": "EPIC-1",
        "index": "1",
        "epic_id": "86abc",            # opaque ClickUp id — link target only
        "description": _FULL_DESC,
    }]

    await pm_bulk_create_impl(
        "BACKLOG", stories, True,
        client=client, action_log=action_log, config=config,
    )

    _list_id, task_data = client.create_task.await_args.args
    assert task_data["name"] == "[SHIELD] EPIC-1-S1: Install Istio"


@pytest.mark.asyncio
async def test_bulk_create_does_not_prefix_with_opaque_epic_id() -> None:
    """With no epic_label, the caller's name is used verbatim — the opaque
    relationship epic_id never leaks into the display name."""
    client, action_log, config = _mocks()
    stories = [{
        "name": "[SHIELD] EPIC-1-S1: Already formatted",
        "epic_id": "86abc",
        "description": _FULL_DESC,
    }]

    await pm_bulk_create_impl(
        "BACKLOG", stories, True,
        client=client, action_log=action_log, config=config,
    )

    _list_id, task_data = client.create_task.await_args.args
    assert task_data["name"] == "[SHIELD] EPIC-1-S1: Already formatted"
    assert "86abc" not in task_data["name"]


@pytest.mark.asyncio
async def test_bulk_create_heading_less_summary_not_flagged() -> None:
    client, action_log, config = _mocks()
    desc = (
        "This story does a thing and matters because reasons.\n\n"
        "## Tasks\n- [ ] do it\n\n"
        "## Context / Notes\n- note\n\n"
        "## Acceptance Criteria\n- [ ] verified"
    )
    stories = [{"name": "Story", "description": desc}]

    result = await pm_bulk_create_impl(
        "BACKLOG", stories, False,
        client=client, action_log=action_log, config=config,
    )

    assert "format_warnings" not in result
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd shield/adapters/clickup && uv run pytest tests/test_bulk_create.py -v`
Expected: FAIL — `test_bulk_create_formats_name_from_epic_label_and_index` produces `86abc - Install Istio`; the heading-less-Summary test sees a `format_warnings` entry; the format-warnings test still expects "Summary".

- [ ] **Step 3: Rewrite the naming + section logic**

In `shield/adapters/clickup/server/tools/bulk_create.py`:

Replace the top-of-file block (currently lines 14-35) — remove `_EPIC_PREFIX_RE` and `_auto_format_name`, drop "Summary" from required headings, and import the shared formatter. Also delete the now-unused `import re` (currently line 5), since `_EPIC_PREFIX_RE` was its only consumer:

```python
from server.action_log import ActionLog
from server.clickup_client import ClickUpClient, ClickUpAPIError
from server.config import SprintPlannerConfig
from server.naming import format_story_name
from server.tools._helpers import milestone_tag

# Required *headings* in card descriptions. "Summary" is intentionally absent:
# per card-format.md the summary is a heading-less lead paragraph.
_REQUIRED_SECTIONS = ["Tasks", "Context", "Acceptance Criteria"]


def _display_name(story: dict, config: SprintPlannerConfig) -> str:
    """Canonical display name.

    When the caller supplies a human epic label, format via the shared
    formatter; otherwise use the caller's name verbatim. The relationship
    target ``epic_id`` (an opaque ClickUp task id) is never used as a prefix.
    """
    name = story["name"]
    epic_label = story.get("epic_label")
    if epic_label:
        return format_story_name(
            config.naming.story_format,
            prefix=config.naming.project_prefix,
            epic_id=epic_label,
            index=story.get("index", ""),
            name=name,
        )
    return name


def _check_description_sections(description: str | None) -> list[str]:
    """Return required-heading names missing from a card description."""
    if not description:
        return list(_REQUIRED_SECTIONS)
    desc_lower = description.lower()
    return [s for s in _REQUIRED_SECTIONS if s.lower() not in desc_lower]
```

Then change the per-story line that builds the name (currently line 71):

```python
        formatted_name = _display_name(story, config)
```

(Leave the rest of the loop — `task_data`, relationship linking via `story.get("epic_id")`, milestone tag, logging — unchanged.)

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd shield/adapters/clickup && uv run pytest tests/test_bulk_create.py -v`
Expected: PASS (all). The relationship tests still pass because linking continues to read `story.get("epic_id")`.

- [ ] **Step 5: Commit**

```bash
git add shield/adapters/clickup/server/tools/bulk_create.py shield/adapters/clickup/tests/test_bulk_create.py
git commit -m "fix(shield/clickup): bulk_create uses shared formatter; no opaque-id prefix; relax Summary check

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: `rename` — shared formatter + pm_id correlation

**Files:**
- Modify: `shield/adapters/clickup/server/tools/rename.py`
- Modify: `shield/adapters/clickup/tests/test_rename_sidecar.py`

- [ ] **Step 1: Write the failing tests**

In `shield/adapters/clickup/tests/test_rename_sidecar.py`, add a helper that sets story pm_ids and two new tests:

```python
def _plan_with_story_pm_ids(
    tmp_path: Path,
    epic_pm_ids: dict[int, str | None],
    story_pm_ids: dict[tuple[int, int], str],
) -> Path:
    """Set epic and story pm_ids on the fixture, write to tmp_path."""
    plan_data = json.loads(FIXTURE.read_text())
    for idx, value in epic_pm_ids.items():
        plan_data["epics"][idx]["pm_id"] = value
    for (e_idx, s_idx), value in story_pm_ids.items():
        plan_data["epics"][e_idx]["stories"][s_idx]["pm_id"] = value
    p = tmp_path / "plan.json"
    p.write_text(json.dumps(plan_data))
    return p


@pytest.mark.asyncio
async def test_rename_does_not_crash_on_prefix_index_format(
    mock_client: MagicMock,
    mock_config: MagicMock,
    mock_action_log: MagicMock,
    tmp_path: Path,
) -> None:
    """A story_format using {prefix} and {index} must not raise KeyError."""
    mock_config.naming.project_prefix = "SHIELD"
    mock_config.naming.story_format = "[{prefix}] {epic_id}-S{index}: {name}"
    # Story EPIC-1-S1 synced to STORY-PM-1.
    p = _plan_with_story_pm_ids(
        tmp_path, {0: "EPIC-PM-1"}, {(0, 0): "STORY-PM-1"}
    )

    backlog_tasks = [
        {
            "id": "STORY-PM-1",
            "name": "Story one",
            "custom_fields": [
                {"id": "REL-FIELD-UUID", "value": [{"id": "EPIC-PM-1"}]}
            ],
        }
    ]
    mock_client.get_tasks_by_list = AsyncMock(side_effect=[backlog_tasks, []])

    result = await pm_bulk_rename_impl(
        plan_json_path=str(p),
        client=mock_client,
        config=mock_config,
        action_log=mock_action_log,
        apply=False,
    )

    story_renames = [r for r in result["renames"] if r["type"] == "story"]
    assert len(story_renames) == 1
    # index recovered from plan story id EPIC-1-S1 -> "1", name from plan.
    assert story_renames[0]["new_name"] == "[SHIELD] EPIC-1-S1: Story one"


@pytest.mark.asyncio
async def test_rename_uncorrelated_task_falls_back_to_stripped_name(
    mock_client: MagicMock,
    mock_config: MagicMock,
    mock_action_log: MagicMock,
    tmp_path: Path,
) -> None:
    """A linked task with no matching plan story (pm_id) keeps working off its
    stripped current name, with empty index."""
    mock_config.naming.story_format = "{epic_id}: {name}"
    p = _plan_with_pm_ids(tmp_path, {0: "EPIC-PM-1"})  # story pm_ids stay null

    backlog_tasks = [
        {
            "id": "UNKNOWN-TASK",
            "name": "Story one",
            "custom_fields": [
                {"id": "REL-FIELD-UUID", "value": [{"id": "EPIC-PM-1"}]}
            ],
        }
    ]
    mock_client.get_tasks_by_list = AsyncMock(side_effect=[backlog_tasks, []])

    result = await pm_bulk_rename_impl(
        plan_json_path=str(p),
        client=mock_client,
        config=mock_config,
        action_log=mock_action_log,
        apply=False,
    )

    story_renames = [r for r in result["renames"] if r["type"] == "story"]
    assert len(story_renames) == 1
    assert story_renames[0]["new_name"] == "EPIC-1: Story one"
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd shield/adapters/clickup && uv run pytest tests/test_rename_sidecar.py -v`
Expected: `test_rename_does_not_crash_on_prefix_index_format` FAILs with `KeyError: 'prefix'`; the fallback test FAILs (helper/behavior not present).

- [ ] **Step 3: Rewrite rename to use the shared formatter + correlation**

In `shield/adapters/clickup/server/tools/rename.py`:

Change the imports (currently lines 8-13) to add the formatter:

```python
from shield_parsers.sidecar import load_plan

from server.action_log import ActionLog
from server.clickup_client import ClickUpClient, ClickUpAPIError
from server.config import SprintPlannerConfig
from server.naming import format_epic_name, format_story_name, story_index
from server.tools._helpers import _get_linked_epic_ids
```

After `plan = load_plan(plan_json_path)` (currently line 50), build a pm_id→story-info map across the whole plan:

```python
    plan = load_plan(plan_json_path)

    # Correlate ClickUp story tasks back to plan stories by pm_id so we can
    # recover the canonical bare name and the true S-index for {index} formats.
    story_by_pm_id: dict[str, tuple[str, str]] = {}  # pm_id -> (index, name)
    for plan_epic in plan.epics:
        for plan_story in plan_epic.stories:
            if plan_story.pm_id:
                story_by_pm_id[plan_story.pm_id] = (
                    story_index(plan_story.id),
                    plan_story.name,
                )

    epics_to_check = plan.epics
```

Replace the epic-card formatting block (currently lines 91-97) with the shared helper:

```python
        epic_task = epic_tasks_by_id.get(epic_cfg.pm_id)
        if epic_task:
            name = epic_task.get("name", "")
            clean_name = strip_re.sub("", name).strip() if strip_re else name
            new_name = format_epic_name(
                epic_epic_fmt,
                prefix=config.naming.project_prefix,
                epic_id=epic_cfg.id,
                name=clean_name,
                epic_name=epic_cfg.name,
            )
```

Replace the story formatting block (currently lines 112-118) with correlation + the shared helper:

```python
        for task in linked_tasks:
            name = task.get("name", "")
            clean_name = strip_re.sub("", name).strip() if strip_re else name
            correlated = story_by_pm_id.get(task["id"])
            if correlated:
                idx, canonical_name = correlated
            else:
                idx, canonical_name = "", clean_name
            new_name = format_story_name(
                epic_story_fmt,
                prefix=config.naming.project_prefix,
                epic_id=epic_cfg.id,
                index=idx,
                name=canonical_name,
            )
```

(Leave the `renames.append({...})` blocks, preview/apply flow, and action logging unchanged.)

- [ ] **Step 4: Run the full rename suite to verify it passes**

Run: `cd shield/adapters/clickup && uv run pytest tests/test_rename_sidecar.py -v`
Expected: PASS (all). Existing tests still pass: their `story_format="{epic_id}: {name}"` doesn't reference `{prefix}`/`{index}`, stories have null pm_ids so they hit the stripped-name fallback, and `config.naming.project_prefix` (a MagicMock) is passed but unreferenced by those formats.

- [ ] **Step 5: Commit**

```bash
git add shield/adapters/clickup/server/tools/rename.py shield/adapters/clickup/tests/test_rename_sidecar.py
git commit -m "fix(shield/clickup): bulk_rename uses shared formatter + pm_id correlation (no KeyError on {prefix}/{index})

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 5: Documentation alignment

**Files:**
- Modify: `shield/adapters/clickup/skills/pm-sync/SKILL.md` (or the plugin-root pm-sync skill — see Step 1)
- Modify: `shield/adapters/clickup/commands/pm-sync.md` (or plugin-root command)
- Modify: the `pm-sync/card-format.md` referenced by the skill

> The live skill loads from the plugin root. Confirm the source-of-truth paths first.

- [ ] **Step 1: Locate the tracked skill/command/card-format sources**

Run: `git ls-files | grep -E 'pm-sync/(SKILL|card-format)\.md|commands/pm-sync\.md'`
Expected: the tracked paths under `shield/` (the `~/.claude/plugins/...` cache copies are NOT tracked — do not edit those).

- [ ] **Step 2: Document the bulk_create story-dict shape**

In the tracked `pm-sync/SKILL.md` "Creating Stories" workflow, replace the line that reads
`Names auto-formatted as "{epic_id} - {name}" (e.g. "EPIC-1 - Install Istio")`
with:

```markdown
   - Pass each story with: `name` (bare story title), `epic_label` (human epic id,
     e.g. "EPIC-1"), `index` (story index, e.g. 1), and `epic_id` (the **ClickUp epic
     task id** — used only to set the relationship link, never as a display prefix).
   - The adapter formats the display name via `config.naming.story_format`
     (e.g. `[{prefix}] {epic_id}-S{index}: {name}`). Do NOT pre-format the name yourself.
   - For epic cards, pre-format the name with `config.naming.epic_format` so create
     and a later `pm_bulk_rename` agree.
```

- [ ] **Step 3: Note the heading-less Summary in card-format.md**

In `pm-sync/card-format.md`, under "Required Sections", append to the Summary bullet:

```markdown
   (The Summary is a heading-less lead paragraph — `pm_bulk_create` does not require a
   literal `## Summary` heading. The Tasks, Context, and Acceptance Criteria headings
   are required.)
```

- [ ] **Step 4: Mirror the contract note in the command doc**

In `commands/pm-sync.md`, under the create behavior, add one line:

```markdown
- Stories are sent with `epic_label` + `index` + bare `name` (display name formatted
  adapter-side); `epic_id` is the relationship link target only.
```

- [ ] **Step 5: Run the full adapter suite as a regression gate**

Run: `cd shield/adapters/clickup && uv run pytest -v`
Expected: PASS (all tests across naming, config, bulk_create, rename, sync).

- [ ] **Step 6: Commit**

```bash
git add shield/adapters/clickup/skills/pm-sync/SKILL.md shield/adapters/clickup/skills/pm-sync/card-format.md shield/adapters/clickup/commands/pm-sync.md
git commit -m "docs(shield/pm-sync): document bulk_create structured naming + heading-less Summary

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

> If Step 1 shows the tracked skill/command live at the plugin root (not under `shield/adapters/clickup/`), adjust the paths in Steps 2-4 and 6 accordingly.

---

## Definition of done

- `cd shield/adapters/clickup && uv run pytest -v` is green.
- A `story_format` using `{prefix}`/`{index}` no longer crashes `pm_bulk_rename` (Task 4 regression test).
- `pm_bulk_create` never stamps an opaque ClickUp id as a display prefix (Task 3 test).
- A well-formed card with a heading-less Summary emits no `format_warnings` (Task 3 test).
- Skill/command/card-format docs describe the new contract.
- Per CLAUDE.md, the eval surface is the pytest suite above (RED→GREEN captured per task); note this explicitly in the PR body.
