# Shield Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the Shield plugin directory structure, config system, schemas, hooks, and init/migrate commands — the foundation everything else builds on.

**Architecture:** Create the `shield/` plugin directory within the Tesseract marketplace. Migrate the marketplace.json to point at Shield. Set up the `~/.tesseract/` config system with JSON schema validation. Port and adapt hooks from infra-review. Build `/shield init` and `/shield migrate` commands.

**Tech Stack:** Markdown (commands, skills), JSON (schemas, config), Bash (hooks, scripts), Python (MCP server config resolution)

---

## Chunk 1: Repo Scaffolding

### Task 1: Create Shield plugin directory structure

**Files:**
- Create: `shield/.claude-plugin/plugin.json`
- Create: `shield/skills/general/.gitkeep`
- Create: `shield/skills/terraform/.gitkeep`
- Create: `shield/skills/atmos/.gitkeep`
- Create: `shield/skills/github-actions/.gitkeep`
- Create: `shield/agents/.gitkeep`
- Create: `shield/commands/.gitkeep`
- Create: `shield/hooks/scripts/.gitkeep`
- Create: `shield/adapters/clickup/.gitkeep`
- Create: `shield/schemas/.gitkeep`
- Create: `shield/config-examples/.gitkeep`
- Create: `shield/examples/terraform-vpc/.gitkeep`
- Create: `shield/examples/python-api/.gitkeep`
- Create: `shield/tests/.gitkeep`
- Create: `shield/evals/inputs/.gitkeep`
- Create: `shield/evals/expected/.gitkeep`

- [ ] **Step 1: Create the shield plugin directory tree**

```bash
mkdir -p shield/.claude-plugin
mkdir -p shield/skills/{general,terraform,atmos,github-actions}
mkdir -p shield/agents
mkdir -p shield/commands
mkdir -p shield/hooks/scripts
mkdir -p shield/adapters/clickup
mkdir -p shield/schemas
mkdir -p shield/config-examples
mkdir -p shield/examples/{terraform-vpc,python-api}
mkdir -p shield/tests
mkdir -p shield/evals/{inputs,expected}
```

- [ ] **Step 2: Create plugin.json with permissions**

Create `shield/.claude-plugin/plugin.json`:

```json
{
  "name": "shield",
  "description": "Unified SDLC plugin — research, planning, PM integration, implementation, and continuous review with multi-domain support and specialist agents.",
  "author": {
    "name": "Ashwini Manoj"
  },
  "repository": "https://github.com/infraspecdev/tesseract",
  "license": "MIT",
  "keywords": [
    "sdlc", "review", "security", "cost", "architecture", "operations",
    "terraform", "atmos", "clickup", "sprint", "planning", "research",
    "implementation", "tdd", "well-architected", "infrastructure"
  ],
  "permissions": {
    "allow": [
      "Read(${CLAUDE_PLUGIN_ROOT}/**)",
      "Glob(${CLAUDE_PLUGIN_ROOT}/**)",
      "Grep(${CLAUDE_PLUGIN_ROOT}/**)"
    ]
  }
}
```

- [ ] **Step 3: Commit**

```bash
git add shield/
git commit -m "feat: scaffold shield plugin directory structure

Create the shield/ plugin directory with subdirectories for skills
(general, terraform, atmos, github-actions), agents, commands,
hooks, adapters, schemas, examples, tests, and evals. Add plugin.json
with read permissions for the plugin's own directory."
```

### Task 2: Update marketplace.json to point at Shield

**Files:**
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Update marketplace.json**

Replace the three old plugin entries with a single Shield entry. Keep the old entries commented out is not possible in JSON, so replace entirely:

```json
{
  "$schema": "https://anthropic.com/claude-code/marketplace.schema.json",
  "name": "tesseract",
  "description": "Claude Code plugin marketplace for the software development lifecycle",
  "owner": {
    "name": "Ashwini Manoj"
  },
  "plugins": [
    {
      "name": "shield",
      "description": "Unified SDLC plugin — research, planning, PM integration, implementation, and continuous review with multi-domain support and specialist agents",
      "version": "2.0.0",
      "source": "./shield",
      "category": "development"
    }
  ]
}
```

- [ ] **Step 2: Commit**

```bash
git add .claude-plugin/marketplace.json
git commit -m "feat: update marketplace to point at shield plugin

Replace the three separate plugin entries (infra-review,
clickup-sprint-planner, dev-workflow) with a single shield entry.
Bump version to 2.0.0 for the major restructure."
```

### Task 3: Update .gitignore for new structure

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Update .gitignore**

Add Shield-specific ignores while keeping existing ones:

```gitignore
# Python
__pycache__/
*.py[cod]
.venv/
*.egg-info/

# Config files with sensitive data
clickup-sprint-planner/examples/sprint-planner.json
clickup-sprint-planner/phases/

# Environment files
.env*

# Local dev settings
**/.claude/settings.local.json

# OS
.DS_Store

# IDE
.idea/
.vscode/

# Shield — generated at runtime by session-start hook
shield/.mcp.json

# Superpowers brainstorming sessions (visual companion artifacts)
.superpowers/
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: update gitignore for shield plugin structure"
```

### Task 4: Add release workflow

**Files:**
- Create: `.github/workflows/release.yml`

- [ ] **Step 1: Create release workflow**

A custom GitHub Actions workflow that detects version changes in `marketplace.json` on push to main. If a plugin version was bumped, it creates a git tag and GitHub Release for that plugin.

