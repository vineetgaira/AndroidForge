"""Command line interface for AndroidForge's ADB-backed foundation."""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Any

import typer

app = typer.Typer(
    name="androidforge",
    help="A capability-driven control layer for Android devices.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)
operation_app = typer.Typer(help="List and run available device operations.")
app.add_typer(operation_app, name="operation")


class AndroidForgeError(Exception):
    """An expected, user-facing CLI error."""


def _fail(message: str) -> None:
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(code=1)


def _adb_path() -> str:
    adb = shutil.which("adb")
    if adb is None:
        raise AndroidForgeError(
            "adb was not found. Install Android platform-tools and add adb to PATH."
        )
    return adb


def _adb(*args: str, serial: str | None = None, timeout: float = 15) -> str:
    command = [_adb_path()]
    if serial:
        command.extend(("-s", serial))
    command.extend(args)
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=timeout, check=False
        )
    except subprocess.TimeoutExpired as exc:
        raise AndroidForgeError(
            f"ADB command timed out after {timeout:g}s: {shlex.join(command)}"
        ) from exc
    except OSError as exc:
        raise AndroidForgeError(f"Could not run adb: {exc}") from exc
    if result.returncode:
        detail = result.stderr.strip() or result.stdout.strip()
        raise AndroidForgeError(
            f"ADB command failed ({result.returncode}): {detail or shlex.join(command)}"
        )
    return result.stdout.strip()


def _devices() -> list[dict[str, str]]:
    output = _adb("devices", "-l")
    devices: list[dict[str, str]] = []
    for line in output.splitlines()[1:]:
        fields = line.split()
        if len(fields) < 2:
            continue
        item = {"serial": fields[0], "state": fields[1]}
        for field in fields[2:]:
            key, separator, value = field.partition(":")
            if separator:
                item[key] = value
        devices.append(item)
    return devices


def _select_device(serial: str | None) -> str:
    devices = _devices()
    usable = [item for item in devices if item["state"] == "device"]
    if serial:
        match = next((item for item in devices if item["serial"] == serial), None)
        if match is None:
            raise AndroidForgeError(f"Device {serial!r} is not listed by adb devices.")
        if match["state"] != "device":
            hint = (
                "Approve the USB debugging prompt"
                if match["state"] == "unauthorized"
                else "Check the device connection"
            )
            raise AndroidForgeError(
                f"Device {serial!r} is {match['state']}. {hint}, then try again."
            )
        return serial
    if not usable:
        if devices:
            states = ", ".join(f"{d['serial']} ({d['state']})" for d in devices)
            raise AndroidForgeError(f"No ready devices. adb reports: {states}.")
        raise AndroidForgeError(
            "No Android devices found. Connect a device and enable USB debugging."
        )
    if len(usable) > 1:
        serials = ", ".join(item["serial"] for item in usable)
        raise AndroidForgeError(
            f"More than one device is connected ({serials}); choose one with --serial."
        )
    return usable[0]["serial"]


def _getprop(serial: str, prop: str) -> str:
    try:
        return _adb("shell", "getprop", prop, serial=serial)
    except AndroidForgeError:
        return ""


def _inspect(serial: str) -> dict[str, Any]:
    props = {
        "manufacturer": "ro.product.manufacturer",
        "model": "ro.product.model",
        "device": "ro.product.device",
        "android_version": "ro.build.version.release",
        "sdk": "ro.build.version.sdk",
        "build_fingerprint": "ro.build.fingerprint",
    }
    data: dict[str, Any] = {"serial": serial}
    for key, prop in props.items():
        value = _getprop(serial, prop)
        if value:
            data[key] = value
    for key, args in (
        ("screen_size", ("wm", "size")),
        ("screen_density", ("wm", "density")),
    ):
        try:
            data[key] = _adb("shell", *args, serial=serial)
        except AndroidForgeError:
            pass
    return data


def _emit(data: Any, as_json: bool) -> None:
    if as_json:
        typer.echo(json.dumps(data, indent=2, sort_keys=True))
        return
    if isinstance(data, dict):
        width = max((len(str(key)) for key in data), default=0)
        for key, value in data.items():
            typer.echo(f"{key.replace('_', ' ').title():<{width}}  {value}")
    else:
        typer.echo(data)


def _history_path() -> Path:
    state_dir = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
    return state_dir / "androidforge" / "history.jsonl"


def _record(operation: str, serial: str, result: str) -> None:
    path = _history_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(
                json.dumps(
                    {
                        "id": datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ"),
                        "timestamp": datetime.now(UTC).isoformat(),
                        "operation": operation,
                        "serial": serial,
                        "result": result,
                        "rollback_supported": False,
                    }
                )
                + "\n"
            )
    except OSError as exc:
        raise AndroidForgeError(f"Could not write history to {path}: {exc}") from exc


@app.callback(invoke_without_command=True)
def main(
    version: Annotated[
        bool, typer.Option("--version", help="Show the version and exit.")
    ] = False,
) -> None:
    if version:
        from androidforge import __version__

        typer.echo(f"androidforge {__version__}")
        raise typer.Exit()


