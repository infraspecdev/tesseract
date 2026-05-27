# Shield ClickUp Milestone Tags — Design

**Status:** Draft for review
**Date:** 2026-05-27
**Owner:** ashwinimanoj
**Depends on:** the `/pm-sync` sidecar refactor (`pm_sync_sidecar` + `shield_parsers`), already on `feat/plan-trd-refactor`.

## 1. Problem

`/pm-sync` mirrors a plan's epics and stories to ClickUp but drops milestones entirely — `plan.json.milestones[]` and each story's `milestone_id` never reach ClickUp. There's no way to see, in ClickUp, which milestone a story belongs to. (`grep -rn "milestone" shield/adapters/clickup/server/` returns zero matches.)

## 2. Goal

When `/pm-sync` creates a story task in ClickUp, tag it with its milestone so milestones are visible and filterable in the ClickUp UI.

## 3. Non-Goals (explicitly deferred)

- **Reassignment** — a story moving `M1` → `M2` on a re-sync. Create-time tagging only; re-sync does not reconcile existing tags.
- **Clear** — `milestone_id` set to `null` after a tag already exists. Not reconciled.
- **Milestone-drift detection in the diff** — `pm_sync_sidecar` does not compare a story's expected milestone tag against ClickUp's actual tags.
- **Cross-adapter milestone forwarding** — no `forward_milestones` protocol in `_common`. Other adapters (Jira fix-version, Notion select, GitHub native milestones) are out of scope. The `shield:ms:` tag convention is ClickUp-specific.
- **Milestone metadata** — outcome / exit-criteria are not carried to ClickUp; only the milestone id, as a tag.

These are deferred, not rejected. A follow-up can add a reconcile pass (and the diff change it requires) on top of this.

## 4. Design

### 4.1 Tag convention (ClickUp-local)

Milestone tags use a Shield-owned namespace so they're unambiguous and a future reconcile can find them by prefix without disturbing human-authored tags:

```
shield:ms:<milestone_id>      e.g.  shield:ms:m1
```

Two properties:
- **Stable** — keyed on `milestone_id` (`M1`), not the mutable milestone name. A milestone rename does not orphan the tag.
- **Lowercased** — ClickUp normalizes tag names to lowercase, so `M1` renders as `m1`. The helper lowercases at construction so callers and any future matcher compare apples to apples.

Helper (ClickUp adapter, e.g. `server/tools/_helpers.py`):

```python
MILESTONE_TAG_PREFIX = "shield:ms:"

def milestone_tag(milestone_id: str) -> str:
    """Canonical ClickUp tag for a milestone. Lowercased — ClickUp lowercases tags."""
    return f"{MILESTONE_TAG_PREFIX}{milestone_id}".lower()
```

The convention (prefix + lowercasing + id-keyed) is documented in the pm-sync card-format doc so a later reconcile step or another adapter can follow it.

### 4.2 `pm_bulk_create` change

ClickUp's create endpoint (`POST /list/{id}/task`) accepts a `tags` array in the payload. `pm_bulk_create` already builds a `task_data` dict per story; add the milestone tag when the story carries a `milestone_id`:

```python
# in the per-story loop, after the existing task_data fields are set:
if story.get("milestone_id"):
    task_data["tags"] = [milestone_tag(story["milestone_id"])]
```

- A story with no `milestone_id` gets no `tags` key — behavior unchanged.
- The tool docstring gains a `milestone_id` bullet in the per-story dict description.
- No extra API call — the tag rides along in the create payload.

### 4.3 Skill wiring

`shield/skills/pm-sync/SKILL.md`: when the skill assembles the `stories=[...]` argument for `pm_bulk_create`, include `milestone_id` from each plan.json story (already present on the typed `Story` object via `shield_parsers`).

## 5. Data flow

```
plan.json story (milestone_id="M1")
  → skill builds story dict {name, description, epic_id, milestone_id="M1", ...}
  → pm_bulk_create computes milestone_tag("M1") = "shield:ms:m1"
  → task_data["tags"] = ["shield:ms:m1"]
  → POST /list/{backlog}/task  (tag set at creation)
  → ClickUp task carries tag "shield:ms:m1"
```

## 6. Failure semantics

Tagging is part of the create payload, so it shares the create's fate: if `create_task` succeeds, the tag is set; if it fails, the story is already reported in `pm_bulk_create`'s `failed[]` and retried on the next sync. No partial tag state independent of the task.

## 7. Testing

`shield/adapters/clickup/tests/test_bulk_create.py` (new or extended), respx-mocked:

- `test_bulk_create_sets_milestone_tag` — a story with `milestone_id: "M1"` produces a create request whose JSON body has `tags == ["shield:ms:m1"]`.
- `test_bulk_create_no_milestone_no_tag` — a story without `milestone_id` produces a create body with no `tags` key.
- `test_milestone_tag_lowercases` — `milestone_tag("M2") == "shield:ms:m2"` (unit test of the helper).

No-regression: the existing ClickUp adapter tests stay green. Coverage on touched lines ≥ 85% per the project's patch-coverage gate.

## 8. Eval coverage (CLAUDE.md mandate)

Extend the existing `shield/evals/pm-sync-sidecar` eval: assert that a created story in the fixture (which has `milestone_id` set) results in a `pm_bulk_create` call whose story payload carries `milestone_id`, and that the resulting tag is `shield:ms:<id>`. RED→GREEN paper trail recorded in the PR body (RED: pre-change create payload has no tags; GREEN: payload carries the milestone tag).

## 9. Versioning

This is additive ClickUp adapter behavior under the same `feat/plan-trd-refactor` body of work, which ships as a single **2.20.0** plugin release (per the consolidation in commit `7add9c7`). No new plugin version bump. The clickup adapter package version stays at its branch value unless a separate decision says otherwise.

## 10. Definition of done

- `pm_bulk_create` sets `shield:ms:<id>` on stories that have a `milestone_id`; stories without one are unaffected.
- The `/pm-sync` skill forwards `milestone_id` into the `pm_bulk_create` stories arg.
- Three unit tests green; existing ClickUp tests still green.
- `pm-sync-sidecar` eval asserts the milestone tag on a created story.
- The `shield:ms:` convention + deferred-reconcile note documented in the pm-sync card-format doc.
