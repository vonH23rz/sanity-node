# Sanity Node

> Observe. Announce. Stay sane.

Sanity Node is a lightweight homelab dashboard that observes systems, services, storage, snapshots, backups, replications, and update states from one small Linux / Utility collector node.

It was originally built for my own homelab, where a Utility Node watches TrueNAS systems, Docker services, helper containers, ZFS pools, snapshot tasks, replication jobs, local storage, and backup status.

The goal is simple:

**Open one page and know whether the homelab is still doing what it should be doing.**

Because in a homelab, everything works perfectly until it does not.

---

## Screenshot

![Sanity Node dashboard screenshot](docs/assets/sanity-node-dashboard-readme.png)

---

## Current project status

Sanity Node now contains two deliberately separate runtime paths:

- the original homelab-tested reference dashboard
- the completed Phase 2F configuration-driven runtime preview

The reference dashboard remains available because it is the known-good production view for the original homelab. Phase 2F did not overwrite or silently replace it.

**Phase 2F is complete.**

The Phase 2F closure baseline includes:

- configuration-driven hosts and host-based cards
- Systems, Storage, Protection, and Services summary cards
- HTTP, collector-local Docker, and TrueNAS app checks
- remote Linux Docker checks over explicit host-specific SSH
- collector-local and remote Linux storage checks
- collector-local and remote Linux backup-status checks
- TrueNAS snapshot-task and replication-task collection
- snapshot and replication overlays for configured protection relationships
- Diun and TrueNAS-native image-update collection
- service update overlays with unhealthy-state precedence
- unreachable-host handling and collector-error classification
- configuration validation
- safe preview rendering under `/tmp`
- **153 deterministic standard-library regression tests**

The repository also includes the public runtime scaffold:

- `Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `requirements.txt`
- `scripts/docker-entrypoint.sh`
- `scripts/validate-config.py`
- `scripts/render-preview.sh`

The original hardcoded dashboard and the Phase 2F public preview remain intentionally isolated. Replacing the reference dashboard, publishing a polished installation flow, and adding new monitoring families belong to Phase 3.

---

## What Sanity Node monitors

Sanity Node can display and summarize:

- Linux / TrueNAS system information
- host online/offline state
- hostname, OS, kernel, uptime, CPU, memory, and load
- TrueNAS pool health
- pool capacity
- disk temperature summaries
- SMART status
- snapshot task freshness
- replication state
- backup status
- running apps
- helper services
- HTTP-checked services
- local storage on the collector node
- Docker container status
- image update state through Diun metrics or TrueNAS-native app fields

The dashboard separates services into simple categories:

### Apps

User-facing services you actually open and use, such as:

- Jellyfin
- Wiki.js
- SearXNG
- OpenWebUI
- File Browser
- Scrutiny
- Dockge
- Pi-hole
- NGINX Proxy Manager

### Helpers

Backend or infrastructure services that keep things alive in the background, such as:

- Cloudflare Tunnel
- Redis
- Ollama
- databases
- Tailscale
- Diun

This makes the dashboard easier to read than a plain container count.

Instead of:

```text
14 containers running
```

Sanity Node can show:

```text
14 Services · 13 UP · 1 UPDATE · 0 DOWN
```

Much better. Less guessing. More sanity.

---

## Why this exists

The problem was not that my homelab had no information.

The problem was that the information was everywhere.

To check everything manually, I had to open TrueNAS, Docker, Dockge, service web UIs, snapshot pages, replication pages, SSH sessions, logs, and possibly a small emotional support terminal.

Sanity Node gives me one clean overview.

It does not replace TrueNAS, Grafana, Uptime Kuma, Scrutiny, Netdata, or any other proper monitoring tool.

It is my sanity check layer.

One page.
One view.
One quick answer:

**Is everything still OK?**

---

## Documentation

The project/concept page explains what Sanity Node is, why it exists, what it monitors, and how the dashboard concept evolved:

[Project Sanity Node](https://wiki.homelabvonh23rz.me/en/Project_Sanity_Node)

The installation tutorial explains the public install direction, requirements, collector-node concept, TrueNAS SSH requirement, Docker Compose layout, `config.yaml`, and the start-small approach:

[Installing Sanity Node](https://wiki.homelabvonh23rz.me/en/Install_Sanity_Node)

The repository now contains the Docker Compose and configuration-driven runtime scaffold. The installation tutorial still needs a final public first-run pass, so treat it as guidance rather than a polished release installer.

---

## Repository structure

```text
sanity-node/
├── README.md
├── LICENSE
├── docs/
│   └── assets/
│       └── sanity-node-dashboard-readme.png
├── examples/
│   └── config.example.yaml
├── scripts/
│   ├── generate-dashboard.py
│   ├── render-preview.sh
│   ├── startup-preflight.py
│   └── validate-config.py
├── tests/
│   ├── test_config_runtime.py
│   └── test_startup_preflight.py
├── systemd/
│   ├── sanity-node-generate.service
│   ├── sanity-node-generate.timer
│   └── sanity-node-web.service
└── web/
    └── favicon and web manifest assets
