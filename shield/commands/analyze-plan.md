---
name: analyze-plan
description: Analyze terraform plan output for security, cost, and destructive action impact
args: "[path to plan JSON]"
outputs:
  - review_summary    # review_type=code (treat Terraform-plan analysis as a code-review variant)
  - review_summary_html
---

# Analyze Terraform Plan

Analyze `terraform plan -json` output for security, cost, and operational impact.

## Usage

`/analyze-plan [path to plan JSON]`

## Paths

Writes registry-tracked paths under `{review_dir}` = `{output_dir}/{feature}/reviews/code/{date}{_counter}` (review_type=code). See `shield/schema/output-paths.yaml` and the counter-resolution rule in `/review`. Only `{review_summary}` (+ its HTML render) is declared — analyze-plan does not dispatch detailed reviewer subagents.

## Behavior

1. Detect the component (src/ vs components/terraform/)
2. Locate or generate plan:
   - User-provided JSON path
   - Existing .tfplan file
   - Or offer to run `terraform plan -json` (NEVER `terraform apply`)
3. Invoke `shield:terraform:plan-analysis` skill
4. The skill analyzes: change summary, destructive actions, security changes, cost impact, drift
5. Determine `{feature}` (current feature directory name; if none exists yet, derive from current context + `-YYYYMMDD`). Resolve `{date}{_counter}` per the counter rule in `/review`.
6. Write the report to `{review_summary}` = `{output_dir}/{feature}/reviews/code/{date}{_counter}/summary.md`
7. Render `{review_summary_html}` under `{output_dir}/{feature}/outputs/reviews/code/{date}{_counter}/summary.html`
8. Present summary with flagged items

## Important

- NEVER run `terraform apply`
- Use `-lock=false` when generating plans
- Flag destructive actions (destroy, replace) prominently
- Numbered run subfolders are gone — runs are date-keyed under `{review_dir}` and never overwrite
