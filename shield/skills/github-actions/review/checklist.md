# GitHub Actions Review Checklist

Detailed checklist items for evaluating GitHub Actions workflows.

## 1. Cross-Workflow Version Consistency

Check that shared tools use the same version everywhere:

| What to Check | Where to Look |
|----------------|---------------|
| **Release tooling version** | All workflows using release-please (`googleapis/release-please-action@v4`) or semantic-release (action `semantic_version`, npx `--package` version) |
| **Node.js version** | `actions/setup-node`, env vars, action defaults |
| **Terraform version** | `hashicorp/setup-terraform`, `versions.tf` constraint |
| **Action versions** | Same action should use same version tag across workflows |

**Red flag:** Preview workflow uses a different release tool version than the actual release workflow — version prediction may differ from actual release.

## 2. Plugin and Config Alignment

**For release-please repos:**
- Verify `release-please-config.json` and `.release-please-manifest.json` exist and are consistent (same set of components)
- Check that the release workflow and preview workflow reference the same config/manifest files
- Ensure all components under `components/terraform/` are registered in the config — missing components won't get versioned

**For semantic-release repos:**
- Verify both install the **same set of plugins** that `.releaserc.json` (or equivalent config) expects
- Check that plugin versions are consistent between `extra_plugins` and npx `--package` flags
- If config file exists (`.releaserc.json`), both workflows should respect it — not override with CLI flags unless intentional

**Red flag:** A component directory exists under `components/terraform/` but is not listed in `release-please-config.json` packages — it will never get a version tag.

## 3. Permissions (Least Privilege)

Every workflow and job should declare only the permissions it needs:

| Operation | Minimum Permission |
|-----------|-------------------|
| Read code | `contents: read` |
| Push commits/tags | `contents: write` |
| Comment on PR | `pull-requests: write` |
| Update check status | `statuses: write` |
| Read PR metadata | `pull-requests: read` |

**Checks:**
- Prefer job-level `permissions` over workflow-level (narrower scope)
- Dry-run / read-only workflows should NOT have `contents: write` unless the tool requires it for auth
- Never use `permissions: write-all` — always enumerate

## 4. Concurrency Control

**PR workflows — cancel superseded runs:**

```yaml
concurrency:
  group: ${{ github.workflow }}-${{ github.event.pull_request.number || github.ref }}
  cancel-in-progress: true
```

Apply to all `pull_request` triggered workflows — rapid pushes shouldn't queue up.

**Release/deploy workflows — queue, never cancel:**

```yaml
concurrency:
  group: release
```

Without `cancel-in-progress` (defaults to `false`), subsequent runs **wait in queue** until the current run finishes. This prevents:
- Two parallel runs racing to create the same version tag
- Conflicting changelog commits from `@semantic-release/git`
- Lost releases from cancelled mid-run workflows

**Red flag:** Release workflow on `main` with no `concurrency` group — runs execute in parallel by default, creating race conditions on tag creation and changelog commits.

**When NOT to apply `cancel-in-progress: true`:**
- Release/deploy workflows on `main`/`production` — cancelling mid-release is dangerous
- Workflows that perform destructive operations

## 5. Path Filters

Check that workflows only trigger when relevant files change:

| Workflow Type | Suggested Paths |
|---------------|-----------------|
| Terraform validation | `components/**`, `.github/workflows/**` |
| Release (actual) | `components/**` |
| Release preview | `components/**` (skip for docs-only PRs) |
| PR title check | No path filter needed (all PRs need valid titles) |
| Docs generation | `docs/**`, `*.md` |

**Red flag:** Release preview runs on ALL PRs including docs-only changes — wastes CI minutes on PRs that won't trigger a release.

## 6. Reusable Workflow Patterns

Check for DRY violations:

- If the same logic (validation, linting) appears in multiple workflows, extract to a reusable workflow with `workflow_call` trigger
- Caller workflows should use `needs:` to gate dependent jobs
- Reusable workflows should NOT have hardcoded triggers — let callers decide when to run

## 7. Action Pinning

| Strategy | Security | Maintenance | Recommended For |
|----------|----------|-------------|-----------------|
| SHA pin (`@abc123`) | Best | Hardest | High-security repos, supply chain concerns |
| Version tag (`@v4.1.2`) | Good | Medium | Repos that want reproducibility |
| Major tag (`@v4`) | OK | Easiest | Most repos (default GitHub convention) |

**Minimum:** Major tag pinning (`@v4`). For third-party actions from less-known publishers, prefer version tag or SHA.

## 8. Environment and Secrets

- `GITHUB_TOKEN` should be passed via `env:` not `with:` for most actions (check action docs)
- Don't use `secrets.GITHUB_TOKEN` where the default `github.token` suffices
- Avoid hardcoding bot names/emails if they can be derived from the action

## Grading Scale

| Grade | Meaning |
|-------|---------|
| **A** | All checks pass, consistent versions, least-privilege permissions, concurrency controls |
| **B** | Minor inconsistencies, missing concurrency or path filters, but functionally correct |
| **C** | Version drift or plugin mismatches that could cause different behavior between workflows |
| **D** | Security issues (overly broad permissions), missing validation gates, broken plugin configs |
| **F** | Workflows contradict each other, missing critical permissions, or fundamentally broken |
