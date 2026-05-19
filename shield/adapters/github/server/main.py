"""Shield PM adapter MCP server entry point (GitHub)."""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.config import load_config, load_shield_config, get_github_token
from server.github_client import GitHubClient
from server.tools import (
    capabilities,
    relationships,
    bulk_create,
    sync,
    status,
    bulk_update,
    rename,
    action_log_tool,
)

mcp = FastMCP(
    "shield-pm-adapter",
    instructions="Shield PM adapter — sprint planning tools for GitHub Issues + Projects v2.",
)


def _resolve_relative(path_str: str, config_path: Path) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (config_path.parent / p).resolve()


class _LazyProxy:
    def __init__(self, loader, attr_name):
        object.__setattr__(self, "_loader", loader)
        object.__setattr__(self, "_attr_name", attr_name)

    def _real(self):
        self._loader.ensure_loaded()
        return getattr(self._loader, self._attr_name)

    def __getattr__(self, name):
        return getattr(self._real(), name)

    def __truediv__(self, other):
        return self._real() / other

    def __iter__(self):
        return iter(self._real())

    def __str__(self):
        return str(self._real())

    def __bool__(self):
        return bool(self._real())


class _DepsLoader:
    def __init__(self):
        self._loaded = False
        self._config = None
        self._client = None
        self._action_log = None
        self._base_path = None

    def ensure_loaded(self):
        if self._loaded:
            return
        self._loaded = True

        config = load_shield_config()
        if config is not None:
            config_path = Path.cwd()
        else:
            config_path = Path(
                os.environ.get("SPRINT_PLANNER_CONFIG", "./sprint-planner.json")
            ).resolve()
            config = load_config(config_path)

        token = get_github_token(config)
        self._config = config
        self._client = GitHubClient(token, config.github.owner, config.github.repo)
        self._base_path = _resolve_relative(config.plan_docs.base_path, config_path)
        log_path = _resolve_relative(config.action_log.path, config_path)
        self._action_log = ActionLog(log_path)

    @property
    def config(self):
        return self._config

    @property
    def client(self):
        return self._client

    @property
    def action_log(self):
        return self._action_log

    @property
    def base_path(self):
        return self._base_path


_deps = _DepsLoader()


def _register_tools():
    client = _LazyProxy(_deps, "client")
    config = _LazyProxy(_deps, "config")
    action_log = _LazyProxy(_deps, "action_log")
    base_path = _LazyProxy(_deps, "base_path")

    capabilities.register(mcp)
    relationships.register(mcp, client, action_log)
    bulk_create.register(mcp, client, action_log, config)
    sync.register(mcp, client, config, base_path, action_log)
    status.register(mcp, client, config)
    bulk_update.register(mcp, client, action_log)
    rename.register(mcp, client, action_log, config)
    action_log_tool.register(mcp, action_log)


_register_tools()

if __name__ == "__main__":
    mcp.run()
