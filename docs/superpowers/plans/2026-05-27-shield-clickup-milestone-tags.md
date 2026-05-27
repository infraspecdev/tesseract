# Shield ClickUp Milestone Tags Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When `/pm-sync` creates a ClickUp story task, tag it with `shield:ms:<milestone_id>` so milestones are visible/filterable in ClickUp. Create-time only; reassignment/clear deferred.

**Architecture:** Add a ClickUp-local `milestone_tag()` helper, extract `pm_bulk_create`'s body into a testable `pm_bulk_create_impl` (matching the existing `*_impl` pattern in `sync.py`), have it inject `task_data["tags"]` when a story carries `milestone_id`, and wire `milestone_id` through the `/pm-sync` skill's `pm_bulk_create` call.

**Tech Stack:** Python 3.11+, uv, pytest + pytest-asyncio, `unittest.mock` (MagicMock/AsyncMock — the adapter's established test style), mcp[cli], httpx.

**Spec:** [`docs/superpowers/specs/2026-05-27-shield-clickup-milestone-tags-design.md`](../specs/2026-05-27-shield-clickup-milestone-tags-design.md)

---

## File Structure

| File | Responsibility | Change |
|---|---|---|
| `shield/adapters/clickup/server/tools/_helpers.py` | Shared adapter helpers | Add `MILESTONE_TAG_PREFIX` + `milestone_tag()` |
| `shield/adapters/clickup/server/tools/bulk_create.py` | Batch task creation | Extract `pm_bulk_create_impl`; inject milestone tag into create payload |
| `shield/adapters/clickup/tests/test_bulk_create.py` | Tests for bulk_create | New file — helper unit test + tagging tests + no-regression of existing behavior |
| `shield/skills/pm-sync/SKILL.md` | Sync orchestration | Pass `milestone_id` into the `pm_bulk_create` stories arg |
| `shield/skills/pm-sync/card-format.md` | Card/tag conventions doc | Document the `shield:ms:` convention + deferred reconcile |
| `shield/evals/pm-sync-sidecar/eval.yaml` | Skill eval | Assert created story carries its milestone tag |

---

## Task 1: Add the `milestone_tag` helper

**Files:**
- Modify: `shield/adapters/clickup/server/tools/_helpers.py`
- Test: `shield/adapters/clickup/tests/test_bulk_create.py` (new)

- [ ] **Step 1.1: Write the failing unit test**

Create `shield/adapters/clickup/tests/test_bulk_create.py`:

```python
"""Tests for pm_bulk_create milestone tagging + the milestone_tag helper."""

from __future__ import annotations

from server.tools._helpers import MILESTONE_TAG_PREFIX, milestone_tag


def test_milestone_tag_lowercases() -> None:
    assert milestone_tag("M2") == "shield:ms:m2"


def test_milestone_tag_uses_prefix() -> None:
    assert milestone_tag("M1").startswith(MILESTONE_TAG_PREFIX)
    assert milestone_tag("M1") == "shield:ms:m1"
```

- [ ] **Step 1.2: Run the test — expect failure**

Run:
```bash
uv run --directory shield/adapters/clickup --extra test pytest tests/test_bulk_create.py -v
```
Expected: FAIL with `ImportError: cannot import name 'milestone_tag' from 'server.tools._helpers'`.

- [ ] **Step 1.3: Implement the helper**

Append to `shield/adapters/clickup/server/tools/_helpers.py`:

```python
MILESTONE_TAG_PREFIX = "shield:ms:"


def milestone_tag(milestone_id: str) -> str:
    """Canonical ClickUp tag for a milestone.

    Lowercased because ClickUp normalizes tag names to lowercase; keying on the
    stable milestone_id (e.g. "M1") rather than the mutable milestone name means
    a rename never orphans the tag.
    """
    return f"{MILESTONE_TAG_PREFIX}{milestone_id}".lower()
```

- [ ] **Step 1.4: Run the test — expect pass**

Run:
```bash
uv run --directory shield/adapters/clickup --extra test pytest tests/test_bulk_create.py -v
```
Expected: PASS (2 tests).

- [ ] **Step 1.5: Commit**

```bash
git add shield/adapters/clickup/server/tools/_helpers.py shield/adapters/clickup/tests/test_bulk_create.py
git commit -m "feat(shield/clickup): add milestone_tag helper (shield:ms:<id>, lowercased)"
```

---

## Task 2: Extract `pm_bulk_create_impl` (no behavior change)

This refactor makes the create logic callable from tests, matching the `pm_sync_sidecar_impl` pattern already in `sync.py`. No behavior change — a pure extraction.

**Files:**
- Modify: `shield/adapters/clickup/server/tools/bulk_create.py`

- [ ] **Step 2.1: Move the tool body into a module-level async function**

In `shield/adapters/clickup/server/tools/bulk_create.py`, replace the `register()` function (lines ~37–161) with an extracted impl + a thin tool wrapper. The impl is the existing body verbatim, taking `client`/`action_log`/`config` as explicit parameters:

```python
async def pm_bulk_create_impl(
    list_id: str,
    stories: list[dict],
    set_relationships: bool,
    *,
    client: ClickUpClient,
    action_log: ActionLog,
    config: SprintPlannerConfig,
) -> dict:
    """Create multiple ClickUp tasks in one call with optional EPIC relationship linking.

    Each story dict may have:
      - name (required): Task name
      - description: Task description
      - assignee: User ID string
      - priority: "urgent", "high", "normal", or "low"
      - orderindex: Position in the list (string, e.g. "1000")
      - epic_id: EPIC task ID to link via relationship field (requires set_relationships=true)
    """
    priority_map = {"urgent": 1, "high": 2, "normal": 3, "low": 4}

    created = []
    failed = []
    relationships = []
    format_warnings = []

    for story in stories:
        formatted_name = _auto_format_name(story)
        task_data: dict = {"name": formatted_name}

        missing = _check_description_sections(story.get("description"))
        if missing:
            format_warnings.append({
                "name": formatted_name,
                "missing_sections": missing,
            })

        if story.get("description"):
            task_data["description"] = story["description"]
        if story.get("assignee"):
            task_data["assignees"] = [int(story["assignee"])]
        if story.get("priority") and story["priority"] in priority_map:
            task_data["priority"] = priority_map[story["priority"]]
        if story.get("orderindex") is not None:
            task_data["orderindex"] = str(story["orderindex"])

        try:
            result = await client.create_task(list_id, task_data)
            task_id = result["id"]
            task_url = result.get("url", f"https://app.clickup.com/t/{task_id}")
            created.append({
                "task_id": task_id,
                "task_url": task_url,
                "name": formatted_name,
                "status": "success",
            })

            if set_relationships and story.get("epic_id"):
                field_id = config.clickup.relationship_field.id
                try:
                    await client.set_relationship_field(
                        task_id, field_id, [story["epic_id"]]
                    )
                    relationships.append({
                        "task_id": task_id,
                        "epic_id": story["epic_id"],
                        "status": "success",
                    })
                except ClickUpAPIError as e:
                    relationships.append({
                        "task_id": task_id,
                        "epic_id": story["epic_id"],
                        "status": "failed",
                        "error": str(e),
                    })

        except ClickUpAPIError as e:
            failed.append({
                "name": formatted_name,
                "status": "failed",
                "error": str(e),
            })

    log_warning = None
    try:
        action_log.log_action(
            action="bulk_create",
            status="success" if not failed else "partial",
            summary=f"Created {len(created)}/{len(stories)} tasks in list {list_id}",
            results=created + failed,
            relationships=relationships,
            undo={
                "type": "bulk_delete",
                "task_ids": [c["task_id"] for c in created],
                "relationships_to_remove": [
                    {
                        "task_id": r["task_id"],
                        "epic_id": r["epic_id"],
                        "field_id": config.clickup.relationship_field.id,
                    }
                    for r in relationships
                    if r["status"] == "success"
                ],
            },
        )
    except Exception as e:
        log_warning = f"Action logging failed: {e}"

    result = {
        "created": created,
        "failed": failed,
        "relationships": relationships,
    }
    if format_warnings:
        result["format_warnings"] = format_warnings
    if log_warning:
        result["log_warning"] = log_warning
    return result


def register(mcp: FastMCP, client: ClickUpClient, action_log: ActionLog, config: SprintPlannerConfig):
    @mcp.tool()
    async def pm_bulk_create(
        list_id: str,
        stories: list[dict],
        set_relationships: bool = False,
    ) -> dict:
        """Create multiple ClickUp tasks in one call with optional EPIC relationship linking.

        Each story dict may have:
          - name (required): Task name
          - description: Task description
          - assignee: User ID string
          - priority: "urgent", "high", "normal", or "low"
          - orderindex: Position in the list (string, e.g. "1000")
          - epic_id: EPIC task ID to link via relationship field (requires set_relationships=true)

        Args:
            list_id: The ClickUp list ID to create tasks in.
            stories: Array of story objects to create.
            set_relationships: If true, link each task to its epic_id via the relationship field.
        """
        return await pm_bulk_create_impl(
            list_id,
            stories,
            set_relationships,
            client=client,
            action_log=action_log,
            config=config,
        )
```

Keep the existing module-level imports, `_EPIC_PREFIX_RE`, `_REQUIRED_SECTIONS`, `_auto_format_name`, and `_check_description_sections` exactly as they are.

- [ ] **Step 2.2: Run the full adapter suite — confirm no regression**

Run:
```bash
uv run --directory shield/adapters/clickup --extra test pytest -v
```
Expected: all existing tests PASS (the extraction is behavior-preserving) plus Task 1's 2 helper tests.

- [ ] **Step 2.3: Commit**

```bash
git add shield/adapters/clickup/server/tools/bulk_create.py
git commit -m "refactor(shield/clickup): extract pm_bulk_create_impl (no behavior change)"
```

---

## Task 3: Inject the milestone tag into the create payload

**Files:**
- Modify: `shield/adapters/clickup/server/tools/bulk_create.py`
- Test: `shield/adapters/clickup/tests/test_bulk_create.py`

- [ ] **Step 3.1: Write the failing tests**

Append to `shield/adapters/clickup/tests/test_bulk_create.py`:

```python
from unittest.mock import AsyncMock, MagicMock

import pytest

from server.tools.bulk_create import pm_bulk_create_impl


def _mocks() -> tuple[MagicMock, MagicMock, MagicMock]:
    client = MagicMock()
    client.create_task = AsyncMock(
        return_value={"id": "T1", "url": "https://app.clickup.com/t/T1"}
    )
    client.set_relationship_field = AsyncMock(return_value={})
    action_log = MagicMock()
    action_log.log_action = MagicMock(return_value=None)
    config = MagicMock()
    config.clickup.relationship_field.id = "REL-FIELD"
    return client, action_log, config


@pytest.mark.asyncio
async def test_bulk_create_sets_milestone_tag() -> None:
    client, action_log, config = _mocks()
    stories = [{
        "name": "Story one",
        "description": "Summary\nTasks\nContext\nAcceptance Criteria",
        "milestone_id": "M1",
    }]

    await pm_bulk_create_impl(
        "BACKLOG", stories, False,
        client=client, action_log=action_log, config=config,
    )

    # create_task called once with task_data carrying the milestone tag.
    assert client.create_task.await_count == 1
    _list_id, task_data = client.create_task.await_args.args
    assert task_data["tags"] == ["shield:ms:m1"]


@pytest.mark.asyncio
async def test_bulk_create_no_milestone_no_tag() -> None:
    client, action_log, config = _mocks()
    stories = [{
        "name": "Story without milestone",
        "description": "Summary\nTasks\nContext\nAcceptance Criteria",
    }]

    await pm_bulk_create_impl(
        "BACKLOG", stories, False,
        client=client, action_log=action_log, config=config,
    )

    _list_id, task_data = client.create_task.await_args.args
    assert "tags" not in task_data


@pytest.mark.asyncio
async def test_bulk_create_null_milestone_no_tag() -> None:
    client, action_log, config = _mocks()
    stories = [{
        "name": "Story with null milestone",
        "description": "Summary\nTasks\nContext\nAcceptance Criteria",
        "milestone_id": None,
    }]

    await pm_bulk_create_impl(
        "BACKLOG", stories, False,
        client=client, action_log=action_log, config=config,
    )

    _list_id, task_data = client.create_task.await_args.args
    assert "tags" not in task_data
```

- [ ] **Step 3.2: Run the tests — expect failure**

Run:
```bash
uv run --directory shield/adapters/clickup --extra test pytest tests/test_bulk_create.py -v
```
Expected: `test_bulk_create_sets_milestone_tag` FAILs (`KeyError: 'tags'`); the two no-tag tests may pass already (no tags key today). The point is the tagging test fails.

- [ ] **Step 3.3: Implement the tag injection**

In `pm_bulk_create_impl` (the function from Task 2), add the milestone-tag line in the per-story loop, immediately after the `orderindex` block and before the `try:` that calls `create_task`:

```python
        if story.get("orderindex") is not None:
            task_data["orderindex"] = str(story["orderindex"])
        if story.get("milestone_id"):
            task_data["tags"] = [milestone_tag(story["milestone_id"])]

        try:
            result = await client.create_task(list_id, task_data)
```

Add the import at the top of `bulk_create.py`:

```python
from server.tools._helpers import milestone_tag
```

(Note: `story.get("milestone_id")` is falsy for both missing and `None`, so the null case writes no `tags` key — covered by the two no-tag tests.)

- [ ] **Step 3.4: Run the tests — expect pass**

Run:
```bash
uv run --directory shield/adapters/clickup --extra test pytest tests/test_bulk_create.py -v
```
Expected: all PASS (5 tests in this file).

- [ ] **Step 3.5: Run the full adapter suite — confirm no regression**

Run:
```bash
uv run --directory shield/adapters/clickup --extra test pytest -v
```
Expected: all PASS.

- [ ] **Step 3.6: Commit**

```bash
git add shield/adapters/clickup/server/tools/bulk_create.py shield/adapters/clickup/tests/test_bulk_create.py
git commit -m "feat(shield/clickup): tag created stories with shield:ms:<milestone_id>"
```

---

## Task 4: Wire `milestone_id` through the `/pm-sync` skill

**Files:**
- Modify: `shield/skills/pm-sync/SKILL.md`

- [ ] **Step 4.1: Inspect the current bulk_create story-dict construction in the skill**

Run:
```bash
grep -n "pm_bulk_create\|milestone\|epic_id\|stories=\|orderindex" shield/skills/pm-sync/SKILL.md
```

- [ ] **Step 4.2: Add `milestone_id` to the documented story-dict shape**

In `shield/skills/pm-sync/SKILL.md`, in the "Creating Stories" workflow where it shows the `pm_bulk_create(... stories=[...])` call, add `milestone_id` to the per-story fields. Find the bullet list / example that enumerates story fields (name, description, epic_id, orderindex) and add:

```
   - milestone_id: the story's milestone_id from plan.json (e.g. "M1"); omit or null if the story has none. pm_bulk_create turns it into a shield:ms:<id> tag on the ClickUp task.
```

If the workflow shows a concrete `pm_bulk_create` example, update it to include `milestone_id` in each story object, e.g.:

```
pm_bulk_create(
  list_id=config.lists.backlog.id,
  stories=[
    { "name": "...", "description": "...", "epic_id": <epic.pm_id>,
      "orderindex": "1000", "milestone_id": "M1" },
    ...
  ],
  set_relationships=true
)
```

- [ ] **Step 4.3: Commit**

```bash
git add shield/skills/pm-sync/SKILL.md
git commit -m "docs(shield/pm-sync): forward milestone_id into pm_bulk_create stories"
```

---

## Task 5: Document the tag convention in `card-format.md`

**Files:**
- Modify: `shield/skills/pm-sync/card-format.md`

- [ ] **Step 5.1: Inspect the doc to find where custom fields / tags are described**

Run:
```bash
grep -n "tag\|custom field\|## \|### " shield/skills/pm-sync/card-format.md
```

- [ ] **Step 5.2: Add a "Milestone tags" subsection**

Append (or insert near the custom-field reference) in `shield/skills/pm-sync/card-format.md`:

```markdown
## Milestone tags

`/pm-sync` tags each created story task with its milestone using a Shield-owned
namespace:

    shield:ms:<milestone_id>      e.g.  shield:ms:m1

- Set at **creation time** by `pm_bulk_create` when the story dict carries a
  `milestone_id`. Keyed on the stable `milestone_id` (not the mutable milestone
  name), and lowercased because ClickUp lowercases tag names.
- The `shield:ms:` prefix marks the tag as machine-managed — do not hand-edit.
- **Deferred (not yet implemented):** reassignment (a story moving M1 → M2 on a
  re-sync) and clear (milestone_id → null) are NOT reconciled. Milestone tags are
  applied at creation only. A future reconcile step would find existing tags by
  the `shield:ms:` prefix.
```

- [ ] **Step 5.3: Commit**

```bash
git add shield/skills/pm-sync/card-format.md
git commit -m "docs(shield/pm-sync): document shield:ms: milestone tag convention + deferred reconcile"
```

---

## Task 6: Extend the `pm-sync-sidecar` eval to assert the milestone tag

**Files:**
- Modify: `shield/evals/pm-sync-sidecar/eval.yaml`
- Possibly modify: `shield/evals/pm-sync-sidecar/fixtures/plan-v14-minimal.json`

- [ ] **Step 6.1: Inspect the eval + fixture**

Run:
```bash
cat shield/evals/pm-sync-sidecar/eval.yaml
cat shield/evals/pm-sync-sidecar/fixtures/plan-v14-minimal.json
```

- [ ] **Step 6.2: Ensure the fixture story has a milestone_id**

Confirm `fixtures/plan-v14-minimal.json`'s story has `"milestone_id": "M1"` and the plan has a matching `milestones[]` entry with `id: "M1"`. If the story's `milestone_id` is missing or null, set it to `"M1"` and ensure `milestones[]` contains `{"id": "M1", "name": "...", "outcome": "...", "exit_criteria": ["..."]}`.

- [ ] **Step 6.3: Add the tag expectation**

In `shield/evals/pm-sync-sidecar/eval.yaml`, under `expectations.positive`, add:

```yaml
    - "The pm_bulk_create story payload for EPIC-1-S1 includes milestone_id: \"M1\""
    - "The created story task carries the tag shield:ms:m1 (milestone_id lowercased, shield:ms: prefix)"
```

Under `expectations.negative`, add:

```yaml
    - "A story with no milestone_id is NOT given any shield:ms: tag"
```

- [ ] **Step 6.4: Run the eval**

Run:
```bash
uv run --with pyyaml shield/evals/run.py shield/evals/pm-sync-sidecar
```
Expected: the eval passes with the new tag expectations. (If `run.py` takes different args, check `shield/evals/README.md` for the invocation.)

- [ ] **Step 6.5: Commit**

```bash
git add shield/evals/pm-sync-sidecar/
git commit -m "eval(shield): assert created story carries shield:ms: milestone tag"
```

---

## Task 7: Final checkpoint — full suite + coverage + DoD

- [ ] **Step 7.1: Run the full ClickUp adapter suite with coverage**

Run:
```bash
uv run --directory shield/adapters/clickup --extra test pytest \
  --cov=server --cov-report=term-missing tests/
```
Expected: all tests PASS; coverage on `bulk_create.py` touched lines ≥ 85%.

- [ ] **Step 7.2: Verify DoD items**

- `pm_bulk_create` sets `shield:ms:<id>` on stories with a `milestone_id`; stories without one are unaffected — confirmed by `test_bulk_create_sets_milestone_tag` + `test_bulk_create_no_milestone_no_tag`.
- The `/pm-sync` skill forwards `milestone_id` into `pm_bulk_create` — Task 4.
- Existing ClickUp tests still green — Step 7.1.
- The `pm-sync-sidecar` eval asserts the milestone tag — Task 6.
- The `shield:ms:` convention + deferred reconcile documented — Task 5.

- [ ] **Step 7.3: Confirm no version bump crept in**

Run:
```bash
grep -A3 '"name": "shield"' .claude-plugin/marketplace.json | grep version
grep '^version' shield/adapters/clickup/pyproject.toml
```
Expected: marketplace `2.20.0`, clickup adapter `2.1.0` — unchanged (this work ships under the consolidated release).

- [ ] **Step 7.4: Tag the green checkpoint**

```bash
git commit --allow-empty -m "chore(shield): milestone-tags feature complete — DoD met"
```

---

## Self-Review

**1. Spec coverage:**
- Spec §4.1 (tag convention) → Task 1
- Spec §4.2 (`pm_bulk_create` change) → Tasks 2 (refactor) + 3 (tag injection)
- Spec §4.3 (skill wiring) → Task 4
- Spec §6 (failure semantics) → covered implicitly; tag rides the create call, no separate test needed (the `failed[]` path is existing behavior)
- Spec §7 (testing) → Tasks 1, 3 (the three named tests + helper tests)
- Spec §8 (eval) → Task 6
- Spec §9 (versioning, no bump) → Task 7 Step 7.3
- Spec §10 (DoD) → Task 7 Step 7.2

**2. Placeholder scan:** No TBD/TODO. Task 4/5/6 begin with an `inspect` step because the exact insertion point in prose docs/eval depends on current file content — the step then gives the exact text to add. Acceptable (the content to add is fully specified).

**3. Type consistency:** `milestone_tag(milestone_id: str) -> str` used identically in Task 1 (def), Task 3 (call), tests. `pm_bulk_create_impl(list_id, stories, set_relationships, *, client, action_log, config)` signature matches between Task 2 (def) and Task 3 (tests call it with the same kwargs).

---

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-05-27-shield-clickup-milestone-tags.md`. Two execution options:

**1. Subagent-Driven (recommended)** — I dispatch a fresh subagent per task, review between tasks, fast iteration.

**2. Inline Execution** — Execute tasks in this session using executing-plans, batch execution with checkpoints.

Which approach?