```

---

## Current reference implementation

The current reference implementation uses:

- Python 3
- systemd
- a static generated HTML dashboard
- SSH access from the Utility Node to configured remote systems
- TrueNAS SCALE middleware calls through `midclt`
- local Docker checks on the collector
- host-specific SSH Docker checks on eligible remote Linux hosts
- HTTP checks for selected services

Some values are still hardcoded in:

```text
scripts/generate-dashboard.py
```

This includes personal hostnames, IP addresses, services, pool relationships, local paths, and backup targets.

That remains intentional for the original reference path. The Phase 2F public runtime reads its monitoring definitions from `config.yaml`; replacing the reference path is a separate Phase 3 migration rather than unfinished Phase 2F work.

---

## Configuration direction

The completed Phase 2F public configuration model is represented in:

```text
examples/config.example.yaml
```

That file is intentionally self-documenting. It uses:

```text
🟧 Required = review or change this for your environment
🩵 Optional = enable only if you use this feature
```

The goal is that users should be able to describe their own homelab without editing the Python code.

Completed Phase 2F configuration-driven behavior:

- configured hosts can appear as host-based summary cards
- host Web UI links can show preview reachability badges
- a confirmed TrueNAS SSH/network timeout collapses that host card to `Host unreachable` instead of listing every configured service
- confirmed TrueNAS host unreachability also overrides the host's Web UI result in the four-card Systems summary
- Web UI-only, authentication, host-key, and parsing failures retain the normal per-service detail and Systems status
- configured HTTP services can report live `UP` / `DOWN`
- configured Docker services on the collector node can report live local container status
- configured Docker services on eligible remote `type: linux` hosts can report live container status over host-specific SSH
- configured TrueNAS app services can report live app status for enabled `type: truenas` hosts
- enabled TrueNAS hosts with `modules.snapshots: true` can report live snapshot-task state and latest-snapshot freshness
- enabled TrueNAS hosts with `modules.replications: true` can report live replication-task configuration and execution state
- configured image update sources can report live Diun container-image updates and TrueNAS-native app updates
- configured local storage checks can report collector-local or eligible remote Linux filesystem usage using `df`
- configured backup checks can report collector-local or eligible remote Linux marker-file freshness and optional systemd timer state
- Collector Errors include a classified Type badge for timeouts, network failures, host-key problems, authentication failures, refused connections, parsing failures, command failures, unknown messages, and other errors
- all Collector Errors remain failure rows; classification improves presentation only and does not change Overall Status handling
- configured protection relationships can render preview backup/replication relationships from `config.yaml`
- replication relationships can inherit live task status when source host, configured datasets, and target prefix confidently match a discovered TrueNAS replication task
- replication relationships can also inherit live snapshot status when every configured dataset is confidently covered by an exact snapshot task or an explicitly recursive ancestor task
- recursive snapshot coverage respects TrueNAS exclusion paths; missing, malformed, partial, or ambiguous coverage leaves the relationship unchanged
- snapshot and replication overlays combine using worst-severity precedence, while a live `OK` relationship still counts as configured
- unmatched or incomplete relationships retain their configuration-preview status instead of being treated as failures
- configured `summary_cards` can render the first four-card public preview: Systems, Storage, Protection, and Services
- `summary_cards` controls card order and selection; duplicate names are removed, unknown names are ignored, and an empty/invalid list falls back to the default four cards
- when the four-card Services summary is active, host-based cards retain their service counts but show only non-`UP` service exceptions; fully healthy hosts show one `ALL UP` line
- when the Services summary is disabled, host-based cards retain the full per-service detail list
- remote Docker services remain `NOT CHECKED` unless their host is an eligible Linux host with explicit SSH credentials
- remote local storage checks remain `NOT CHECKED` unless their host is an eligible Linux host with explicit SSH credentials
- remote backup checks remain `NOT CHECKED` unless their host is an eligible Linux host with explicit SSH credentials
- TrueNAS app checks on non-TrueNAS hosts are shown as `NOT CHECKED` for now
- live snapshot and replication overlays affect only the config-driven Protection preview and card; they do not affect Overall Status or replace the original reference checks
- the original hardcoded five-card reference summary remains untouched; replacing it is outside the completed Phase 2F scope

### Remote Linux Docker checks

Collector-hosted Docker services continue to use local `docker inspect`. Docker services assigned to another Linux host can be checked through that host's explicit SSH identity.

A remote Docker host must be enabled and provide:

- `type: linux`
- `modules.docker: true`
- a non-empty `address`
- `ssh.enabled: true`
- non-empty `ssh.user` and `ssh.key_file`

The service must use `check: docker` and define its container name. Container names are shell-quoted before being sent remotely. Successful SSH commands parse Docker JSON from stdout only, so warning or legal banners written to stderr do not corrupt the response.

Running containers report `UP`; containers not found after a successful SSH connection report `MISSING`; SSH transport failures and malformed Docker responses report `UNKNOWN`. Ineligible hosts are not contacted, and their Docker services remain `NOT CHECKED`.

Remote Docker checks remain part of the config-driven preview path. They do not affect Overall Status or modify the original hardcoded service cards.

### Remote Linux local-storage checks

Collector-hosted local-storage checks continue to use local `df -P`. Local-storage checks assigned to another Linux host can use that host's explicit SSH identity.

A remote storage host must be enabled and provide:

- `type: linux`
- `modules.local_storage: true`
- a non-empty `address`
- `ssh.enabled: true`
- non-empty `ssh.user` and `ssh.key_file`

Each storage check must reference that host and define its mountpoint. Mountpoints are shell-quoted before being sent remotely. Successful SSH commands parse `df` output from stdout only, so warning or legal banners written to stderr do not corrupt the response.

Filesystem usage below the warning threshold reports `OK`; warning and critical thresholds report `WARNING` and `CRITICAL`. A missing mount after a successful SSH connection reports `MISSING`. SSH transport failures and malformed `df` output report `UNKNOWN`. Ineligible remote checks remain `NOT CHECKED`.

Remote local-storage checks remain part of the config-driven preview path. They do not affect Overall Status or modify the original hardcoded storage checks.

### Remote Linux backup checks

Collector-hosted backup checks continue to read marker-file modification times and optional systemd timer state locally. Backup checks assigned to another Linux host can use that host's explicit SSH identity.

A remote backup host must be enabled and provide:

- `type: linux`
- `modules.backup_status: true`
- a non-empty `address`
- `ssh.enabled: true`
- non-empty `ssh.user` and `ssh.key_file`

The remote command verifies that the marker exists, reads its epoch modification time with `stat -c %Y`, and optionally reads `systemctl is-active` for the configured timer. Marker paths and timer names are shell-quoted before use. Successful SSH commands parse stdout only, so unrelated stderr banners do not corrupt the response.

Fresh markers report `OK`; stale markers report `OLD`; inactive timers report `WARNING`; missing markers report `MISSING`. SSH transport failures, marker-stat failures, and malformed responses report `UNKNOWN`. Ineligible remote checks remain `NOT CHECKED`.

Remote backup checks remain part of the config-driven preview path. They do not affect Overall Status or modify the original hardcoded backup checks.

### TrueNAS snapshot checks

Live snapshot monitoring is enabled per host:

```yaml
hosts:
  - id: truenas-main
    enabled: true
    type: truenas
    address: 192.168.1.20

    modules:
      snapshots: true
