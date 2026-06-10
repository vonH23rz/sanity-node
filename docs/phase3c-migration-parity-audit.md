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

    apps
    services

`system_info` became operational in Phase 3C.2 and `pools` became
operational in Phase 3C.3.

Configured services are selected through their service-level `check`
value and host eligibility rather than `modules.apps` or
`modules.services`.

Those two compatibility flags require later clarification,
deprecation, or removal.

## Migration parity matrix

| Capability | Public state | Parity | Required work |
|---|---|---:|---|
| Host inventory | Configuration-driven | Supported | Complete production inventory rehearsed in isolated configuration during Phase 3C.8 |
| Host Web UI reachability | Implemented | Supported | Integrated into the Systems domain in Phase 3C.6 |
| Hostname, OS, kernel, uptime, CPU, memory, load | Implemented | Supported | Completed in Phase 3C.2 |
| Collector-local system information | Implemented | Supported | Local telemetry requires no SSH |
| Remote Linux and TrueNAS system information | Implemented | Supported | Host-aware SSH telemetry with conservative failure handling |
| TrueNAS pool inventory | Implemented | Supported | Completed in Phase 3C.3 |
| Pool size and capacity | Implemented | Supported | Completed in Phase 3C.3 |
| ZFS pool health | Implemented | Supported | Completed in Phase 3C.3 |
| Pool temperatures | Implemented | Supported | Completed in Phase 3C.4 |
| SMART health | Implemented | Supported | Completed in Phase 3C.4 |
| Local and remote filesystem capacity | Implemented | Supported | Unified in Phase 3C.6 |
| Backup marker and timer checks | Implemented | Supported | Unified in Phase 3C.6 |
| Snapshot task and freshness checks | Implemented | Supported | Unified in Phase 3C.6 |
| Replication task checks | Implemented | Supported | Unified in Phase 3C.6 |
| Protection overlays | Implemented | Supported | Severity normalized in Phase 3C.5 and unified in Phase 3C.6 |
| Collector-local Docker services | Implemented | Supported | No new collector required |
| Remote Linux Docker services | Implemented | Supported | No new collector required |
| TrueNAS application services | Implemented | Supported | No new collector required |
| HTTP and manual services | Implemented | Supported | Populate through config |
| Service links and app/helper types | Implemented | Supported | Populate through config |
| Image-update monitoring | Implemented | Supported | `UPDATE` remains informational |
| TrueNAS host-unreachable collapse | Implemented | Supported | Integrated into unified host health |
| Collector-error presentation | Implemented | Supported | Severity and deduplication completed in Phase 3C.6 |
| Four-card public summary | Implemented | Supported | Public layout retained |
| Public Runtime Detail presentation | Implemented | Supported | Explicit builder context completed in Phase 3C.7 |
| Shared public severity classification | Implemented | Supported | Overall Status and Systems summary share one contract from Phase 3C.7 |
| Public Overall Status | Implemented | Supported | Unified cross-domain aggregation completed in Phase 3C.6 |

## Overall Status findings

Phase 3C.6 closes the unified-severity migration gap. Public Overall
Status now evaluates configuration-driven results in deterministic
domain order:

    Systems
    Storage
    Protection
    Services
    Uncovered collector errors

Global severity follows:

    NOK > WARNING > INFO > OK

Critical domain results produce `NOK`; warning and disabled results
produce `WARNING`; uncertain, active, update, and other informational
results produce `INFO`; healthy results produce `OK`.

Collector errors are classified separately. Critical transport failures
can produce `NOK`; authentication, host-key, parsing, command, unknown,
and other collector failures are warning-grade. Image-update collector
failures remain warning-grade.

Collector errors already represented by a domain result elevate that
result when necessary instead of creating a duplicate issue. Placeholder
raw values do not consume collector errors. The first issue at the
highest active severity becomes the displayed Overall Status note.

Reference-mode Overall Status remains unchanged.

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

At Phase 3C.2 completion, integration with global Overall Status was
intentionally deferred. Phase 3C.6 now consumes system-information and
host-health results through the public Systems domain.

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

