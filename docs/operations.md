# Read-only operations

AndroidForge currently provides 17 read-only operations. Run `androidforge operation list` to see their names and short descriptions. Run an operation with:

```bash
androidforge operation run NAME [--serial SERIAL] [--json]
```

If exactly one ready ADB device is connected, AndroidForge selects it automatically. With multiple ready devices, pass `--serial` (or `-s`). `--json` emits JSON where the result supports it.

## Operation reference

| Operation | What it reads | Main data source |
| --- | --- | --- |
| `device-info` | Serial, manufacturer, model, Android release and SDK, build fingerprint, display size and density | `getprop`, `wm` |
| `battery` | Current battery status | `dumpsys battery` |
| `storage` | Mounted filesystem capacity and usage | `df -h` |
| `memory` | System memory usage | `dumpsys meminfo` |
| `cpu-uptime` | CPU activity summary and uptime | `dumpsys cpuinfo`, `uptime` |
| `processes` | Running processes visible to the ADB shell | `ps -A` |
| `installed-packages` | Installed package names, including system packages | `pm list packages` |
| `system-settings` | Selected brightness, screen timeout, rotation, airplane mode, Wi-Fi, Bluetooth, location, and automatic time settings | `settings get` |
| `security-build` | Android release, SDK level, security patch, and build fingerprint | `getprop` |
| `wifi` | Wi-Fi service and connection state/details | `dumpsys wifi` |
| `mobile-network` | Telephony registration and signal details exposed by the system | `dumpsys telephony.registry` |
| `bluetooth` | Bluetooth service state and details | `dumpsys bluetooth_manager` |
| `network-config` | Interface addresses, routes, and DNS properties | `ip`, `getprop` |
| `location` | Location providers and service state | `dumpsys location` |
| `battery-health` | Battery health, temperature, voltage, and charging status when reported | `dumpsys battery` |
| `display-config` | Display size, density, refresh/display service details | `wm`, `dumpsys display` |
| `sensors-camera` | Sensor service data, camera service data, and advertised hardware features | `dumpsys sensorservice`, `dumpsys media.camera`, `pm list features` |

## Examples

```bash
androidforge operation list
androidforge operation run device-info
androidforge operation run wifi --json
androidforge operation run installed-packages --serial emulator-5554
androidforge operation run network-config --json
```

## Availability and privacy

These operations only issue read queries; they do not change device settings or install, remove, or launch apps. ADB shell visibility varies across Android releases and device vendors. Some services redact details or expose different output formats; some commands may be missing or restricted. For multi-source operations, AndroidForge returns available results and labels individual failed queries as unavailable. A failure from a single-source operation is reported as an error.

Package names and process or network details can be sensitive. Treat captured output and local operation history as device data. Results are stored in the JSON Lines history file described in the main [README](../README.md#run-operations).
