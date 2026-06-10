# Phase 3C.10 — Reference retirement decision

Status: decision complete; controlled production cutover pending.

## Purpose

Phase 3C.10 makes the explicit retirement decision for the original
reference runtime after the configuration-driven public runtime completed
its parity, production-configuration, and scheduled cutover rehearsals.

The decision is intentionally separate from implementation and activation.
Passing a rehearsal does not by itself authorize deletion of the reference
runtime.

## Evidence baseline

The decision is based on the completed Phase 3C evidence:

- configuration-driven collection reached the required monitoring parity;
- public presentation and severity behavior were consolidated;
- a complete private production configuration passed validation and
  startup preflight;
- the host-native public runtime completed repeated scheduled generation;
- output publication remained atomic;
- output ownership and mode remained stable;
- lifecycle stop, start, disable, enable, removal, and restoration tests
  succeeded;
- the served dashboard remained on the reference implementation throughout
  the rehearsal;
- the reference generator remained unchanged.

The existing reverse-proxy endpoint continues to forward to TCP port 8088.
The production decision does not require a DNS, certificate, hostname, or
reverse-proxy route change.

## Retirement options

### Option A — immediate retirement

Promote public mode and immediately remove the reference implementation.

This option is rejected because deletion would remove a proven rollback
path before the public runtime has accumulated real production operating
history.

### Option B — disabled reference fallback

Promote public mode to the served dashboard, disable the reference
generator and web service, and retain the complete reference implementation
temporarily as rollback protection.

This option is selected.

### Option C — continued parallel rehearsal

Keep the reference implementation serving production while continuing the
parallel public rehearsal indefinitely.

This option is rejected as the final Phase 3C state because the scheduled,
lifecycle, and rollback rehearsals already produced the required evidence.
Continuing duplicate collection would preserve operational ambiguity and
unnecessary workload.

## Selected production architecture

The permanent host-native public workspace is:

`/opt/sanity-node`

Its runtime layout is:

- `/opt/sanity-node/app`
- `/opt/sanity-node/config/config.yaml`
- `/opt/sanity-node/html/index.html`
- `/opt/sanity-node/logs/generator.log`
- `/opt/sanity-node/run/generator.lock`
- `/opt/sanity-node/ssh`

The permanent units are:

- `sanity-node-generate.service`
- `sanity-node-generate.timer`
- `sanity-node-web.service`

The generation service uses:

`scripts/run-public-production.sh`

The web service serves `/opt/sanity-node/html` on TCP port 8088.

The reverse-proxy route remains unchanged. Cutover is performed by changing
which systemd web service owns port 8088, not by overwriting the reference
dashboard directory and not by changing the proxy configuration.

## Fail-closed production generation

Every permanent production generation:

1. verifies that all application, configuration, output, log, and lock
   paths remain inside `/opt/sanity-node`;
2. rejects overlap with the retained reference and rehearsal roots;
3. acquires a non-blocking execution lock;
4. validates the configuration;
5. requires `dashboard.runtime_mode: public`;
6. runs startup preflight;
7. renders to a process-specific temporary file;
8. requires nonempty output;
9. requires Dashboard Summary and Runtime Detail markers;
10. rejects obsolete Config Preview wording;
11. applies output mode `0664`;
12. atomically replaces the last successful production output;
13. records the output hash and locale-stable runtime duration.

A failed run does not replace the last successful production dashboard.

## Systemd contract

The committed unit templates use the generic `sanity-node` service account.
A private deployment may use a systemd drop-in when collector-local access
requires another account.

The generation service uses:

- network-online ordering;
- no-new-privileges;
- private temporary storage;
- read-only system protection;
- read-only access to retained legacy runtime roots when they exist;
- write access only to `/opt/sanity-node`;
- SUID/SGID restrictions;
- locked process personality.

The timer runs every five minutes, uses one-second accuracy, has no random
delay, and uses persistent catch-up behavior appropriate for permanent
production.

The web service:

