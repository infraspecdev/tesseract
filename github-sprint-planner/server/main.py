"""github-sprint-planner MCP server entry point.

Registers all tools and runs the FastMCP server over stdio.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp.server.fastmcp import FastMCP

from server.action_log import ActionLog
from server.config import load_config, get_github_token
from server.github_client import GitHubClient
from server.tools import (
    sync,
    bulk_create,
    bulk_update,
    bulk_rename,
    sprint_status,
    action_log_tool,
)

mcp = FastMCP(
    "github-sprint-planner",
    instructions="Sprint planning tools for GitHub Issues + Projects v2 — bulk operations, sub-issue linking, plan doc sync.",
)


def _resolve_relative(path_str: str, config_path: Path) -> Path:
    p = Path(path_str)
    if p.is_absolute():
        return p
    return (config_path.parent / p).resolve()


def _register_tools():
    import os

    config_path = Path(
        os.environ.get("SPRINT_PLANNER_CONFIG", "./sprint-planner.json")
    ).resolve()
    config = load_config(config_path)
    token = get_github_token(config)
    client = GitHubClient(token, config.github.owner, config.github.repo)

    log_path = _resolve_relative(config.action_log.path, config_path)
    base_path = _resolve_relative(config.plan_docs.base_path, config_path)
    action_log = ActionLog(log_path)

    sync.register(mcp, client, config, base_path, action_log)
    bulk_create.register(mcp, client, action_log, config)
    bulk_update.register(mcp, client, action_log)
    bulk_rename.register(mcp, client, action_log, config)
    sprint_status.register(mcp, client, config)
    action_log_tool.register(mcp, action_log)


_register_tools()

if __name__ == "__main__":
    mcp.run()
