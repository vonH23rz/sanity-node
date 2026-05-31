# Sanity Node

> Observe. Announce. Stay sane.

Sanity Node is a lightweight homelab dashboard that observes systems, services, pools, snapshots, and replications from one small Linux machine.

It was originally built for my own homelab, where a small **Utility Node** watches multiple TrueNAS systems, Docker services, helper containers, ZFS pools, snapshot tasks, and replication jobs.

The goal is simple:

**Open one page and know whether the homelab is still doing what it should be doing.**

Because in a homelab, everything works perfectly until it does not.

---

## Screenshot

![Sanity Node dashboard screenshot](docs/assets/sanity-node-dashboard-readme.png)

---

## Current project status

Sanity Node is currently in an early public-preparation state.

This repository contains the working homelab-tested version, but it is not yet a universal one-click installer.

Current confidence level:

- Works in my own homelab
- Useful as a reference implementation
- Needs configuration cleanup before general use
- Some paths, hosts, services, and IP addresses are still tailored to my environment

In other words:

> It works.  
> It is useful.  
> It is not yet pretending to be enterprise software.  
> Very healthy.

---

## What Sanity Node monitors

Sanity Node can display:

- Linux / TrueNAS system information
- host uptime
- CPU and memory information
- load average
- TrueNAS pools
- ZFS pool health
- pool capacity
- disk temperatures
- SMART status
- snapshot task freshness
- replication state
- running apps
- helper containers
- HTTP-checked services

The dashboard separates services into two simple categories:

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
- Nginx Proxy Manager

### Helpers

Backend or infrastructure services that keep things alive in the background, such as:

- Cloudflare Tunnel
- Redis
- Ollama
- databases
- Tailscale

This makes the dashboard easier to read than a plain container count.

Instead of:

```text
14 containers running
```

Sanity Node can show:

```text
10 Apps · 4 Helpers · 14 UP · 0 DOWN
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

The full installation and explanation guide is available on the vonH23rz Wiki:

[Install Sanity Node](https://wiki.homelabvonh23rz.me/en/Install_Sanity-Node)

The wiki contains the more human explanation: what Sanity Node is, why it exists, what the dashboard blocks mean, and how it is used in my homelab.

---

## Repository structure

```text
sanity-node/
├── README.md
├── docs/
│   └── assets/
│       └── sanity-node-dashboard-readme.png
├── examples/
│   └── config.example.yaml
├── scripts/
│   └── generate-dashboard.py
├── systemd/
│   ├── sanity-node-generate.service
│   ├── sanity-node-generate.timer
│   └── sanity-node-web.service
└── web/
    └── favicon and web manifest assets
```

---

## Requirements

Current working environment:

- Ubuntu Linux for the Utility Node
- Python 3
- systemd
- SSH access from the Utility Node to TrueNAS systems
- TrueNAS SCALE systems reachable over LAN
- Docker access where local container checks are used
- HTTP access for services checked by URL

The current version assumes a fairly similar setup to the original homelab deployment.

The future version should move more of this into a proper configuration file.

---

## Systemd services

Example systemd unit files are included under:

```text
systemd/
```

They provide:

- a dashboard generator service
- a timer that regenerates the dashboard every 5 minutes
- a small Python HTTP server for serving the generated dashboard

The intended public install path is:

```text
/opt/sanity-node
```

---

## Important note

This project is currently being cleaned up for GitHub.

Some values may still be hardcoded, including:

- hostnames
- IP addresses
- service names
- TrueNAS-specific replication paths
- local dashboard paths

That is intentional for the first public version.

The goal is to publish the working version first, then slowly convert it into a cleaner, configuration-driven project.

No fake perfection.  
No magical installer lies.  
Just honest homelab progress.

---

## Future plans

Planned improvements:

- configuration-driven hosts
- configuration-driven services
- configurable apps/helpers
- configurable replication relationships
- cleaner install script
- safer first-run checks
- improved documentation
- example configs for different homelab layouts
- better separation between personal deployment and public template

---

## Philosophy

Sanity Node should stay simple.

It should observe what matters, announce clearly, and avoid becoming a monitoring monster.

The purpose is not to collect every metric possible.

The purpose is to answer:

```text
Is my homelab still sane?
```

And if the answer is no, it should point me in the right direction before I waste half an evening blaming DNS again.

Although, to be fair, it probably was DNS.