```

For each matching host, Sanity Node:

- queries periodic snapshot tasks through `midclt call pool.snapshottask.query`
- reads the available ZFS snapshots over SSH
- identifies the latest snapshot for every configured task dataset
- evaluates freshness against the task schedule
- distinguishes enabled, disabled, missing, old, and fresh tasks
- respects TrueNAS `allow_empty: false` behavior when no dataset changes have occurred

The host must be enabled, use `type: truenas`, have an `address`, and have `modules.snapshots` set to `true`. The current preview uses the configured Sanity Node SSH credentials.

Configured replication relationships can use these live snapshot rows as a precondition overlay. Every configured relationship dataset must be confidently covered. An exact task dataset always qualifies. An ancestor task qualifies only when `recursive` is explicitly `true`, the configured dataset is below that task dataset on a dataset boundary, and no TrueNAS exclusion equals or contains the configured dataset. Missing or malformed recursion/exclusion metadata, partial coverage, and collector failures do not convert an unmatched relationship into a warning or failure.

Snapshot preview and Protection-overlay results do not affect Overall Status, and the original hardcoded snapshot cards remain untouched.

### TrueNAS replication checks

Enable live replication monitoring per TrueNAS host:

```yaml
hosts:
  - id: truenas-main
    enabled: true
    type: truenas
    address: 192.168.1.20

    modules:
      replications: true
