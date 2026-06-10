# Phase 3C.8 — Production configuration migration rehearsal

Status: complete

## Purpose

Phase 3C.8 verifies that the configuration-driven public runtime can
represent the complete current production monitoring inventory without
cutting production over.

The rehearsal separates two questions:

1. can the public runtime represent and collect the production
   inventory correctly;
2. can the standard container deployment access every collector-local
   production resource correctly.

The rehearsal was performed read-only and used only isolated
configuration, output, log, SSH, Compose, container, image, and network
resources.

No production generator, dashboard, configuration, service, timer, SSH
authorization, or monitoring endpoint was modified.

## Rehearsed configuration scope

The isolated production configuration represented:

- three enabled systems;
- twenty-three enabled services;
- eight collector-local Docker checks;
- eleven native TrueNAS application checks;
- four HTTP checks;
- two collector-local filesystem checks;
- one backup-marker and timer check;
- one off-host replication relationship covering six datasets;
- three image-update sources;
- all four public summary cards.

All personal deployment inventory remained in the isolated
configuration. No hostnames, addresses, URLs, dataset names, key paths,
or deployment-specific service definitions were added to runtime code
or committed documentation.

Configuration validation completed with zero errors and zero warnings.

## Host-native rehearsal result

The public generator was executed directly on the collector host while
using the isolated production configuration and isolated output paths.

Startup preflight passed and identified both remote storage systems as
requiring SSH-backed monitoring.

The host-native public runtime discovered and rendered:

- all three configured systems;
- all twenty-three configured services;
- seven data pools;
- nine pool-level disk-health results;
- twelve snapshot tasks;
- eight replication tasks;
- the complete configured protection relationship;
- all configured collector-local storage and backup checks;
- all configured image-update sources.

The result reached functional production parity.

At rehearsal time, Overall Status was informational because one healthy
service had an available image update. No monitoring domain was degraded
or missing.

The reference runtime was skipped, public Runtime Detail wording was
rendered directly, and no compatibility-only Config Preview wording was
visible.

## Standard container rehearsal result

The same configuration was then started through an isolated build of
the standard Docker deployment.

The container:

- validated its configuration successfully;
- passed startup preflight;
- generated a dashboard;
- served the generated output successfully;
- passed its health check;
- remained isolated from production paths;
- was removed together with its dedicated image and network after the
  rehearsal.

The deployment was operational as a container, but it did not reproduce
production monitoring parity. Overall Status correctly became critical
because required collector-local and SSH-backed resources were not
available inside the standard container boundary.

This is a deployment integration gap, not a configuration-schema or
collector-logic gap.

## Confirmed deployment blockers

### SSH host trust

The private SSH key was available inside the container, but the
collector host's verified `known_hosts` data was not.

Remote systems were reachable over the ordinary Docker bridge, but SSH
failed closed with host-key verification errors.

A cutover deployment must provide explicit verified host trust. It must
not disable host-key verification.

### Collector-local Docker monitoring

The standard image does not contain the Docker CLI and the Compose
definition does not expose the host Docker socket.

Collector-local Docker checks therefore reported uncertainty even
though the containers were healthy on the host.

Supporting this collector path in a container requires an explicit
security decision covering both the Docker client and access to the
Docker daemon.

### Collector filesystem identity

The container root filesystem is not the collector host root
filesystem.

The second monitored host mount was also absent. A container cannot
interpret these configuration paths as collector-host storage unless
the required host filesystems are mounted deliberately and mapped to
unambiguous container paths.

### Backup marker, logs, and timer state

The collector-host backup marker and logs were not mounted into the
container.

The backup check also expects the collector host's systemd timer state.
The standard container has no supported host-systemd integration.

A cutover design must either provide safe read-only host integration or
move this check behind a remote or host-side collector boundary.

### Collector-local Diun endpoint

The collector-host Diun metrics endpoint is bound to host loopback.

Container loopback refers to the container itself, not the collector
host. The endpoint was also unavailable through the collector's LAN
address from the ordinary Docker bridge.

The production configuration therefore cannot reuse a host-loopback
Diun URL unchanged inside the standard container.

### Collector self-reachability

The ordinary Docker bridge reached both remote storage systems and the
remote HTTP services successfully.

It could not connect back to the collector host's dashboard endpoint or
loopback-only image-update endpoint through the collector's LAN
address. This is a collector self-reachability or hairpin boundary, not
a general LAN routing failure.

## Interpretation

Phase 3C.8 proves that the public runtime has complete configuration and
collector capability for the current production inventory.

The validated host-native execution path reached production parity
without runtime changes.

The standard Docker deployment remains suitable for generic public
installations, but the current production deployment cannot be moved
into that container unchanged. Additional host integration would be
required for SSH trust, Docker access, host filesystem checks, backup
state, systemd state, and collector-local endpoints.

These integrations have meaningful privilege and security implications
and must not be added implicitly.

## Phase 3C.9 boundary

Phase 3C.9 is the public-mode production cutover rehearsal.

Based on Phase 3C.8 evidence, its safest initial candidate is the
host-native public runtime because that path already demonstrated full
production parity without modifying SSH authorization or exposing
privileged host interfaces to a container.

The cutover rehearsal must still:

- use an isolated public configuration and output path;
- preserve the existing reference service as the known-good fallback;
- define an explicit rollback procedure;
- compare public and reference output during the same observation
  window;
- prove timer, ownership, logging, and refresh behavior;
- avoid writing the live dashboard until the final controlled cutover
  decision;
- leave reference retirement to Phase 3C.10.

A container-based production cutover remains possible only after its
host-integration design is reviewed and validated separately.

## Validation evidence

Phase 3C.8 completed:

- read-only reference inventory auditing;
- exact configuration translation;
- configuration validation with zero errors and warnings;
- startup-preflight validation;
- full host-native public rendering;
- public presentation checks;
- inventory and domain-count comparison;
- isolated Docker Compose model validation;
- isolated image build and healthy container startup;
- generated-versus-served output comparison;
- bridge-network reachability probes;
- deterministic blocker classification;
- container, image, and network cleanup;
- repeated production generator fingerprint protection;
- repeated production dashboard hash and modification-time protection.

Production remained unchanged throughout the rehearsal.
