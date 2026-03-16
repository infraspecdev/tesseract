# Shield Tests

## Quick Tests (pre-commit)

Fast structural tests that run on every commit (~5 seconds):

```bash
shield/tests/run-all.sh
```

Covers: JSON schema validation, config examples, plugin structure, shellcheck, reference integrity, eval criteria, session-start E2E, example projects, contract tests. **31 tests.**

## E2E Tests (manual)

Full end-to-end tests using headless Claude Code sessions. **Run manually** — these take 2-5 minutes each and use API tokens.

```bash
# All E2E tests (~15-30 min)
shield/tests/e2e/run-all.sh

# Single phase test (~2-5 min)
shield/tests/e2e/run-all.sh test-review
```

Covers: `/shield init`, `/research`, `/plan`, `/plan-review`, `/pm-status`, `/implement`, `/review`. Each test verifies the correct skill is invoked and no premature actions occur.

**Requirements:** `claude` CLI installed and authenticated.
