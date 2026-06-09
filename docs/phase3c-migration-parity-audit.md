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

    system_info
    docker
    local_storage
    backup_status
    snapshots
    replications

These example configuration switches are not operational collector gates:

    pools
    apps
    services

`system_info` became operational in Phase 3C.2. `pools` remains a genuine
missing public capability.

Configured services are selected through their service-level `check`
value and host eligibility rather than `modules.apps` or
`modules.services`.

Those two flags require later clarification, deprecation, or removal.

## Migration parity matrix

| Capability | Public state | Parity | Required work |
|---|---|---:|---|
| Host inventory | Configuration-driven | Partial | Move production inventory entirely into configuration |
| Host Web UI reachability | Implemented | Partial | Define global severity behavior |
| Hostname, OS, kernel, uptime, CPU, memory, load | Implemented | Supported | Completed in Phase 3C.2 |
| Collector-local system information | Implemented | Supported | Local telemetry requires no SSH |
| Remote Linux and TrueNAS system information | Implemented | Supported | Host-aware SSH telemetry with conservative failure handling |
| TrueNAS pool inventory | Reference-only | Missing | Operationalize `modules.pools` |
| Pool size and capacity | Reference-only | Missing | Add generic capacity collection |
| ZFS pool health | Reference-only | Missing | Add health status and severity |
| Pool temperatures | Implemented | Supported | Completed in Phase 3C.4 |
| SMART health | Implemented | Supported | Completed in Phase 3C.4 |
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

## Phase 3C.2 completion

Phase 3C.2 operationalized `modules.system_info` while preserving the
reference runtime unchanged.

The public runtime now supports:

- collector-local Linux system information without SSH;
- remote Linux system information over explicit host-specific SSH;
- remote TrueNAS system information and application activity over explicit
  host-specific SSH;
- hostname, OS, kernel, uptime, CPU, memory, load, and Apps or Containers
  activity fields;
- `NOT CHECKED`, `UNKNOWN`, and `UNREACHABLE` failure semantics;
- partial successful payloads without invented values;
- generic configured-host system-information cards;
- system-information propagation into the public Systems summary;
- validation and startup-preflight enforcement for remote hosts.

System-information results intentionally do not contribute to global Overall
Status yet. That severity boundary remains assigned to Phase 3C.6.

## Phase 3C.3 completion

Phase 3C.3 operationalized `modules.pools` while preserving the
reference runtime unchanged.

The public runtime now supports:

- enabled TrueNAS pool hosts selected through `modules.pools: true`;
- explicit host-specific SSH identities and startup-preflight discovery;
- live `midclt call pool.query` collection;
- pool name, ZFS status, total capacity, allocated capacity, available
  capacity, and calculated allocation percentage;
- conservative `OK`, `WARNING`, `CRITICAL`, and `UNKNOWN` pool-health
  classification;
- `NOT CHECKED`, `UNKNOWN`, and `UNREACHABLE` host-level failure
  semantics;
- generic Configured TrueNAS Pools Runtime Detail output;
- live pool rows and host failures in the public Storage summary card;
- configuration validation requiring TrueNAS host type and explicit SSH.

Pool severity intentionally affects only the public Storage card and
Runtime Detail. It does not yet contribute to global Overall Status;
that unified severity boundary remains assigned to Phase 3C.6.

Validation included 212 deterministic regression tests, official and
starter configuration validation, real read-only pool queries against
two TrueNAS hosts with seven pools discovered, deterministic faulted-pool
severity testing, public/reference isolation, and unchanged production
dashboard output.

## Phase 3C.4 completion

Phase 3C.4 operationalized configuration-driven TrueNAS temperature
and SMART monitoring while preserving the reference runtime unchanged.

The public runtime now supports:

- independent `modules.temperatures` and `modules.smart` switches;
- enabled TrueNAS hosts with explicit host-specific SSH identities;
- pool-to-device mapping through `zpool status -P`;
- temperature collection through `midclt call disk.temperatures`;
- pool-level average and maximum temperature summaries;
- separate SATA/SAS and NVMe temperature thresholds;
- conservative `smartctl -H` health classification;
- explicit SMART and NVMe failures reported as `CRITICAL`;
- unavailable or unrecognized SMART data reported as `UNKNOWN`;
- worst-severity aggregation across temperature and SMART results;
- public Storage-card integration;
- a promoted TrueNAS disk-health runtime detail table;
- validator and startup-preflight enforcement;
- deterministic regression coverage for collection, parsing,
  classification, rendering, configuration gates, and SSH requirements.

Temperature and SMART results intentionally do not contribute to global
Overall Status yet. That severity boundary remains assigned to
Phase 3C.6.

## Phase 3C.5 completion — data-protection severity parity

Phase 3C.5 establishes one deterministic public severity contract
across the configuration-driven data-protection domain.

The public Protection summary card now aggregates:

- configured backup-marker checks;
- live TrueNAS snapshot-task rows;
- live TrueNAS replication-task rows;
- configured protection relationships and their live overlays.

Protection results use worst-state precedence:

```text
CRITICAL > WARNING > INFO > OK
```

The normalized contract is:

- `CRITICAL`: missing backup markers, missing required snapshots,
  and failed, errored, or aborted replication tasks;
- `WARNING`: stale backups, inactive or uncertain timers, stale or
  disabled snapshot tasks, paused or disabled replication tasks,
  unknown states, malformed responses, SSH failures, parsing
  failures, schedule uncertainty, and collector uncertainty;
- `INFO`: active replication states such as `RUNNING`, `PENDING`,
  and `WAITING`, plus configuration-only relationship intent;
- `OK`: current backup markers, fresh snapshots, successful
  replication tasks, and healthy matched relationships.

Unknown protection-check results are therefore warning-grade and
cannot silently leave the Protection card healthy. Disabled
snapshot and replication tasks are also warning-grade because an
expected protection mechanism is not operating.

Relationship overlays retain their conservative matching rules.
Snapshot status propagates only when every configured dataset has
confident coverage. Replication status propagates only when source
host, source datasets, and target prefix match confidently. When
both sources match, the worst live severity wins.

The change is isolated to the configuration-driven Protection
domain. Global Overall Status remains unchanged and is reserved
for Phase 3C.6.

Deterministic validation completed with 230 passing tests. An
isolated public render confirmed the integrated Protection card
contract without modifying the production dashboard.

## Validated Phase 3C sequence

    Phase 3C.1  Reference-to-public migration parity audit
                 Complete

    Phase 3C.2  Config-driven host system information parity
                 Complete

    Phase 3C.3  Config-driven TrueNAS pool capacity and health parity
                 Complete

    Phase 3C.4  Config-driven TrueNAS temperature and SMART parity
                 Complete

    Phase 3C.5  Data-protection severity parity
                 Complete

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
