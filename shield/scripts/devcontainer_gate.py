# shield/scripts/devcontainer_gate.py
"""Pre-flight decision for /implement: should it run in this repo's devcontainer?

Public API:
    decide(repo, in_container, user_input) -> Decision

CLI entry point at the bottom: invoked from /implement's first step.

Read .shield.json -> devcontainer.required (default 'ask'). Compose decision
with SHIELD_IN_DEVCONTAINER env var (passed in as `in_container`) and an
optional user answer when the gate has to prompt.
"""
from __future__ import annotations

import enum
import json
import sys
from pathlib import Path


class Decision(enum.Enum):
    PROCEED = "proceed"
    REFUSE = "refuse"


def _read_required(repo: Path) -> str:
    cfg_path = repo / ".shield.json"
    if not cfg_path.exists():
        return "ask"
    try:
        data = json.loads(cfg_path.read_text())
    except json.JSONDecodeError:
        return "ask"
    return str(data.get("devcontainer", {}).get("required", "ask"))


def _set_required(repo: Path, value: str) -> None:
    cfg_path = repo / ".shield.json"
    data: dict = {}
    if cfg_path.exists():
        try:
            data = json.loads(cfg_path.read_text())
        except json.JSONDecodeError:
            data = {}
    data.setdefault("devcontainer", {})["required"] = value
    cfg_path.write_text(json.dumps(data, indent=2) + "\n")


def decide(repo: Path, in_container: bool, user_input: str | None) -> Decision:
    repo = Path(repo)

    if in_container:
        return Decision.PROCEED

    if not (repo / ".devcontainer").is_dir():
        return Decision.PROCEED

    required = _read_required(repo)

    if required == "false":
        return Decision.PROCEED
    if required == "true":
        return Decision.REFUSE

    # required == 'ask'
    if user_input is None:
        # Caller is responsible for prompting; if they didn't, default to REFUSE
        # to be safe. Tests always supply a value.
        return Decision.REFUSE

    answer = user_input.strip().lower()
    if answer == "y":
        return Decision.REFUSE
    if answer == "n":
        return Decision.PROCEED
    if answer == "always":
        _set_required(repo, "true")
        return Decision.REFUSE
    if answer == "never":
        _set_required(repo, "false")
        return Decision.PROCEED
    # Unrecognized: default safe = refuse
    return Decision.REFUSE


def _cli() -> int:
    """Invoked from /implement's first step. Reads SHIELD_IN_DEVCONTAINER.

    Prompts interactively in the 'ask' branch when stdin is a TTY.
    Exits 0 on PROCEED, 1 on REFUSE.
    """
    import os

    repo = Path(os.environ.get("SHIELD_REPO", "."))
    in_container = os.environ.get("SHIELD_IN_DEVCONTAINER") == "true"
    required = _read_required(repo)

    user_input: str | None = None
    if (not in_container
            and (repo / ".devcontainer").is_dir()
            and required == "ask"):
        sys.stderr.write(
            "This repo has a Shield devcontainer.\n"
            "Run /implement inside it? [y / n / always / never]: "
        )
        sys.stderr.flush()
        user_input = sys.stdin.readline().strip()

    decision = decide(repo, in_container, user_input)

    if decision == Decision.REFUSE:
        sys.stderr.write(
            "Refusing to /implement on host.\n"
            "  VS Code:  reopen folder in container ('Reopen in Container').\n"
            "  CLI:      devcontainer up --workspace-folder . \\\n"
            "            && devcontainer exec --workspace-folder . bash\n"
            "            then run /implement inside.\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