```

For each matching host, Sanity Node:

- queries tasks with `midclt call replication.query`
- reports enabled or disabled task state
- shows direction, transport, source datasets, and target dataset
- reports the current or latest execution state
- shows the last execution time and last snapshot when available
- reports when no replication tasks are configured

The host must be enabled, use `type: truenas`, have an `address`, and have `modules.replications` set to `true`. The preview uses the configured Sanity Node SSH credentials. Results do not affect Overall Status yet, and the original hardcoded replication table remains untouched.

Configured replication relationships can use these live rows as an informational overlay. A match requires the same `source_host`, every configured relationship dataset to exist in the task's source datasets, and the task target dataset to equal or sit below the configured `target_prefix`. When several tasks match, the most severe live state is shown. Relationships without a confident match retain their existing configuration-preview status.

When both snapshot and replication overlays match the same relationship, Sanity Node keeps the worst live severity. A snapshot warning can therefore override healthy replication, while an existing replication failure is not hidden by healthy snapshots.

### Image update monitoring

Configure image update monitoring through explicit sources:

```yaml
image_updates:
  enabled: true

  sources:
    - id: collector-diun
      host: collector
      provider: diun
      url: http://127.0.0.1:9092/metrics

    - id: truenas-main-apps
      host: truenas-main
      provider: truenas
```

Supported providers:

- `diun` reads Prometheus image-check metrics
- `truenas` reads native app update fields through `midclt call app.query`

The preview reports tracked images or apps, available updates, and update details. `UPDATE` is a maintenance notice, not a service failure.

Diun sources require a metrics URL. TrueNAS sources require an enabled `type: truenas` host with working SSH access.

Image-update results can overlay healthy configuration-driven services:

- collector-local and eligible remote Linux Docker services are matched using the image reference returned by `docker inspect`
- configured TrueNAS app services are matched using their `app_id`
- only an existing `UP` service can become `UPDATE`
- existing `DOWN`, `MISSING`, `UNKNOWN`, and `NOT CHECKED` states always take precedence
- the Services summary counts `UPDATE` separately from `UP`, `DOWN`, and other informational states

Update overlays remain informational. They do not affect Overall Status, and they do not modify the original hardcoded service cards.

### `summary_cards`

The public four-card preview is controlled by the optional `summary_cards` list in `config.yaml`.

Supported card names are:

```yaml
summary_cards:
  - systems
  - storage
  - protection
  - services