At Phase 3C.3 completion, pool severity was limited to the public
Storage card and Runtime Detail. Phase 3C.6 now includes pool and
host-level pool health in unified public Overall Status.

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

At Phase 3C.4 completion, temperature and SMART severity remained
limited to the Storage domain. Phase 3C.6 now includes these disk-health
results in unified public Overall Status.

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

At Phase 3C.5 completion, the normalized contract remained isolated
to the configuration-driven Protection domain. Phase 3C.6 now consumes
that contract as part of unified public Overall Status.

Deterministic validation completed with 230 passing tests. An
isolated public render confirmed the integrated Protection card
contract without modifying the production dashboard.

## Phase 3C.6 completion — unified public Overall Status

Phase 3C.6 establishes one deterministic public Overall Status across
the complete configuration-driven runtime.

The aggregation consumes results in this order:

1. Systems;
2. Storage;
3. Protection;
4. Services;
5. uncovered collector errors.

The global result follows `NOK > WARNING > INFO > OK`. The first issue
at the highest active severity becomes the displayed note.

Systems includes configured host Web UI, system-information, and
service-derived reachability. Storage includes local and remote
filesystem checks, TrueNAS pool health, temperatures, and SMART health.
Protection includes backup-marker checks, snapshot tasks, replication
tasks, and configured relationships. Services includes HTTP, local and
remote Docker, and TrueNAS application status after image-update
overlays.

Collector errors are classified and contribute conservatively.
Network, timeout, and refused-connection failures are critical.
Authentication, host-key, parsing, command, unknown, and other failures
are warning-grade. Image-update collector failures remain
warning-grade.

When the same failure is already represented by a domain result, the
domain result is elevated when necessary and the collector issue is
deduplicated. Placeholder raw values such as `-`, `N/A`, `none`, and
`unknown` do not suppress uncovered collector failures.

The implementation is active only in `public` mode. Reference mode
retains its original collectors, presentation, and Overall Status
behavior.

Validation completed with 182 configuration-runtime tests and 240
tests across complete unittest discovery. Python compilation, shell
syntax, configuration validation, Docker Compose validation, isolated
safe rendering, test-structure guards, and public/reference runtime
regressions passed. The isolated render produced a configuration-driven
`NOK` result for an unreachable example host while the production
dashboard hash and modification time remained unchanged.

## Phase 3C.7 completion — public schema and presentation consolidation

Phase 3C.7 removes the post-render whole-HTML promotion shim and makes
public or reference presentation an explicit input to every
configuration-driven Runtime Detail builder.

Public mode now renders `Runtime Detail`, current Overall Status
contribution descriptions, and public-safe result wording directly at
the source. Reference mode retains its existing `Config Preview`
compatibility presentation. Collector results and status dictionaries
remain unchanged by presentation rendering.

The Overall Status severity classifier was also promoted to the shared
`public_status_severity()` contract. Unified public Overall Status and
the Systems summary now classify healthy, informational, warning, and
critical states consistently. In particular, a healthy Web UI result
with unavailable optional telemetry remains healthy, while warning-grade
system telemetry produces a warning card.

Validation completed with 187 configuration-runtime tests and 245 tests
across complete unittest discovery. Python and shell syntax checks,
configuration validation, Docker Compose validation, AST/test-harness
guards, isolated public rendering, and public/reference regressions all
passed. The production dashboard hash and modification time remained
unchanged, and the production generation timer remained active and
enabled.


## Phase 3C.8 completion — production configuration migration rehearsal

Phase 3C.8 translated the complete current production monitoring
inventory into an isolated configuration without adding personal
deployment data to runtime code or tracked repository configuration.

The rehearsal configuration represented three systems, twenty-three
services, two collector-local storage checks, one backup check, one
off-host protection relationship covering six datasets, three
image-update sources, and all four public summary cards. Configuration
validation completed with zero errors and zero warnings.

Host-native public execution passed startup preflight and reached full
monitoring parity. It discovered seven data pools, nine pool-level
disk-health results, twelve snapshot tasks, eight replication tasks,
all configured services, and all configured collector-local checks.
Reference collectors were skipped and production remained unchanged.

