# Phase 3C.9 — Public-mode production cutover rehearsal

Status: complete.

## Purpose

Phase 3C.9 rehearses the configuration-driven public runtime beside the
existing reference runtime. It does not replace, stop, or retire the
reference implementation.

The host-native path is used because Phase 3C.8 demonstrated monitoring
parity without privileged container integration or weaker SSH security.

## Rehearsal components

The repository provides:

- `scripts/run-public-rehearsal.sh`;
- `sanity-node-public-rehearsal.service`;
- `sanity-node-public-rehearsal.timer`;
- deterministic fail-closed tests;
- this activation, observation, and rollback contract.

The standard private workspace is
`/opt/sanity-node-public-rehearsal`.

It contains a fixed repository snapshot, private configuration, isolated
dashboard output, generator log, and execution lock. Private runtime
files and inventory are not committed.

## Isolation contract

The rehearsal uses distinct service and timer names, application and
configuration paths, dashboard output, generator log, lock file, and
systemd journal entries.

Application, configuration, output, and log paths must remain within the
rehearsal workspace. The workspace must not overlap the protected
reference-production root.

## Fail-closed execution

Every run:

1. acquires a non-blocking lock;
2. validates the configuration;
3. requires `dashboard.runtime_mode: public`;
4. runs startup preflight;
5. renders to a temporary file;
6. requires nonempty output;
7. requires Dashboard Summary and Runtime Detail markers;
8. rejects obsolete Config Preview wording;
9. atomically publishes only the isolated output;
10. records the output hash and runtime duration.

A failed run never replaces the last successful rehearsal output.

## Systemd contract

The committed service template uses the generic `sanity-node` account.
A private deployment drop-in may select the collector account.

The oneshot service uses network-online ordering, no-new-privileges,
private temporary storage, read-only system protection, read-only access
to the protected reference root, and write access only to the rehearsal
workspace.

The timer has a distinct name, a five-minute interval, one-second
accuracy, no randomized delay, and no persistent catch-up behavior.

## Production safeguards

Phase 3C.9 must not:

- modify the reference generator;
- replace or serve the rehearsal dashboard as production;
- stop or disable the reference timer;
- change SSH authorization solely for testing;
- disable SSH host-key verification;
- expose privileged container interfaces;
- publish private inventory or credentials.

Reference-dashboard hash and modification-time changes are accepted only
when correlated with successful normal reference generation.

## Activation sequence

Before activation:

1. capture reference generator and dashboard fingerprints;
2. confirm the reference timer is active and enabled;
3. create the isolated workspace;
4. copy a fixed repository snapshot into the workspace;
5. install the private public configuration;
6. validate ownership and permissions;
7. install the two distinct rehearsal units;
8. add any required private service-account drop-in;
9. verify the installed units;
10. reload systemd.

Activation begins with one manual service run. The rehearsal timer is
enabled only after that manual run succeeds.

## Scheduled observation

Multiple consecutive five-minute runs must be observed.

Each public run is compared with a reference run from the same
observation window for:

- Overall Status;
- Systems inventory and severity;
- Storage inventory and severity;
- Protection inventory and severity;
- Services inventory and severity;
- update overlays;
- collector errors;
- output ownership and mode;
- logging;
- runtime duration;
- timer trigger and waiting state.

Intentional presentation differences are recorded separately from
monitoring-parity defects.

## Lifecycle tests

The rehearsal must demonstrate:

1. successful manual service start;
2. timer enablement;
3. multiple successful scheduled runs;
4. timer stop;
5. timer disablement;
6. manual service restart;
7. timer re-enablement;
8. unchanged reference service and timer behavior.

## Rollback procedure

Rollback affects rehearsal resources only.

The rehearsal timer is disabled and stopped first. The rehearsal service
is then stopped. Its service file, timer file, and private drop-in are
removed before systemd is reloaded and the rehearsal service failure
state is reset.

The isolated workspace can then be archived or removed.

The reference runtime requires no recovery action because it remains
active and unchanged throughout the rehearsal.

## Rehearsal result

Phase 3C.9 completed the host-native public-mode production cutover
rehearsal while preserving the reference runtime as the served
production path.

The installed isolated runtime passed configuration validation, startup
preflight, public-presentation checks, complete configured monitoring
coverage, ownership and permission checks, and atomic output
publication.

A locale-stable runtime-duration correction was committed, deployed as a
new immutable application snapshot, and validated before scheduled
observation continued.

The scheduled observation captured three consecutive scheduled public
generations and two scheduled reference generations in the same
observation window. Every public run retained complete monitoring
coverage, successful service results, locale-stable duration logging,
valid output ownership and mode, and atomic publication without leftover
temporary output.

The lifecycle rehearsal successfully demonstrated:

- timer stop while remaining enabled;
- timer restart;
- timer disablement;
- manual service restart while disabled;
- timer re-enablement;
- continued reference-runtime operation throughout.

A full rollback and restore rehearsal removed the rehearsal timer,
service, private drop-in, and active workspace, verified the
reference-only state, restored the exact private runtime artifacts and
unit fingerprints, completed another successful manual public
generation, and restored scheduled operation.

Both timers finished active, enabled, and waiting with concrete next
triggers. The reference generator remained unchanged throughout the
rehearsal.

## Completion boundary

Phase 3C.9 demonstrates that public mode is technically ready for a
controlled production cutover using the validated host-native deployment
model and documented rollback procedure.

It does not switch the served production dashboard, retire reference
mode, or make the reference-retirement decision.

That decision remains Phase 3C.10.
