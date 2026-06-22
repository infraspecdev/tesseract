# execute-steps — RED→GREEN paper trail

**Change:** Gave the `execute-steps` skill a real producer. Before this change the
skill was prose-only: it told skills to hand-write `steps.json`, and the path it
documented (`~/.shield/shield/<project>/`) did not match the session-start hook,
which reads `~/.shield/projects/<project>/`. The file a skill produced could
therefore never be found for resume.

New producer: `shield/scripts/steps_store.py` (init/start/complete/fail/read/clear),
modeled on `backlog_store.py`. It resolves the path the hook reads. The skill now
drives the script instead of the Write tool.

## RED (baseline — old skill)

Dispatched a subagent with the *old* skill content + scenario (project "Shield",
feature "vpc-20260622", 3 mandatory steps), asked for the literal first startup action.

Result — both failure modes reproduced:
- Wrote to `/Users/apple/.shield/shield/Shield/steps.json` — the **wrong path**
  (hook reads `.shield/projects/Shield/`), so the hook would never surface resume.
- Created the file by **hand-writing JSON via the Write tool** (no producer, fragile schema).

Against this behavior the committed eval (`01-producer-path-and-schema`) fails: a
`read` resolving the correct path returns `none`, so `"skill": "research"` is absent
and no `/projects/<project>/steps.json` path is printed.

## GREEN (new skill)

Same scenario, rewritten skill. The subagent ran:
- `uv run shield/scripts/steps_store.py read`
- `uv run shield/scripts/steps_store.py init --skill research --feature vpc-20260622 --steps-json '[...]'`

No path typed, no hand-written JSON — the script resolved `~/.shield/projects/<project>/steps.json`.

## Committed regression coverage

- `shield/scripts/test_steps_store.py` — 13 pytest cases (path-matches-hook, init/status/clear lifecycle, CLI exit codes). Primary gate.
- `shield/evals/execute-steps/01-producer-path-and-schema.md` — end-to-end: `RESULT: PASS` (2/2 structural, coverage 1/1).
