# Changelog

All notable changes to Sanity Node are documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project uses semantic versioning for public release tags.

## [Unreleased]

### Added

- No unreleased changes are recorded yet.

## [0.3.0] - 2026-06-10

Sanity Node `v0.3.0` promotes the configuration-driven public runtime from a
qualified preview into a production-capable monitoring and deployment path.
It is a major runtime, installation, validation, and operational milestone
rather than a small corrective release.

### Added

- A safe first-run workspace bootstrap that creates managed runtime
  directories, installs a credential-free collector-only starter
  configuration, and preserves existing files unless replacement is
  explicitly requested.
- `examples/config.starter.yaml` as a minimal public starting point alongside
  the comprehensive example configuration.
- A fail-closed startup preflight covering configuration validity, runtime
  paths, output requirements, conditional SSH credentials, and initial
  dashboard generation.
- Explicit public and reference runtime modes, with whole-generator isolation
  tests that prevent public mode from invoking personal reference collectors.
- Configuration-driven host system information for enabled Linux and TrueNAS
  hosts.
- Live TrueNAS pool capacity and health monitoring.
- Independent TrueNAS temperature and SMART monitoring with conservative
  severity aggregation and pool-to-device mapping.
- Host-native public production and rehearsal runners with atomic output
  publication, deterministic logging, process locking, and explicit failure
  handling.
- Dedicated systemd service and timer definitions for the permanent
  host-native public runtime and isolated public rehearsal runtime.
- Deterministic documentation, lifecycle, runtime-mode, startup-preflight,
  bootstrap, production-cutover, and rollback regression coverage.

### Changed

- The configuration-driven public dashboard now uses the promoted production
  presentation instead of the earlier preview-oriented layout.
- The public runtime now integrates configured Systems, Storage, Protection,
  and Services monitoring into one consistent four-card summary.
- Public Overall Status now aggregates domain results and uncovered collector
  errors with deterministic `NOK > WARNING > INFO > OK` precedence.
- Data-protection severity now combines configured relationships with live
  snapshot and replication evidence using conservative worst-severity
  handling.
- Existing configuration-driven TrueNAS application, snapshot, replication,
  image-update, local-storage, backup, Docker, HTTP, and remote Linux
  SSH-backed checks are now part of the qualified public production path.
- Healthy services with detected image updates can be represented as
  informational `UPDATE` states without overriding genuine service failures.
- Explicitly unreachable configured hosts can be summarized at host level
  while authentication, parsing, and partial-service failures retain detailed
  collector results.
- Scheduled Docker refreshes now execute configuration validation, startup
  preflight, and generation in that order.
- The permanent web service is decoupled from generation startup so an
  existing valid dashboard remains available during generator failures.
- Public presentation wording and status classification are generated
  directly by the relevant runtime builders instead of a whole-document
  promotion shim.

### Fixed

- Invalid Docker refresh configuration no longer falls back to reference mode,
  invokes the generator, or replaces the last successfully generated
  dashboard.
- Warning-grade host and protection states now propagate consistently into
  their summary cards and public Overall Status.
- Healthy Web UI results without optional telemetry no longer incorrectly
  elevate the Systems summary to informational severity.
- Public rehearsal runtime logging is locale-stable and therefore suitable
  for deterministic validation.
- Host-native service startup ordering no longer requires successful
  generation before the web service can serve an existing valid output.

### Security

- Invalid or incomplete public configuration fails closed instead of silently
  activating the personal reference runtime.
- Public runtime-mode isolation prevents reference collectors and private
  inventory from being used by public-mode generation.
- Host-native SSH guidance requires persistent verified `known_hosts` entries
  and explicitly rejects disabling host-key verification.
- SSH private keys used by the service account must be owned by that account
  and restricted to mode `0600`, matching OpenSSH permission enforcement.
- Deployment guidance uses a dedicated unprivileged service account,
  restrictive systemd hardening, explicit writable paths, and narrowly scoped
  credential access.
- Atomic output replacement and last-successful-output retention reduce the
  risk of serving a partial or invalid dashboard.

### Documentation

- Added `docs/installation.md` for the qualified public Docker installation
  path.
- Added `docs/deployment.md` for advanced host-native installation,
  operation, update, backup, rollback, and removal.
- Added `docs/v0.3.0-installation-qualification.md` with the clean-clone
  Docker qualification procedure and evidence.
- Added the Phase 3C migration parity audit, production-configuration
  rehearsal, public cutover rehearsal, and reference-retirement decision
  records.
- Expanded the README with public runtime behavior, configuration guidance,
  deployment boundaries, regression coverage, and Phase 3 completion status.