```

The order in the list is the order shown on the dashboard. Unknown card names are ignored. Duplicate card names are removed while preserving the first occurrence. If the list is empty, missing, or contains no valid card names, Sanity Node falls back to the default four cards:

```text
Systems · Storage · Protection · Services
```

The preview header also shows the active card selection, making it easier to confirm which cards were actually rendered.

To avoid rendering the same complete service inventory twice, host-based cards use compact service details whenever the Services card is active. Their App, Helper, UP, DOWN, UPDATE, and INFO counts remain unchanged, but only non-`UP` services are listed. When every configured service is healthy, the host card shows one `Configured services — ALL UP` line. Disabling the Services card restores the full host-level service list. An unreachable TrueNAS host still collapses to `Host unreachable` and `UNAVAILABLE` before this compaction is applied.

The Systems card normally reflects each enabled host's Web UI check. When all configured TrueNAS app checks for a host are `UNKNOWN` because of a recognized SSH or network timeout, that host is instead shown as `UNREACHABLE` and counted as `DOWN`. Authentication failures, host-key failures, connection refusal, parsing errors, partial app success, Linux hosts, and HTTP-only hosts retain the existing Web UI-based Systems status.

The Protection card normally reflects configuration completeness. Confidently matched live replication tasks and complete snapshot coverage can replace `CONFIGURED` with their current live status. Every configured dataset must be covered before snapshot status propagates. When both live sources match, the worst severity wins. A live `OK` relationship still counts as configured.

These propagations are preview-only and do not affect Overall Status or the original hardcoded summary cards.

### Configuration validation

Validate the example configuration with:

```bash
./scripts/validate-config.py
```

Validate another configuration file by passing its path:

```bash
./scripts/validate-config.py config/config.yaml
```

The validator checks:

- YAML syntax and top-level structure
- required dashboard and collector settings
- host IDs, host types, and duplicate hosts
- enabled references to known hosts
- service types, check types, URLs, containers, and TrueNAS app IDs
- local storage warning and critical thresholds
- backup marker settings and maximum age values
- protection relationships and dataset lists
- image update source IDs, providers, host references, Diun metrics URLs, and TrueNAS host types
- supported and duplicate `summary_cards` values

Validation errors return exit code `1`. Warnings describe runtime fallback behavior, such as ignored summary cards, but do not fail validation. The validator reads configuration only; it does not generate or overwrite a dashboard.

### Startup preflight

Docker startup now fails closed before the web server is exposed. The container startup sequence is:

1. validate `config.yaml`
2. check runtime paths and required SSH credentials
3. remove any stale generated `index.html`
4. require one successful, nonempty dashboard render
5. start the refresh loop and web server

The startup preflight checks:

- that the configuration file exists, is readable, and contains a YAML mapping
- that the dashboard-output and generator-log directories exist and are writable
- that SSH users and key files exist for enabled checks that actually require SSH
- that disabled modules and collector-local checks do not incorrectly require SSH credentials

Run it manually with:

```bash
./scripts/startup-preflight.py \
  --config config/config.yaml \
  --output html/index.html \
  --log logs/generator.log
