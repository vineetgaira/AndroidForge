"""Read-only device operations available through the CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from androidforge.adb import run_adb
from androidforge.device import inspect_device
from androidforge.errors import AndroidForgeError


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
    "storage": Operation("storage", "Read filesystem storage capacity and usage."),
    "memory": Operation("memory", "Read system memory usage."),
    "cpu-uptime": Operation("cpu-uptime", "Read CPU summary and device uptime."),
    "processes": Operation("processes", "List running processes and services."),
    "installed-packages": Operation(
        "installed-packages", "List installed package names."
    ),
    "system-settings": Operation(
        "system-settings", "Read selected global and system settings."
    ),
    "security-build": Operation(
        "security-build", "Read Android build and security patch details."
    ),
    "wifi": Operation("wifi", "Read Wi-Fi state and connection details."),
    "mobile-network": Operation(
        "mobile-network", "Read mobile network and signal details."
    ),
    "bluetooth": Operation("bluetooth", "Read Bluetooth state and service details."),
    "network-config": Operation(
        "network-config", "Read IP addresses, routes, and DNS configuration."
    ),
    "location": Operation("location", "Read location service state."),
    "battery-health": Operation(
        "battery-health", "Read battery health, temperature, and charging state."
    ),
    "display-config": Operation(
        "display-config", "Read display size, density, and refresh configuration."
    ),
    "sensors-camera": Operation(
        "sensors-camera", "Read sensor service and camera feature availability."
    ),
}


def _shell(serial: str, *args: str) -> str:
    return run_adb("shell", *args, serial=serial)


def _settings(serial: str, namespace: str, *keys: str) -> dict[str, str]:
    values: dict[str, str] = {}
    # Settings vary by Android version and vendor, so one missing key should not
    # take down the whole read-only report.
    for key in keys:
        try:
            values[key] = _shell(serial, "settings", "get", namespace, key)
        except AndroidForgeError as exc:
            values[key] = f"unavailable: {exc}"
    return values


def _queries(serial: str, *commands: tuple[str, ...]) -> dict[str, str]:
    values: dict[str, str] = {}
    # Preserve each query independently: partial data is more useful than a blank report.
    for command in commands:
        label = " ".join(command)
        try:
            values[label] = _shell(serial, *command)
        except AndroidForgeError as exc:
            values[label] = f"unavailable: {exc}"
    return values


def run_operation(name: str, serial: str) -> tuple[Any, str]:
    """Run an operation and return its output and history summary."""
    if name == "device-info":
        result = inspect_device(serial)
        return result, json.dumps(result, sort_keys=True)
    if name == "battery":
        result = run_adb("shell", "dumpsys", "battery", serial=serial)
        return result, result
    queries: dict[str, tuple[str, ...]] = {
        "storage": ("df", "-h"),
        "memory": ("dumpsys", "meminfo"),
        "cpu-uptime": ("dumpsys", "cpuinfo"),
        "processes": ("ps", "-A"),
        "installed-packages": ("pm", "list", "packages"),
        "security-build": ("getprop",),
        "wifi": ("dumpsys", "wifi"),
        "mobile-network": ("dumpsys", "telephony.registry"),
        "bluetooth": ("dumpsys", "bluetooth_manager"),
        "network-config": ("ip", "address"),
        "location": ("dumpsys", "location"),
        "battery-health": ("dumpsys", "battery"),
        "display-config": ("dumpsys", "display"),
        "sensors-camera": ("dumpsys", "sensorservice"),
    }
    if name == "system-settings":
        result: Any = {
            "system": _settings(
                serial,
                "system",
                "screen_brightness",
                "screen_brightness_mode",
                "screen_off_timeout",
                "accelerometer_rotation",
                "user_rotation",
            ),
            "global": _settings(
                serial,
                "global",
                "airplane_mode_on",
                "wifi_on",
                "bluetooth_on",
                "location_mode",
                "auto_time",
            ),
        }
        return result, json.dumps(result, sort_keys=True)
    if name in queries:
        if name == "cpu-uptime":
            result = _queries(serial, queries[name], ("uptime",))
        elif name == "security-build":
            result = _queries(
                serial,
                ("getprop", "ro.build.version.release"),
                ("getprop", "ro.build.version.sdk"),
                ("getprop", "ro.build.version.security_patch"),
                ("getprop", "ro.build.fingerprint"),
            )
        elif name == "network-config":
            result = _queries(
                serial,
                queries[name],
                ("ip", "route"),
                ("getprop", "net.dns1"),
                ("getprop", "net.dns2"),
            )
        elif name == "display-config":
            result = _queries(serial, ("wm", "size"), ("wm", "density"), queries[name])
        elif name == "sensors-camera":
            result = _queries(
                serial,
                queries[name],
                ("dumpsys", "media.camera"),
                ("pm", "list", "features"),
            )
        else:
            result = _queries(serial, queries[name])
        return result, json.dumps(result, sort_keys=True)
    raise ValueError(f"Unknown operation: {name}")
