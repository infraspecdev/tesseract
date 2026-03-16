# Named Plans Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the single `shield/plan.json` with named plans in `shield/docs/plans/<name>.json` so multiple features can be planned in parallel.

**Architecture:** Move from a single-file sidecar at `shield/plan.json` to a directory of named plans at `shield/docs/plans/<name>.json`. All readers resolve the plan by name — `/implement EPIC-1-S1` looks up which plan contains that story, `/plan-review auth-feature` reviews a specific plan. The `/plan` command writes to a named file derived from the topic. Plans live under `shield/docs/` alongside all other artifacts.

**Tech Stack:** Bash (e2e tests), Markdown (skills/commands), JSON Schema

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `shield/schemas/plan.schema.json` | Modify | Add optional `name` field to schema |
| `shield/skills/general/plan-docs/SKILL.md` | Modify | Write to `shield/docs/plans/<name>.json` |
| `shield/skills/general/plan-docs/sidecar-schema.md` | Modify | Document `name` field and new path |
| `shield/commands/plan.md` | Modify | Write to `shield/docs/plans/<name>.json`, accept `--name` |
| `shield/commands/implement.md` | Modify | Search all plans for story ID |
| `shield/commands/plan-review.md` | Modify | Accept plan name, default to listing |
| `shield/commands/review.md` | Modify | Search all plans for AC context |
| `shield/skills/general/implement-feature/SKILL.md` | Modify | Search `shield/docs/plans/*.json` for story |
| `shield/skills/general/plan-review/SKILL.md` | Modify | Read from `shield/docs/plans/<name>.json` |
| `shield/skills/general/review/SKILL.md` | Modify | Read AC from all plans in `shield/docs/plans/` |
| `shield/skills/pm-sync/SKILL.md` | Modify | Accept plan name, sync specific plan |
| `shield/skills/general/execute-steps/SKILL.md` | Modify | Reference `shield/docs/plans/` path |
| `shield/hooks/scripts/session-start.sh` | Modify | Update artifact output message |
| `shield/tests/e2e/fixtures/setup-fixture.sh` | Modify | Copy to `shield/docs/plans/` |
| `shield/tests/e2e/fixtures/python-api/plan.json` | Keep | Rename destination in setup-fixture |
| `shield/tests/e2e/phases/plan.sh` | Modify | Assert plan in `shield/docs/plans/` |
| `shield/tests/e2e/phases/implement.sh` | Modify | Look for plan in `shield/docs/plans/` |
| `shield/tests/e2e/test-implement.sh` | Modify | Write plan to `shield/docs/plans/` |

## Chunk 1: Schema and Plan Resolution

### Task 1: Add `name` field to plan schema

**Files:**
- Modify: `shield/schemas/plan.schema.json`

- [ ] **Step 1: Add `name` to required fields and properties**

Add `"name"` to the `required` array (after `"project"`) and add the property definition:

```json
"name": { "type": "string", "pattern": "^[a-z0-9-]+$", "description": "Plan name — used as filename: shield/docs/plans/<name>.json" },
```

The `name` field is kebab-case, used as the filename. Example: `"name": "auth-feature"` → `shield/docs/plans/auth-feature.json`.

- [ ] **Step 2: Commit**

```bash
git add shield/schemas/plan.schema.json
git commit -m "feat: add name field to plan schema for named plans"
```

### Task 2: Update sidecar-schema.md documentation

**Files:**
- Modify: `shield/skills/general/plan-docs/sidecar-schema.md`

- [ ] **Step 1: Update the example JSON**

Add `"name": "<kebab-case-plan-name>"` after the `"project"` field in the example. Add a rule: "The `name` field determines the filename: `shield/docs/plans/<name>.json`".

- [ ] **Step 2: Update the Rules section**

Add:
- Plan name must be kebab-case (`^[a-z0-9-]+$`)
- Each plan lives at `shield/docs/plans/<name>.json`
- Story IDs must be unique across all plans in a project

- [ ] **Step 3: Commit**