The standard container deployment also validated, started, served, and
passed its health check. It did not reach production parity because the
container boundary lacked verified SSH host trust, collector Docker
access, host filesystem identity, backup marker and host-systemd state,
and access to collector-local endpoints.

Ordinary Docker bridge networking reached the remote systems and remote
HTTP services successfully. The remaining network failure was limited
to reaching services back on the collector host, confirming a
collector self-reachability boundary rather than a general LAN routing
problem.

The complete evidence and Phase 3C.9 boundary are documented in
`docs/phase3c-production-configuration-rehearsal.md`.

Phase 3C.8 therefore closes production-configuration representation and
identifies deployment integration as the remaining cutover concern.
No runtime change was required.

## Phase 3C.9 completion — public-mode production cutover rehearsal

Phase 3C.9 installed the host-native public runtime as an isolated
parallel candidate while preserving the reference runtime as the served
production path.

The rehearsal validated:

- fail-closed configuration validation and startup preflight;
- public-mode presentation and complete configured monitoring coverage;
- atomic output publication with isolated ownership and permissions;
- locale-stable runtime-duration logging;
- three consecutive scheduled public runs beside two scheduled reference
  runs;
- timer stop, restart, disablement, manual service restart, and
  re-enablement;
- full removal, reference-only operation, exact restoration, and resumed
  scheduled operation.

The reference generator remained unchanged. The reference timer remained
the known-good production path throughout the rehearsal.

Phase 3C.9 therefore confirms that the host-native public deployment
model is technically ready for a controlled production cutover. It does
not switch the served dashboard or retire reference mode.

## Phase 3C.10 completion — reference retirement and production cutover

Phase 3C.10 selected Option B and completed the controlled production
cutover.

The completed state is:

- the permanent host-native public runtime under `/opt/sanity-node` owns the
  served dashboard;
- the permanent web service and generation timer are active and enabled;
- the retained reference runtime is installed but disabled;
- the public rehearsal runtime is retained but disabled;
- the existing reverse-proxy route remains unchanged;
- permanent deletion of the reference implementation still requires a
  separate later decision.

The production activation included an inactive installation, private
configuration migration, manual generation, a temporary cutover, a complete
rollback rehearsal, rollback-state verification, final cutover, and
multiple consecutive scheduled permanent generations.

Commit `bf0aa34` corrected the permanent web-service startup ordering. The
web service no longer starts or requires the generator, and scheduled
generation does not restart the web service.

Atomic output publication, local and reverse-proxy output equivalence,
configured monitoring coverage, and retained fallback integrity were
confirmed throughout observation.

The detailed decision, permanent runtime contract, completed cutover,
rollback procedure, retained fallback state, retention period, and release
boundary are documented in
`docs/phase3c-reference-retirement-decision.md`.

Phase 3C is complete. After completion publication and merge verification,
`main` becomes the `v0.3.0` release candidate. The release tag remains
deferred until the clean public installation journey is qualified.

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
                 Complete

    Phase 3C.7  Public schema and presentation consolidation
                 Complete

    Phase 3C.8  Production configuration migration rehearsal
                 Complete

    Phase 3C.9  Public-mode production cutover rehearsal
                 Complete

    Phase 3C.10 Reference retirement and production cutover
                 Complete

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

The generic collector, severity, schema, presentation, and production
configuration representation gaps are closed through Phase 3C.8.

Host-native public execution reached complete monitoring parity. The
standard container identified explicit deployment integration
requirements rather than missing runtime capability.

The retirement decision, controlled production cutover, rollback
rehearsal, and sustained scheduled observation are complete.

The permanent public runtime now owns production. The reference and
rehearsal runtimes remain installed but disabled, and the reference runtime
remains available for the documented rollback-retention period.

Phase 3C is closed. Completion publication and merge verification establish
the merged `main` branch as the `v0.3.0` release candidate. The actual
release remains gated by the clean public installation qualification,
installation and deployment documentation, changelog, and final release
validation.
