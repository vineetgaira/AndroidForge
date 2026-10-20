"""Read-only device inspection and capability reporting."""

from __future__ import annotations

from typing import Any

from androidforge.adb import run_adb
from androidforge.errors import AndroidForgeError

DEVICE_PROPERTIES = {
    "manufacturer": "ro.product.manufacturer",
    "model": "ro.product.model",
    "device": "ro.product.device",
    "android_version": "ro.build.version.release",
    "sdk": "ro.build.version.sdk",
    "build_fingerprint": "ro.build.fingerprint",
}


def inspect_device(serial: str) -> dict[str, Any]:
    """Read basic build and display information from a device."""
    data: dict[str, Any] = {"serial": serial}
    for key, prop in DEVICE_PROPERTIES.items():
        try:
            value = run_adb("shell", "getprop", prop, serial=serial)
        except AndroidForgeError:
            continue
        if value:
            data[key] = value

    for key, command in (
        ("screen_size", ("wm", "size")),
        ("screen_density", ("wm", "density")),
    ):
        try:
            data[key] = run_adb("shell", *command, serial=serial)
        except AndroidForgeError:
            continue
    return data


def get_capabilities(serial: str) -> dict[str, Any]:
    """Report capabilities that have been verified for the selected device."""
    identity = run_adb("shell", "id", serial=serial)
    return {
        "serial": serial,
        "adb_connected": True,
        "shell_access": bool(identity),
        "shell_identity": identity,
        "root_access": "available" if "uid=0" in identity else "not detected",
        "shizuku": "not implemented",
        "mutating_operations": "none available",
    }