```

The container health check requires both a nonempty generated dashboard and a working HTTP response. A running web server alone is no longer considered healthy.

### Safe local preview render

Contributors can safely render the public runtime preview with:

```bash
./scripts/render-preview.sh
```

The helper:

- uses `examples/config.example.yaml`
- writes the generated dashboard to `/tmp/sanity-node-preview.html`
- removes any previous temporary preview before rendering
- verifies that the output exists and is not empty
- checks for the public four-card preview and active-card markers
- never writes to `/opt/homelab-dashboard/html/index.html`

This provides a repeatable way to test public-preview changes without overwriting the live reference dashboard.

### Configuration-driven runtime regression tests

Run the standard-library regression suite with:

```bash
python3 -m unittest discover -s tests -v
```

The current tests protect:

- Docker image-reference normalization and Docker Hub aliases
- remote Linux Docker eligibility, host-specific SSH commands, transport failures, shell-safe container names, state/image parsing, missing containers, malformed responses, and stderr banner isolation
- remote Linux local-storage eligibility, collector-local preservation, host-specific SSH commands, shell-safe mountpoints, threshold classification, missing mounts, transport failures, malformed output, and ineligible-host fallback
- remote Linux backup eligibility, collector-local preservation, shell-safe marker/timer commands, marker freshness, inactive timers, missing markers, transport/stat failures, malformed responses, and ineligible-host fallback
- Diun update matching for configured Docker services
- native TrueNAS app-update matching
- update-overlay host scoping
- unhealthy service status precedence over update notices
- SSH and network-error classification for unreachable hosts
- TrueNAS host-collapse gating, including partial success, authentication errors, Linux hosts, HTTP-only services, and missing statuses
- Systems-summary host-health propagation, Web UI fallback behavior, and mixed HTTP/TrueNAS service handling
- collector-error classification precedence, fallback behavior, Type badges, HTML escaping, and empty-section rendering
- summary-card normalization and fallback behavior
- compact host-service exception rendering, `ALL UP` output, full-detail fallback, and unreachable-host precedence
- Storage, Protection, and Services summary-card empty states, counts, severity precedence, detail rendering, and multi-column behavior
- TrueNAS snapshot and replication preview empty states, host/task counts, task and execution badges, dataset details, and HTML escaping
- snapshot freshness decisions, five-minute grace handling, `allow_empty` behavior, and TrueNAS replication execution-state classification
- snapshot and replication collector error rows, empty-task handling, task sorting, field normalization, and successful row assembly
- snapshot schedule cron parsing, normal and overnight windows, TrueNAS weekday mapping, and deterministic previous-run searches
- TrueNAS snapshot and replication host eligibility, explicit module gating, ID requirements, display-name fallbacks, and address preservation
- date parsing and formatting, snapshot inventory SSH/error handling, inventory row parsing, latest-snapshot selection, and replication metadata helpers
- assembled four-card summary selection, normalized ordering, duplicate removal, unknown-card filtering, and default fallback
- protection-to-replication matching, path normalization, conservative no-match behavior, live severity overlays, and configured-count preservation
- protection-to-snapshot matching, exact and recursive dataset coverage, exclusion handling, complete-coverage requirements, metadata retention, and snapshot/replication worst-severity precedence

The configuration-driven runtime tests extract only selected pure functions from `scripts/generate-dashboard.py` through Python's AST support. This avoids executing live collectors or writing dashboard output during unit tests.

`tests/test_startup_preflight.py` separately covers missing and malformed configuration, runtime paths, conditional SSH credential requirements, startup ordering, failed initial generation, refresh-loop shutdown, and generated-dashboard health-check requirements.

The current runtime scaffold separates:

```text
docker-compose.yml = how Sanity Node runs
config.yaml        = what Sanity Node monitors
.env               = optional local overrides
ssh/               = optional SSH keys for remote checks
html/              = generated dashboard output
logs/              = runtime logs
```

---

## Public install direction

The current scaffolded public install flow is:

```text
git clone
create config, html, logs, and optional ssh directories
copy examples/config.example.yaml to config/config.yaml
optionally copy .env.example to .env
edit dashboard, collector, and host settings
add SSH keys only for enabled SSH-backed checks
start Sanity Node with Docker Compose
confirm the container reports healthy
open http://collector-ip:8099
enable optional features later
```

Sanity Node should start small and grow with the environment.

A first useful setup can be as simple as:

```text
dashboard
collector
one host
one or two basic modules
```

Optional features can be enabled later:

```text
services
local storage
backup checks
snapshot checks
replication checks
image update monitoring
```

---
## Phase 3 boundary

Phase 2F is closed. The following work is intentionally deferred to Phase 3 and is not considered a Phase 2F loose end:

- make the configuration-driven runtime the primary public dashboard path
- complete and validate a clean end-user installation and first-run guide
- add safer first-run, credential, and environment checks
- refine the four global summary cards for the public layout
- improve separation between the personal reference deployment and public template
- add optional remote Linux check families beyond Docker, storage, and backup status
- add backup-status providers beyond marker files
- add protection relationship types beyond replication
- decide when the original hardcoded reference path has reached migration parity

New Phase 3 features should continue using the established safeguards:

- narrowly scoped feature branches
- deterministic tests
- full regression validation
- configuration validation
- preview output only under `/tmp`
- production dashboard hash and mtime protection
- preserved remote feature references

---

## Philosophy

Sanity Node should stay simple.

It should observe what matters, announce clearly, and avoid becoming a monitoring monster.

Sanity Node is custom-built, open-source-minded, and hands-on by design.

It grew from learning, testing, breaking things, fixing them again, and turning those lessons into a dashboard that announces whether the homelab is still behaving as expected.

The purpose is not to collect every metric possible.

The purpose is to answer:

```text
Is my homelab still sane?
```

And if the answer is no, it should point me in the right direction before I waste half an evening blaming DNS again.

Although, to be fair, it probably was DNS.
