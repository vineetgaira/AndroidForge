# AndroidForge

AndroidForge is an early-stage, ADB-backed command-line tool for inspecting Android devices. Its current operations are read-only. The project aims to grow into a capability-driven control layer with validation, verification, history, and rollback support.

## Requirements

- Python 3.11 or newer
- Android SDK Platform-Tools (`adb`) installed and available on `PATH`
- An Android device with USB debugging enabled, or an ADB-connected emulator

When connecting a physical device, unlock it and accept the USB debugging authorization prompt. Check that ADB can see it with `adb devices -l`.

## Install for development

From the repository root, create the development environment and install AndroidForge:

```bash
uv sync --extra dev
```

Run the CLI through uv:

```bash
uv run androidforge --help
```

Or install the project into the active Python environment with `python -m pip install -e .`, then run `androidforge` directly.

## Commands

```text
androidforge --version
androidforge devices [--json]
androidforge inspect [--serial SERIAL] [--json]
androidforge capabilities [--serial SERIAL] [--json]
androidforge operation list
androidforge operation run NAME [--serial SERIAL] [--json]
androidforge history [--limit COUNT] [--json]
androidforge rollback ID
```

### Find and select a device

List devices and their connection states:

```bash
androidforge devices
androidforge devices --json
```

Inspection commands select the only ready device automatically. If more than one device is ready, pass its serial using `--serial` (or `-s`):

```bash
androidforge inspect --serial emulator-5554
```

`inspect` shows the serial, manufacturer, model, Android version, SDK level, build fingerprint, and display size and density when the device provides them. `capabilities` reports the ADB shell identity and the capabilities AndroidForge currently recognizes. It does not attempt to enable root or Shizuku.

### Run operations

See the available operations:

```bash
androidforge operation list
```

Currently available operations are read-only:

- `device-info` reads basic build and display information.
- `battery` reads the output of Android's `dumpsys battery` command.

For example:

```bash
androidforge operation run device-info
androidforge operation run battery --serial emulator-5554 --json
```

Operation results are recorded locally in JSON Lines format at `$XDG_STATE_HOME/androidforge/history.jsonl`, or at `~/.local/state/androidforge/history.jsonl` when `XDG_STATE_HOME` is not set. View recent entries with `androidforge history`; use `--limit` to change the number shown or `--json` to output JSON.

### Rollback status

The `rollback` command can look up a history entry, but no current operation has a rollback handler because all available operations only read device state. It reports that limitation for a valid entry. No device changes can currently be made through AndroidForge.

## Development checks

Format and lint the Python package with the project's Ruff configuration:

```bash
ruff format src/androidforge
ruff check src/androidforge
```

## Project direction

AndroidForge is being developed incrementally. Planned work includes broader device capability discovery, safe configuration operations, validation before changes, verification afterward, and rollback for operations that can be reversed. Shizuku, root backends, and OEM-specific adapters are future work.

The project is licensed under the Apache License 2.0; see [LICENSE](LICENSE).