- requires a successful generation service start;
- requires a nonempty production dashboard;
- serves only `/opt/sanity-node/html`;
- listens on TCP port 8088;
- uses the same process-hardening controls;
- does not read from the reference or rehearsal dashboard directories.

## Pre-cutover requirements

Before the served dashboard changes:

1. preserve fingerprints of the reference generator, dashboard, units, and
   workspace;
2. confirm the reference timer and web service are healthy;
3. confirm the rehearsal timer and service are healthy;
4. install an immutable application snapshot under `/opt/sanity-node/app`;
5. install private configuration and SSH credentials without committing
   them;
6. validate ownership and permissions;
7. validate the production configuration;
8. run startup preflight;
9. install the permanent unit files and any private account drop-ins;
10. run one successful manual permanent generation;
11. verify output markers, hash, ownership, mode, and absence of temporary
    output;
12. verify that the reference and rehearsal outputs remain unchanged.

No reference unit may be stopped before the permanent output and rollback
path have both been validated.

## Controlled cutover sequence

The production switch uses this order:

1. generate and validate the permanent public dashboard while the existing
   served reference dashboard remains active;
2. disable and stop the public rehearsal timer;
3. disable and stop the reference generator timer;
4. stop and disable the reference web service;
5. start and enable `sanity-node-web.service`;
6. verify the local TCP port 8088 response;
7. verify the reverse-proxied production response;
8. verify that the served response matches
   `/opt/sanity-node/html/index.html`;
9. start and enable `sanity-node-generate.timer`;
10. observe multiple successful scheduled permanent generations;
11. confirm that the reference generator and dashboard remain unchanged.

The intended final service state is:

- `sanity-node-web.service`: active and enabled;
- `sanity-node-generate.timer`: active and enabled;
- `sanity-node-generate.service`: successful and normally inactive between
  oneshot runs;
- reference generator timer: inactive and disabled;
- reference web service: inactive and disabled;
- public rehearsal timer: inactive and disabled.

## Rollback triggers

Rollback is required when any of the following occurs:

- production configuration validation fails;
- startup preflight fails;
- permanent generation fails;
- output is missing, empty, or contains invalid presentation markers;
- output ownership or mode is incorrect;
- the permanent web service cannot bind or serve TCP port 8088;
- the reverse-proxied endpoint does not return the permanent output;
- configured monitoring coverage unexpectedly disappears;
- materially incorrect status or severity is displayed;
- repeated collector failures indicate a production regression;
- the permanent timer or web service enters a failed state.

## Rollback procedure

Rollback restores the retained reference implementation without deleting the
new workspace.

The deployment-specific rollback order is:

1. disable and stop `sanity-node-generate.timer`;
2. stop and disable `sanity-node-web.service`;
3. run the retained reference generator once;
4. start and enable the retained reference web service;
5. start and enable the retained reference generator timer;
6. verify the local TCP port 8088 response;
7. verify the reverse-proxied response;
8. verify that the served output matches the retained reference dashboard;
9. keep the failed public production workspace intact for diagnosis.

The public rehearsal timer remains disabled during rollback unless a
separate diagnostic decision explicitly reactivates it.

## Reference retention period

The disabled reference implementation is retained until both conditions
are satisfied:

1. public mode has served production successfully for at least 30 days;
2. at least one release after `v0.3.0` has been published and validated.

The later of those two milestones controls retirement eligibility.

Eligibility does not authorize automatic deletion. Permanent removal of the
reference workspace and units requires a separate explicit decision and a
final archived rollback record.

## Release boundary

A successful controlled cutover and post-cutover observation will:

- close Phase 3C;
- make the merged main branch the `v0.3.0` release candidate;
- leave the existing `v0.2.0` tag unchanged;
- retain the disabled reference implementation for rollback;
- defer the actual `v0.3.0` tag until final validation and publication
  cleanup pass.

Phase 3C.10 does not create or move a release tag merely by recording this
decision.

## Privacy and repository boundary

The repository contains only generic runtime templates, deterministic
tests, and reusable operational policy.

Private configuration, credentials, host addresses, hostnames, datasets,
service inventory, account overrides, and deployment-specific fingerprints
remain outside Git.
