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

Sanity Node is currently moving from a personal, homelab-tested reference implementation toward a public, configuration-driven project.

The current repository contains the working reference version that has been tested in my own environment. Some logic is still hardcoded for that setup.

The public direction is now defined:

- one Linux / Utility collector node
- one or more configured hosts
- optional TrueNAS SCALE monitoring
- optional local, Docker, HTTP, backup, replication, and update checks
- a self-documenting `config.yaml`
- a future Docker Compose install flow on port `8099`
- host-based public summary preview cards generated from configured hosts
- a public-preview four-card summary model:
  - Systems
  - Storage
  - Protection
  - Services / Updates

In other words:

> It works.
> It is useful.
> It is becoming more reusable.
> No fake perfection.

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

The current GitHub repository is still being aligned with that public install direction. Until the Docker/Compose/config-driven version is implemented, treat the installation tutorial as the target architecture for the next public phase.

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
│   └── validate-config.py
├── tests/
│   └── test_config_runtime.py
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
- SSH access from the Utility Node to TrueNAS systems
- TrueNAS SCALE middleware calls through `midclt`
- local Docker checks where available
- HTTP checks for selected services

Some values are still hardcoded in:

```text
scripts/generate-dashboard.py
```

This includes personal hostnames, IP addresses, services, pool relationships, local paths, and backup targets.

That is intentional for the current reference version. The next major development goal is to move those definitions into `config.yaml`.

---

## Configuration direction

The future public configuration model is represented in:

```text
examples/config.example.yaml
```

That file is intentionally self-documenting. It uses:

```text
🟧 Required = review or change this for your environment
🩵 Optional = enable only if you use this feature
```

The goal is that users should be able to describe their own homelab without editing the Python code.

Current Phase 2 public-preview behavior:

- configured hosts can appear as host-based summary cards
- host Web UI links can show preview reachability badges
- a confirmed TrueNAS SSH/network timeout collapses that host card to `Host unreachable` instead of listing every configured service
- confirmed TrueNAS host unreachability also overrides the host's Web UI result in the four-card Systems summary
- Web UI-only, authentication, host-key, and parsing failures retain the normal per-service detail and Systems status
- configured HTTP services can report live `UP` / `DOWN`
- configured Docker services on the collector node can report live container status
- configured TrueNAS app services can report live app status for enabled `type: truenas` hosts
- enabled TrueNAS hosts with `modules.snapshots: true` can report live snapshot-task state and latest-snapshot freshness
- enabled TrueNAS hosts with `modules.replications: true` can report live replication-task configuration and execution state
- configured image update sources can report live Diun container-image updates and TrueNAS-native app updates
- configured local storage checks can report collector-local filesystem usage using `df`
- configured backup checks can report collector-local marker-file freshness and optional systemd timer state
- Collector Errors include a classified Type badge for timeouts, network failures, host-key problems, authentication failures, refused connections, parsing failures, command failures, unknown messages, and other errors
- all Collector Errors remain failure rows; classification improves presentation only and does not change Overall Status handling
- configured protection relationships can render preview backup/replication relationships from `config.yaml`
- replication relationships can inherit live task status when source host, configured datasets, and target prefix confidently match a discovered TrueNAS replication task
- unmatched or incomplete relationships retain their configuration-preview status instead of being treated as failures
- configured `summary_cards` can render the first four-card public preview: Systems, Storage, Protection, and Services
- `summary_cards` controls card order and selection; duplicate names are removed, unknown names are ignored, and an empty/invalid list falls back to the default four cards
- when the four-card Services summary is active, host-based cards retain their service counts but show only non-`UP` service exceptions; fully healthy hosts show one `ALL UP` line
- when the Services summary is disabled, host-based cards retain the full per-service detail list
- Docker checks for other hosts, TrueNAS app checks on non-TrueNAS hosts, local storage checks for non-collector hosts, and backup checks for non-collector hosts are shown as `NOT CHECKED` for now
- live replication overlays affect only the config-driven Protection preview and card; they do not affect Overall Status or replace the original reference replication checks
- snapshot results remain separate from configured protection relationships for now
- the original hardcoded five-card reference summary remains untouched while this preview path is developed

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

The host must be enabled, use `type: truenas`, have an `address`, and have `modules.snapshots` set to `true`. The current preview uses the configured Sanity Node SSH credentials. Snapshot preview results do not affect Overall Status yet, and the original hardcoded snapshot cards remain untouched.

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

- collector-local Docker services are matched using the image reference returned by `docker inspect`
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

The Protection card normally reflects configuration completeness. Confidently matched live replication tasks can replace `CONFIGURED` with their current live status. A live `OK` relationship still counts as configured; warning and failure states retain their normal severity precedence.

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
- assembled four-card summary selection, normalized ordering, duplicate removal, unknown-card filtering, and default fallback
- protection-to-replication matching, path normalization, conservative no-match behavior, live severity overlays, and configured-count preservation

The tests extract only selected pure functions from `scripts/generate-dashboard.py` through Python's AST support. This avoids executing live collectors or writing dashboard output during unit tests.

The future model separates:

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

The planned public install flow is:

```text
git clone
copy config.example.yaml to config.yaml
edit dashboard, collector, and host settings
add SSH keys if TrueNAS monitoring is enabled
start Sanity Node with Docker Compose
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
## Future plans

Planned improvements:

- configuration-driven hosts
- configuration-driven services
- configuration-driven local storage checks
- configuration-driven backup checks
- live validation for configuration-driven protection relationships
- Docker Compose runtime
- `.env.example`
- Dockerfile
- safer first-run checks
- public-preview layout refinement for the four global summary cards
- cleaner separation between personal deployment and public template

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
