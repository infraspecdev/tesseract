# pm-sync naming-format fix — design

**Date:** 2026-05-27
**Branch:** `fix/pm-sync-naming-format`
**Scope:** ClickUp adapter (`shield/adapters/clickup/`)

## Problem

A live `/pm-sync` run (16 stories + 5 epics) surfaced four defects in the ClickUp
adapter's task-naming logic. All trace to one root cause: **`pm_bulk_create` and
`pm_bulk_rename` format task names with independent, mismatched logic, and neither
supplies the full set of placeholders the configured format string can use.**

| # | Defect | Location | Severity |
|---|--------|----------|----------|
| 1 | `bulk_create` stamps the opaque ClickUp epic **task id** as a display prefix (e.g. `86d34tc9d - [SHIELD] EPIC-1-S1: …`) | `bulk_create.py:14-27` | bug |
| 2 | `bulk_rename` crashes (`KeyError: 'prefix'`) on configs whose format uses `{prefix}`/`{index}` | `rename.py:47,93,115` + `config.py:150-153` | bug |
| 3 | `format_warnings` false-positives on the heading-less "Summary" lead paragraph | `bulk_create.py:18,30-35` | noise |
| 4 | `bulk_create` and `bulk_rename` disagree on the canonical epic/story name | both | inconsistency |

### Root causes (grounded)

- **#1** — `_auto_format_name` prepends `{epic_id} - {name}` unless the name matches a
  legacy regex (`^[A-Z]\d+[a-z]?\s*-\s*`, e.g. `P3 - `). The `epic_id` field is overloaded:
  it is *both* the ClickUp relationship target (an opaque task id, required for linking) *and*
  the display-prefix source. When `set_relationships=true`, the opaque id becomes a junk prefix.
  The dedup regex also doesn't recognize the project's configured format, so an
  already-formatted name (`[SHIELD] EPIC-1-S1: …`) is treated as unformatted.
- **#2** — `config.py:150-153` reads only `story_format`/`epic_format` from the Shield
  config and **silently drops `project_prefix`**. The live `story_format` is
  `"[{prefix}] {epic_id}-S{index}: {name}"`, but `rename.py` calls
  `.format(epic_id=…, name=…)` — never supplying `prefix` or `index` → `KeyError: 'prefix'`.
  `NamingConfig` (`config.py:42-44`) does not even declare `project_prefix`.
- **#3** — `_check_description_sections` substring-matches the literal word `summary`, but
  `card-format.md` specifies the Summary as a heading-less lead paragraph. Every
  well-formed card is therefore flagged.
- **#4** — `bulk_create` writes epics as `[SHIELD] EPIC-1: …`; `bulk_rename`'s default
  `epic_format` (`[EPIC] {name} | [{epic_id}]`) considers that non-compliant. The create
  flow and the rename flow have no shared definition of "canonical".

## Design (Approach A — shared naming module)

### New: `server/naming.py`

Single source of truth for task naming:

```python
def format_story_name(fmt: str, *, prefix: str, epic_id: str,
                      index: int | str, name: str) -> str
def format_epic_name(fmt: str, *, prefix: str, epic_id: str,
                     epic_name: str) -> str
```

- A safe formatter supplies the full known placeholder set
  (`prefix, epic_id, index, name` for stories; `prefix, epic_id, epic_name` for epics).
- A format string using any *subset* of those works.
- A genuinely-unknown placeholder raises a clear, named error
  (e.g. `ValueError: story_format references unknown placeholder {foo}; allowed: …`)
  instead of a bare `KeyError`.

### `config.py`

- Add `project_prefix: str = ""` to `NamingConfig`.
- Read it in `from_shield_config` (currently dropped at `config.py:150-153`).

### `bulk_create.py`

- Delete `_auto_format_name`'s opaque-id prefixing and `_EPIC_PREFIX_RE`.
- Story dict gains optional `epic_label` and `index`:
  - When `epic_label` is present, the display name is built via
    `format_story_name(config.naming.story_format, prefix=config.naming.project_prefix,
    epic_id=epic_label, index=index, name=name)`.
  - When absent, the caller's `name` is used **verbatim** — no silent re-prefixing.
- `epic_id` reverts to *only* the relationship target (link), never a display source.
- Fix `_check_description_sections`: drop `"Summary"` from the required-*heading* set
  (the lead paragraph satisfies it per `card-format.md`); keep requiring
  `Tasks`, `Context`, `Acceptance Criteria`.

### `rename.py`

- Replace inline `.format(epic_id=…, name=…)` calls with the shared `naming.py` helpers,
  supplying `prefix` (from `config.naming.project_prefix`) and `index`.
- Correlate each linked ClickUp task back to its plan story **by `pm_id`** to recover the
  true `index` and canonical bare `name`. This is what lets rename satisfy a
  `{index}`-bearing format and produce names byte-identical to `bulk_create`'s.
- Tasks with no matching plan story (orphans / manually-created) are left untouched
  rather than mis-renamed.

### Contract ripple

- `skills/pm-sync/SKILL.md` workflow + `commands/pm-sync.md`: document the new
  `bulk_create` story-dict shape (`epic_label`, `index`, bare `name`; `epic_id` = link target).
- `skills/pm-sync/card-format.md`: note that Summary is a heading-less lead paragraph
  (align doc with the relaxed check).

## Testing (RED → GREEN)

Per `CLAUDE.md`, the executable eval is the pytest suite.

**RED** (reproduce against the *real* format `"[{prefix}] {epic_id}-S{index}: {name}"`):
- `bulk_rename` with that `story_format` + a `project_prefix` raises `KeyError` today.
- `bulk_create` with `epic_id` = opaque id + `set_relationships=true` produces a
  `<id> - …` junk prefix today.
- A well-formed card description (heading-less Summary) emits a `format_warnings` entry today.

**GREEN** (after fix):
- `naming.py` unit tests: each format permutation (`{epic_id}{name}`,
  `{prefix}{epic_id}{index}{name}`, epic format) renders correctly; unknown placeholder
  raises the named error.
- `test_bulk_create.py`: structured-input path renders the canonical name; no opaque-id
  prefix; absent `epic_label` ⇒ verbatim name; heading-less Summary ⇒ no warning.
- `test_rename_sidecar.py`: `{prefix}`/`{index}` format no longer crashes; pm_id
  correlation yields correct `index`; orphan tasks untouched.
- `config.py`: `project_prefix` round-trips from a Shield config dict.

## Out of scope

- Jira / Confluence / Notion adapters (no `bulk_create`/`bulk_rename`; only ClickUp has them).
- Re-running the live `/pm-sync` — the existing cards are already correctly named via the
  manual rename we applied; the backfilled `plan.json` is stashed on `feat/shield-backlog`.
- Milestone-tag reassignment / reconcile (separate deferred item).
