---
name: render
description: Build the browsable Shield HTML site locally from committed Markdown
args: "[output dir — optional, defaults to docs/shield]"
---

# Render Shield Output

Shield commits Markdown + JSON sidecars only. HTML (per-artifact pages and the
browsable dashboard) is a **local build artifact** — gitignored and regenerated
on demand. Run this command to (re)build the site, then open the HTML locally.

## Usage

`/shield render` — rebuild the whole site under `docs/shield/`
`/shield render <output dir>` — rebuild a site rooted at a custom dir

## Behavior

1. Run the build script, which renders every source `.md` to its
   `outputs/*.html` and then writes the dashboard (`index.html`) and shared
   assets (`manifest.js`, CSS, nav JS):

   ```bash
   "$CLAUDE_PLUGIN_ROOT/scripts/render-output.sh" "$ARGUMENTS"
   ```

   (`$ARGUMENTS` is empty for the default `docs/shield/` location.)

2. Report the built site path and remind the user the output is gitignored —
   open `docs/shield/index.html` in a browser to view.

## Important

- This command does NOT author or modify any Markdown — it only renders.
- HTML is never committed; do not `git add` anything under `outputs/` or the
  generated root assets.
