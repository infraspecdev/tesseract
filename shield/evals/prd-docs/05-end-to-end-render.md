---
name: 05-end-to-end-render
skill_under_test: shield:prd-docs
scenario: After /prd writes prd.md and prd.html, verify the rendered HTML has all new affordances
---

## Setup
```bash
mkdir -p docs/shield/render-e2e-20260522
cat > .shield.json <<'EOF'
{ "output_dir": "docs/shield" }
EOF
```

## Prompt
> Author a standard PRD for the feature folder "render-e2e-20260522" (topic: cache-warm-on-deploy) using the shield:prd-docs skill. Include at least one Mermaid block in §5 Architecture & flows. Write outputs to the v2 flat-path layout — prd.md at `docs/shield/render-e2e-20260522/prd.md` and the rendered prd.html at `docs/shield/render-e2e-20260522/outputs/prd.html`. Do NOT use numbered-run subfolders (no `prd/{N}-{slug}/`). Confirm by printing the path to prd.html and the first 80 lines of prd.html.

## Success criteria

### Structural
- <nav class="toc">
- <a href="#2-terminologies">2. Terminologies
- <a href="#5-architecture.{1,2}flows">5. Architecture
- <a href="#8-user-stories.{1,2}scenarios">8. User stories
- <pre class="mermaid">
- (Type:|<strong>Type</strong>)

### Qualitative
- The TOC links match the document's actual h2 headings (no dangling or missing entries).
- At least one story renders the Type field in the HTML output.

## Pass threshold
6 of 6 structural + 2 of 2 qualitative.
