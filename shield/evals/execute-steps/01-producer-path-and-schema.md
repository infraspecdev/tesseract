---
name: 01-producer-path-and-schema
skill_under_test: shield:execute-steps
scenario: A skill registers its step skeleton via the execute-steps utility; the file must land where the session-start hook reads it
---

## Setup
```bash
mkdir -p .shield-sandbox
cat > .shield.json <<'EOF'
{ "project": "steps-eval", "output_dir": "docs/shield" }
EOF
```

## Prompt
> Using the `shield:execute-steps` skill, register this step skeleton for the `research` skill, feature `vpc-20260622`:
> 1. Repo scan (mandatory)
> 2. Q&A walk (mandatory)
> 3. Synthesize findings (mandatory)
>
> Actually RUN the commands the skill specifies — do not just describe them, and do not create any file with the Write tool. Prefix every command with `SHIELD_HOME=$PWD/.shield-sandbox` so state stays in this sandbox. After registering, run the skill's "read" command to print the registered state. Leave the file in place (do not run clear). Show the command output.

## Success criteria

### Structural (deterministic, bidirectional must-find)
- /projects/[^/]*/steps\.json
- "skill": *"research"

## Pass threshold
2 of 2 structural
