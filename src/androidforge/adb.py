"""ADB command execution and device selection."""

from __future__ import annotations

import shlex
import shutil
import subprocess

from androidforge.errors import AndroidForgeError


def run_adb(*args: str, serial: str | None = None, timeout: float = 15) -> str:
    """Run an ADB command and return its standard output."""
    adb = shutil.which("adb")
    if adb is None:
        raise AndroidForgeError(
            "adb was not found. Install Android platform-tools and add adb to PATH."
        )

    command = [adb]
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


def list_devices() -> list[dict[str, str]]:
    """Return devices and metadata reported by ``adb devices -l``."""
    output = run_adb("devices", "-l")
    devices: list[dict[str, str]] = []
    for line in output.splitlines()[1:]:
        fields = line.split()
        if len(fields) < 2:
            continue
        device = {"serial": fields[0], "state": fields[1]}
        for field in fields[2:]:
            key, separator, value = field.partition(":")
            if separator:
                device[key] = value
        devices.append(device)
    return devices


def select_device(serial: str | None = None) -> str:
    """Return the selected ready device serial or raise an actionable error."""
    devices = list_devices()
    ready_devices = [device for device in devices if device["state"] == "device"]

    if serial:
        device = next((item for item in devices if item["serial"] == serial), None)
        if device is None:
            raise AndroidForgeError(f"Device {serial!r} is not listed by adb devices.")
        if device["state"] != "device":
            hint = (
                "Approve the USB debugging prompt"
                if device["state"] == "unauthorized"
                else "Check the device connection"
            )
            raise AndroidForgeError(
                f"Device {serial!r} is {device['state']}. {hint}, then try again."
            )
        return serial

    if not ready_devices:
        if devices:
            states = ", ".join(
                f"{device['serial']} ({device['state']})" for device in devices
            )
            raise AndroidForgeError(f"No ready devices. adb reports: {states}.")
        raise AndroidForgeError(
            "No Android devices found. Connect a device and enable USB debugging."
        )

    if len(ready_devices) > 1:
        serials = ", ".join(device["serial"] for device in ready_devices)
        raise AndroidForgeError(
            f"More than one device is connected ({serials}); choose one with --serial."
        )
    return ready_devices[0]["serial"]
