# Shield SAST Adapters

This directory holds adapters that integrate Static Application Security Testing (SAST) tools into shield's `backend-reviewer` agent.

## Why SAST adapters

Shield's backend-domain skills (under `shield/skills/backend/`) are LLM-driven rubrics. They excel at architectural and judgment-based review (god class detection, YAGNI, deployment-safety reasoning) but duplicate work for pattern-detectable checks (annotations, imports, fixed call patterns) that SAST tools handle deterministically.

Plan 4 introduces a hybrid: SAST tools run alongside skills for the deterministic checks; skills focus on the judgment layer. Findings from both flow through the same aggregation pipeline.

See the design spec at `docs/superpowers/specs/2026-05-07-shield-sast-integration-design.md` for the full rationale.

## How adapters work

Each adapter lives in `<tool>/` (e.g., `semgrep/`, `sonarqube/`) and provides:

- `adapter.md` — LLM-readable contract: what the adapter does, how it's configured, what fallback modes it supports
- `adapter.py` — Python runtime: invokes the tool (or consumes its output), parses results, normalizes them to the schema in `common.py`
- `tests/fixtures/` — captured tool output samples for deterministic parser tests
- `tests/test_adapter.py` — pytest tests over the parser + dispatch logic

When `backend-reviewer` runs, it iterates the `sast.adapters` list from `.shield.json` and calls each adapter's `run()` function in parallel with the skill review.

## Layered fallback

Each adapter tries three modes in order:

1. **Consume existing output.** Look for SAST output at known paths. If the mtime is newer than the HEAD commit, parse and return.
2. **Invoke locally.** If no fresh output found, check the tool is installed and run it on the target path.
3. **Best-effort skip.** If the tool isn't available and can't be invoked, return zero findings with a `note` field. Don't fail the review.

Stale output (mtime older than HEAD commit) is treated as missing — fall through to invoke or skip.

## Adding a new adapter

1. Create `shield/adapters/sast/<tool>/` with `adapter.md`, `adapter.py`, `tests/`
2. Implement `run(target_path: str, config: dict, head_commit_time: float | None) -> AdapterResult`
3. Add fixture-based parser tests under `tests/`
4. Update `shield/agents/backend-reviewer.md` Skill Loading and Configuration sections to mention the new adapter
5. Document configuration knobs in `adapter.md`

## Adapters

- `semgrep/` — Lightweight CLI pattern matcher. Ships custom rule packs for Spring 3.x patterns. Default mode: invoke locally.
- `sonarqube/` — Self-hosted code-quality server. Reads existing reports via REST API or SARIF; falls back to local `sonar-scanner`. Default mode: consume.
