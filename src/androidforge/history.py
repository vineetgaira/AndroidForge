"""Local JSON Lines operation history."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from androidforge.errors import AndroidForgeError


def history_path() -> Path:
    """Get the history file path, respecting the XDG state directory."""
    state_dir = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return state_dir / "androidforge" / "history.jsonl"


def read_history() -> list[dict[str, Any]]:
    """Read all history records from disk."""
    path = history_path()
    if not path.exists():
        return []
    try:
        return [
            json.loads(line)
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
    except (OSError, json.JSONDecodeError) as exc:
        raise AndroidForgeError(f"Could not read history at {path}: {exc}") from exc


def record_operation(operation: str, serial: str, result: str) -> dict[str, Any]:
    """Append an operation record and return it."""
    now = datetime.now(UTC)
    entry = {
        "id": now.strftime("%Y%m%dT%H%M%S%fZ"),
        "timestamp": now.isoformat(),
        "operation": operation,
        "serial": serial,
        "result": result,
        "rollback_supported": False,
    }
    path = history_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(entry) + "\n")
    except OSError as exc:
        raise AndroidForgeError(f"Could not write history to {path}: {exc}") from exc
    return entry
