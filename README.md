# AndroidForge

**AndroidForge** is an open-source, capability-driven control layer for Android.

It aims to provide a unified interface for discovering device capabilities, selecting the appropriate privilege mechanism, safely executing operations, verifying results, and tracking changes across different Android devices and OEM implementations.

> **Status:** Early development — API and architecture are subject to change.

## Goals

AndroidForge is being built around a few core ideas:

* Discover what an Android device can actually do.
* Detect which backend is required for an operation.
* Support multiple privilege mechanisms such as ADB, Shizuku, and eventually root.
* Abstract OEM-specific differences.
* Validate operations before execution.
* Verify that changes actually occurred.
* Track changes and support rollback where possible.
* Provide a foundation for future Android customization and automation tools.

## Architecture

```text
                    AndroidForge
                         │
                  Capability Engine
                         │
          ┌──────────────┼──────────────┐
          │              │              │
         ADB          Shizuku         Root
          │              │              │
          └──────────────┼──────────────┘
                         │
                  Android Devices
```

The core concepts are:

```text
Device
Capability
Backend
Operation
OperationPlan
StateSnapshot
OperationResult
DeviceAdapter
```

## Current Focus

The first milestone is a CLI-based foundation.

Planned initial commands:

```bash
androidforge --version
androidforge devices
androidforge inspect
androidforge capabilities
androidforge operation list
androidforge operation run <name>
androidforge history
androidforge rollback <id>
```

Initial operations will focus on safe device inspection and basic system configuration.

## Design Principles

AndroidForge follows:

* **Capability-driven design**
* **Least privilege**
* **Validation before mutation**
* **Verification after mutation**
* **Dry-run support**
* **State snapshots**
* **Audit/history**
* **Idempotent operations where possible**
* **Explicit handling of unsupported operations**
* **OEM-specific adapters instead of hard-coded assumptions**

An operation should not simply assume that a command works.

Conceptually:

```text
Discover
   ↓
Check capability
   ↓
Plan
   ↓
Snapshot
   ↓
Confirm
   ↓
Apply
   ↓
Verify
   ↓
Record
```

## Development Philosophy

AndroidForge is being developed using a **learn-while-building** approach.

The project itself is the learning environment:

```text
Build
 ↓
Encounter an unknown
 ↓
Learn the required concept
 ↓
Implement
 ↓
Break it
 ↓
Debug
 ↓
Understand the failure
 ↓
Improve the design
 ↓
Document
```

The goal is not to hide Android's complexity behind arbitrary abstractions, but to understand the underlying systems well enough to build reliable abstractions.

## Roadmap

### v0.1

* [ ] Project structure
* [ ] CLI
* [ ] ADB backend
* [ ] Device discovery
* [ ] Device inspection
* [ ] Capability engine
* [ ] Operation registry
* [ ] Initial operations
* [ ] Validation
* [ ] Verification
* [ ] History
* [ ] Basic rollback
* [ ] Tests
* [ ] Documentation

### Future

* Shizuku backend
* Root backend
* OEM adapters
* Android application
* Theme/customization engine
* Plugin architecture
* Advanced diagnostics
* Broader device compatibility

## Project Status

AndroidForge is currently a personal open-source engineering project in early development.

The architecture, APIs, and capabilities may change significantly before the first stable release.

## License

AndroidForge is licensed under the **Apache License 2.0**.

See [`LICENSE`](LICENSE) for the full license text.

## Contributing

Contribution guidelines will be added as the project approaches its first public development release.
