"""Shield PM adapter MCP server entry point.

Registers all tools and runs the FastMCP server over stdio.
Config is loaded lazily on first tool call, not at startup,
so the server starts cleanly even without a project context.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Add parent directory to path so server package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.clickup_client import ClickUpClient
from server.config import load_config, load_shield_config, get_api_token
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
    instructions="Shield PM adapter — sprint planning tools for ClickUp via abstract PM operations.",
)


def _resolve_relative(path_str: str, config_path: Path) -> Path:
    """Resolve a path relative to the config file's directory."""
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (config_path.parent / p).resolve()


class _LazyProxy:
    """Proxy that defers to a real object loaded on first attribute access.

    Tool modules store references like `client` and call `client.get_tasks()`
    later. This proxy intercepts those calls, triggers config loading, then
    forwards to the real object. This lets the server start without config
    and load it when tools are actually invoked.
    """

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
    """Lazily loads all PM adapter dependencies on first access."""

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

        api_token = get_api_token(config)
        self._config = config
        self._client = ClickUpClient(api_token)
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
    """Register all tool modules with lazy proxies — no config needed at startup."""
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
