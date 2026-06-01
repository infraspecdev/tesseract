# Tesseract — Claude Code plugin marketplace
#
# Local dev commands. Same targets are invoked by .pre-commit-config.yaml
# (`make test`) and .github/workflows/test.yml (`make install` + `make test`).

.PHONY: help install test lint ci

help:  ## Show available targets
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-10s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install:  ## Ensure uv is present (test deps are provisioned per-run via `uv run --with`)
	@command -v uv >/dev/null 2>&1 \
		|| (echo "Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh)
	@echo "✓ uv ready (jsonschema/pyyaml/pytest are pulled in on demand by uv run --with)"

test:  ## Run the full Shield test suite
	@bash shield/tests/run-all.sh

lint:  ## Run shellcheck on shipped shell scripts (if available)
	@command -v shellcheck >/dev/null 2>&1 \
		&& shellcheck shield/hooks/scripts/*.sh shield/scripts/*.sh \
		|| echo "⚠ shellcheck not installed, skipping"

ci: install test lint  ## Install deps and run tests + lint (used by CI)