Create `.github/workflows/release.yml`:

```yaml
name: Release
on:
  push:
    branches: [main]

permissions:
  contents: write

jobs:
  check-release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
        with:
          fetch-depth: 2

      - name: Detect version changes and create releases
        run: |
          # Get marketplace.json from current and previous commit
          CURRENT=$(cat .claude-plugin/marketplace.json)
          PREVIOUS=$(git show HEAD~1:.claude-plugin/marketplace.json 2>/dev/null || echo '{"plugins":[]}')

          # Compare each plugin's version
          echo "$CURRENT" | jq -r '.plugins[] | "\(.name) \(.version)"' | while read -r name version; do
            prev_version=$(echo "$PREVIOUS" | jq -r --arg n "$name" '.plugins[] | select(.name == $n) | .version // "0.0.0"')

            if [ "$version" != "$prev_version" ]; then
              echo "Version changed for $name: $prev_version -> $version"
              TAG="${name}-v${version}"

              # Check if tag already exists
              if git rev-parse "$TAG" >/dev/null 2>&1; then
                echo "Tag $TAG already exists, skipping"
                continue
              fi

              # Create tag
              git tag "$TAG"
              git push origin "$TAG"

              # Build release notes from git log since last tag for this plugin
              PREV_TAG=$(git tag -l "${name}-v*" --sort=-v:refname | head -2 | tail -1)
              if [ -n "$PREV_TAG" ] && [ "$PREV_TAG" != "$TAG" ]; then
                NOTES=$(git log --pretty=format:"- %s" "${PREV_TAG}..HEAD" -- "${name}/")
              else
                NOTES="Initial release"
              fi

              # Create GitHub Release
              gh release create "$TAG" \
                --title "${name} v${version}" \
                --notes "$NOTES" \
                --target main
            fi
          done
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

- [ ] **Step 2: Commit**

```bash
mkdir -p .github/workflows
git add .github/workflows/release.yml
git commit -m "ci: add version-based release workflow

Detects version changes in marketplace.json on push to main.
Creates git tags and GitHub Releases with commit-based release
notes for each plugin whose version was bumped."
```

## Chunk 2: JSON Schemas and Config Examples

### Task 5: Create config JSON schema

**Files:**
- Create: `shield/schemas/config.schema.json`

- [ ] **Step 1: Create config schema**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Shield Global Config",
  "description": "Global configuration for the Shield plugin (~/.tesseract/config.json)",
  "type": "object",
  "properties": {
    "reviewers": {
      "type": "object",
      "properties": {
        "auto_select": {
          "type": "boolean",
          "default": true,
          "description": "Automatically select reviewers based on content"
        },
        "always_include": {
          "type": "array",
          "items": { "type": "string" },
          "default": [],
          "description": "Reviewers that always run regardless of auto-detection"
        },
        "never_include": {
          "type": "array",
          "items": { "type": "string" },
          "default": [],
          "description": "Reviewers that are skipped even if auto-detected"
        }
      },
      "additionalProperties": false
    },
    "pm_tool": {
      "type": "string",
      "enum": ["clickup", "jira", "none"],
      "default": "none",
      "description": "Active PM tool adapter"
    },
    "review_on_commit": {
      "type": "object",
      "properties": {
        "enabled": {
          "type": "boolean",
          "default": false,
          "description": "Enable pre-commit code review"
        },
        "block_threshold": {
          "type": "string",
          "enum": ["critical", "important", "warning", "none"],
          "default": "critical",
          "description": "Severity level that blocks commits"
        },
        "warn_threshold": {
          "type": "string",
          "enum": ["critical", "important", "warning", "none"],
          "default": "important",
          "description": "Severity level that prints warnings"
        }
      },
      "additionalProperties": false
    },
    "defaults": {
      "type": "object",
      "properties": {
        "plan_format": {
          "type": "string",
          "enum": ["html", "markdown"],
          "default": "html"
        },
        "summary_detail": {
          "type": "string",
          "enum": ["concise", "detailed"],
          "default": "concise"
        }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 2: Commit**

```bash
git add shield/schemas/config.schema.json
git commit -m "feat: add config JSON schema

Schema for ~/.tesseract/config.json covering reviewer selection,
PM tool choice, review-on-commit thresholds, and default settings."
```

### Task 6: Create project marker JSON schema

**Files:**
- Create: `shield/schemas/tesseract.schema.json`

- [ ] **Step 1: Create project marker schema**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Tesseract Project Marker",
  "description": "Project configuration file (.tesseract.json) committed to the repo",
  "type": "object",
  "required": ["project", "domains"],
  "properties": {
    "project": {
      "type": "string",
      "description": "Project name — used as key in ~/.tesseract/projects/"
    },
    "domains": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "minItems": 1,
      "description": "Active domains for this project (e.g., terraform, atmos, python)"
    },
    "external_skills": {
      "type": "object",
      "description": "External plugin skills mapped to phases",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "research": { "type": "array", "items": { "type": "string" } },
          "plan": { "type": "array", "items": { "type": "string" } },
          "implement": { "type": "array", "items": { "type": "string" } },
          "review": { "type": "array", "items": { "type": "string" } },
          "debug": { "type": "array", "items": { "type": "string" } }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 2: Commit**

```bash
git add shield/schemas/tesseract.schema.json
git commit -m "feat: add project marker JSON schema

