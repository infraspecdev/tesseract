"""clickup-sprint-planner MCP server entry point.

Registers all tools and runs the FastMCP server over stdio.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add parent directory to path so server package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.clickup_client import ClickUpClient
from server.config import load_config, get_api_token
from server.tools import (
    capabilities,
    relationships,
    bulk_create,
    sync,
    sprint_status,
    bulk_update,
    rename,
    action_log_tool,
)

mcp = FastMCP(
    "clickup-sprint-planner",
    instructions="Sprint planning tools for ClickUp — bulk operations, relationship fields, plan doc sync.",
)


def _resolve_relative(path_str: str, config_path: Path) -> Path:
    """Resolve a path relative to the config file's directory."""
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (config_path.parent / p).resolve()


def _register_tools():
    """Load config, create client, and register all tool modules."""
    import os

    config_path = Path(
        os.environ.get("SPRINT_PLANNER_CONFIG", "./sprint-planner.json")
    ).resolve()
    config = load_config(config_path)
    api_token = get_api_token(config)
    client = ClickUpClient(api_token)

    # Resolve paths relative to config file location
    log_path = _resolve_relative(config.action_log.path, config_path)
    base_path = _resolve_relative(config.plan_docs.base_path, config_path)
    action_log = ActionLog(log_path)

    # Register tools — each module adds @mcp.tool() decorated functions
    capabilities.register(mcp)
    relationships.register(mcp, client, action_log)
    bulk_create.register(mcp, client, action_log, config)
    sync.register(mcp, client, config, base_path, action_log)
    sprint_status.register(mcp, client, config)
    bulk_update.register(mcp, client, action_log)
    rename.register(mcp, client, action_log, config)
    action_log_tool.register(mcp, action_log)


_register_tools()

if __name__ == "__main__":
    mcp.run()
