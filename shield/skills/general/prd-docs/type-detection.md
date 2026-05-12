# PRD Type Detection

How `/prd` (and `/prd-review` ingest) determines whether a PRD is `standard` or `lean`.

## Detection rules

Parse the PRD's top-level `## <N>. <section name>` headings:

1. **Lean** — only these headings present:
   - Header
   - Problem & context
   - Target users / personas
   - Goals & non-goals
   - Success metrics
   - Open questions
   - Out of scope / Non-goals

2. **Standard** — at least 12 of the 18 numbered standard sections present (sections 6 through 17 are the load-bearing standard-only sections; presence of any 4+ implies standard intent)

3. **Custom** — heading set doesn't match either pattern. Treat as standard for grading purposes; user can override.

## Override flow

After auto-detection, ALWAYS confirm with the user:

```
"This looks like a {type} PRD ({reason}). Apply {type} treatment? (yes / lean / standard)"
```

User can override. Override is recorded in `prd.meta.json.type`.

## Edge cases

- **Empty PRD** (just header): treated as in-progress; type defaults to standard
- **Lean PRD with one extra section** (e.g., Risks added): treated as still lean structurally but flag that it's drifting; user can override
- **Standard PRD missing a section** (e.g., GTM section omitted): treated as standard, missing-section flagged by `/prd-review` rubric
- **Heading variations** (e.g., "## 1. Header" vs "## Header"): normalize by stripping leading numbering before matching