```bash
git add shield/skills/general/plan-docs/sidecar-schema.md
git commit -m "docs: update sidecar schema docs for named plans"
```

### Task 3: Update plan-docs skill to write named plans

**Files:**
- Modify: `shield/skills/general/plan-docs/SKILL.md`

- [ ] **Step 1: Update Output Paths section**

Change item 1 from:
```
1. `shield/plan.json` — machine-readable sidecar (updated in place, no timestamp)
```
to:
```
1. `shield/docs/plans/<name>.json` — machine-readable sidecar (named plan, updated in place)
```

Where `<name>` is derived from the planning topic (kebab-case, e.g., "input-validation", "auth-feature"). If the user provides a name explicitly, use it. Otherwise derive from the topic.

- [ ] **Step 2: Update "Critical: Sidecar First" section**

Change the reference from `shield/plan.json` to `shield/docs/plans/<name>.json`.

- [ ] **Step 3: Update the meta tag reference in HTML**

Change from:
```html
<meta name="sidecar" content="./plan.json">
```
to:
```html
<meta name="sidecar" content="./plans/<name>.json">
```

(HTML docs and plans are both under `shield/docs/`, so `./plans/<name>.json` works.)

- [ ] **Step 4: Update Common Mistakes table**

Add a row:
| Writing to `shield/plan.json` (old path) | Write to `shield/docs/plans/<name>.json` — named plans, not single file |

- [ ] **Step 5: Commit**

```bash
git add shield/skills/general/plan-docs/SKILL.md
git commit -m "feat: plan-docs skill writes to shield/docs/plans/<name>.json"
```

### Task 4: Update /plan command

**Files:**
- Modify: `shield/commands/plan.md`

- [ ] **Step 1: Update Output Paths section**

Change item 1 from:
```
1. `{project_root}/shield/plan.json` — machine-readable sidecar (updated in place, no timestamp)
```
to:
```
1. `{project_root}/shield/docs/plans/<name>.json` — machine-readable sidecar (named plan, updated in place)
```

- [ ] **Step 2: Update usage to accept optional name**

```
`/plan [--name <plan-name>] [topic or requirements]`
```

If `--name` not provided, derive from the topic (kebab-case). Example: `/plan input validation` → `shield/docs/plans/input-validation.json`.

- [ ] **Step 3: Update behavior step 4**

Change `shield/plan.json` references to `shield/docs/plans/<name>.json`.

- [ ] **Step 4: Update the meta tag in step 6**

Change `content="./plan.json"` to `content="./plans/<name>.json"`.

- [ ] **Step 5: Commit**

```bash
git add shield/commands/plan.md
git commit -m "feat: /plan command writes named plans to shield/docs/plans/"
```

## Chunk 2: Update All Readers

### Task 5: Update /implement command and implement-feature skill

**Files:**
- Modify: `shield/commands/implement.md`
- Modify: `shield/skills/general/implement-feature/SKILL.md`

- [ ] **Step 1: Update implement command**