Schema for .tesseract.json covering project name, active domains,
and external plugin skill mappings."
```

### Task 7: Create PM config JSON schema

**Files:**
- Create: `shield/schemas/pm.schema.json`

- [ ] **Step 1: Create PM config schema**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Shield PM Config",
  "description": "Project-specific PM adapter configuration (~/.tesseract/projects/<project>/pm.json)",
  "type": "object",
  "required": ["adapter"],
  "properties": {
    "adapter": {
      "type": "string",
      "description": "PM adapter name (e.g., clickup, jira)"
    },
    "adapter_mode": {
      "type": "string",
      "enum": ["native", "hybrid", "full"],
      "default": "hybrid",
      "description": "Adapter tier: native (Tier 1), hybrid (Tier 2), full (Tier 3)"
    },
    "workspace_id": {
      "type": "string",
      "description": "PM workspace identifier"
    },
    "space_id": {
      "type": "string",
      "description": "PM space/project identifier"
    },
    "naming": {
      "type": "object",
      "properties": {
        "project_prefix": {
          "type": "string",
          "description": "Prefix for task naming (e.g., PROJ)"
        },
        "story_format": {
          "type": "string",
          "default": "[{prefix}] {epic_id}-S{index}: {name}",
          "description": "Template for story/task names"
        }
      },
      "additionalProperties": false
    },
    "tool_mapping": {
      "type": "object",
      "description": "Tier 1 only: maps pm_* tool names to native MCP tool names",
      "additionalProperties": { "type": "string" }
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 2: Commit**

```bash
git add shield/schemas/pm.schema.json
git commit -m "feat: add PM adapter config JSON schema

Schema for ~/.tesseract/projects/<project>/pm.json covering
adapter selection, tier mode, workspace config, naming conventions,
and Tier 1 tool name mapping."
```

### Task 8: Create plan sidecar JSON schema

**Files:**
- Create: `shield/schemas/plan-sidecar.schema.json`

- [ ] **Step 1: Create sidecar schema**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Shield Plan Sidecar",
  "description": "Machine-readable plan data — source of truth for stories, AC, and status",
  "type": "object",
  "required": ["version", "project", "epics"],
  "properties": {
    "version": {
      "type": "string",
      "const": "1.0"
    },
    "project": {
      "type": "string",
      "description": "Project name"
    },
    "phase": {
      "type": "string",
      "description": "Phase name (e.g., Phase 3 — Multi-Region Networking)"
    },
    "epics": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "name", "stories"],
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string" },
          "stories": {
            "type": "array",
            "items": {
              "type": "object",
              "required": ["id", "name", "status", "tasks", "acceptance_criteria"],
              "properties": {
                "id": { "type": "string" },
                "name": { "type": "string" },
                "status": {
                  "type": "string",
                  "enum": ["draft", "ready", "in-progress", "in-review", "done", "blocked"]
                },
                "assignee": { "type": ["string", "null"] },
                "priority": {
                  "type": "string",
                  "enum": ["urgent", "high", "normal", "low"]
                },
                "week": { "type": ["string", "null"] },
                "description": { "type": "string" },
                "tasks": {
                  "type": "array",
                  "items": { "type": "string" }
                },
                "acceptance_criteria": {
                  "type": "array",
                  "items": { "type": "string" }
                },
                "pm_id": { "type": ["string", "null"] },
                "pm_url": { "type": ["string", "null"] }
              }
            }
          }
        }
      }
    },
    "metadata": {
      "type": "object",
      "properties": {
        "created_at": { "type": "string", "format": "date" },
        "domains": {
          "type": "array",
          "items": { "type": "string" }
        },
        "reviewer_grades": {
          "type": "object",
          "additionalProperties": { "type": "string" }
        }
      }
    }
  },
  "additionalProperties": false
}
```

- [ ] **Step 2: Commit**

```bash
git add shield/schemas/plan-sidecar.schema.json
git commit -m "feat: add plan sidecar JSON schema

Schema for plan-sidecar.json covering epics, stories, tasks,
acceptance criteria, status, assignees, and PM integration fields."
```

### Task 9: Create credentials JSON schema

**Files:**
- Create: `shield/schemas/credentials.schema.json`

