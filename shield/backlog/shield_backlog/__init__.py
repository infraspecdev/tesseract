"""shield-backlog — public API.

Used by Shield skills mid-task to capture ideas, by /backlog command flows for
view/promote/remove, and by /plan + /implement for end-of-run reconciliation.

LOCKED capture() signature (TRD §11, plan-review 2026-05-27):

    capture(text: str, *, kind: str = "task",
            feature: str | None = None, epic: str | None = None,
            source: str) -> str
"""
from shield_backlog.store import (
    BacklogInvalid,
    capture,
    read_backlog,
    remove,
)
from shield_backlog.triggers import eager_prune, kill_switch_enabled, lazy_sweep

__all__ = [
    "BacklogInvalid",
    "capture",
    "eager_prune",
    "kill_switch_enabled",
    "lazy_sweep",
    "read_backlog",
    "remove",
]
