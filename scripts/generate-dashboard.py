#!/usr/bin/env python3

import subprocess
import json
import html
import re
import os
from datetime import datetime, timedelta
from pathlib import Path
from statistics import mean

OUT = Path(os.environ.get("SANITY_NODE_OUTPUT", "/opt/homelab-dashboard/html/index.html"))
CONFIG_PATH = Path(os.environ.get("SANITY_NODE_CONFIG", "/app/config/config.yaml"))


def load_config(path):
    if not path.exists():
        return {}

    try:
        import yaml
    except Exception as exc:
        print(f"Config file found at {path}, but PyYAML is unavailable: {exc}")
        return {}

    try:
        data = yaml.safe_load(path.read_text()) or {}
    except Exception as exc:
        print(f"Failed to read config file {path}: {exc}")
        return {}

    if not isinstance(data, dict):
        print(f"Config file {path} did not contain a YAML mapping; ignoring it")
        return {}

    return data


CONFIG = load_config(CONFIG_PATH)


def cfg_get(path, default=None):
    current = CONFIG

    for key in path:
        if not isinstance(current, dict) or key not in current:
            return default
        current = current[key]

    return current


def cfg_int(path, default):
    value = cfg_get(path, default)

    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def cfg_list(path, default=None):
    value = cfg_get(path, default if default is not None else [])

    if isinstance(value, list):
        return value

    print(f"Config value {'.'.join(path)} is not a list; ignoring it")
    return []


def enabled_items(items):
    return [
        item for item in items
        if isinstance(item, dict) and item.get("enabled", True)
    ]


CONFIG_HOSTS = cfg_list(("hosts",))
CONFIG_ENABLED_HOSTS = enabled_items(CONFIG_HOSTS)

CONFIG_SERVICES = cfg_list(("services",))
CONFIG_ENABLED_SERVICES = enabled_items(CONFIG_SERVICES)

CONFIG_PROTECTION = cfg_list(("protection",))
CONFIG_ENABLED_PROTECTION = enabled_items(CONFIG_PROTECTION)

print(
    "Loaded config inventory: "
    f"{len(CONFIG_ENABLED_HOSTS)}/{len(CONFIG_HOSTS)} hosts enabled, "
    f"{len(CONFIG_ENABLED_SERVICES)}/{len(CONFIG_SERVICES)} services enabled, "
    f"{len(CONFIG_ENABLED_PROTECTION)}/{len(CONFIG_PROTECTION)} protection relationships enabled"
)


DASHBOARD_TITLE = str(cfg_get(("dashboard", "title"), "Sanity Node"))
DASHBOARD_SUBTITLE = str(cfg_get(("dashboard", "subtitle"), "Observe. Announce. Stay sane."))
REFRESH_MINUTES = cfg_int(("dashboard", "refresh_minutes"), 5)
COLLECTOR_DISPLAY_NAME = str(cfg_get(("collector", "display_name"), "Utility Node"))
STALE_AFTER_SECONDS = max(REFRESH_MINUTES, 1) * 3 * 60

SSH_USER = os.environ.get("SANITY_NODE_SSH_USER", "truenas_admin")
SSH_KEY = os.environ.get("SANITY_NODE_SSH_KEY", "/home/controls/.ssh/id_ed25519")

# ---------------------------------------------------------------------------
# Reference dashboard runtime configuration
# ---------------------------------------------------------------------------
#
# These values still describe the original/personal reference dashboard.
# Phase 2 public-runtime work is being added beside this path first, using
# CONFIG_HOSTS / CONFIG_SERVICES and preview-only rendering. Do not remove or
# rewrite the reference runtime in one large step; migrate collectors and layout
# gradually while keeping the known-good dashboard behavior available.
#
T620_IP = "192.168.30.10"
T330_IP = "192.168.30.33"

HOSTS = {
    "T620 TrueNAS": {
        "ip": T620_IP,
        "url": "http://192.168.30.10:81",
    },
    "T330 TrueNAS": {
        "ip": T330_IP,
        "url": "http://192.168.30.33",
    },
}


HOST_STATUS_HOSTS = dict(HOSTS)
BECKHOFF_SERVICES = [
    {"id": "familienbudget", "display": "Familienbudget", "type": "app", "url": "http://192.168.30.11:7579"},
    {"id": "wikijs-private", "display": "Wiki.js Private", "type": "app", "url": "http://192.168.30.11:3011"},
    {"id": "pihole", "display": "Pi-hole", "type": "app", "url": "http://192.168.30.11:8081/admin/"},
    {"id": "nginx-proxy-manager", "display": "Nginx Proxy Manager", "type": "app", "url": "http://192.168.30.11:81"},
    {"id": "dockge", "display": "Dockge", "type": "app", "url": "http://192.168.30.11:5001"},
    {"id": "tunnel", "display": "Cloudflare Tunnel", "type": "helper", "url": None},
    {"id": "wikijs-private-db", "display": "Wiki.js Database", "type": "helper", "url": None},
]


T620_SERVICES = [
    {"id": "searxng", "display": "SearXNG", "type": "app", "url": "http://192.168.30.10:30053/"},
    {"id": "jellyfin", "display": "Jellyfin", "type": "app", "url": "http://192.168.30.10:8069/"},
    {"id": "open-webui", "display": "OpenWebUI", "type": "app", "url": "http://192.168.30.10:31028/"},
    {"id": "filebrowser-quantum", "display": "File Browser", "type": "app", "url": "http://192.168.30.10:30334/"},
    {"id": "scrutiny", "display": "Scrutiny", "type": "app", "url": "http://192.168.30.10:31054/"},
    {"id": "open-speed-test", "display": "Open Speed Test", "type": "app", "url": "http://192.168.30.10:30116/"},
    {"id": "dockge", "display": "Dockge", "type": "app", "url": "http://192.168.30.10:5001/"},
    {"id": "portracker", "display": "Portracker", "type": "app", "url": "http://192.168.30.10:4999", "check": "http"},
    {"id": "qbittorrent-vpn", "display": "qBittorrent VPN", "type": "app", "url": "http://192.168.30.10:8080", "check": "http"},
    {"id": "wikijs", "display": "Wiki.js", "type": "app", "url": "http://192.168.30.10:9190", "check": "http"},
    {"id": "tailscale", "display": "Tailscale", "type": "helper", "url": None},
    {"id": "cloudflared", "display": "Cloudflare Tunnel", "type": "helper", "url": None},
    {"id": "ollama", "display": "Ollama", "type": "helper", "url": None},
    {"id": "redis", "display": "Redis", "type": "helper", "url": None},
]


def service_label_from_state(raw_state, exists=True):
    if not exists:
        return "MISSING", "bad"

    if raw_state is None:
        return "UNKNOWN", "info"

    state = str(raw_state).strip().upper()

    if state in ("RUNNING", "UP", "HEALTHY", "TRUE"):
        return "UP", "ok"

    if state in ("DEPLOYING", "STARTING", "STOPPING", "INITIALIZING", "RESTARTING"):
        return "INFO", "info"

    return "DOWN", "bad"


