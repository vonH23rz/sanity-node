# Phase 3C.1 — Reference-to-public migration parity audit

Status: complete
Baseline: `7f4b523` — Merge public dashboard layout promotion
Audit date: 2026-06-09

## Purpose

Phase 3C migrates generic monitoring capabilities that remain available
only in the hardcoded reference runtime into the configuration-driven
public runtime.

This audit defines the migration boundary before implementation begins.
It does not modify or retire reference mode.

## Architectural boundary

Sanity Node currently has two explicit runtime paths.

### Public runtime

Public mode uses:

    dashboard:
      runtime_mode: public

The public runtime:

- reads monitoring inventory from configuration
- executes configuration-driven collectors only
- renders the promoted four-card public layout
- excludes personal reference collectors and output
- supports deterministic isolated first-run validation

### Reference runtime

Reference mode uses:

    dashboard:
      runtime_mode: reference

The reference runtime:

- preserves the original hardcoded production deployment
- contains the original host, pool, temperature, SMART, snapshot,
  replication, and service behavior
- remains the default when `runtime_mode` is absent
- stays intact until migration parity has been proven

## Audit method

The repository was inspected read-only before this documentation branch
was created.

The audit covered:

- runtime-mode isolation
- reference collectors and presentation
- public collectors and configuration schema
- module gating
- summary-card inputs
- collector-error handling
- Overall Status contributions
- deterministic test coverage
- personal and production-specific assumptions

No runtime or production files were modified.

## Module-gating findings

The generator currently consumes these host module switches:

    docker
    local_storage
    backup_status
    snapshots
    replications

These example configuration switches are not operational collector gates:

    system_info
    pools
    apps
    services

`system_info` and `pools` represent genuine missing public capabilities.

Configured services are selected through their service-level `check`
value and host eligibility rather than `modules.apps` or
`modules.services`.

Those two flags require later clarification, deprecation, or removal.

## Migration parity matrix

| Capability | Public state | Parity | Required work |
|---|---|---:|---|
| Host inventory | Configuration-driven | Partial | Move production inventory entirely into configuration |
| Host Web UI reachability | Implemented | Partial | Define global severity behavior |
| Hostname, OS, kernel, uptime, CPU, memory, load | Missing | Missing | Operationalize `modules.system_info` |
| Collector-local system information | Missing | Missing | Add local telemetry |
| Remote Linux and TrueNAS system information | Missing | Missing | Add host-aware SSH telemetry |
| TrueNAS pool inventory | Reference-only | Missing | Operationalize `modules.pools` |
| Pool size and capacity | Reference-only | Missing | Add generic capacity collection |
| ZFS pool health | Reference-only | Missing | Add health status and severity |
| Pool temperatures | Reference-only | Missing | Generalize temperature collection |
| SMART health | Reference-only | Missing | Generalize disk mapping and SMART checks |
| Local and remote filesystem capacity | Implemented | Supported | Connect to unified severity |
| Backup marker and timer checks | Implemented | Partial | Connect to unified severity |
| Snapshot task and freshness checks | Implemented | Partial | Connect to unified severity |
| Replication task checks | Implemented | Partial | Connect to unified severity |
| Protection overlays | Implemented | Partial | Define final severity behavior |
| Collector-local Docker services | Implemented | Supported | No new collector required |
| Remote Linux Docker services | Implemented | Supported | No new collector required |
| TrueNAS application services | Implemented | Supported | No new collector required |
| HTTP and manual services | Implemented | Supported | Move personal services into config |
| Service links and app/helper types | Implemented | Supported | Populate through config |
| Image-update monitoring | Implemented | Supported | Keep `UPDATE` informational |
| TrueNAS host-unreachable collapse | Implemented | Partial | Integrate with broader host health |
| Collector-error presentation | Implemented | Partial | Define severity contribution |
| Four-card public summary | Implemented | Supported | Do not copy the legacy layout |
| Public Overall Status | Service results only | Major gap | Add unified cross-domain aggregation |

## Overall Status findings

Public Overall Status currently reacts to configured services:

    bad configured service     -> NOK
    non-UP configured service  -> INFO
    all configured services UP -> OK