@app.command()
def devices(
    as_json: Annotated[bool, typer.Option("--json", help="Output JSON.")] = False,
) -> None:
    """List connected Android devices and their ADB state."""
    try:
        found = _devices()
        if as_json:
            _emit(found, True)
        elif not found:
            typer.echo("No devices found.")
        else:
            typer.echo(f"{'SERIAL':<24} {'STATE':<14} DETAILS")
            for item in found:
                details = " ".join(
                    f"{k}={v}" for k, v in item.items() if k not in {"serial", "state"}
                )
                typer.echo(f"{item['serial']:<24} {item['state']:<14} {details}")
    except AndroidForgeError as exc:
        _fail(str(exc))


@app.command()
def inspect(
    serial: Annotated[
        str | None, typer.Option("--serial", "-s", help="ADB serial to inspect.")
    ] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Output JSON.")] = False,
) -> None:
    """Show basic Android build and display information."""
    try:
        _emit(_inspect(_select_device(serial)), as_json)
    except AndroidForgeError as exc:
        _fail(str(exc))


@app.command()
def capabilities(
    serial: Annotated[
        str | None, typer.Option("--serial", "-s", help="ADB serial to inspect.")
    ] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Output JSON.")] = False,
) -> None:
    """Report capabilities currently verified through the ADB connection."""
    try:
        selected = _select_device(serial)
        identity = _adb("shell", "id", serial=selected)
        capabilities_data = {
            "serial": selected,
            "adb_connected": True,
            "shell_access": bool(identity),
            "shell_identity": identity,
            "root_access": "available" if "uid=0" in identity else "not detected",
            "shizuku": "not implemented",
            "mutating_operations": "none available",
        }
        _emit(capabilities_data, as_json)
    except AndroidForgeError as exc:
        _fail(str(exc))


OPERATIONS = {
    "device-info": "Read basic model, Android version, build, and display information.",
    "battery": "Read the current battery status from dumpsys.",
}


@operation_app.command("list")
def operation_list() -> None:
    """List available read-only operations."""
    typer.echo(f"{'NAME':<16} DESCRIPTION")
    for name, description in OPERATIONS.items():
        typer.echo(f"{name:<16} {description}")


@operation_app.command("run")
def operation_run(
    name: str,
    serial: Annotated[
        str | None, typer.Option("--serial", "-s", help="ADB serial to use.")
    ] = None,
    as_json: Annotated[
        bool, typer.Option("--json", help="Output JSON where available.")
    ] = False,
) -> None:
    """Run a named read-only operation."""
    if name not in OPERATIONS:
        _fail(
            f"Unknown operation {name!r}. Run 'androidforge operation list' "
            "to see available operations."
        )
    try:
        selected = _select_device(serial)
        if name == "device-info":
            result = _inspect(selected)
            _emit(result, as_json)
            summary = json.dumps(result, sort_keys=True)
        else:
            result = _adb("shell", "dumpsys", "battery", serial=selected)
            if as_json:
                _emit({"serial": selected, "battery": result}, True)
            else:
                typer.echo(result)
            summary = result
        _record(name, selected, summary)
    except AndroidForgeError as exc:
        _fail(str(exc))


@app.command()
def history(
    limit: Annotated[
        int, typer.Option("--limit", min=1, help="Maximum entries to show.")
    ] = 20,
    as_json: Annotated[bool, typer.Option("--json", help="Output JSON.")] = False,
) -> None:
    """Show locally recorded operation history."""
    path = _history_path()
    try:
        entries = (
            [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if path.exists()
            else []
        )
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"Could not read history at {path}: {exc}")
    entries = entries[-limit:]
    if as_json:
        _emit(entries, True)
    elif not entries:
        typer.echo("No operation history yet.")
    else:
        for entry in entries:
            typer.echo(
                f"{entry['id']}  {entry['operation']}  {entry['serial']}  "
                "rollback: unavailable"
            )


@app.command()
def rollback(operation_id: str) -> None:
    """Attempt to roll back a recorded operation when it supports rollback."""
    path = _history_path()
    try:
        entries = (
            [
                json.loads(line)
                for line in path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            if path.exists()
            else []
        )
    except (OSError, json.JSONDecodeError) as exc:
        _fail(f"Could not read history at {path}: {exc}")
    entry = next((item for item in entries if item.get("id") == operation_id), None)
    if entry is None:
        _fail(f"No history entry found for {operation_id!r}.")
    _fail(
        f"Operation {operation_id!r} ({entry.get('operation')}) "
        "has no rollback handler."
    )


@app.command("operations", hidden=True)
def operations_alias() -> None:
    """Compatibility alias for 'operation list'."""
    operation_list()


def run() -> None:
    """Run the CLI and convert expected errors to clean messages."""
    try:
        app()
    except AndroidForgeError as exc:
        _fail(str(exc))


if __name__ == "__main__":
    run()
