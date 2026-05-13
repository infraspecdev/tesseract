"""Append-only JSON action log for audit and undo support."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ActionLog:
    """Reads and appends to a structured JSON action log file."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._ensure_file()

    def _ensure_file(self):
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(json.dumps({"metadata": {}, "actions": []}, indent=2))

    def _read(self) -> dict:
        return json.loads(self.path.read_text())

    def _write(self, data: dict):
        self.path.write_text(json.dumps(data, indent=2, default=str))

    def _next_seq(self, data: dict) -> int:
        actions = data.get("actions", [])
        if not actions:
            return 1
        return max(a.get("seq", 0) for a in actions) + 1

    def log_action(
        self,
        action: str,
        status: str,
        summary: str,
        results: list[dict] | None = None,
        undo: dict | None = None,
        **extra: Any,
    ) -> dict:
        data = self._read()
        entry = {
            "seq": self._next_seq(data),
            "action": action,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
            "summary": summary,
        }
        if results is not None:
            entry["results"] = results
        if undo is not None:
            entry["undo"] = undo
        entry.update(extra)
        data["actions"].append(entry)
        self._write(data)
        return entry

    def get_actions(
        self,
        *,
        epic: str | None = None,
        action: str | None = None,
        since: str | None = None,
        last_n: int | None = None,
    ) -> list[dict]:
        data = self._read()
        actions = data.get("actions", [])
        if epic:
            actions = [a for a in actions if a.get("epic") == epic]
        if action:
            actions = [a for a in actions if a.get("action") == action]
        if since:
            actions = [a for a in actions if a.get("timestamp", "") >= since]
        if last_n:
            actions = actions[-last_n:]
        return actions