def collect_local_docker_services(services):
    statuses = {}
    errors = []

    for service in services:
        service_id = service["id"]

        try:
            result = subprocess.run(
                ["docker", "inspect", service_id],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except Exception as e:
            statuses[service_id] = {"label": "UNKNOWN", "css": "info", "raw": str(e)}
            errors.append(f"{service_id}: {e}")
            continue

        if result.returncode != 0:
            output = (result.stdout + result.stderr).strip()
            statuses[service_id] = {"label": "MISSING", "css": "bad", "raw": output}
            errors.append(f"{service_id}: {output}")
            continue

        try:
            payload = json.loads(result.stdout)
            state = payload[0].get("State", {})
            raw_state = "RUNNING" if state.get("Running") else state.get("Status")
            label, css = service_label_from_state(raw_state, exists=True)
        except Exception as e:
            raw_state = str(e)
            label, css = "UNKNOWN", "info"
            errors.append(f"{service_id}: Docker inspect parse error: {e}")

        statuses[service_id] = {"label": label, "css": css, "raw": raw_state}

    return statuses, errors


def config_service_safe_name(name):
    return re.sub(r"[^a-zA-Z0-9_.-]+", "-", str(name).lower()).strip("-")


def normalize_config_service(service, index):
    if not isinstance(service, dict):
        return None

    name = service.get("name") or service.get("id") or f"Service {index}"
    safe_name = config_service_safe_name(name)
    service_id = service.get("id") or f"config-service-{index}-{safe_name or 'service'}"

    service_type = service.get("type", "app")
    if service_type not in ("app", "helper"):
        service_type = "app"

    return {
        "id": str(service_id),
        "display": str(name),
        "type": service_type,
        "url": service.get("url"),
        "host": service.get("host"),
        "check": service.get("check"),
    }


def normalize_config_services_for_summary(services):
    normalized = []

    for index, service in enumerate(services, start=1):
        normalized_service = normalize_config_service(service, index)
        if normalized_service:
            normalized.append(normalized_service)

    return normalized


def normalize_config_http_services(services):
    return [
        service for service in normalize_config_services_for_summary(services)
        if service.get("check") == "http"
    ]


def collect_http_services(services):
    statuses = {}

    for service in services:
        service_id = service["id"]
        url = service.get("url")

        if not url:
            statuses[service_id] = {"label": "UNKNOWN", "css": "info", "raw": "missing url"}
            continue

        try:
            result = subprocess.run(
                [
                    "curl",
                    "-k",
                    "-L",
                    "-s",
                    "-o",
                    "/dev/null",
                    "--connect-timeout",
                    "5",
                    "--max-time",
                    "10",
                    "-w",
                    "%{http_code}",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )

            http_code = (result.stdout + result.stderr).strip()
            ok = (
                result.returncode == 0
                and http_code.isdigit()
                and int(http_code) != 0
                and int(http_code) < 500
            )

            if ok:
                statuses[service_id] = {"label": "UP", "css": "ok", "raw": f"HTTP {http_code}"}
            else:
                raw = f"HTTP {http_code}" if http_code else "HTTP check failed"
                statuses[service_id] = {"label": "DOWN", "css": "bad", "raw": raw}

        except Exception as e:
            statuses[service_id] = {"label": "DOWN", "css": "bad", "raw": str(e)}

    return statuses



def collect_truenas_app_services(ip, services):
    statuses = {}

    # HTTP-checked services are useful for Dockge/Compose stacks and any service
    # where web reachability matters more than the underlying app source.
    for service in services:
        if service.get("check") != "http":
            continue

        service_id = service["id"]
        url = service.get("url")

        if not url:
            statuses[service_id] = {"label": "UNKNOWN", "css": "info", "raw": "missing url"}
            continue

        try:
            result = subprocess.run(
                [
                    "curl",
                    "-k",
                    "-L",
                    "-s",
                    "-o",
                    "/dev/null",
                    "--connect-timeout",
                    "5",
                    "--max-time",
                    "10",
                    "-w",
                    "%{http_code}",
                    url,
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )

            http_code = (result.stdout + result.stderr).strip()
            ok = (
                result.returncode == 0
                and http_code.isdigit()
                and int(http_code) != 0
                and int(http_code) < 500
            )

            if ok:
                statuses[service_id] = {"label": "UP", "css": "ok", "raw": f"HTTP {http_code}"}
            else:
                raw = f"HTTP {http_code}" if http_code else "HTTP check failed"
                statuses[service_id] = {"label": "DOWN", "css": "bad", "raw": raw}

        except Exception as e:
            statuses[service_id] = {"label": "DOWN", "css": "bad", "raw": str(e)}

    app_services = [service for service in services if service.get("check") != "http"]

    apps, error = remote_json(ip, "midclt call app.query")

    if apps is None:
        for service in app_services:
            statuses[service["id"]] = {"label": "UNKNOWN", "css": "info", "raw": error}
        return statuses, error

    app_by_name = {}

    for app in apps:
        name = app.get("name") or app.get("id")
        if name:
            app_by_name[name] = app

    for service in app_services:
        service_id = service["id"]
        app = app_by_name.get(service_id)

        if not app:
            label, css = service_label_from_state(None, exists=False)
            raw_state = "missing"
        else:
            raw_state = app.get("state") or app.get("status")
            label, css = service_label_from_state(raw_state, exists=True)

        statuses[service_id] = {"label": label, "css": css, "raw": raw_state}

    return statuses, None



def display_os_for_host(host_name, status):
    raw_os = status.get("os", "-")
    kernel = status.get("kernel", "")

    if "truenas" in str(kernel).lower():
        return "TrueNAS SCALE"

    return raw_os


def activity_label_for_host(host_name):
    if host_name == "Utility Node":
        return "Containers"
    return "Apps"


def activity_value_for_host(host_name, status):
    if host_name == "Utility Node":
        running = status.get("containers_running", "-")
        total = status.get("containers_total", "-")
    else:
        running = status.get("apps_running", "-")
        total = status.get("apps_total", "-")

    if running == "-" and total == "-":
        return "-"

    return f"{running} / {total} running"


def info_item(label, value):
    return (
        '<div class="info-item">'
        f'<div class="info-label">{h(label)}</div>'
        f'<div class="info-value">{h(value)}</div>'
        '</div>'
    )


def system_info_card(host_name, status):
    card_css = "ok" if status.get("reachable") else "bad"
    reachable_label = "ONLINE" if status.get("reachable") else "OFFLINE"
    reachable_css = "ok" if status.get("reachable") else "bad"

    return (
        f'<div class="system-card {card_css}">'
        '<div class="system-card-header">'
        '<div>'
        '<div class="system-card-kicker">System Information</div>'
        f'<h3>{h(host_name)}</h3>'
        '</div>'
        f'{badge(reachable_label, reachable_css)}'
        '</div>'
        '<div class="system-info-grid">'
        f'{info_item("Hostname", status.get("hostname", "-"))}'
        f'{info_item("OS", display_os_for_host(host_name, status))}'
        f'{info_item("Kernel", status.get("kernel", "-"))}'
        f'{info_item("Uptime", status.get("uptime", "-"))}'
        '<div class="info-item wide">'
        '<div class="info-label">CPU Model</div>'
        f'<div class="info-value">{h(status.get("cpu_model", "-"))}</div>'
        '</div>'
        f'{info_item("CPU Cores", status.get("cpu_cores", "-"))}'
        f'{info_item("Memory", status.get("memory_total", "-"))}'
        f'{info_item("Load", status.get("load", "-"))}'
        f'{info_item(activity_label_for_host(host_name), activity_value_for_host(host_name, status))}'
        '</div>'
        '</div>'
    )



def pool_status_card(host_name, rows):
    if not rows:
        body = (
            '<div class="pool-placeholder">'
            'Local storage monitoring not configured.'
            '</div>'
        )
    else:
        body = (
            '<table>'
            '<tr>'
            '<th>Pool</th>'
            '<th>Size</th>'
            '<th>Cap</th>'
            '<th>Disk Temp</th>'
            '<th>SMART</th>'
            '<th>Health</th>'
            '</tr>'
            f'{rows}'
            '</table>'
        )

    return (
        '<div class="pool-card">'
        '<div class="pool-card-header">'
        '<div>'
        '<div class="pool-card-kicker">Pool Status</div>'
        '</div>'
        '</div>'
        f'{body}'
        '</div>'
    )



def replication_status_card(rows, title="Snapshot / Replication", empty_text="No replications configured."):
    if not rows:
        body = (
            '<div class="pool-placeholder">'
            f'{h(empty_text)}'
            '</div>'
        )
    else:
        body = (
            '<table>'
            '<tr>'
            '<th>Source</th>'
            '<th>T620</th>'
            '<th>T330</th>'
            '<th>Sync</th>'
            '<th>Fresh</th>'
            '<th>Repl</th>'
            '</tr>'
            f'{rows}'
            '</table>'
        )

    return (
        '<div class="replication-card">'
        '<div class="pool-card-header">'
        '<div>'
        f'<div class="pool-card-kicker">{h(title)}</div>'
        '</div>'
        '</div>'
        f'{body}'
        '</div>'
    )


def build_service_summary(services, statuses):
    app_count = len([service for service in services if service.get("type") == "app"])
    helper_count = len([service for service in services if service.get("type") == "helper"])

    up_count = 0
    down_count = 0
    info_count = 0
    detail_html = ""

    for service in services:
        service_id = service["id"]
        status = statuses.get(service_id, {"label": "UNKNOWN", "css": "info", "raw": "-"})
        label = status["label"]
        css = status["css"]

        if label == "UP":
            up_count += 1
        elif css == "bad":
            down_count += 1
        else:
            info_count += 1

        name = h(service["display"])
        url = service.get("url")

        if url:
            name_html = f'<a class="service-link" href="{h(url)}" target="_blank" rel="noopener noreferrer">{name}</a>'
        else:
            name_html = name

        detail_html += (
            '<span class="service-line">'
            f'<strong>{name_html}</strong> '
            f'<span class="{status_text_class(label)}">{h(label)}</span>'
            '</span>\n'
        )

    value = f"{app_count} Apps · {helper_count} Helpers · {up_count} UP · {down_count} DOWN"

    if info_count:
        value += f" · {info_count} INFO"

    if down_count:
        card_css = "bad"
    elif info_count:
        card_css = "info"
    else:
        card_css = ""

    return {
        "value": value,
        "details": detail_html,
        "details_class": "two-column" if len(services) > 6 else "",
        "css": card_css,
        "up": up_count,
        "down": down_count,
        "info": info_count,
    }




def configured_host_key(host):
    return str(host.get("id") or host.get("display_name") or host.get("hostname") or host.get("address") or "")


def collect_configured_host_web_statuses(hosts):
    statuses = {}

    for host in hosts:
        if not isinstance(host, dict):
            continue

        host_key = configured_host_key(host)

        if not host_key:
            continue

        if not bool(host.get("enabled", True)):
            statuses[host_key] = {"label": "DISABLED", "css": "info", "raw": "host disabled"}
            continue

        web_url = host.get("web_url")

        if not web_url:
            statuses[host_key] = {"label": "NO URL", "css": "info", "raw": "missing web_url"}
            continue

        try:
            result = subprocess.run(
                [
                    "curl",
                    "-k",
                    "-L",
                    "-s",
                    "-o",
                    "/dev/null",
                    "--connect-timeout",
                    "5",
                    "--max-time",
                    "10",
                    "-w",
                    "%{http_code}",
                    str(web_url),
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )

            http_code = (result.stdout + result.stderr).strip()
            ok = (
                result.returncode == 0
                and http_code.isdigit()
                and int(http_code) != 0
                and int(http_code) < 500
            )

            if ok:
                statuses[host_key] = {"label": "OK", "css": "ok", "raw": f"HTTP {http_code}"}
            else:
                raw = f"HTTP {http_code}" if http_code else "HTTP check failed"
                statuses[host_key] = {"label": "DOWN", "css": "bad", "raw": raw}

        except Exception as e:
            statuses[host_key] = {"label": "DOWN", "css": "bad", "raw": str(e)}

    return statuses


def build_configured_hosts_preview(hosts, web_statuses=None):
    if not hosts:
        return ""

    web_statuses = web_statuses or {}
    rows = ""

    sorted_hosts = sorted(
        [host for host in hosts if isinstance(host, dict)],
        key=lambda host: (
            not bool(host.get("enabled", True)),
            str(host.get("display_name") or host.get("hostname") or host.get("id") or "").lower(),
        ),
    )

    enabled_count = len([host for host in sorted_hosts if bool(host.get("enabled", True))])
    disabled_count = len(sorted_hosts) - enabled_count

    for host in sorted_hosts:
        host_key = configured_host_key(host)
        enabled = bool(host.get("enabled", True))
        label = "ENABLED" if enabled else "DISABLED"
        css = "ok" if enabled else "info"
        row_class = "enabled" if enabled else "disabled"

        display_name = host.get("display_name") or host.get("hostname") or host.get("id") or "-"
        host_type = host.get("type", "-")
        address = host.get("address", "-")
        host_id = host.get("id", "-")
        web_url = host.get("web_url")

        web_status = web_statuses.get(host_key, {"label": "NO URL", "css": "info", "raw": "-"})
        web_label = web_status.get("label", "UNKNOWN")
        web_css = web_status.get("css", "info")

        if web_url:
            name_html = f'<a class="host-link" href="{h(web_url)}" target="_blank" rel="noopener noreferrer">{h(display_name)}</a>'
        else:
            name_html = h(display_name)

        rows += f"""
      <tr class="configured-host-row {h(row_class)}">
        <td>{badge(label, css)}</td>
        <td>{name_html}</td>
        <td>{h(host_id)}</td>
        <td>{h(host_type)}</td>
        <td><span class="mono">{h(address)}</span></td>
        <td>{badge(web_label, web_css)}</td>
      </tr>
"""

    if not rows:
        return ""

    return f"""
  <div class="configured-hosts-preview">
    <div class="configured-hosts-preview-header">
      <div>
        <div class="configured-hosts-kicker">Config Preview</div>
        <h3>Configured Hosts</h3>
      </div>
      <div class="configured-hosts-meta">{h(enabled_count)} enabled · {h(disabled_count)} disabled</div>
    </div>
    <p class="muted-small">Read from config.yaml. Web UI checks are preview-only and do not affect Overall Status yet.</p>
    <table>
      <tr>
        <th>Status</th>
        <th>Name</th>
        <th>ID</th>
        <th>Type</th>
        <th>Address</th>
        <th>Web UI</th>
      </tr>
      {rows}
    </table>
  </div>
"""



def configured_host_display_name(host):
    return str(host.get("display_name") or host.get("hostname") or host.get("id") or "Configured Host")


def configured_host_sort_key(host):
    # Public summary cards are host/system based, not category based.
    # Preferred order:
    #   1. collector / Utility Node
    #   2. TrueNAS systems
    #   3. any additional enabled configured hosts
    host_id = str(host.get("id") or "").lower()
    host_type = str(host.get("type") or "").lower()
    collector_id = str(cfg_get(("collector", "id"), "collector")).lower()

    if host_id == collector_id or host_id == "collector":
        group = 0
    elif host_type == "truenas":
        group = 1
    else:
        group = 2

    return (group, configured_host_display_name(host).lower())


def build_public_host_summary_preview(hosts, services, statuses, web_statuses=None):
    # This is intentionally preview-only while the existing reference summary row
    # remains active. The four-column CSS is a layout maximum, not a fixed number
    # of required cards: two configured hosts should render two summary cards.
    enabled_hosts = enabled_items(hosts)
    web_statuses = web_statuses or {}

    if not enabled_hosts:
        return ""

    sorted_hosts = sorted(enabled_hosts, key=configured_host_sort_key)
    services_by_host = {}

    for service in services:
        host_id = service.get("host")
        if not host_id:
            continue

        services_by_host.setdefault(str(host_id), []).append(service)

    cards_html = ""

    for host in sorted_hosts:
        host_id = str(host.get("id") or "")
        title = configured_host_display_name(host)
        host_key = configured_host_key(host)
        host_web_status = web_statuses.get(host_key, {"label": "NO URL", "css": "info", "raw": "-"})
        host_services = services_by_host.get(host_id, [])
        summary = build_service_summary(host_services, statuses)
        host_web_css = host_web_status.get("css", "info")
        host_card_css = summary["css"]

        if host_web_css == "bad":
            host_card_css = "bad"
        elif host_web_css == "info" and not host_card_css:
            host_card_css = "info"

        details = summary["details"]

        if not details:
            details = '<span class="service-line"><strong>No services configured yet</strong> <span class="info-text">INFO</span></span>'

        cards_html += f"""
    <div class="summary-card {h(host_card_css)}">
      <div class="title">{h(title)} {badge(host_web_status.get("label", "UNKNOWN"), host_web_status.get("css", "info"))}</div>
      <div class="value">{h(summary["value"])}</div>
      <div class="summary-details service-details {h(summary["details_class"])}">
        {details}
      </div>
    </div>
"""

    return f"""
<div class="public-summary-preview">
  <div class="public-summary-preview-header">
    <div>
      <div class="public-summary-kicker">Public Layout Preview</div>
      <h2>Host-based summary direction</h2>
    </div>
    <div class="public-summary-note">Preview only · existing summary cards unchanged</div>
  </div>
  <div class="public-summary-row">
    {cards_html}
  </div>
</div>
"""


def h(value):
    return html.escape(str(value))


def run_ssh(ip, command, timeout=30):
    cmd = [
        "ssh",
        "-i", SSH_KEY,
        "-o", "IdentitiesOnly=yes",
        "-o", "BatchMode=yes",
        "-o", "ConnectTimeout=5",
        f"{SSH_USER}@{ip}",
        command,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        output = (result.stdout + result.stderr).strip()

        if result.returncode != 0:
            return False, output

        return True, output

    except subprocess.TimeoutExpired:
        return False, "Command timed out"


def remote_json(ip, command):
    ok, output = run_ssh(ip, command)

    if not ok:
        return None, output

    try:
        return json.loads(output), None
    except json.JSONDecodeError as e:
        return None, f"JSON parse error: {e}\n{output}"


def parse_datetime(value):
    if value is None:
        return None

    if isinstance(value, dict) and "$date" in value:
        try:
            return datetime.fromtimestamp(int(value["$date"]) / 1000)
        except Exception:
            return None

    raw = str(value).strip()

    if raw.isdigit():
        number = int(raw)
        if number > 100000000000:
            number = number / 1000
        return datetime.fromtimestamp(number)

    cleaned = re.sub(r"\s+", " ", raw)

    for fmt in ("%a %b %d %H:%M %Y", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(cleaned, fmt)
        except ValueError:
            pass

    return None


def fmt_dt(dt):
    if not dt:
        return "-"
    return dt.strftime("%Y-%m-%d %H:%M")


def human_delta(dt, future=False):
    if not dt:
        return "-"

    now = datetime.now()
    delta = dt - now if future else now - dt
    seconds = int(delta.total_seconds())

    if seconds < 0:
        seconds = abs(seconds)

    minutes = seconds // 60
    days = minutes // 1440
    hours = (minutes % 1440) // 60
    mins = minutes % 60

    parts = []

    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{mins}m")

    return " ".join(parts)


def parse_cron_field(value, minimum, maximum):
    value = str(value).strip()

    if value == "*" or value == "":
        return set(range(minimum, maximum + 1))

    result = set()

    for part in value.split(","):
        part = part.strip()

        if part.startswith("*/"):
            step = int(part[2:])
            result.update(range(minimum, maximum + 1, step))

        elif "-" in part:
            if "/" in part:
                range_part, step_part = part.split("/", 1)
                step = int(step_part)
            else:
                range_part = part
                step = 1

            start, end = range_part.split("-", 1)
            result.update(range(int(start), int(end) + 1, step))

        else:
            result.add(int(part))

    return {x for x in result if minimum <= x <= maximum}


def parse_clock(value):
    hour, minute = str(value).split(":")
    return int(hour), int(minute)


def inside_window(dt, begin, end):
    begin_hour, begin_minute = parse_clock(begin)
    end_hour, end_minute = parse_clock(end)

    current = dt.hour * 60 + dt.minute
    start = begin_hour * 60 + begin_minute
    stop = end_hour * 60 + end_minute

    if start <= stop:
        return start <= current <= stop

    return current >= start or current <= stop


def matches_schedule(dt, schedule):
    minutes = parse_cron_field(schedule.get("minute", "*"), 0, 59)
    hours = parse_cron_field(schedule.get("hour", "*"), 0, 23)
    doms = parse_cron_field(schedule.get("dom", "*"), 1, 31)
    months = parse_cron_field(schedule.get("month", "*"), 1, 12)
    dows = parse_cron_field(schedule.get("dow", "*"), 1, 7)

    begin = schedule.get("begin", "00:00")
    end = schedule.get("end", "23:59")

    truenas_dow = dt.weekday() + 1

    return (
        dt.minute in minutes
        and dt.hour in hours
        and dt.day in doms
        and dt.month in months
        and truenas_dow in dows
        and inside_window(dt, begin, end)
    )


def previous_run(schedule):
    now = datetime.now().replace(second=0, microsecond=0)
    candidate = now

    for _ in range(366 * 24 * 60):
        if matches_schedule(candidate, schedule):
            return candidate
        candidate -= timedelta(minutes=1)

    return None


def collect_snapshots(ip):
    ok, output = run_ssh(ip, "zfs list -H -p -t snapshot -o name,creation -s creation", timeout=60)

    snapshots = {}

    if not ok:
        return snapshots, output

    for line in output.splitlines():
        if not line.strip():
            continue

        if "\t" in line:
            name, created = line.split("\t", 1)
        else:
            parts = line.split(None, 1)
            if len(parts) != 2:
                continue
            name, created = parts

        snapshots[name] = parse_datetime(created)

    return snapshots, None


def latest_snapshot(snapshots, dataset):
    prefix = dataset + "@"
    matches = []

    for name, created in snapshots.items():
        if name.startswith(prefix) and created:
            matches.append((name, created))

    if not matches:
        return None, None

    return max(matches, key=lambda item: item[1])


def short_snapshot(name):
    if not name:
        return "-"
    if "@" not in name:
        return name
    return name.split("@", 1)[1]


def badge(label, css):
    return f'<span class="badge {h(css)}">{h(label)}</span>'


def temp_badge(label, css):
    return f'<span class="temp-badge {h(css)}">{h(label)}</span>'


def status_text_class(label):
    if label in ("OK", "FINISHED", "SUCCESS", "YES", "ONLINE", "UP"):
        return "ok-text"
    if label in ("INFO", "PENDING", "RUNNING", "UNKNOWN"):
        return "info-text"
    if label in ("WARNING", "OLD", "DIFFERENT"):
        return "warning-text"
    return "bad-text"


def freshness_status(task, latest_dt):
    if not task:
        return "UNKNOWN", "warning", "-"

    if not task.get("enabled"):
        return "DISABLED", "disabled", "snapshot task disabled"

    if not latest_dt:
        return "MISSING", "bad", "no snapshot found"

    schedule = task.get("schedule") or {}
    prev = previous_run(schedule)

    if not prev:
        return "UNKNOWN", "warning", "cannot calculate previous run"

    grace = timedelta(minutes=5)

    if latest_dt + grace >= prev:
        return "OK", "ok", "fresh enough"

    if task.get("allow_empty") is False:
        return "OK", "ok", "no changes since last schedule; allow_empty=false"

    return "OLD", "warning", "older than last scheduled run"


def replication_time(replication):
    state = replication.get("state") or {}
    dt = parse_datetime(state.get("datetime"))
    return fmt_dt(dt)


def replication_state(replication):
    state = replication.get("state") or {}
    return state.get("state") or "-"


def collect_pools(ip):
    ok, output = run_ssh(ip, "zpool list -H -o name,size,alloc,free,cap,health")

    pools = []

    if not ok:
        return pools, output

    for line in output.splitlines():
        parts = line.split()
        if len(parts) < 6:
            continue

        pool, size, used, free, cap, health = parts[:6]
        pools.append({
            "pool": pool,
            "size": size,
            "used": used,
            "free": free,
            "cap": cap,
            "health": health,
        })

    return pools, None


def temp_to_int(value):
    if value is None:
        return None

    if isinstance(value, dict):
        for key in ("temperature", "temp", "value"):
            if key in value:
                return temp_to_int(value[key])
        return None

    raw = str(value).strip()
    match = re.search(r"-?\d+", raw)

    if not match:
        return None

    try:
        return int(match.group(0))
    except ValueError:
        return None


def collect_pool_temperatures(ip):
    remote_script = r"""python3 - <<'REMOTE_PY'
import json
import os
import re
import subprocess


def run(cmd):
    return subprocess.check_output(
        cmd,
        shell=True,
        text=True,
        stderr=subprocess.DEVNULL,
    )


def base_device(path):
    real = os.path.realpath(path)
    name = os.path.basename(real)

    # nvme0n1p1 -> nvme0n1
    m = re.match(r"^(nvme\d+n\d+)p\d+$", name)
    if m:
        return m.group(1)

    # sda1 -> sda, sdi3 -> sdi, vda1 -> vda
    m = re.match(r"^((?:sd|vd|xvd|hd)[a-z]+)\d+$", name)
    if m:
        return m.group(1)

    return name


try:
    temps = json.loads(run("midclt call disk.temperatures"))
except Exception as e:
    print(json.dumps({"error": f"disk.temperatures failed: {e}", "pools": {}}))
    raise SystemExit(0)

try:
    status = run("zpool status -P")
except Exception as e:
    print(json.dumps({"error": f"zpool status failed: {e}", "pools": {}}))
    raise SystemExit(0)

current_pool = None
pool_devices = {}

for line in status.splitlines():
    pool_match = re.match(r"\s*pool:\s+(\S+)", line)

    if pool_match:
        current_pool = pool_match.group(1)
        pool_devices.setdefault(current_pool, set())
        continue

    if not current_pool:
        continue

    parts = line.split()

    if not parts:
        continue

    token = parts[0]

    if token.startswith("/dev/"):
        dev = base_device(token)
        pool_devices.setdefault(current_pool, set()).add(dev)

result = {}

for pool, devices in pool_devices.items():
    values = []

    for dev in sorted(devices):
        value = temps.get(dev)

        if value is None:
            value = temps.get(f"/dev/{dev}")

        if value is None:
            continue

        try:
            values.append(float(value))
        except Exception:
            pass

    if values:
        result[pool] = {
            "avg": round(sum(values) / len(values)),
            "max": round(max(values)),
            "devices": sorted(devices),
        }

print(json.dumps({"error": None, "pools": result}))
REMOTE_PY"""

    ok, output = run_ssh(ip, remote_script, timeout=60)

    if not ok:
        return {}, output

    try:
        payload = json.loads(output.strip().splitlines()[-1])
    except Exception as e:
        return {}, f"temperature JSON parse error: {e}\n{output}"

    return payload.get("pools", {}), payload.get("error")

def pool_is_nvme(pool_name, temp_info):
    if "nvme" in pool_name.lower():
        return True

    for dev in temp_info.get("devices", []):
        if dev.startswith("nvme"):
            return True

    return False


def temperature_status(pool_name, temp_info):
    if not temp_info:
        return "-", "disabled", None

    avg_temp = temp_info.get("avg")
    max_temp = temp_info.get("max")

    if avg_temp is None or max_temp is None:
        return "-", "disabled", None

    is_nvme = pool_is_nvme(pool_name, temp_info)

    if is_nvme:
        if max_temp >= 70:
            return f"{avg_temp}°C avg / {max_temp}°C max · WARNING", "warning", f"{pool_name} NVMe temperature warning"
        if max_temp >= 60:
            return f"{avg_temp}°C avg / {max_temp}°C max · INFO", "info", f"{pool_name} NVMe temperature warm, below warning threshold"
        return f"{avg_temp}°C avg / {max_temp}°C max", "ok", None

    if max_temp >= 58:
        return f"{avg_temp}°C avg / {max_temp}°C max · WARNING", "warning", f"{pool_name} disk temperature warning"
    if max_temp >= 50:
        return f"{avg_temp}°C avg / {max_temp}°C max · INFO", "info", f"{pool_name} disk temperature warm"
    return f"{avg_temp}°C avg / {max_temp}°C max", "ok", None



def collect_pool_smart(ip):
    remote_script = r"""python3 - <<'REMOTE_PY'
import json
import os
import re
import subprocess


def run(cmd):
    return subprocess.run(
        cmd,
        shell=True,
        text=True,
        capture_output=True,
        timeout=30,
    )


def base_device(path):
    real = os.path.realpath(path)
    name = os.path.basename(real)

    m = re.match(r"^(nvme\d+n\d+)p\d+$", name)
    if m:
        return m.group(1)

    m = re.match(r"^((?:sd|vd|xvd|hd)[a-z]+)\d+$", name)
    if m:
        return m.group(1)

    return name


def pool_devices_from_zpool():
    result = {}

    zpool = run("zpool status -P")
    if zpool.returncode != 0:
        return result, zpool.stdout + zpool.stderr

    current_pool = None

    for line in zpool.stdout.splitlines():
        pool_match = re.match(r"\s*pool:\s+(\S+)", line)

        if pool_match:
            current_pool = pool_match.group(1)
            result.setdefault(current_pool, set())
            continue

        if not current_pool:
            continue

        parts = line.split()

        if not parts:
            continue

        token = parts[0]

        if token.startswith("/dev/"):
            result.setdefault(current_pool, set()).add(base_device(token))

    return result, None


def smart_for_device(dev):
    commands = [
        f"sudo -n smartctl -H /dev/{dev}",
        f"smartctl -H /dev/{dev}",
    ]

    last_output = ""

    for cmd in commands:
        proc = run(cmd)
        output = (proc.stdout + proc.stderr).strip()
        last_output = output

        lower = output.lower()

        # NVMe: only a non-zero critical warning is truly bad.
        if "critical warning" in lower:
            match = re.search(r"critical warning:\s*0x([0-9a-f]+)", lower)
            if match:
                if match.group(1) != "00":
                    return "NOK", f"{dev}: NVMe critical warning"
                return "OK", f"{dev}: NVMe critical warning 0x00"

        # SATA/SAS: only explicit health FAILED is truly bad.
        if re.search(r"overall-health.*result:\s*failed", lower):
            return "NOK", f"{dev}: SMART health failed"

        if re.search(r"smart health status:\s*failed", lower):
            return "NOK", f"{dev}: SMART health failed"

        if re.search(r"smart overall-health.*failed", lower):
            return "NOK", f"{dev}: SMART health failed"

        # Clear good states.
        if re.search(r"overall-health.*result:\s*passed", lower):
            return "OK", f"{dev}: SMART passed"

        if re.search(r"smart health status:\s*ok", lower):
            return "OK", f"{dev}: SMART passed"

        if "passed" in lower and "failed" not in lower:
            return "OK", f"{dev}: SMART passed"

        # Query/permission/transport problems are INFO, not NOK.
        if (
            "read smart data failed" in lower
            or "permission denied" in lower
            or "a password is required" in lower
            or "requires option" in lower
            or "unknown usb bridge" in lower
            or "smart support is: unavailable" in lower
            or "unable to detect device type" in lower
            or "scsi error" in lower
            or "unsupported" in lower
        ):
            continue

    if last_output:
        return "INFO", f"{dev}: SMART unavailable"

    return "INFO", f"{dev}: SMART unavailable"


pool_devices, error = pool_devices_from_zpool()

if error:
    print(json.dumps({"error": error, "pools": {}}))
    raise SystemExit(0)

pool_results = {}

for pool, devices in pool_devices.items():
    device_results = []

    for dev in sorted(devices):
        state, note = smart_for_device(dev)
        device_results.append({
            "device": dev,
            "state": state,
            "note": note,
        })

    states = [x["state"] for x in device_results]

    if "NOK" in states:
        state = "NOK"
        css = "bad"
    elif "INFO" in states:
        state = "INFO"
        css = "info"
    else:
        state = "OK"
        css = "ok"

    pool_results[pool] = {
        "state": state,
        "css": css,
        "devices": device_results,
    }

print(json.dumps({"error": None, "pools": pool_results}))
REMOTE_PY"""

    ok, output = run_ssh(ip, remote_script, timeout=90)

    if not ok:
        return {}, output

    try:
        payload = json.loads(output.strip().splitlines()[-1])
    except Exception as e:
        return {}, f"SMART JSON parse error: {e}\n{output}"

    return payload.get("pools", {}), payload.get("error")


def smart_status(pool_smart):
    if not pool_smart:
        return "INFO", "info", "SMART unavailable"

    state = pool_smart.get("state", "INFO")
    css = pool_smart.get("css", "info")
    devices = pool_smart.get("devices", [])

    if state == "OK":
        return "OK", "ok", "SMART passed"

    if state == "NOK":
        bad_notes = [x.get("note", "") for x in devices if x.get("state") == "NOK"]
        return "NOK", "bad", bad_notes[0] if bad_notes else "SMART problem"

    info_notes = [x.get("note", "") for x in devices if x.get("state") == "INFO"]
    return "INFO", "info", info_notes[0] if info_notes else "SMART info"

def parse_host_status(output):
    data = {
        "hostname": "-",
        "os": "-",
        "kernel": "-",
        "cpu_model": "-",
        "cpu_cores": "-",
        "memory_total": "-",
        "uptime": "-",
        "load": "-",
        "apps_running": "-",
        "apps_total": "-",
        "containers_running": "-",
        "containers_total": "-",
    }

    key_map = {
        "HOSTNAME": "hostname",
        "OS": "os",
        "KERNEL": "kernel",
        "CPU_MODEL": "cpu_model",
        "CPU_CORES": "cpu_cores",
        "MEMORY_TOTAL": "memory_total",
        "UPTIME": "uptime",
        "LOAD": "load",
        "APPS_RUNNING": "apps_running",
        "APPS_TOTAL": "apps_total",
        "DOCKER_RUNNING": "containers_running",
        "DOCKER_TOTAL": "containers_total",
    }

    for line in output.splitlines():
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        if key in key_map:
            data[key_map[key]] = value

    return data


generated = datetime.now()
generated_epoch = int(generated.timestamp())

nok_issues = []
warning_issues = []
info_issues = []
collection_errors = []

snapshot_tasks, snapshot_task_error = remote_json(T620_IP, "midclt call pool.snapshottask.query")
t330_snapshot_tasks, t330_snapshot_task_error = remote_json(T330_IP, "midclt call pool.snapshottask.query")
replications, replication_error = remote_json(T620_IP, "midclt call replication.query")

if snapshot_tasks is None:
    snapshot_tasks = []
    collection_errors.append(("T620 snapshot task query", snapshot_task_error))

if t330_snapshot_tasks is None:
    t330_snapshot_tasks = []
    collection_errors.append(("T330 snapshot task query", t330_snapshot_task_error))

if replications is None:
    replications = []
    collection_errors.append(("Replication query", replication_error))

task_by_dataset = {task.get("dataset"): task for task in snapshot_tasks}

t620_snapshots, t620_snapshot_error = collect_snapshots(T620_IP)
t330_snapshots, t330_snapshot_error = collect_snapshots(T330_IP)

if t620_snapshot_error:
    collection_errors.append(("T620 snapshot collection", t620_snapshot_error))
if t330_snapshot_error:
    collection_errors.append(("T330 snapshot collection", t330_snapshot_error))

host_rows = ""
host_statuses = {}

for host_name, host_info in HOST_STATUS_HOSTS.items():
    ip = host_info["ip"]
    url = host_info["url"]
    check = host_info.get("check", "ssh")

    if check == "http":
        try:
            result = subprocess.run(
                ["curl", "-k", "-fsS", "-I", "--connect-timeout", "5", url],
                capture_output=True,
                text=True,
                timeout=10,
            )
            ok = result.returncode == 0
            output = (result.stdout + result.stderr).strip()
        except Exception as e:
            ok = False
            output = str(e)

        css = "ok" if ok else "bad"

        if not ok:
            nok_issues.append(f"{host_name} Web UI unreachable")
            status = {
                "uptime": output,
                "load": "-",
            }
        else:
            status = {
                "uptime": "Web UI OK",
                "load": "-",
            }

    else:
        host_command = r"""python3 - <<'REMOTE_PY'
import json
import os
import subprocess


def read_os_pretty_name():
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return "-"


def read_cpu_model():
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return "-"


def read_memory_total():
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    gib = round(kb / 1024 / 1024)
                    return f"{gib}Gi"
    except Exception:
        pass
    return "-"


def safe_output(cmd, default="-"):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip() or default
    except Exception:
        return default


print(f"HOSTNAME={safe_output(['hostname'])}")
print(f"OS={read_os_pretty_name()}")
print(f"KERNEL={safe_output(['uname', '-r'])}")
print(f"CPU_MODEL={read_cpu_model()}")
print(f"CPU_CORES={os.cpu_count() or '-'}")
print(f"MEMORY_TOTAL={read_memory_total()}")
print(f"UPTIME={safe_output(['uptime', '-p'])}")

try:
    load = ", ".join(f"{x:.2f}" for x in os.getloadavg())
except Exception:
    load = "-"
print(f"LOAD={load}")

try:
    raw = subprocess.check_output(["midclt", "call", "app.query"], text=True, stderr=subprocess.STDOUT)
    apps = json.loads(raw)
    total = len(apps)
    running = len([app for app in apps if app.get("state") == "RUNNING"])
    print(f"APPS_RUNNING={running}")
    print(f"APPS_TOTAL={total}")
except Exception:
    print("APPS_RUNNING=-")
    print("APPS_TOTAL=-")
REMOTE_PY"""
        ok, output = run_ssh(ip, host_command)

        css = "ok" if ok else "bad"

        if not ok:
            nok_issues.append(f"{host_name} unreachable")
            status = {
                "uptime": output,
                "load": "-",
            }
        else:
            status = parse_host_status(output)

    host_statuses[host_name] = {
        "name": host_name,
        "ip": ip,
        "url": url,
        "reachable": ok,
        **status,
    }

    host_rows += f"""
<tr class="{css}">
  <td><a class="host-link" href="{h(url)}" target="_blank" rel="noopener noreferrer">{h(host_name)}</a></td>
  <td>{h(ip)}</td>
  <td>{badge("YES" if ok else "NO", css)}</td>
  <td><span class="mono">{h(status.get("uptime", "-"))}</span></td>
  <td><span class="mono">{h(status.get("load", "-"))}</span></td>
</tr>
"""

def local_output(cmd, default="-"):
    try:
        if isinstance(cmd, str):
            return subprocess.check_output(cmd, shell=True, text=True, stderr=subprocess.DEVNULL).strip() or default

        return subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip() or default
    except Exception:
        return default


def local_os_pretty_name():
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
    except Exception:
        pass
    return "-"


def local_cpu_model():
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if line.lower().startswith("model name"):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return "-"


def local_memory_total():
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    gib = round(kb / 1024 / 1024)
                    return f"{gib}Gi"
    except Exception:
        pass
    return "-"


try:
    local_load = ", ".join(f"{x:.2f}" for x in __import__("os").getloadavg())
except Exception:
    local_load = "-"

host_statuses["Utility Node"] = {
    "name": "Utility Node",
    "ip": "192.168.30.11",
    "url": "http://192.168.30.11",
    "reachable": True,
    "hostname": local_output(["hostname"]),
    "os": local_os_pretty_name(),
    "kernel": local_output(["uname", "-r"]),
    "cpu_model": local_cpu_model(),
    "cpu_cores": str(__import__("os").cpu_count() or "-"),
    "memory_total": local_memory_total(),
    "uptime": local_output(["uptime", "-p"]),
    "load": local_load,
    "apps_running": "-",
    "apps_total": "-",
    "containers_running": local_output("docker ps -q | wc -l"),
    "containers_total": local_output("docker ps -aq | wc -l"),
}


system_info_order = ["T330 TrueNAS", "T620 TrueNAS", "Utility Node"]
system_info_html = ""

for system_name in system_info_order:
    status = host_statuses.get(system_name)

    if not status:
        continue

    system_info_html += system_info_card(system_name, status)

pool_rows = ""
pool_rows_by_host = {host_name: "" for host_name in HOSTS}
storage_pool_total = 0
storage_pool_status_counts = {
    "OK": 0,
    "INFO": 0,
    "WARNING": 0,
    "BAD": 0,
}

for host_name, host_info in HOSTS.items():
    ip = host_info["ip"]

    pools, pool_error = collect_pools(ip)
    pool_temps, temp_error = collect_pool_temperatures(ip)
    pool_smart, smart_error = collect_pool_smart(ip)

    if pool_error:
        nok_issues.append(f"{host_name} pool query failed")
        collection_errors.append((f"{host_name} pool query", pool_error))
        pool_rows += f"""
<tr class="bad">
  <td>{h(host_name)}</td>
  <td colspan="8"><pre>{h(pool_error)}</pre></td>
</tr>
"""
        pool_rows_by_host[host_name] += f"""
<tr class="bad">
  <td colspan="8"><pre>{h(pool_error)}</pre></td>
</tr>
"""
        continue

    if temp_error:
        info_issues.append(f"{host_name} disk temperature unavailable")
        collection_errors.append((f"{host_name} temperature query", temp_error))

    if smart_error:
        info_issues.append(f"{host_name} SMART unavailable")
        collection_errors.append((f"{host_name} SMART query", smart_error))

    for pool in pools:
        pool_name = pool["pool"]
        health = pool["health"]

        temp_label, temp_css, temp_issue = temperature_status(pool_name, pool_temps.get(pool_name))
        smart_label, smart_css, smart_note = smart_status(pool_smart.get(pool_name))

        if temp_issue:
            if temp_css == "warning":
                warning_issues.append(f"{host_name} {temp_issue}")
            elif temp_css == "info":
                info_issues.append(f"{host_name} {temp_issue}")

        if smart_css == "bad":
            nok_issues.append(f"{host_name} pool {pool_name}: {smart_note}")
        elif smart_css == "info":
            info_issues.append(f"{host_name} pool {pool_name}: {smart_note}")

        if health != "ONLINE":
            row_css = "bad"
            nok_issues.append(f"{host_name} pool {pool_name} is {health}")
        elif smart_css == "bad":
            row_css = "bad"
        elif temp_css == "warning":
            row_css = "warning"
        elif temp_css == "info" or smart_css == "info":
            row_css = "info"
        else:
            row_css = "ok"

        storage_pool_total += 1

        if row_css == "bad":
            storage_pool_status_counts["BAD"] += 1
        elif row_css == "warning":
            storage_pool_status_counts["WARNING"] += 1
        elif row_css == "info":
            storage_pool_status_counts["INFO"] += 1
        else:
            storage_pool_status_counts["OK"] += 1

        pool_rows += f"""
<tr class="{row_css}">
  <td>{h(host_name)}</td>
  <td>{h(pool_name)}</td>
  <td>{h(pool["size"])}</td>
  <td>{h(pool["used"])}</td>
  <td>{h(pool["free"])}</td>
  <td>{h(pool["cap"])}</td>
  <td>{temp_badge(temp_label, temp_css)}</td>
  <td>{badge(smart_label, smart_css)}</td>
  <td>{badge(health, "ok" if health == "ONLINE" else "bad")}</td>
</tr>
"""
        pool_rows_by_host[host_name] += f"""
<tr class="{row_css}">
  <td>{h(pool_name)}</td>
  <td>{h(pool["size"])}</td>
  <td>{h(pool["cap"])}</td>
  <td>{temp_badge(temp_label, temp_css)}</td>
  <td>{badge(smart_label, smart_css)}</td>
  <td>{badge(health, "ok" if health == "ONLINE" else "bad")}</td>
</tr>
"""



t330_reps = []

for rep in replications:
    target = rep.get("target_dataset") or ""
    sources = rep.get("source_datasets") or []

    if target.startswith("backup/t620/zfs-replication/") and sources:
        t330_reps.append(rep)

comparison_rows = ""
snapshot_summary_details = []
t330_snapshot_summary_details = []
replication_summary_details = []

snapshot_status_counts = {
    "OK": 0,
    "INFO": 0,
    "WARNING": 0,
    "BAD": 0,
}

t330_snapshot_status_counts = {
    "OK": 0,
    "INFO": 0,
    "WARNING": 0,
    "BAD": 0,
}

for rep in sorted(t330_reps, key=lambda x: x.get("id", 0)):
    source_dataset = rep.get("source_datasets")[0]
    target_dataset = rep.get("target_dataset")
    task = task_by_dataset.get(source_dataset)

    source_snap, source_dt = latest_snapshot(t620_snapshots, source_dataset)
    target_snap, target_dt = latest_snapshot(t330_snapshots, target_dataset)

    source_short = short_snapshot(source_snap)
    target_short = short_snapshot(target_snap)

    if source_short != "-" and source_short == target_short:
        sync_label = "OK"
        sync_css = "ok"
    elif source_short == "-" or target_short == "-":
        sync_label = "MISSING"
        sync_css = "bad"
        nok_issues.append(f"{source_dataset} snapshot missing on source or target")
    else:
        sync_label = "DIFFERENT"
        sync_css = "warning"
        warning_issues.append(f"{source_dataset} latest source/target snapshot differs")

    fresh_label, fresh_css, fresh_note = freshness_status(task, source_dt)

    if fresh_css == "ok":
        snapshot_status_counts["OK"] += 1
    elif fresh_css == "info":
        snapshot_status_counts["INFO"] += 1
        info_issues.append(f"{source_dataset}: {fresh_note}")
    elif fresh_css == "warning":
        snapshot_status_counts["WARNING"] += 1
        warning_issues.append(f"{source_dataset}: {fresh_note}")
    else:
        snapshot_status_counts["BAD"] += 1
        nok_issues.append(f"{source_dataset}: {fresh_note}")

    snapshot_summary_details.append((source_dataset, fresh_label, fresh_css))

    rep_state = replication_state(rep)
    rep_css = "ok" if rep_state == "FINISHED" else "info" if rep_state in ("PENDING", "RUNNING") else "bad"

    if rep_css == "bad":
        nok_issues.append(f"{rep.get('name', source_dataset)} replication state {rep_state}")
    elif rep_css == "info":
        info_issues.append(f"{rep.get('name', source_dataset)} replication state {rep_state}")

    replication_summary_details.append((source_dataset, rep_state, rep_css))

    if sync_css == "bad" or rep_css == "bad":
        row_css = "bad"
    elif sync_css == "warning" or fresh_css == "warning":
        row_css = "warning"
    elif fresh_css == "info" or rep_css == "info":
        row_css = "info"
    else:
        row_css = "ok"

    comparison_rows += f"""
<tr class="{row_css}">
  <td>{h(source_dataset)}</td>
  <td>{fmt_dt(source_dt)}</td>
  <td>{fmt_dt(target_dt)}</td>
  <td>{badge(sync_label, sync_css)}</td>
  <td>{badge(fresh_label, fresh_css)}</td>
  <td>{badge(rep_state, rep_css)}</td>
</tr>
"""

systems_layout_html = ""

for system_name in system_info_order:
    status = host_statuses.get(system_name)

    if not status:
        continue

    pool_rows_for_system = pool_rows_by_host.get(system_name, "")

    if system_name == "T620 TrueNAS":
        replication_rows_for_system = comparison_rows
        replication_title = "T620 → T330 Snapshot / Replication"
        replication_empty = "No replications configured."
    else:
        replication_rows_for_system = ""
        replication_title = "Snapshot / Replication"
        replication_empty = "No replications configured."

    if system_name == "Utility Node":
        pool_rows_for_system = ""

    systems_layout_html += f"""
  <div class="system-row three-column">
    {system_info_card(system_name, status)}
    {pool_status_card(system_name, pool_rows_for_system)}
    {replication_status_card(replication_rows_for_system, replication_title, replication_empty)}
  </div>
"""



configured_host_web_statuses = collect_configured_host_web_statuses(CONFIG_HOSTS)
configured_hosts_preview_html = build_configured_hosts_preview(CONFIG_HOSTS, configured_host_web_statuses)


enabled_snapshot_tasks = len([t for t in snapshot_tasks if t.get("enabled")])

snapshot_detail_html = ""

for dataset, label, css in snapshot_summary_details:
    snapshot_detail_html += f"""
      <span><strong>{h(dataset)}</strong> <span class="{status_text_class(label)}">{h(label)}</span></span>
"""

enabled_t330_snapshot_tasks = len([t for t in t330_snapshot_tasks if t.get("enabled")])

for task in sorted(t330_snapshot_tasks, key=lambda x: x.get("dataset") or ""):
    dataset = task.get("dataset")
    latest_snap, latest_dt = latest_snapshot(t330_snapshots, dataset)
    fresh_label, fresh_css, fresh_note = freshness_status(task, latest_dt)

    if fresh_css == "ok":
        t330_snapshot_status_counts["OK"] += 1
    elif fresh_css == "info":
        t330_snapshot_status_counts["INFO"] += 1
        info_issues.append(f"{dataset}: {fresh_note}")
    elif fresh_css == "warning":
        t330_snapshot_status_counts["WARNING"] += 1
        warning_issues.append(f"{dataset}: {fresh_note}")
    else:
        t330_snapshot_status_counts["BAD"] += 1
        nok_issues.append(f"{dataset}: {fresh_note}")

    t330_snapshot_summary_details.append((dataset, fresh_label, fresh_css))

t330_snapshot_detail_html = ""

for dataset, label, css in t330_snapshot_summary_details:
    t330_snapshot_detail_html += f"""
      <span><strong>{h(dataset)}</strong> <span class="{status_text_class(label)}">{h(label)}</span></span>
"""

finished_replications = len([x for x in replication_summary_details if x[1] == "FINISHED"])
replication_detail_html = ""

for dataset, label, css in replication_summary_details:
    replication_detail_html += f"""
      <span><strong>{h(dataset)}</strong> <span class="{status_text_class(label)}">{h(label)}</span></span>
"""


beckhoff_service_statuses, beckhoff_service_errors = collect_local_docker_services(BECKHOFF_SERVICES)

for error in beckhoff_service_errors:
    collection_errors.append(("Utility Node service query", error))

t620_service_statuses, t620_service_error = collect_truenas_app_services(T620_IP, T620_SERVICES)

if t620_service_error:
    collection_errors.append(("T620 app query", t620_service_error))

for service in BECKHOFF_SERVICES:
    status = beckhoff_service_statuses.get(service["id"], {"label": "UNKNOWN", "css": "info"})
    label = status["label"]
    css = status["css"]

    if css == "bad":
        nok_issues.append(f"Utility Node service {service['display']} is {label}")
    elif css == "info":
        info_issues.append(f"Utility Node service {service['display']} is {label}")

for service in T620_SERVICES:
    status = t620_service_statuses.get(service["id"], {"label": "UNKNOWN", "css": "info"})
    label = status["label"]
    css = status["css"]

    if css == "bad":
        nok_issues.append(f"T620 service {service['display']} is {label}")
    elif css == "info":
        info_issues.append(f"T620 service {service['display']} is {label}")

beckhoff_service_summary = build_service_summary(BECKHOFF_SERVICES, beckhoff_service_statuses)
t620_service_summary = build_service_summary(T620_SERVICES, t620_service_statuses)

config_http_services = normalize_config_http_services(CONFIG_ENABLED_SERVICES)
config_http_statuses = collect_http_services(config_http_services)

for service in config_http_services:
    status = config_http_statuses.get(service["id"], {"label": "UNKNOWN", "css": "info"})
    label = status["label"]

    if status.get("css") == "bad":
        nok_issues.append(f"Configured service {service['display']} is {label}")
    elif label != "UP":
        info_issues.append(f"Configured service {service['display']} is {label}")

if config_http_services:
    print(f"Configured HTTP services checked: {len(config_http_services)}")

if nok_issues:
    overall_label = "NOK"
    overall_css = "bad"
    overall_note = nok_issues[0]
elif warning_issues:
    overall_label = "WARNING"
    overall_css = "warning"
    overall_note = warning_issues[0]
elif info_issues:
    overall_label = "INFO"
    overall_css = "info"
    overall_note = info_issues[0]
else:
    overall_label = "OK"
    overall_css = "ok"
    overall_note = "Data fresh"

errors_section = ""

if collection_errors:
    error_rows = ""

    for name, error in collection_errors:
        error_rows += f"""
<tr class="bad">
  <td>{h(name)}</td>
  <td><pre>{h(error)}</pre></td>
</tr>
"""

    errors_section = f"""
<section>
  <h2>Collector Errors</h2>
  <table>
    <tr>
      <th>Check</th>
      <th>Result</th>
    </tr>
    {error_rows}
  </table>
</section>
"""

public_summary_services = normalize_config_services_for_summary(CONFIG_ENABLED_SERVICES)
public_summary_preview_html = build_public_host_summary_preview(
    CONFIG_HOSTS,
    public_summary_services,
    config_http_statuses,
    configured_host_web_statuses,
)

page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>{h(DASHBOARD_TITLE)}</title>
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="48x48" href="/favicon-48x48.png">
<link rel="icon" type="image/png" sizes="96x96" href="/favicon-96x96.png">
<link rel="icon" type="image/png" sizes="128x128" href="/favicon-128x128.png">
<link rel="icon" type="image/png" sizes="256x256" href="/favicon-256x256.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<meta name="theme-color" content="#00c98b">
<meta name="msapplication-TileColor" content="#000000">
<meta name="msapplication-TileImage" content="/mstile-150x150.png">
<meta name="msapplication-config" content="/browserconfig.xml">
<meta http-equiv="refresh" content="300">
<style>
:root {{
  --bg: #f3f5f7;
  --panel: #ffffff;
  --header: #0f172a;
  --table-header: #f4f6f8;
  --text: #111111;
  --muted: #64748b;
  --ok-row: #ffffff;
  --info-row: #ffffff;
  --warning-row: #ffffff;
  --bad-row: #ffffff;
  --ok-badge: #34c759;
  --info-badge: #0a84ff;
  --warning-badge: #ffb020;
  --bad-badge: #ff453a;
  --border: #d9e1ea;
}}

* {{
  box-sizing: border-box;
}}

body {{
  font-family: Arial, Helvetica, sans-serif;
  background: var(--bg);
  color: var(--text);
  margin: 0;
  padding: 12px;
  font-size: 12px;
}}

header {{
  background: #ffffff;
  color: #111827;
  padding: 14px 16px;
  border-radius: 12px;
  margin-bottom: 14px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 18px;
  border: 1px solid var(--border);
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}}

.header-left {{
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}}

.header-logo {{
  width: 44px;
  height: 44px;
  border-radius: 12px;
  flex: 0 0 auto;
  box-shadow: 0 1px 4px rgba(0,0,0,0.10);
}}

.header-title {{
  min-width: 0;
}}

.header-left h1 {{
  margin: 0;
  font-size: 22px;
  line-height: 1.15;
}}

.subtitle {{
  margin-top: 3px;
  font-size: 12px;
  color: #475569;
}}

.header-meta {{
  display: grid;
  grid-template-columns: auto auto;
  gap: 4px 10px;
  align-items: center;
  text-align: right;
  font-size: 12px;
  color: #111827;
  white-space: nowrap;
}}

.header-meta .label {{
  color: #64748b;
  font-weight: 700;
}}

section {{
  margin-bottom: 14px;
}}

h2 {{
  font-size: 15px;
  margin: 0 0 6px 0;
  line-height: 1.2;
}}

table {{
  width: 100%;
  border-collapse: collapse;
  background: var(--panel);
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}}

th, td {{
  padding: 6px 8px;
  border-bottom: 1px solid var(--border);
  text-align: left;
  vertical-align: top;
  line-height: 1.25;
}}

th {{
  background: var(--table-header);
  color: #475569;
  font-size: 13px;
  font-weight: 800;
}}

td {{
  font-size: 12px;
}}

tr.ok td {{ background: var(--ok-row); }}
tr.info td {{ background: var(--info-row); }}
tr.warning td {{ background: var(--warning-row); }}
tr.bad td {{ background: var(--bad-row); }}
tr.disabled td {{
  background: #eeeeee;
  color: #777;
}}

.badge, .temp-badge {{
  display: inline-block;
  padding: 2px 7px;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.02em;
  white-space: nowrap;
}}

.badge.ok, .temp-badge.ok {{ background: var(--ok-badge); color: #ffffff; }}
.badge.info, .temp-badge.info {{ background: var(--info-badge); color: #ffffff; }}
.badge.warning, .temp-badge.warning {{ background: var(--warning-badge); color: #1f2937; }}
.badge.bad, .temp-badge.bad {{ background: var(--bad-badge); color: #ffffff; }}
.badge.disabled, .temp-badge.disabled {{ background: #ccc; }}

pre, .mono {{
  margin: 0;
  white-space: pre-wrap;
  font-family: "Courier New", Courier, monospace;
  font-size: 12px;
  line-height: 1.25;
}}

.small {{
  font-size: 11px;
  color: var(--muted);
  word-break: break-all;
}}

.host-link {{
  color: inherit;
  font-weight: 700;
  text-decoration: none;
  border-bottom: 1px dotted rgba(0,0,0,0.35);
}}

.host-link:hover {{
  text-decoration: underline;
}}

.overall-status {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  background: var(--panel);
  border-left: 6px solid #34c759;
  border-radius: 8px;
  padding: 9px 12px;
  margin-bottom: 10px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  font-size: 12px;
}}

.overall-status strong {{
  font-size: 15px;
}}

.overall-status .meta {{
  display: flex;
  gap: 12px;
  color: var(--muted);
  white-space: nowrap;
}}

.overall-status.ok {{
  border-left-color: #34c759;
  background: var(--panel);
}}

.overall-status.info {{
  border-left-color: #0a84ff;
  background: var(--panel);
}}

.overall-status.warning {{
  border-left-color: #ffb020;
  background: var(--panel);
}}

.overall-status.bad,
.overall-status.stale {{
  border-left-color: #ff453a;
  background: var(--panel);
}}


.public-summary-preview {{
  background: #ffffff;
  border: 1px dashed #cbd5e1;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.04);
  margin: -2px 0 16px;
  padding: 14px;
}}

.public-summary-preview-header {{
  align-items: flex-start;
  display: flex;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 10px;
}}

.public-summary-kicker {{
  color: var(--muted);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}

.public-summary-preview h2 {{
  font-size: 17px;
  line-height: 1.2;
  margin: 2px 0 0;
}}

.public-summary-note {{
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
  padding: 5px 9px;
  white-space: nowrap;
}}

.public-summary-row {{
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}}

.public-summary-row .summary-card {{
  box-shadow: none;
}}

@media (max-width: 1200px) {{
  .public-summary-row {{
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }}
}}

@media (max-width: 900px) {{
  .public-summary-preview-header {{
    flex-direction: column;
  }}

  .public-summary-row {{
    grid-template-columns: 1fr;
  }}
}}

.summary-row {{
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}}

.summary-card {{
  background: var(--panel);
  border-radius: 8px;
  padding: 10px 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  border-left: 6px solid #9ad29a;
}}

.summary-card.info {{ border-left-color: #9cc9ff; }}
.summary-card.warning {{ border-left-color: #e2b24b; }}
.summary-card.bad {{ border-left-color: #ff9c9c; }}

.system-info-row {{
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}}

.system-card {{
  background: var(--panel);
  border-radius: 10px;
  padding: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  border: 1px solid var(--border);
  border-left: 6px solid #9ad29a;
}}

.system-card.bad {{
  border-left-color: #ff9c9c;
}}

.system-card-header {{
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 10px;
}}

.system-card-kicker {{
  color: var(--muted);
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  margin-bottom: 2px;
}}

.system-card h3 {{
  margin: 0;
  font-size: 16px;
  line-height: 1.2;
}}

.system-info-grid {{
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px 14px;
}}

.info-item {{
  min-width: 0;
  padding-top: 6px;
  border-top: 1px solid #eeeeee;
}}

.info-item.wide {{
  grid-column: 1 / -1;
}}

.info-label {{
  color: var(--muted);
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  margin-bottom: 2px;
}}

.info-value {{
  font-size: 12px;
  font-weight: 700;
  line-height: 1.25;
  word-break: break-word;
}}

@media (max-width: 1200px) {{
  .system-info-row {{
    grid-template-columns: 1fr;
  }}
}}

.systems-list {{
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 14px;
}}

.system-row {{
  display: grid;
  grid-template-columns: minmax(320px, 0.9fr) minmax(520px, 1.6fr);
  gap: 12px;
  align-items: stretch;
}}

.system-row.utility-only {{
  grid-template-columns: minmax(320px, 0.9fr) minmax(520px, 1.6fr);
}}

.pool-card {{
  background: var(--panel);
  border-radius: 10px;
  padding: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  border: 1px solid var(--border);
}}

.pool-card-header {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}}

.pool-card-kicker {{
  color: var(--muted);
  font-size: 10px;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}}

.pool-card h3 {{
  margin: 0;
  font-size: 16px;
  line-height: 1.2;
}}

.pool-card table {{
  margin-top: 6px;
  box-shadow: none;
  border: 1px solid var(--border);
}}

.pool-card th {{
  font-size: 10px;
  padding: 5px 6px;
}}

.pool-card td {{
  font-size: 10px;
  padding: 5px 6px;
}}

.pool-placeholder {{
  color: var(--muted);
  font-size: 12px;
  line-height: 1.4;
  padding: 12px;
  border: 1px dashed var(--border);
  border-radius: 8px;
  background: #fafafa;
}}

.system-row.three-column {{
  grid-template-columns: minmax(300px, 0.75fr) minmax(440px, 1fr) minmax(520px, 1.25fr);
}}

.replication-card {{
  background: var(--panel);
  border-radius: 10px;
  padding: 12px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  border: 1px solid var(--border);
}}

.replication-card table {{
  margin-top: 6px;
  box-shadow: none;
  border: 1px solid var(--border);
}}

.replication-card th {{
  font-size: 9px;
  padding: 5px 5px;
}}

.replication-card td {{
  font-size: 10px;
  padding: 5px 5px;
}}

.replication-card .badge {{
  font-size: 9px;
  padding: 2px 7px;
}}

/* Cleaner white-dominant table styling */
.pool-card th,
.replication-card th {{
  background: #f4f6f8 !important;
  color: #4b5563 !important;
  border-bottom: 1px solid #d9e1ea !important;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}}

.pool-card tr.ok,
.pool-card tr.info,
.pool-card tr.warning,
.pool-card tr.bad,
.replication-card tr.ok,
.replication-card tr.info,
.replication-card tr.warning,
.replication-card tr.bad {{
  background: #ffffff !important;
}}

.pool-card tr.ok td,
.pool-card tr.info td,
.pool-card tr.warning td,
.pool-card tr.bad td,
.replication-card tr.ok td,
.replication-card tr.info td,
.replication-card tr.warning td,
.replication-card tr.bad td {{
  background: #ffffff !important;
}}

.pool-card tr:nth-child(even) td,
.replication-card tr:nth-child(even) td {{
  background: #fbfcfe !important;
}}

.pool-card td,
.replication-card td {{
  border-bottom: 1px solid #edf1f5;
}}

.pool-card tr:last-child td,
.replication-card tr:last-child td {{
  border-bottom: none;
}}

.badge.ok,
.temp-badge.ok {{
  background: #34c759 !important;
  color: #ffffff !important;
}}

.badge.info,
.temp-badge.info {{
  background: #0a84ff !important;
  color: #ffffff !important;
}}

.badge.warning,
.temp-badge.warning {{
  background: #ffb020 !important;
  color: #1f2937 !important;
}}

.badge.bad,
.temp-badge.bad {{
  background: #ff453a !important;
  color: #ffffff !important;
}}

/* Align table typography with System Information cards */
.pool-card,
.replication-card {{
  font-family: inherit;
}}

.pool-card th,
.replication-card th {{
  font-size: 10px !important;
  font-weight: 800 !important;
  line-height: 1.2 !important;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}}

.pool-card td,
.replication-card td {{
  font-size: 11px !important;
  font-weight: 700 !important;
  line-height: 1.25 !important;
  color: #111827;
}}

.pool-card .badge,
.pool-card .temp-badge,
.replication-card .badge,
.replication-card .temp-badge {{
  font-size: 10px !important;
  font-weight: 800 !important;
  line-height: 1.1 !important;
}}

.pool-card-kicker {{
  font-size: 10px !important;
  font-weight: 800 !important;
  letter-spacing: 0.04em;
}}

/* Refine table body weight after typography alignment */
.pool-card td,
.replication-card td {{
  font-weight: 600 !important;
}}

.pool-card td:first-child,
.replication-card td:first-child {{
  font-weight: 700 !important;
}}

.pool-card .badge,
.pool-card .temp-badge,
.replication-card .badge,
.replication-card .temp-badge {{
  font-weight: 800 !important;
}}

@media (max-width: 1200px) {{
  .system-row.three-column {{
    grid-template-columns: 1fr;
  }}
}}

@media (max-width: 1200px) {{
  .system-row,
  .system-row.utility-only {{
    grid-template-columns: 1fr;
  }}
}}

.summary-card .title {{
  color: var(--muted);
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  margin-bottom: 2px;
}}

.summary-card .value {{
  font-size: 16px;
  font-weight: 800;
}}

.summary-details {{
  display: grid;
  grid-template-columns: 1fr;
  gap: 3px 12px;
  margin-top: 6px;
  font-size: 11px;
  line-height: 1.25;
}}

.summary-details span {{
  white-space: nowrap;
}}

.summary-details.service-details {{
  grid-template-columns: 1fr;
}}

.summary-details.service-details.two-column {{
  grid-template-columns: repeat(2, minmax(0, 1fr));
}}

.service-line {{
  display: flex;
  justify-content: space-between;
  gap: 8px;
}}

.service-link {{
  color: inherit;
  text-decoration: none;
  border-bottom: 1px dotted rgba(0,0,0,0.35);
}}

.service-link:hover {{
  text-decoration: underline;
}}

@media (max-width: 1200px) {{
  .summary-row {{
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }}
}}


.ok-text {{
  color: #205d20;
  font-weight: 700;
}}

.info-text {{
  color: #245b8a;
  font-weight: 700;
}}

.warning-text {{
  color: #8a641c;
  font-weight: 700;
}}

.bad-text {{
  color: #8a1f1f;
  font-weight: 700;
}}

@media (max-width: 900px) {{
  header {{
    align-items: flex-start;
    flex-direction: column;
  }}

  .header-meta {{
    text-align: left;
  }}

  .summary-row {{
    grid-template-columns: 1fr;
  }}

  .overall-status {{
    align-items: flex-start;
    flex-direction: column;
  }}

  .overall-status .meta {{
    flex-direction: column;
    gap: 3px;
  }}
}}


.configured-hosts-preview {{
  background: #ffffff;
  border: 1px solid var(--border);
  border-left: 4px solid #9cc9ff;
  border-radius: 16px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.05);
  margin-top: 12px;
  padding: 14px;
}}

.configured-hosts-preview-header {{
  align-items: flex-start;
  display: flex;
  justify-content: space-between;
  gap: 14px;
  margin-bottom: 4px;
}}

.configured-hosts-kicker {{
  color: var(--muted);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}}

.configured-hosts-preview h3 {{
  font-size: 17px;
  line-height: 1.2;
  margin: 2px 0 0;
}}

.configured-hosts-meta {{
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 999px;
  color: var(--muted);
  font-size: 12px;
  font-weight: 800;
  padding: 5px 9px;
  white-space: nowrap;
}}

.muted-small {{
  color: var(--muted);
  font-size: 12px;
  margin: 6px 0 10px;
}}

.configured-hosts-preview table {{
  font-size: 12px;
  margin-top: 8px;
}}

.configured-hosts-preview th {{
  background: #f8fafc;
  color: #475569;
  font-size: 11px;
}}

.configured-hosts-preview td {{
  background: #ffffff;
}}

.configured-host-row.disabled td {{
  color: #64748b;
  opacity: 0.82;
}}

.configured-host-row.disabled .host-link {{
  color: #64748b;
}}

.dashboard-footer {{
  margin-top: 14px;
  padding: 10px 4px 2px;
  color: var(--muted);
  font-size: 11px;
  text-align: center;
}}

.dashboard-footer strong {{
  color: #475569;
  font-weight: 800;
}}

</style>
</head>
<body>
<header>
  <div class="header-left">
    <img class="header-logo" src="/favicon-96x96.png" alt="{h(DASHBOARD_TITLE)} logo">
    <div class="header-title">
      <h1>{h(DASHBOARD_TITLE)}</h1>
      <div class="subtitle">{h(DASHBOARD_SUBTITLE)}</div>
    </div>
  </div>
  <div class="header-meta">
    <div class="label">Generated:</div><div>{h(generated.strftime("%Y-%m-%d %H:%M:%S"))}</div>
    <div class="label">Collector:</div><div>{h(COLLECTOR_DISPLAY_NAME)}</div>
  </div>
</header>

<div id="overallStatus" class="overall-status {h(overall_css)}">
  <strong id="overallStatusText">Overall Status: {h(overall_label)}</strong>
  <div class="meta">
    <span>Last generated {h(generated.strftime("%Y-%m-%d %H:%M"))}</span>
    <span>Collector {h(COLLECTOR_DISPLAY_NAME)}</span>
    <span id="overallStatusNote">{h(overall_note)}</span>
  </div>
</div>

<div class="summary-row">
  <div class="summary-card {'info' if t330_snapshot_status_counts["INFO"] else 'warning' if t330_snapshot_status_counts["WARNING"] else 'bad' if t330_snapshot_status_counts["BAD"] else ''}">
    <div class="title">T330 Snapshot Tasks</div>
    <div class="value">{h(enabled_t330_snapshot_tasks)} Enabled · {t330_snapshot_status_counts["OK"]} OK · {t330_snapshot_status_counts["INFO"]} Info</div>
    <div class="summary-details">
      {t330_snapshot_detail_html}
    </div>
  </div>
  <div class="summary-card {'info' if snapshot_status_counts["INFO"] else 'warning' if snapshot_status_counts["WARNING"] else 'bad' if snapshot_status_counts["BAD"] else ''}">
    <div class="title">T620 Snapshot Tasks</div>
    <div class="value">{h(enabled_snapshot_tasks)} Enabled · {snapshot_status_counts["OK"]} OK · {snapshot_status_counts["INFO"]} Info</div>
    <div class="summary-details">
      {snapshot_detail_html}
    </div>
  </div>
  <div class="summary-card">
    <div class="title">T620 Replication</div>
    <div class="value">{h(len(t330_reps))} To T330 · {h(finished_replications)} Finished</div>
    <div class="summary-details">
      {replication_detail_html}
    </div>
  </div>
  <div class="summary-card {h(t620_service_summary["css"])}">
    <div class="title">T620 Services</div>
    <div class="value">{h(t620_service_summary["value"])}</div>
    <div class="summary-details service-details {h(t620_service_summary["details_class"])}">
      {t620_service_summary["details"]}
    </div>
  </div>
  <div class="summary-card {h(beckhoff_service_summary["css"])}">
    <div class="title">Utility Node Services</div>
    <div class="value">{h(beckhoff_service_summary["value"])}</div>
    <div class="summary-details service-details {h(beckhoff_service_summary["details_class"])}">
      {beckhoff_service_summary["details"]}
    </div>
  </div>
</div>

{public_summary_preview_html}

<section>
  <h2>1. Systems</h2>
  <div class="systems-list">
    {systems_layout_html}
  </div>
  {configured_hosts_preview_html}
</section>

{errors_section}

<footer class="dashboard-footer">
  Generated by <strong>{h(DASHBOARD_TITLE)}</strong> · Collector: <strong>{h(COLLECTOR_DISPLAY_NAME)}</strong> · Refresh: <strong>{h(REFRESH_MINUTES)} min</strong>
</footer>

<script>
const generatedEpoch = {generated_epoch};
const staleAfterSeconds = {STALE_AFTER_SECONDS};

function checkDashboardFreshness() {{
  const age = Math.floor(Date.now() / 1000) - generatedEpoch;

  if (age > staleAfterSeconds) {{
    const overall = document.getElementById("overallStatus");
    const text = document.getElementById("overallStatusText");
    const note = document.getElementById("overallStatusNote");

    overall.className = "overall-status stale";
    text.textContent = "Overall Status: NOK";
    note.textContent = "Dashboard data stale";
  }}
}}

checkDashboardFreshness();
setInterval(checkDashboardFreshness, 30000);
</script>

</body>
</html>
"""

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(page)
print(f"Wrote {OUT}")