Change step 1 from:
```
1. If a story ID is provided (e.g., EPIC-1-S1), look up the story in `shield/plan.json`
```
to:
```
1. If a story ID is provided (e.g., EPIC-1-S1), search all plans in `shield/docs/plans/*.json` for the story
```

Change step 6 reference from `shield/plan.json` to `shield/docs/plans/<plan>.json` (the plan containing the story).

- [ ] **Step 2: Update implement-feature skill**

Change the header line from:
```
**Plan sidecar:** `shield/plan.json` (reads and updates story status in place)
```
to:
```
**Plan sidecar:** `shield/docs/plans/*.json` (searches all named plans, updates story status in place)
```

Update "From plan sidecar (preferred)" section — change the lookup logic from reading a single `plan.json` to globbing `shield/docs/plans/*.json` and searching for the story ID across all plans. When found, update status in that specific plan file.

- [ ] **Step 3: Commit**

```bash
git add shield/commands/implement.md shield/skills/general/implement-feature/SKILL.md
git commit -m "feat: implement searches all named plans for story ID"
```

### Task 6: Update plan-review command and skill

**Files:**
- Modify: `shield/commands/plan-review.md`
- Modify: `shield/skills/general/plan-review/SKILL.md`

- [ ] **Step 1: Update plan-review command**

Change step 2 from:
```
2. If no path, check for `{project_root}/shield/plan.json`
```
to:
```
2. If no path, list plans in `{project_root}/shield/docs/plans/*.json`:
   - If exactly one plan exists, use it
   - If multiple plans exist, present a list and ask which to review
   - Accept plan name as shorthand: `/plan-review auth-feature`
```

- [ ] **Step 2: Update plan-review skill**

Change the "Plan Input" priority list item 1 from:
```
1. **Plan sidecar JSON** (`shield/plan.json`) — if present, use stories and AC from the sidecar
```
to:
```
1. **Named plan sidecar** (`shield/docs/plans/<name>.json`) — if name provided or only one plan exists. If multiple plans exist and no name given, list them and ask.
```

Update the "Always start by checking" line to reference `shield/docs/plans/`.

- [ ] **Step 3: Commit**

```bash
git add shield/commands/plan-review.md shield/skills/general/plan-review/SKILL.md
git commit -m "feat: plan-review accepts plan name, lists when ambiguous"
```

### Task 7: Update review command and skill

**Files:**
- Modify: `shield/commands/review.md`
- Modify: `shield/skills/general/review/SKILL.md`

- [ ] **Step 1: Update review command**

Change the AC verification reference from:
```
- Acceptance criteria verification (if story context from `{project_root}/shield/plan.json`)
```
to:
```
- Acceptance criteria verification (if story context from plans in `{project_root}/shield/docs/plans/`)
```

- [ ] **Step 2: Update review skill**

In "Load Prior Context", change:
```
- **Plan sidecar** — `shield/plan.json` for stories and acceptance criteria
```
to:
```
- **Plan sidecars** — `shield/docs/plans/*.json` for stories and acceptance criteria (reads all active plans)
```

In "Acceptance Criteria Verification", change to read AC from all plans in `shield/docs/plans/`.

- [ ] **Step 3: Commit**

```bash
git add shield/commands/review.md shield/skills/general/review/SKILL.md
git commit -m "feat: review reads AC from all named plans"
```

### Task 8: Update pm-sync skill

**Files:**
- Modify: `shield/skills/pm-sync/SKILL.md`

- [ ] **Step 1: Update rule 5**

Change from:
```
5. **Read the plan sidecar JSON** for story data — not raw HTML or plan docs.
```
to:
```
5. **Read the named plan sidecar JSON** (`shield/docs/plans/<name>.json`) for story data — not raw HTML or plan docs. If multiple plans exist and no name specified, list them and ask.
```

- [ ] **Step 2: Update workflows**

In "Creating Stories", change `pm_sync(epic="P1a")` to note that the plan name should be specified: `pm_sync(plan="auth-feature", epic="P1a")`.

- [ ] **Step 3: Commit**

```bash
git add shield/skills/pm-sync/SKILL.md
git commit -m "feat: pm-sync accepts plan name for named plans"
```

### Task 9: Update execute-steps skill and session-start hook

**Files:**
- Modify: `shield/skills/general/execute-steps/SKILL.md`
- Modify: `shield/hooks/scripts/session-start.sh`

- [ ] **Step 1: Update execute-steps**

Change the artifact paths table row from:
```
| Planning | `shield/plan.json` + ... |
```
to:
```
| Planning | `shield/docs/plans/<name>.json` + ... |
```

And the implementation row from:
```
| Implementation | Updates `shield/plan.json` status |
```
to:
```
| Implementation | Updates `shield/docs/plans/<name>.json` status |
```

- [ ] **Step 2: Update session-start hook**

Change the artifact output message from:
```
The `shield/plan.json` sidecar is updated in place (no timestamp).
```
to:
```
Named plan sidecars live at `shield/docs/plans/<name>.json` (updated in place, no timestamp).
```

- [ ] **Step 3: Commit**

```bash
git add shield/skills/general/execute-steps/SKILL.md shield/hooks/scripts/session-start.sh
git commit -m "feat: update execute-steps and session-start for named plans"
```

## Chunk 3: Update E2E Tests

### Task 10: Update fixture setup for named plans

**Files:**
- Modify: `shield/tests/e2e/fixtures/setup-fixture.sh`

- [ ] **Step 1: Change plan.json copy destination**

In the "Level 3: post-planning" block, change:
```bash
cp "$fixture_dir/plan.json" "$project_dir/shield/plan.json"
```
to:
```bash
mkdir -p "$project_dir/shield/docs/plans"
cp "$fixture_dir/plan.json" "$project_dir/shield/docs/plans/${example}.json"
```

This names the fixture plan after the example (e.g., `python-api.json`).

- [ ] **Step 2: Commit**

```bash
git add shield/tests/e2e/fixtures/setup-fixture.sh
git commit -m "test: fixture setup writes named plans to shield/docs/plans/"
```

### Task 11: Update plan phase assertions

**Files:**
- Modify: `shield/tests/e2e/phases/plan.sh`

- [ ] **Step 1: Update plan.json path in assertions**

Change the find command from:
```bash
sidecar=$(find "$project_dir/shield" -name "plan.json" -type f 2>/dev/null | head -1)
```
to:
```bash
sidecar=$(find "$project_dir/shield/docs/plans" -name "*.json" -type f 2>/dev/null | head -1)
```

Update the `assert_file_glob` or add one for `shield/docs/plans/*.json`.

- [ ] **Step 2: Commit**

```bash
git add shield/tests/e2e/phases/plan.sh
git commit -m "test: plan phase asserts named plans in shield/docs/plans/"
```

### Task 12: Update implement phase and test-implement.sh

**Files:**
- Modify: `shield/tests/e2e/phases/implement.sh` (no change needed — doesn't reference plan.json directly)
- Modify: `shield/tests/e2e/test-implement.sh`

- [ ] **Step 1: Update test-implement.sh**

Change the plan creation from:
```bash
mkdir -p "$PROJECT_DIR/shield"
cat > "$PROJECT_DIR/shield/plan.json" <<'EOF'
```
to:
```bash
mkdir -p "$PROJECT_DIR/shield/docs/plans"
cat > "$PROJECT_DIR/shield/docs/plans/vpc-module.json" <<'EOF'
```

Add `"name": "vpc-module"` to the JSON content.

- [ ] **Step 2: Commit**

```bash
git add shield/tests/e2e/test-implement.sh
git commit -m "test: test-implement uses named plan in shield/docs/plans/"
```

## Chunk 4: Migration and Backward Compatibility

### Task 13: Add migration note to /init command

**Files:**
- Modify: `shield/commands/init.md`

- [ ] **Step 1: Add migration logic**

If `shield/plan.json` exists (old path), suggest migrating:
```
Detected old-style plan sidecar at shield/plan.json.
Move to shield/docs/plans/<name>.json? [y/n]
```

Derive name from the `project` or `phase` field in the JSON.

- [ ] **Step 2: Commit**

```bash
git add shield/commands/init.md
git commit -m "feat: init detects and offers to migrate old plan.json"
```

### Task 14: Add fallback to old path in readers

**Files:**
- Modify: `shield/skills/general/implement-feature/SKILL.md`

- [ ] **Step 1: Add fallback note**

In the "From plan sidecar" section, after searching `shield/docs/plans/*.json`, add:
```
If no plans found in `shield/docs/plans/`, check for legacy `shield/plan.json` and suggest migration.
```

This is a one-line addition to the implement-feature skill only — other readers already fall back through their priority lists.

- [ ] **Step 2: Commit**

```bash
git add shield/skills/general/implement-feature/SKILL.md
git commit -m "feat: implement-feature falls back to legacy shield/plan.json"
```