### Validation

- The installation-qualification baseline passed **304 deterministic
  standard-library tests** before release-documentation assertions were added.
- The completed release-documentation branch contains **322 deterministic
  standard-library tests**, including changelog, README, release-note, claim,
  and privacy-boundary coverage.
- Python compilation and shell syntax validation passed.
- Both supplied example configurations validated with zero errors and zero
  warnings.
- Safe public preview rendering and Docker Compose configuration validation
  passed.
- A clean-clone Docker installation passed bootstrap, validation, image build,
  startup, health checking, HTTP serving, restart, scheduled refresh,
  invalid-configuration rejection, last-successful-output retention,
  automatic recovery, and complete cleanup.
- The host-native public runtime passed isolated production-configuration
  rehearsal, scheduled cutover rehearsal, lifecycle testing, atomic-output
  verification, rollback restoration, and sustained production observation.
- Retained reference and rehearsal outputs remained isolated from release
  qualification and permanent production operation.
- Production-output changes observed during final checks were correlated with
  legitimate scheduled generation, including matching timestamps, logged
  hashes, and served HTTP content.

### Deployment notes

- The qualified Docker Compose path is the simplest public installation and
  is appropriate for HTTP checks and monitoring reachable from inside the
  container.
- The unmodified Compose deployment does not automatically provide
  collector-host Docker access, collector-host filesystem checks,
  collector-host systemd inspection, or persistent host-native SSH trust.
- Host-native deployment is the advanced path for installations requiring
  collector-local operating-system integration or durable SSH-backed remote
  checks.
- The documented host-native production workspace is `/opt/sanity-node`.
- The permanent web service listens on TCP port `8088` by default.
- Host-native generation uses
  `/opt/sanity-node/run/generator.lock` to prevent overlapping runs.
- Production generation publishes complete output atomically and retains the
  last successful dashboard when validation, preflight, collection, or
  rendering fails.

### Upgrade notes

- Back up the current configuration, generated dashboard, service files, and
  SSH trust material before replacing an existing installation.
- Review the current example configuration because `v0.3.0` adds public
  runtime, host-system, TrueNAS pool, temperature, SMART, and deployment
  controls beyond the `v0.2.0` schema.
- Set and verify the intended runtime mode explicitly; public deployments must
  not depend on the reference-mode fallback used by early development
  versions.
- Run `scripts/validate-config.py` and `scripts/startup-preflight.py` before
  restarting a host-native service or bringing up the Docker deployment.
- Reinstall or compare the supplied systemd units when upgrading a
  host-native installation because startup ordering, hardening, locking, and
  failure behavior changed.
- Verify service-account ownership and mode `0600` on SSH private keys, and
  populate persistent verified host keys before enabling remote checks.
- Confirm that a successful manual generation and HTTP health check complete
  before enabling the recurring generation timer.
- The existing `v0.2.0` tag remains unchanged; upgrades do not move or rewrite
  earlier release tags.

## [0.2.0] - 2026-06-07

### Added

- The first configuration-driven runtime and Docker scaffold.
- Configuration validation and safe preview rendering.
- Configured HTTP, collector Docker, TrueNAS application, local storage,
  backup-marker, snapshot, replication, image-update, and protection checks.
- Remote Linux Docker, storage, and backup checks over explicit SSH
  identities.
- The Systems, Storage, Protection, and Services summary-card model.
- Deterministic runtime regression coverage for collectors, rendering,
  schedules, overlays, host normalization, and failure classification.

### Changed

- Configuration-driven monitoring progressed from inventory previews to live
  collector-backed status.
- Snapshot and replication evidence could overlay configured protection
  relationships.
- Image-update information could overlay otherwise healthy configured
  services.
- Unreachable-host and collector-error presentation became more conservative
  and explicit.

## [0.1.1] - 2026-05-31

### Changed

- Clarified the README, installation status, project maturity, and the
  distinction between the homelab-tested reference implementation and the
  developing public configuration path.

## [0.1.0] - 2026-05-31

### Added

- The initial homelab-tested Sanity Node release.
- The original reference dashboard generator and systemd service definitions.
- Initial configuration examples, project documentation, web assets, and MIT
  licensing.
- Host, storage, protection, service, and overall-status presentation based on
  the original deployment.

[Unreleased]: https://github.com/vonH23rz/sanity-node/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/vonH23rz/sanity-node/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/vonH23rz/sanity-node/compare/v0.1.1...v0.2.0
[0.1.1]: https://github.com/vonH23rz/sanity-node/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/vonH23rz/sanity-node/releases/tag/v0.1.0
