"""Typer command definitions for AndroidForge."""

from __future__ import annotations

import json
from typing import Annotated, Any, NoReturn

import typer

from androidforge import __version__
from androidforge.adb import list_devices, select_device
from androidforge.device import get_capabilities, inspect_device
from androidforge.errors import AndroidForgeError
from androidforge.history import read_history, record_operation
from androidforge.operations import OPERATIONS, run_operation

app = typer.Typer(
    name="androidforge",
    help="A capability-driven control layer for Android devices.",
    no_args_is_help=True,
    pretty_exceptions_enable=False,
)
operation_app = typer.Typer(help="List and run available device operations.")
app.add_typer(operation_app, name="operation")


def _fail(message: str) -> NoReturn:
    typer.echo(f"Error: {message}", err=True)
    raise typer.Exit(code=1)


def _emit(data: Any, as_json: bool) -> None:
    if as_json:
        typer.echo(json.dumps(data, indent=2, sort_keys=True))
        return
    if isinstance(data, dict):
        width = max((len(str(key)) for key in data), default=0)
        for key, value in data.items():
            typer.echo(f"{key.replace('_', ' ').title():<{width}}  {value}")
        return
    typer.echo(data)


def _handle_error(error: AndroidForgeError) -> None:
    _fail(str(error))


@app.callback(invoke_without_command=True)
def main(
    version: Annotated[
        bool, typer.Option("--version", help="Show the version and exit.")
    ] = False,
) -> None:
    """Show general AndroidForge command options."""
    if version:
        typer.echo(f"androidforge {__version__}")
        raise typer.Exit()


@app.command()
def devices(
    as_json: Annotated[bool, typer.Option("--json", help="Output JSON.")] = False,
) -> None:
    """List connected Android devices and their ADB state."""
    try:
        found = list_devices()
        if as_json:
            _emit(found, True)
        elif not found:
            typer.echo("No devices found.")
        else:
            typer.echo(f"{'SERIAL':<24} {'STATE':<14} DETAILS")
            for device in found:
                details = " ".join(
                    f"{key}={value}"
                    for key, value in device.items()
                    if key not in {"serial", "state"}
                )
                typer.echo(f"{device['serial']:<24} {device['state']:<14} {details}")
    except AndroidForgeError as exc:
        _handle_error(exc)


@app.command()
def inspect(
    serial: Annotated[
        str | None, typer.Option("--serial", "-s", help="ADB serial to inspect.")
    ] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Output JSON.")] = False,
) -> None:
    """Show basic Android build and display information."""
    try:
        _emit(inspect_device(select_device(serial)), as_json)
    except AndroidForgeError as exc:
        _handle_error(exc)


@app.command()
def capabilities(
    serial: Annotated[
        str | None, typer.Option("--serial", "-s", help="ADB serial to inspect.")
    ] = None,
    as_json: Annotated[bool, typer.Option("--json", help="Output JSON.")] = False,
) -> None:
    """Report capabilities currently verified through the ADB connection."""
    try:
        selected = select_device(serial)
        _emit(get_capabilities(selected), as_json)
    except AndroidForgeError as exc:
        _handle_error(exc)


@operation_app.command("list")
def operation_list() -> None:
    """List available read-only operations."""
    typer.echo(f"{'NAME':<16} DESCRIPTION")
    for operation in OPERATIONS.values():
        typer.echo(f"{operation.name:<16} {operation.description}")


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
        selected = select_device(serial)
        result, summary = run_operation(name, selected)
        if name == "battery" and as_json:
            _emit({"serial": selected, "battery": result}, True)
        else:
            _emit(result, as_json)
        record_operation(name, selected, summary)
    except AndroidForgeError as exc:
        _handle_error(exc)


@app.command()
def history(
    limit: Annotated[
        int, typer.Option("--limit", min=1, help="Maximum entries to show.")
    ] = 20,
    as_json: Annotated[bool, typer.Option("--json", help="Output JSON.")] = False,
) -> None:
    """Show locally recorded operation history."""
    try:
        entries = read_history()[-limit:]
    except AndroidForgeError as exc:
        _handle_error(exc)
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
    """Look up a history entry and report whether rollback is available."""
    try:
        entries = read_history()
    except AndroidForgeError as exc:
        _handle_error(exc)
    entry = next((item for item in entries if item.get("id") == operation_id), None)
    if entry is None:
        _fail(f"No history entry found for {operation_id!r}.")
    if not entry.get("rollback_supported", False):
        _fail(
            f"Operation {operation_id!r} ({entry.get('operation')}) "
            "has no rollback handler."
        )
    _fail("This operation's rollback handler is not available in this CLI version.")


@app.command("operations", hidden=True)
def operations_alias() -> None:
    """Compatibility alias for 'operation list'."""
    operation_list()


if __name__ == "__main__":
    app()
