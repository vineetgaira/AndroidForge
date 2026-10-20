"""Read-only device operations available through the CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from androidforge.adb import run_adb
from androidforge.device import inspect_device


@dataclass(frozen=True)
class Operation:
    """Description of a callable device operation."""

    name: str
    description: str


OPERATIONS = {
    "device-info": Operation(
        "device-info",
        "Read basic model, Android version, build, and display information.",
    ),
    "battery": Operation("battery", "Read the current battery status from dumpsys."),
}


def run_operation(name: str, serial: str) -> tuple[Any, str]:
    """Run an operation and return its output and history summary."""
    if name == "device-info":
        result = inspect_device(serial)
        return result, json.dumps(result, sort_keys=True)
    if name == "battery":
        result = run_adb("shell", "dumpsys", "battery", serial=serial)
        return result, result
    raise ValueError(f"Unknown operation: {name}")