- [ ] **Step 1: Create credentials schema**

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "Shield Credentials",
  "description": "PM tool API tokens (~/.tesseract/credentials.json) — never commit this file",
  "type": "object",
  "properties": {
    "clickup": {
      "type": "object",
      "properties": {
        "api_token": { "type": ["string", "null"] }
      },
      "additionalProperties": false
    },
    "jira": {
      "type": "object",
      "properties": {
        "api_token": { "type": ["string", "null"] },
        "base_url": { "type": ["string", "null"] }
      },
      "additionalProperties": false
    }
  },
  "additionalProperties": {
    "type": "object",
    "description": "Future PM tool credentials"
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add shield/schemas/credentials.schema.json
git commit -m "feat: add credentials JSON schema

Schema for ~/.tesseract/credentials.json covering PM tool API
tokens. This file should never be committed to a repository."
```

### Task 10: Create config example files

**Files:**
- Create: `shield/config-examples/tesseract.example.json`
- Create: `shield/config-examples/config.example.json`
- Create: `shield/config-examples/pm-clickup.example.json`
- Create: `shield/config-examples/credentials.example.json`

- [ ] **Step 1: Create project marker example**

`shield/config-examples/tesseract.example.json`:

```json
{
  "project": "my-project",
  "domains": ["terraform", "atmos"],
  "external_skills": {
    "general": {
      "implement": ["superpowers:test-driven-development"],
      "review": ["superpowers:verification-before-completion"]
    },
    "terraform": {
      "review": ["terraform-skills:validate"]
    }
  }
}
```

- [ ] **Step 2: Create global config example**

`shield/config-examples/config.example.json`:

```json
{
  "reviewers": {
    "auto_select": true,
    "always_include": ["security"],
    "never_include": []
  },
  "pm_tool": "clickup",
  "review_on_commit": {
    "enabled": false,
    "block_threshold": "critical",
    "warn_threshold": "important"
  },
  "defaults": {
    "plan_format": "html",
    "summary_detail": "concise"
  }
}
```

- [ ] **Step 3: Create PM config example**

`shield/config-examples/pm-clickup.example.json`:

```json
{
  "adapter": "clickup",
  "adapter_mode": "hybrid",
  "workspace_id": "YOUR_WORKSPACE_ID",
  "space_id": "YOUR_SPACE_ID",
  "naming": {
    "project_prefix": "PROJ",
    "story_format": "[{prefix}] {epic_id}-S{index}: {name}"
  }
}
```

- [ ] **Step 4: Create credentials example**

`shield/config-examples/credentials.example.json`:

```json
{
  "clickup": {
    "api_token": "pk_YOUR_TOKEN_HERE"
  }
}
```

- [ ] **Step 5: Commit**

```bash
git add shield/config-examples/
git commit -m "feat: add config example files

Example files for .tesseract.json project marker, global config,
ClickUp PM adapter config, and credentials. Users copy and customize
these during setup."
```

## Chunk 3: Config Validation Utility

### Task 11: Create config validation script

**Files:**
- Create: `shield/hooks/scripts/validate-config.sh`

- [ ] **Step 1: Create validate-config.sh**

A lightweight wrapper that validates a JSON file against a JSON schema using Python's `jsonschema` package (falls back gracefully if not installed).

```bash
#!/usr/bin/env bash
set -euo pipefail

# Validate a JSON config file against a JSON schema
# Usage: validate-config.sh <config-file> <schema-file>
# Exit 0 if valid, exit 1 with error message if invalid
# Falls back silently (exit 0) if jsonschema is not installed

CONFIG_FILE="${1:-}"
SCHEMA_FILE="${2:-}"

if [ -z "$CONFIG_FILE" ] || [ -z "$SCHEMA_FILE" ]; then
  echo "Usage: validate-config.sh <config-file> <schema-file>" >&2
  exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
  echo "Config file not found: $CONFIG_FILE" >&2
  exit 1
fi

if [ ! -f "$SCHEMA_FILE" ]; then
  echo "Schema file not found: $SCHEMA_FILE" >&2
  exit 1
fi

# Try validation — fall back silently if jsonschema not available
python3 -c "
import sys
try:
    import json, jsonschema
    config = json.load(open(sys.argv[1]))
    schema = json.load(open(sys.argv[2]))
    jsonschema.validate(config, schema)
except ImportError:
    # jsonschema not installed — skip validation silently
    sys.exit(0)
except json.JSONDecodeError as e:
    print(f'Invalid JSON in {sys.argv[1]}: {e}', file=sys.stderr)
    sys.exit(1)
except jsonschema.ValidationError as e:
    print(f'Config validation error: {e.message}', file=sys.stderr)
    sys.exit(1)
" "$CONFIG_FILE" "$SCHEMA_FILE"
```

- [ ] **Step 2: Make executable**

```bash
chmod +x shield/hooks/scripts/validate-config.sh
```

- [ ] **Step 3: Commit**

```bash
git add shield/hooks/scripts/validate-config.sh
git commit -m "feat: add config validation utility script

Validates JSON config files against JSON schemas. Uses Python
jsonschema package if available, falls back silently if not.
Used by session-start hook and init/migrate commands."
```

## Chunk 4: Hooks

### Task 12: Create the hook runner (polyglot wrapper)

**Files:**
- Create: `shield/hooks/run-hook.cmd`

- [ ] **Step 1: Create run-hook.cmd**

Port from `infra-review/hooks/run-hook.cmd` — this is a polyglot script that works on both Windows (CMD) and Unix (bash):

```bash
: << 'CMDBLOCK'
@echo off
REM Polyglot wrapper: runs .sh scripts cross-platform
REM Usage: run-hook.cmd <script-name> [args...]

if "%~1"=="" (
    echo run-hook.cmd: missing script name >&2
    exit /b 1
)
"C:\Program Files\Git\bin\bash.exe" -l "%~dp0scripts\%~1" %2 %3 %4 %5 %6 %7 %8 %9
exit /b
CMDBLOCK

# Unix shell runs from here
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SCRIPT_NAME="$1"
shift
"${SCRIPT_DIR}/scripts/${SCRIPT_NAME}" "$@"
```

Note: Updated to look in `scripts/` subdirectory (the hook scripts live in `hooks/scripts/`).

- [ ] **Step 2: Make executable**

```bash
chmod +x shield/hooks/run-hook.cmd
```

- [ ] **Step 3: Commit**

```bash
git add shield/hooks/run-hook.cmd
git commit -m "feat: add polyglot hook runner

Cross-platform wrapper that runs hook scripts on both Windows
and Unix. Updated path to look in hooks/scripts/ subdirectory."
```

### Task 13: Create session-start hook

**Files:**
- Create: `shield/hooks/scripts/session-start.sh`

- [ ] **Step 1: Create session-start.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Shield session-start hook
# Detects project config, loads settings, injects context into Claude

TESSERACT_HOME="${HOME}/.tesseract"
MARKER_FILE=".tesseract.json"

# Walk up to find .tesseract.json
find_marker() {
  local dir="$PWD"
  while [ "$dir" != "/" ]; do
    if [ -f "${dir}/${MARKER_FILE}" ]; then
      echo "${dir}/${MARKER_FILE}"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

# --- Detect project ---
MARKER_PATH=""
if MARKER_PATH=$(find_marker); then
  PROJECT_NAME=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['project'])" "$MARKER_PATH" 2>/dev/null || echo "unknown")
  DOMAINS=$(python3 -c "import json,sys; print(', '.join(json.load(open(sys.argv[1])).get('domains',[])))" "$MARKER_PATH" 2>/dev/null || echo "none")
else
  PROJECT_NAME=""
  DOMAINS=""
fi

# --- Load global config ---
PM_TOOL="none"
PLUGIN_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
VALIDATE_SCRIPT="${PLUGIN_ROOT}/hooks/scripts/validate-config.sh"

if [ -f "${TESSERACT_HOME}/config.json" ]; then
  # Validate config against schema if validator exists
  if [ -x "$VALIDATE_SCRIPT" ]; then
    CONFIG_ERRORS=$("$VALIDATE_SCRIPT" "${TESSERACT_HOME}/config.json" "${PLUGIN_ROOT}/schemas/config.schema.json" 2>&1 || true)
    if [ -n "$CONFIG_ERRORS" ]; then
      CONFIG_WARNINGS="Config validation warning: ${CONFIG_ERRORS}. Using defaults."
    fi
  fi
  PM_TOOL=$(python3 -c "import json; print(json.load(open('${TESSERACT_HOME}/config.json')).get('pm_tool','none'))" 2>/dev/null || echo "none")
fi

# --- Load project PM config ---
PM_STATUS="not configured"
if [ -n "$PROJECT_NAME" ] && [ -f "${TESSERACT_HOME}/projects/${PROJECT_NAME}/pm.json" ]; then
  PM_STATUS=$(python3 -c "
import json
pm = json.load(open('${TESSERACT_HOME}/projects/${PROJECT_NAME}/pm.json'))
adapter = pm.get('adapter', 'unknown')
ws = pm.get('workspace_id', 'not set')
print(f'{adapter} (workspace: {ws})')
" 2>/dev/null || echo "configured (details unreadable)")
fi

# --- Set up MCP server if PM tool configured ---
if [ "$PM_TOOL" != "none" ] && [ -f "${PLUGIN_ROOT}/adapters/${PM_TOOL}/.mcp.json" ]; then
  cp "${PLUGIN_ROOT}/adapters/${PM_TOOL}/.mcp.json" "${PLUGIN_ROOT}/.mcp.json"
fi

# --- Build context output ---
if [ -n "$PROJECT_NAME" ]; then
  CONTEXT="Shield project detected: **${PROJECT_NAME}**
- Domains: ${DOMAINS}
- PM tool: ${PM_TOOL} (${PM_STATUS})
- Config: ${TESSERACT_HOME}/projects/${PROJECT_NAME}/
${CONFIG_WARNINGS:+
⚠ ${CONFIG_WARNINGS}}

Available commands: /shield init, /research, /plan, /plan-review, /pm-sync, /pm-status, /implement, /review, /review-security, /review-cost, /review-well-architected, /analyze-plan"
else
  CONTEXT="No .tesseract.json found in this project. Run **/shield init** to set up Shield."
fi

# Escape for JSON
CONTEXT_ESCAPED=$(echo "$CONTEXT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" | sed 's/^"//;s/"$//')

cat <<EOF
{
  "hookSpecificOutput": {
    "additionalContext": "${CONTEXT_ESCAPED}"
  }
}
EOF
```

- [ ] **Step 2: Make executable**

```bash
chmod +x shield/hooks/scripts/session-start.sh
```

- [ ] **Step 3: Commit**

```bash
git add shield/hooks/scripts/session-start.sh
git commit -m "feat: add session-start hook

Detects .tesseract.json project marker, loads config from
~/.tesseract/, sets up MCP server for active PM tool, and
injects project context into Claude session."
```

### Task 14: Create post-edit hook

**Files:**
- Create: `shield/hooks/scripts/post-edit.sh`

- [ ] **Step 1: Create post-edit.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Shield post-edit hook
# Runs lightweight lint checks on edited files that match active domains

MARKER_FILE=".tesseract.json"

# Find .tesseract.json
find_marker() {
  local dir="$PWD"
  while [ "$dir" != "/" ]; do
    if [ -f "${dir}/${MARKER_FILE}" ]; then
      echo "${dir}/${MARKER_FILE}"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

# Claude Code PostToolUse hooks receive tool input via stdin as JSON.
# Parse the file path from the tool input.
INPUT=$(cat)
EDITED_FILE=$(echo "$INPUT" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    # Write/Edit tools pass file_path in the tool input
    print(data.get('tool_input', {}).get('file_path', ''))
except:
    print('')
" 2>/dev/null || echo "")

if [ -z "$EDITED_FILE" ] || [ ! -f "$EDITED_FILE" ]; then
  exit 0
fi

# Only process if we have a project marker
MARKER_PATH=""
if ! MARKER_PATH=$(find_marker); then
  exit 0
fi

# Check file extension and run domain-appropriate checks
REMINDERS=""
case "$EDITED_FILE" in
  *.tf)
    # Check if terraform fmt is available
    if command -v terraform &>/dev/null; then
      FMT_CHECK=$(terraform fmt -check -diff "$EDITED_FILE" 2>/dev/null || true)
      if [ -n "$FMT_CHECK" ]; then
        REMINDERS="File needs formatting: run \`terraform fmt ${EDITED_FILE}\`"
      fi
    fi
    ;;
  *.yaml|*.yml)
    # Basic YAML syntax check
    if command -v python3 &>/dev/null; then
      YAML_CHECK=$(python3 -c "import yaml; yaml.safe_load(open('${EDITED_FILE}'))" 2>&1 || true)
      if echo "$YAML_CHECK" | grep -qi "error\|exception"; then
        REMINDERS="YAML syntax issue in ${EDITED_FILE}"
      fi
    fi
    ;;
esac

if [ -z "$REMINDERS" ]; then
  exit 0
fi

REMINDERS_ESCAPED=$(echo "$REMINDERS" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" | sed 's/^"//;s/"$//')

cat <<EOF
{
  "hookSpecificOutput": {
    "additionalContext": "${REMINDERS_ESCAPED}"
  }
}
EOF
```

- [ ] **Step 2: Make executable**

```bash
chmod +x shield/hooks/scripts/post-edit.sh
```

- [ ] **Step 3: Commit**

```bash
git add shield/hooks/scripts/post-edit.sh
git commit -m "feat: add post-edit hook

Runs lightweight lint checks after Write/Edit on tracked file types.
Terraform files get fmt check, YAML files get syntax check.
Outputs warnings to Claude context without blocking."
```

### Task 15: Create pre-commit review hook

**Files:**
- Create: `shield/hooks/scripts/pre-commit-review.sh`

- [ ] **Step 1: Create pre-commit-review.sh**

```bash
#!/usr/bin/env bash
set -euo pipefail

# Shield pre-commit review hook
# Runs lightweight code review on staged changes before commit
# Disabled by default — enable via review_on_commit.enabled in config
#
# NOTE: Claude Code hooks communicate via JSON output (additionalContext),
# not via exit codes. This hook provides context and thresholds to Claude,
# which then performs the review and decides whether to proceed with the
# commit or ask the user to fix issues first. The blocking is enforced by
# Claude's behavior, not by this script's exit code.

TESSERACT_HOME="${HOME}/.tesseract"

# Check if review_on_commit is enabled
ENABLED="false"
if [ -f "${TESSERACT_HOME}/config.json" ]; then
  ENABLED=$(python3 -c "
import json
cfg = json.load(open('${TESSERACT_HOME}/config.json'))
print(str(cfg.get('review_on_commit', {}).get('enabled', False)).lower())
" 2>/dev/null || echo "false")
fi

if [ "$ENABLED" != "true" ]; then
  exit 0
fi

# Read thresholds
BLOCK_THRESHOLD=$(python3 -c "
import json
cfg = json.load(open('${TESSERACT_HOME}/config.json'))
print(cfg.get('review_on_commit', {}).get('block_threshold', 'critical'))
" 2>/dev/null || echo "critical")

WARN_THRESHOLD=$(python3 -c "
import json
cfg = json.load(open('${TESSERACT_HOME}/config.json'))
print(cfg.get('review_on_commit', {}).get('warn_threshold', 'important'))
" 2>/dev/null || echo "important")

# Get staged files
STAGED_FILES=$(git diff --cached --name-only 2>/dev/null || true)
if [ -z "$STAGED_FILES" ]; then
  exit 0
fi

# Output context for Claude to perform the review
CONTEXT="Pre-commit review triggered. Staged files:
${STAGED_FILES}

Review thresholds — block: ${BLOCK_THRESHOLD}, warn: ${WARN_THRESHOLD}
Review these changes and report findings at or above the warn threshold.
Block the commit (exit non-zero) if any findings are at or above the block threshold."

CONTEXT_ESCAPED=$(echo "$CONTEXT" | python3 -c "import sys,json; print(json.dumps(sys.stdin.read()))" | sed 's/^"//;s/"$//')

cat <<EOF
{
  "hookSpecificOutput": {
    "additionalContext": "${CONTEXT_ESCAPED}"
  }
}
EOF
```

- [ ] **Step 2: Make executable**

```bash
chmod +x shield/hooks/scripts/pre-commit-review.sh
```

- [ ] **Step 3: Commit**

```bash
git add shield/hooks/scripts/pre-commit-review.sh
git commit -m "feat: add pre-commit review hook

Checks review_on_commit config and if enabled, passes staged
file list and severity thresholds to Claude for lightweight
review before commit. Disabled by default."
```

### Task 16: Create hooks.json

**Files:**
- Create: `shield/hooks/hooks.json`

- [ ] **Step 1: Create hooks.json**

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume",
        "hooks": [
          {
            "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd\" session-start.sh"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd\" post-edit.sh"
          }
        ]
      }
    ],
    "PreCommit": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd\" pre-commit-review.sh"
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 2: Commit**

```bash
git add shield/hooks/hooks.json
git commit -m "feat: add hooks.json registration

Register three hooks: SessionStart (project detection + context),
PostToolUse (lint after edits), PreCommit (review before commit)."
```

## Chunk 5: Init and Migrate Commands

### Task 17: Create /shield init command

**Files:**
- Create: `shield/commands/init.md`

- [ ] **Step 1: Create init command**

```markdown
---
name: init
description: Set up Shield for a new project — creates .tesseract.json and ~/.tesseract/ config structure
---

# Shield Init

Set up Shield for this project. If this is a fresh setup, create configuration from scratch. If old plugins are detected, suggest running `/shield migrate` instead.

## Steps

1. **Check for existing setup**
   - If `.tesseract.json` already exists, show current config and ask if user wants to reconfigure
   - If old plugin config is detected (`sprint-planner.json`, `claude/infra-review/`), suggest `/shield migrate` instead

2. **Gather project info**
   - Ask for project name (default: repo directory name)
   - Ask for active domains — show available options:
     - `terraform` — Terraform/HCL infrastructure
     - `atmos` — Atmos stack management
     - `github-actions` — CI/CD workflows
     - (more domains in future)
   - Allow multiple selections

3. **Create `.tesseract.json`** in the repo root:
   ```json
   {
     "project": "<project-name>",
     "domains": ["<selected-domains>"]
   }
   ```

4. **Create `~/.tesseract/` directory structure**:
   ```bash
   mkdir -p ~/.tesseract/projects/<project-name>/runs
   ```

5. **Create `~/.tesseract/config.json`** if it doesn't exist:
   - Copy from `${CLAUDE_PLUGIN_ROOT}/config-examples/config.example.json`
   - Ask user for PM tool preference (clickup / none / skip for now)

6. **If PM tool selected:**
   - Ask for workspace details (workspace_id, space_id, project_prefix)
   - Create `~/.tesseract/projects/<project-name>/pm.json`
   - Ask for API token and save to `~/.tesseract/credentials.json`
   - If `uv` is not on PATH and PM tool requires it, offer install instructions:
     ```
     PM adapter requires uv (Python package manager).
     Install: curl -LsSf https://astral.sh/uv/install.sh | sh
     Or skip PM setup for now — you can configure it later.
     ```

7. **Show summary** of what was created:
   ```
   Shield initialized for project: <name>

   Created:
     ✓ .tesseract.json (project marker)
     ✓ ~/.tesseract/config.json (global config)
     ✓ ~/.tesseract/projects/<name>/pm.json (PM config)

   Enable auto-updates:
     /plugin update --auto-update shield@tesseract

   Next: try /research or /plan to start your workflow
   ```

## Important
- Do NOT create `.tesseract.json` without user confirmation
- Do NOT overwrite existing `~/.tesseract/config.json` — merge if it exists
- Do NOT store API tokens in `.tesseract.json` — credentials go in `~/.tesseract/credentials.json` only
- Validate all inputs against the JSON schemas in `${CLAUDE_PLUGIN_ROOT}/schemas/`
```

- [ ] **Step 2: Commit**

```bash
git add shield/commands/init.md
git commit -m "feat: add /shield init command

Interactive setup command that creates .tesseract.json project
marker and ~/.tesseract/ config structure. Handles PM tool setup
with dependency checking for uv."
```

### Task 18: Create /shield migrate command

**Files:**
- Create: `shield/commands/migrate.md`

- [ ] **Step 1: Create migrate command**

```markdown
---
name: migrate
description: Migrate from old plugins (infra-review, clickup-sprint-planner, dev-workflow) to Shield
---

# Shield Migrate

Detect and migrate configuration from old Tesseract plugins to the Shield config structure.

## Steps

1. **Detect old plugins** — scan for:
   - `sprint-planner.json` or `clickup-sprint-planner/examples/sprint-planner.json` → ClickUp config
   - `claude/infra-review/` directory → infra-review was active
   - Old plugin directories (`infra-review/`, `clickup-sprint-planner/`, `dev-workflow/`) → detect which were installed

2. **Report findings:**
   ```
   Detected old plugins:
     - clickup-sprint-planner (sprint-planner.json found)
     - infra-review (claude/infra-review/ directory found)
     - dev-workflow (commands detected)
   ```
   If nothing detected, suggest `/shield init` instead.

3. **Gather project info:**
   - Ask for project name (default: repo directory name)
   - Infer domains from detected plugins:
     - `infra-review` detected → suggest `terraform`, `atmos`
     - Ask user to confirm/adjust

4. **Create `.tesseract.json`** with confirmed project name and domains

5. **Migrate sprint-planner.json** (if found):
   - Read the old config file
   - Map fields to new structure:

   | Old field | New location |
   |-----------|-------------|
   | `workspace_id` | `~/.tesseract/projects/<project>/pm.json` → `workspace_id` |
   | `space_id` | `~/.tesseract/projects/<project>/pm.json` → `space_id` |
   | `naming.*` | `~/.tesseract/projects/<project>/pm.json` → `naming.*` |
   | `api_token` (if present) | `~/.tesseract/credentials.json` → `clickup.api_token` |

   - Set `adapter: "clickup"` and `adapter_mode: "hybrid"` in pm.json
   - If `CLICKUP_API_TOKEN` env var is set, offer to save it to credentials.json

6. **Create `~/.tesseract/config.json`** with defaults:
   - Set `pm_tool: "clickup"` if sprint-planner was found, otherwise `"none"`
   - Set `review_on_commit.enabled: false`
   - Set default reviewers config

7. **Show migration summary:**
   ```
   Migrated sprint-planner.json:
     ✓ workspace_id → ~/.tesseract/projects/<project>/pm.json
     ✓ space_id → ~/.tesseract/projects/<project>/pm.json
     ✓ naming config → ~/.tesseract/projects/<project>/pm.json
     ⚠ No API token found in config. Add to ~/.tesseract/credentials.json manually.

   Created:
     ✓ .tesseract.json (project marker)
     ✓ ~/.tesseract/config.json (global defaults)
     ✓ ~/.tesseract/projects/<project>/pm.json (PM config)

   Old files left in place (safe to delete after verifying):
     - sprint-planner.json
     - claude/infra-review/

   Next steps:
     1. Add API token to ~/.tesseract/credentials.json
     2. Uninstall old plugins: infra-review, clickup-sprint-planner, dev-workflow
     3. Enable auto-updates: /plugin update --auto-update shield@tesseract
     4. Run /pm-status to verify ClickUp connection
   ```

## Important
- Do NOT delete old config files — leave them in place for user to verify
- Do NOT overwrite existing `~/.tesseract/` files — warn and ask
- Do NOT store API tokens in `.tesseract.json` or pm.json
- Validate migrated config against schemas in `${CLAUDE_PLUGIN_ROOT}/schemas/`
- If `sprint-planner.json` has fields not in the mapping, warn the user about unmapped fields
```

- [ ] **Step 2: Commit**

```bash
git add shield/commands/migrate.md
git commit -m "feat: add /shield migrate command

Migration command that detects old plugin configs (sprint-planner.json,
infra-review artifacts), maps fields to the new ~/.tesseract/ structure,
and reports what was migrated with next steps."
```

## Chunk 6: CI Test Workflow

### Task 19: Create test CI workflow

**Files:**
- Create: `.github/workflows/test.yml`

- [ ] **Step 1: Create test workflow**

```yaml
name: Test
on:
  push:
    branches: [main]
  pull_request:

jobs:
  plugin-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - name: Validate JSON schemas
        run: |
          for schema in shield/schemas/*.schema.json; do
            echo "Validating $schema..."
            python3 -c "import json; json.load(open('$schema'))" || exit 1
          done
          echo "All schemas valid JSON"

      - name: Validate config examples against schemas
        run: |
          pip install jsonschema
          python3 -c "
          import json, jsonschema

          # Validate config example
          schema = json.load(open('shield/schemas/config.schema.json'))
          example = json.load(open('shield/config-examples/config.example.json'))
          jsonschema.validate(example, schema)
          print('✓ config.example.json validates')

          # Validate project marker example
          schema = json.load(open('shield/schemas/tesseract.schema.json'))
          example = json.load(open('shield/config-examples/tesseract.example.json'))
          jsonschema.validate(example, schema)
          print('✓ tesseract.example.json validates')

          # Validate PM config example
          schema = json.load(open('shield/schemas/pm.schema.json'))
          example = json.load(open('shield/config-examples/pm-clickup.example.json'))
          jsonschema.validate(example, schema)
          print('✓ pm-clickup.example.json validates')
          "

      - name: Validate hooks.json structure
        run: |
          python3 -c "
          import json
          hooks = json.load(open('shield/hooks/hooks.json'))
          assert 'hooks' in hooks, 'Missing hooks key'
          for event in ['SessionStart', 'PostToolUse', 'PreCommit']:
              assert event in hooks['hooks'], f'Missing {event} hook'
          print('✓ hooks.json structure valid')
          "

      - name: Validate plugin.json
        run: |
          python3 -c "
          import json
          plugin = json.load(open('shield/.claude-plugin/plugin.json'))
          assert plugin['name'] == 'shield', 'Plugin name mismatch'
          assert 'permissions' in plugin, 'Missing permissions'
          print('✓ plugin.json valid')
          "

      - name: Check hook scripts are executable
        run: |
          for script in shield/hooks/scripts/*.sh; do
            if [ ! -x "$script" ]; then
              echo "ERROR: $script is not executable"
              exit 1
            fi
          done
          echo "✓ All hook scripts executable"

      - name: Shellcheck hook scripts
        run: |
          sudo apt-get install -y shellcheck
          shellcheck shield/hooks/scripts/*.sh
          echo "✓ Shellcheck passed"

  mcp-server-tests:
    runs-on: ubuntu-latest
    if: ${{ hashFiles('shield/adapters/clickup/server/**') != '' }}
    steps:
      - uses: actions/checkout@v6
      - uses: astral-sh/setup-uv@v4
      - name: Run MCP server tests
        run: |
          cd shield/adapters/clickup
          uv run pytest -v
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/test.yml
git commit -m "ci: add test workflow

Validates JSON schemas, config examples, hooks.json structure,
plugin.json, hook script permissions, and shellcheck. MCP server
tests run when adapter code exists."
```

### Task 20: Clean up .gitkeep files

Now that real files exist in the directories, remove the placeholder .gitkeep files.

- [ ] **Step 1: Remove .gitkeep files from populated directories**

```bash
find shield/ -name ".gitkeep" -exec rm {} \;
```

- [ ] **Step 2: Add back .gitkeep only for still-empty directories**

```bash
for dir in shield/skills/general shield/skills/terraform shield/skills/atmos shield/skills/github-actions shield/agents shield/adapters/clickup shield/examples/terraform-vpc shield/examples/python-api shield/tests shield/evals/inputs shield/evals/expected; do
  if [ -z "$(ls -A "$dir" 2>/dev/null)" ]; then
    touch "$dir/.gitkeep"
  fi
done
```

- [ ] **Step 3: Commit**

```bash
git add -u shield/
git add shield/**/.gitkeep
git commit -m "chore: clean up gitkeep placeholders

Remove .gitkeep from directories that now contain real files.
Keep .gitkeep in directories awaiting future plans (agents,
skills, adapters, examples, tests, evals)."
```
