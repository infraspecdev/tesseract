---
name: devcontainer-init
description: Use when scaffolding a .devcontainer/ for Shield. Triggers on /shield init-devcontainer, "set up devcontainer", "isolate /implement".
# No outputs declared: writes .devcontainer/ files and updates .shield.json
# at the repo root — outside the shield output_dir registry scope.
---

# Devcontainer Init

Scaffold a per-repo `.devcontainer/` that runs `/implement` and other agent commands in filesystem + network egress isolation. Follows the design at `docs/superpowers/specs/2026-05-18-devcontainer-implement-design.md`.

## When to Use

- User runs `/shield init-devcontainer`.
- User asks to "set up a devcontainer" or "isolate /implement".

## When NOT to Use

- `.devcontainer/` already exists and matches what we'd produce → tell the user it's already set up.
- User wants cloud / Codespaces / CI launchers → out of scope for v1; suggest local devcontainer first.

## Step Skeleton

| Step | Action | Mandatory |
|------|--------|-----------|
| 1 | Detect stacks via `shield/scripts/detect_stack.py` | Yes |
| 2 | Confirm with user (add / drop / correct) | Yes |
| 3 | Compose `devcontainer.json` via `shield/scripts/compose_devcontainer.py` | Yes |
| 4 | Copy templates: `shield-firewall.sh`, `Dockerfile.tmpl`, fill `postCreate.sh.tmpl` | Yes |
| 5 | Diff against existing `.devcontainer/` if present; prompt before overwrite | Yes |
| 6 | Update `.shield.json` with `devcontainer` block | Yes |
| 7 | Print next-step instructions (VS Code / CLI) | Yes |

## Workflow

### 1. Detect

```bash
uv run python3 -c \
  "from pathlib import Path; \
   import sys; sys.path.insert(0, 'shield/scripts'); \
   from detect_stack import detect_stack; \
   print(' '.join(detect_stack(Path('.'))))"
```

Output is a space-separated list of stack tags (e.g., `python node`).

### 2. Confirm with user

Show the detected stacks. Ask:

```
Detected: python, node
  [a] proceed with these
  [b] drop one or more
  [c] add a stack not detected
```

### 3. Compose devcontainer.json

```bash
uv run python3 -c \
  "from pathlib import Path; \
   import sys, json; \
   sys.path.insert(0, 'shield/scripts'); \
   from compose_devcontainer import compose_devcontainer; \
   fm = Path('shield/skills/devcontainer/feature-map.json'); \
   cfg = compose_devcontainer(stacks=['python', 'node'], feature_map_path=fm); \
   print(json.dumps(cfg, indent=2))" > .devcontainer/devcontainer.json
```

Replace `['python', 'node']` with the confirmed-stack list.

### 4. Copy templates

```bash
mkdir -p .devcontainer
cp shield/skills/devcontainer/templates/shield-firewall.sh .devcontainer/shield-firewall.sh
cp shield/skills/devcontainer/templates/Dockerfile.tmpl    .devcontainer/Dockerfile
```

Fill `postCreate.sh` from `postCreate.sh.tmpl` by substituting `# {{HINTS}}` with each confirmed-stack's `post_create_hint` from `feature-map.json`:

```python
import json
from pathlib import Path

stacks = ["python", "node"]  # confirmed list
fm = json.loads(Path("shield/skills/devcontainer/feature-map.json").read_text())
hints = "\n".join(fm[s]["post_create_hint"] for s in stacks if s in fm)
tmpl = Path("shield/skills/devcontainer/templates/postCreate.sh.tmpl").read_text()
Path(".devcontainer/postCreate.sh").write_text(tmpl.replace("# {{HINTS}}", hints))
```

`chmod 0755 .devcontainer/postCreate.sh .devcontainer/shield-firewall.sh`.

### 5. Diff against existing

Before overwriting any file, `diff` the proposed new content against the existing file. If different, show the user the diff and ask: `[o]verwrite / [k]eep existing / [s]how diff again`.

### 6. Update .shield.json

```python
import json
from pathlib import Path

path = Path(".shield.json")
data = json.loads(path.read_text()) if path.exists() else {}
data["devcontainer"] = {
    "version": 1,
    "stacks_detected": stacks,
    "required": "ask",
    "firewall_extra_allowlist": [],
}
path.write_text(json.dumps(data, indent=2) + "\n")
```

### 7. Print next-step instructions

```
Devcontainer scaffolded.

Next:
  VS Code:  Cmd+Shift+P → "Dev Containers: Reopen in Container"
  CLI:      devcontainer up --workspace-folder .
            devcontainer exec --workspace-folder . bash

Then inside the container:
  claude /login    # one-time per project; creds persist in named volume

Security caveats — see shield/README.md § Devcontainer.
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| Skipping the diff before overwrite | Always diff and confirm; users will lose customizations otherwise |
| Naming the firewall script `init-firewall.sh` | Use `shield-firewall.sh` — claude-code#32113 will silently overwrite the upstream name |
| Hard-coding Feature versions instead of digests | Always use `@sha256:...` from `feature-map.json`; tag-only pins drift |
| Forgetting to update `.shield.json` | Without the `devcontainer` block, the gate (Story 8) defaults to "ask" forever |
