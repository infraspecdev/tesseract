---
name: lld
description: Generate or update a component-scoped Low-Level Design document. Path A — writes to docs/lld/<component>.md. Backend + infra templates with stable kebab-case anchors and §14 Changelog.
args: "[<component>] [--type backend|infra]"
# No outputs declared: /lld writes to docs/lld/<component>.md at the repo root,
# which is project-level and intentionally outside output_dir (shield/schema/output-paths.yaml
# registers lld_canonical_md as such). Path B drafts at docs/shield/{feature}/lld-{component}.md
# are emitted by /plan, not /lld.
---

# LLD

Generate or update a component-scoped Low-Level Design document.

## Usage

`/lld [<component>] [--type backend|infra]`

- `<component>` — kebab-case component identifier (matches the file
  `docs/lld/<component>.md`). When omitted, bare `/lld` scans the repo for
  component-shaped directories and presents undocumented candidates.
- `--type backend|infra` — selects the LLD template variant. When omitted,
  the type is inferred from repo markers at the component's directory path
  (`pyproject.toml` / `package.json` / `pom.xml` / `go.mod` → backend; `*.tf`
  / `Chart.yaml` / `kustomization.yaml` / `atmos.yaml` → infra). Ambiguous
  detection (both backend and infra markers in the component dir) prompts
  the user.

## Paths

This command writes the following registry-tracked path:

| Registry key | Resolved path |
|---|---|
| `lld_canonical_md` | `docs/lld/<component>.md` |

Path A (this command) always writes to the canonical path. Path B
(`/plan` TRD-driven authoring, M2 plan) drafts to `docs/shield/<feature>/lld-<component>.md`
and `/implement` promotes the draft to the canonical path at milestone close
(M2 plan, step 5h).

## Output Paths — MANDATORY

Find the project root by locating `.shield.json`. The canonical LLD path is
**always** `<project_root>/docs/lld/<component>.md` — independent of
`.shield.json` `output_dir` (which controls `docs/shield/` only, not `docs/lld/`).

Write via the lld-docs skill's atomic-write contract: `<target>.tmp` → rename
to `<target>`. On failure, remove `.tmp` and surface error.

**Do NOT** write to `docs/shield/<feature>/`. **Do NOT** write to any other
location. **Do NOT** silently clobber an existing populated `docs/lld/<component>.md`
— see "Re-run behavior" below.

## Behavior

1. If `<component>` is provided, use it (must match `^[a-z0-9-]+$`).
2. If `<component>` is omitted, scan the project root for component-shaped
   directories:
   - top-level dirs with `pyproject.toml` (Python packages)
   - top-level dirs with `package.json` (Node packages)
   - top-level dirs with `pom.xml` or `build.gradle*` (JVM modules)
   - top-level dirs with `go.mod` (Go modules)
   - top-level dirs with `*.tf` files (terraform modules)
   - dirs with `Chart.yaml` (helm charts)
   - dirs with `kustomization.yaml` (kustomize bases)

   Subtract names that already have a matching `docs/lld/<name>.md`. Present
   the remaining list to the user; the user picks one.

   If the scan finds zero candidates, error out with a friendly hint:
   *"No undocumented component-shaped directories found. Pass an explicit
   `<component>` name or initialize a service/module first."*

3. Resolve `--type`:
   - `--type` flag → use it.
   - Walk the component's directory (if it exists in the repo) for markers
     in the order listed in step 2.
   - On ambiguous markers (both backend and infra signals in the same dir),
     prompt the user to pick.
   - If the component directory doesn't exist in the repo (reverse-doc for
     planned-but-not-yet-built component), and `--type` is missing, prompt.

4. Active-feature-folder overlap check:
   - Walk `docs/shield/*/plan.json`.
   - If any sidecar has `lld_components[]` containing an entry where
     `name == <component>`, print a non-blocking warning:

     *"WARNING: component `<component>` is being planned in feature
     `<feature-folder>`; this canonical write will be merged on next /plan.
     Proceeding."*

5. Invoke the lld-docs skill with:
   - `component = <component>`
   - `type = <resolved type>`
   - `mode = draft` if `docs/lld/<component>.md` is absent; `draft` (which
     becomes edit-in-place per the skill's failure-mode contract) if present.
   - `target_path = docs/lld/<component>.md`
   - `context = {}` (Path A has no plan/PRD/research context to inject)

6. On success, print a summary:
   ```
   /lld <component> — <new | edited>
   Path: docs/lld/<component>.md
   Type: <backend|infra>
   Template: lld-template-<type>.md
   Sections populated (non-empty): <N>
   Sections declaring 'n/a': <M>
   ```

## Re-run behavior

When `/lld` is invoked for a component that already has `docs/lld/<component>.md`,
the lld-docs skill operates in edit-in-place mode:
- The existing content is preserved.
- A `manual | YYYY-MM-DD | edit by <owner> | n/a` row is appended to §14
  Changelog.
- The Status header is left unchanged.

`/lld` never deletes a populated `docs/lld/<component>.md`.

## Rollback triggers

Revert this command (and roll back the marketplace version bump that lands
with it in M3) when any of:

- The `lld-docs` eval fails on any positive fixture in a subsequent CI run.
- Two or more user-reported `/lld` runs produce a file that fails the
  lld-docs eval against unchanged content.
- The atomic-write contract leaks a `.tmp` file in normal operation
  (filesystem-level failure to clean up).

Rollback procedure: revert the cutover commits, re-publish the prior
marketplace version, and re-run the lld-docs eval on the prior fixture set
to confirm GREEN.
