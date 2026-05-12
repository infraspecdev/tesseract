# PRD Review — Ingest Pipeline

Classify input, route to a resolver, snapshot the resolved content to `source-prd.md`.

## Step 1: Classify the input

| Class | Detection rule | Handler |
|---|---|---|
| **Local file** | First arg matches `^/` or `^\./` or doesn't match `^https?://` AND is a path to an existing file | Read tool |
| **HTTP(S) URL** | First arg matches `^https?://` | Resolver chain (Step 2) |
| **Paste** | No first arg, OR first arg is `--paste`, OR the user pasted content into the prompt | Read from prompt directly |

If classification ambiguous (e.g., a relative path that's also a valid URL), prefer local-file classification — explicit URL prefix is required for URL handling.

## Step 2: Resolver chain (URLs only)

Walk the resolvers in order. Stop at the first one that returns content.

### Resolver order

1. **Custom resolvers from `.shield.json`** (`prd_ingest_resolvers` array) — matched first
2. **Internal known-host map** (below) — matched second
3. **WebFetch** — catch-all for any HTTP(S) URL (public pages only)
4. **Paste fallback** — if all above fail, prompt the user to paste content

### Internal known-host map (Shield-side knowledge — not config)

| URL pattern | MCP-name pattern Shield searches for at runtime | If MCP absent |
|---|---|---|
| `notion.so/*` or `*.notion.so/*` | `*notion*` (e.g., `notion-fetch`) | Fall through to WebFetch |
| `*.atlassian.net/wiki/*` | `*atlassian*` or `*confluence*` | Fall through to WebFetch |
| `docs.google.com/document/*` | `*google*drive*` or `*google*docs*` | Fall through to WebFetch |
| `github.com/*/blob/*` (any file) | (no MCP needed) | Use `gh api` via Bash directly |
| anything else (https) | (no map entry) | Fall through to WebFetch |

### Resolution flow per URL

1. Match URL against `prd_ingest_resolvers` config first
2. Match URL against internal known-host map
3. If matched, check whether the corresponding MCP is currently available
   - Available → call MCP, return content as markdown
   - Not available → log specific error ("MCP `*atlassian*` not present"), continue to step 4
4. Try WebFetch on the URL
   - Returns content → convert to markdown if needed, return
   - Returns 4xx/5xx or network error → log, continue to step 5
5. Paste fallback — emit to user: "Couldn't fetch from <URL> (reason: <X>). Paste the PRD content here." Then read pasted content.

## Step 3: Convert to markdown + snapshot

Regardless of source class, normalize output to markdown:
- Local file: if `.md`/`.txt` → as-is; if `.pdf` → use Read tool's PDF handling; if `.docx` → paste fallback (DOCX not natively supported)
- URL response: if `Content-Type: text/html` → strip and convert; if already markdown → as-is
- Paste: as-is

Write the result to `{output_dir}/{feature}/prd-review/{N}-{slug}/source-prd.md`. This snapshot is the canonical input to all reviewer agents.

## Step 4: PRD type detection (lean vs standard)

After snapshot, parse `source-prd.md` for top-level `##` headings:

- If headings ⊆ {Header, Problem, Users, Goals, Metrics, Open Questions, Out of scope} → likely **lean**
- If 8+ standard-scaffold sections present → likely **standard**
- Otherwise → likely **standard** (default; lean is opt-in by structural minimalism)

Surface detection result + confirm:

> "This looks like a **standard** PRD (detected sections: Header, Problem, Users, Goals, Metrics, Stories, FRs, NFRs, Rollout, Risks, Out of scope). Apply standard rubric? (yes / lean / standard)"

User can override.

## Failure flow (uniform across resolvers)

When any resolver fails — MCP unavailable, network error, parse error, auth required:
1. Emit specific error: "Notion MCP not authenticated" / "URL returned 403" / "Atlassian MCP not present in session"
2. Offer paste fallback in the same turn
3. User pastes content → continue normally
4. If user declines, abort with clear message; do NOT produce a partial review

## See Also

- `SKILL.md` Step 1 calls into this file's Step 1
- `rubric.md` — the rubric used downstream of ingest