These visible public results do not currently affect Overall Status:

    host Web UI failures
    local-storage warnings and failures
    backup warnings and failures
    snapshot warnings and failures
    replication warnings and failures
    protection warnings and failures
    collector errors
    host-unreachable summaries

Image updates should remain informational rather than service failures.

Pools, temperatures, and SMART cannot contribute until their public
collectors exist.

Unified severity is therefore a major migration-parity requirement.

## Generic behavior to migrate

The following belongs in the public project when implemented generically:

- collector-local and remote host information
- TrueNAS pool inventory, capacity, and ZFS health
- temperature interpretation
- SMART health interpretation
- deterministic host reachability
- protection and backup severity
- cross-domain Overall Status aggregation
- collector-error severity policy

## Personal data to keep in production configuration

The following must not become public hardcoded values:

- hostnames and IP addresses
- service names and URLs
- dataset and replication paths
- host ordering
- SSH users and key paths
- backup destinations
- host-specific notes
- deployment-specific filesystem paths

A personal warning must emerge from generic collector output and
configuration rather than from a hardcoded hostname or pool note.

## Legacy presentation not to migrate

The public runtime should not reproduce:

- the original five-card reference summary
- personal host ordering
- hardcoded source and target labels
- fixed personal snapshot or replication titles
- duplicated host and service inventories

Phase 3C migrates monitoring capability, not the personal dashboard
structure.

## Risk assessment

High risk:

- system-information collection
- pool collection
- temperature and SMART device mapping
- unified Overall Status semantics
- production cutover without silent monitoring loss

Medium risk:

- backup and protection severity
- collector-error severity
- generalized host reachability
- unused module-flag compatibility

Low risk:

- service inventory
- manual HTTP services
- service links and classification
- image-update overlays
- public four-card presentation

## Validated Phase 3C sequence

    Phase 3C.1  Reference-to-public migration parity audit
                 Complete

    Phase 3C.2  Config-driven host system information parity
                 Operationalize modules.system_info

    Phase 3C.3  Config-driven TrueNAS pool capacity and health parity
                 Operationalize modules.pools

    Phase 3C.4  Config-driven TrueNAS temperature and SMART parity

    Phase 3C.5  Data-protection severity parity

    Phase 3C.6  Unified public Overall Status and collector-error parity

    Phase 3C.7  Public schema and presentation consolidation

    Phase 3C.8  Production configuration migration rehearsal

    Phase 3C.9  Public-mode production cutover rehearsal

    Phase 3C.10 Reference retirement decision

A separate service-inventory migration slice is unnecessary. Docker,
TrueNAS application, HTTP/manual service, service-link, classification,
image-update, and host-unreachable support are already configuration
driven.

## Phase 3C safeguards

Every Phase 3C implementation slice must:

- inspect before editing
- use one narrow feature branch
- preserve reference mode
- preserve public personal-data isolation
- preserve fail-closed startup behavior
- preserve safe first-run behavior
- add deterministic tests
- run the full regression suite
- compile Python and validate shell syntax
- validate starter and example configurations
- render test output only under `/tmp`
- use isolated Docker fixtures
- protect the production dashboard hash and mtime
- avoid SSH authorization changes solely for testing
- preserve remote feature branches
- merge with `--no-ff`
- delete only the merged local feature branch

## Completion criteria

Phase 3C.1 is complete when:

- the parity boundary is documented
- missing generic capabilities are separated from personal inventory
- legacy presentation is excluded from migration scope
- the public Overall Status gap is recorded
- the implementation sequence is evidence-based
- no runtime or production files are changed

## Audit conclusion

The public runtime already contains substantial configuration-driven
coverage. Service inventory is not the principal migration blocker.

The required path to production parity is:

1. add generic system telemetry;
2. add TrueNAS pool, temperature, and SMART telemetry;
3. connect existing storage and protection results to global severity;
4. rehearse the full production configuration in isolation;
5. make a separate, explicit reference-retirement decision.

Reference mode remains the known-good fallback throughout this work.
