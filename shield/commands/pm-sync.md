---
name: pm-sync
description: Sync plan stories to your PM tool (ClickUp, Jira, Confluence, Notion) — forwards design_refs[] as web links with idempotent upsert
outputs:
  - plan_json    # updated in place with PM tool IDs and URLs after sync
---

# PM Sync

Sync plan document stories against your project management tool. Includes
forwarding of each story's `design_refs[]` as web links on the synced task
(idempotent upsert keyed by `sha256(story_id + anchor_url)[:32]`).

## Usage

`/pm-sync` · `/pm-sync --tool <clickup|jira|confluence|notion>` (override adapter)

## Paths

This command mutates `{plan_json}` = `{output_dir}/{feature}/plan.json` in place — adding PM tool IDs and URLs to stories after sync. It does NOT write any new files; the `{plan_md}` / `{plan_html}` renders are regenerated from the updated sidecar by the `/plan` rendering flow.

## Behavior

1. Check that a PM tool is configured (`~/.shield/projects/<project>/pm.json` → `adapter`)
2. If not configured, suggest running `/shield init` to set up PM integration
3. Invoke the `shield:pm-sync` skill
4. The skill:
   - Calls `pm_get_capabilities` to verify adapter supports sync
   - Reads `{plan_json}` = `{output_dir}/{feature}/plan.json` for story data
   - Calls `pm_sync` to diff against PM state
   - Presents diff as table (match/new/updated/unlinked)
   - Asks user: apply all / pick which / cancel
   - For new stories: calls `pm_bulk_create`
   - For updates: calls `pm_bulk_update`
   - **For each story with `design_refs[]`:** calls the adapter's
     `forward_design_refs(task_id, refs) -> ForwardResult`. Anchorless
     placeholders (LLD `TODO`) are skipped without an HTTP write.
   - Updates `{plan_json}` with PM IDs and URLs
   - Re-renders `{plan_md}` / `{plan_html}` from the updated sidecar
5. Invoke `shield:summarize` to produce a sync summary
6. Offer next steps: `/pm-status`, `/implement`

## `design_refs[]` forwarding contract

Every adapter (ClickUp, Jira, Confluence, Notion) implements the same signature
from `shield/adapters/_common/shield_adapters_common/design_refs.py`:

```python
def forward_design_refs(task_id: str, refs: list[DesignRef]) -> ForwardResult: ...
```

`ForwardResult` aggregates `{created, skipped, errors[]}`. Each `DesignRef` produces
a deterministic 32-character idempotency key:

```python
idempotency_key = sha256(story_id + anchor_url)[:32]
```

Per-adapter wiring of the idempotency key:

| Adapter    | Storage                                              |
|------------|------------------------------------------------------|
| Jira       | `globalId` on `POST /rest/api/3/issue/{id}/remotelink` (201 = created, 200 = idempotent skip) |
| Confluence | `name` on `PUT /rest/api/content/{id}/relation/link/from` (201 = created, 200 = idempotent skip) |
| ClickUp    | Companion text custom field `Shield Design Link Keys` — adapter scans before writing the URL custom field |
| Notion     | Rich-text property `Shield Link Keys` — adapter scans before PATCHing the URL property |

**Running `/pm-sync` twice on the same plan produces zero duplicates** — each
adapter ships a per-adapter `test_idempotency.py` (Jira, Confluence, Notion) or
`test_forward_design_refs.py` (ClickUp) that asserts this against a mocked
remote (P0-4).

**Adapters with no link affordance** log `'design_refs forwarding skipped — adapter
does not support web links'` and return a result with `skipped == len(refs)`
instead of failing the sync.

## Observability (P1-8)

Each forwarded ref emits one structured log line:

```
action='forward_design_ref' story_id=… adapter=… anchor_url=… outcome=… idempotency_key=…
```

`outcome` is one of `created`, `idempotent_skip`, `skipped_no_anchor`,
`skipped_no_custom_field`. Failures emit `action='forward_design_ref_failed'` with
`{error_class, http_status, idempotency_key}` so on-call can correlate the
failing ref back to the originating story.

## Tool & access requirements (P1-13)

| Adapter    | Live deps                   | Test deps                   | Credentials env var          |
|------------|------------------------------|------------------------------|-------------------------------|
| Jira       | `requests`                   | `pytest`, `responses`        | `SHIELD_JIRA_TOKEN`           |
| Confluence | `requests`                   | `pytest`, `responses`        | `SHIELD_CONFLUENCE_TOKEN`     |
| ClickUp    | `httpx` (existing)           | `pytest`, `respx`            | `SHIELD_CLICKUP_TOKEN`        |
| Notion     | `requests`                   | `pytest`, `responses`        | `SHIELD_NOTION_TOKEN`         |

CI defaults to **mocked mode** (no credentials needed). Live tests require a
free-tier sandbox tenant per adapter and the corresponding env var. The repo
does not commit any credentials; `pm.json` carries opaque references only.

## Rollback triggers

Revert this command's forwarding behavior when any of the following observable
signals fire:

- A per-adapter idempotency test starts flaking in CI (root-cause first).
- `forward_design_ref_failed` rate exceeds 5/min sustained for 15 minutes on
  the live tenant.
- A user reports duplicate web-links on the synced task and a re-run of the
  per-adapter idempotency test reproduces the duplicate locally.

Rollback procedure: revert the adapter-specific commit; per-adapter packages
fall back to the prior PM-sync behavior (URL forwarding skipped, story sync
unchanged).
