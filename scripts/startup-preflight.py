#!/usr/bin/env python3

import argparse
import os
import sys
import tempfile
from pathlib import Path

import yaml


DEFAULT_CONFIG = Path(
    os.environ.get("SANITY_NODE_CONFIG", "/app/config/config.yaml")
)
DEFAULT_OUTPUT = Path(
    os.environ.get("SANITY_NODE_OUTPUT", "/app/html/index.html")
)
DEFAULT_LOG = Path(
    os.environ.get("SANITY_NODE_LOG", "/app/logs/generator.log")
)


def is_enabled(value):
    return isinstance(value, dict) and value.get("enabled", True) is not False


def mapping(value):
    return value if isinstance(value, dict) else {}


def load_config(path):
    path = Path(path)

    if not path.exists():
        raise ValueError(f"configuration file does not exist: {path}")

    if not path.is_file():
        raise ValueError(f"configuration path is not a regular file: {path}")

    try:
        content = path.read_text()
    except OSError as exc:
        raise ValueError(
            f"configuration file is not readable: {path}: {exc}"
        ) from exc

    try:
        config = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ValueError(
            f"configuration file contains invalid YAML: {path}: {exc}"
        ) from exc

    if config is None:
        config = {}

    if not isinstance(config, dict):
        raise ValueError(
            "top-level configuration must be a YAML mapping"
        )

    return config


def enabled_hosts(config):
    hosts = {}

    for host in config.get("hosts", []):
        if not is_enabled(host):
            continue

        host_id = str(host.get("id") or "").strip()

        if host_id:
            hosts[host_id] = host

    return hosts


def collect_ssh_requirements(config):
    hosts = enabled_hosts(config)
    collector_id = str(
        mapping(config.get("collector")).get("id") or ""
    ).strip()

    requirements = {}

    def add(host_id, reason):
        if host_id not in hosts:
            return

        requirements.setdefault(host_id, set()).add(reason)

    for host_id, host in hosts.items():
        host_type = str(host.get("type") or "").strip().lower()
        modules = mapping(host.get("modules"))

        if (
            host_id not in {collector_id, "collector"}
            and host_type in {"linux", "truenas"}
            and modules.get("system_info") is True
        ):
            if host_type == "truenas":
                add(host_id, "TrueNAS system information")
            else:
                add(host_id, "remote Linux system information")

        if host_type == "truenas":
            if modules.get("snapshots") is True:
                add(host_id, "TrueNAS snapshot monitoring")

            if modules.get("replications") is True:
                add(host_id, "TrueNAS replication monitoring")

    for service in config.get("services", []):
        if not is_enabled(service):
            continue

        host_id = str(service.get("host") or "").strip()
        check = str(service.get("check") or "").strip().lower()
        host = hosts.get(host_id)

        if not host:
            continue

        host_type = str(host.get("type") or "").strip().lower()
        modules = mapping(host.get("modules"))

        if check == "truenas_app" and host_type == "truenas":
            add(host_id, "TrueNAS application monitoring")

        if (
            check == "docker"
            and host_type == "linux"
            and host_id != collector_id
            and modules.get("docker") is True
        ):
            add(host_id, "remote Linux Docker monitoring")

    for check in config.get("local_storage", []):
        if not is_enabled(check):
            continue

        host_id = str(check.get("host") or "").strip()
        host = hosts.get(host_id)

        if not host:
            continue

        host_type = str(host.get("type") or "").strip().lower()
        modules = mapping(host.get("modules"))

        if (
            host_type == "linux"
            and host_id != collector_id
            and modules.get("local_storage") is True
        ):
            add(host_id, "remote Linux storage monitoring")

    for check in config.get("backup_checks", []):
        if not is_enabled(check):
            continue

        host_id = str(check.get("host") or "").strip()
        host = hosts.get(host_id)

        if not host:
            continue

        host_type = str(host.get("type") or "").strip().lower()
        modules = mapping(host.get("modules"))

        if (
            host_type == "linux"
            and host_id != collector_id
            and modules.get("backup_status") is True
        ):
            add(host_id, "remote Linux backup monitoring")

    image_updates = mapping(config.get("image_updates"))

    if is_enabled(image_updates):
        for source in image_updates.get("sources", []):
            if not is_enabled(source):
                continue

            provider = str(
                source.get("provider") or ""
            ).strip().lower()

            if provider == "truenas":
                host_id = str(source.get("host") or "").strip()
                add(host_id, "TrueNAS application update monitoring")

    return {
        host_id: sorted(reasons)
        for host_id, reasons in requirements.items()
    }


def check_writable_target(path, label):
    path = Path(path)
    parent = path.parent
    errors = []

    if not parent.exists():
        return [f"{label} directory does not exist: {parent}"]

    if not parent.is_dir():
        return [f"{label} parent is not a directory: {parent}"]

    if path.exists():
        if not path.is_file():
            errors.append(
                f"{label} target is not a regular file: {path}"
            )
        elif not os.access(path, os.W_OK):
            errors.append(
                f"{label} target is not writable: {path}"
            )

    try:
        with tempfile.NamedTemporaryFile(
            dir=parent,
            prefix=".sanity-node-preflight-",
            delete=True,
        ):
            pass
    except OSError as exc:
        errors.append(
            f"{label} directory is not writable: {parent}: {exc}"
        )

    return errors


def check_ssh_credentials(config, requirements):
    hosts = enabled_hosts(config)
    errors = []

    for host_id, reasons in sorted(requirements.items()):
        host = hosts[host_id]
        display_name = str(
            host.get("display_name") or host_id
        ).strip()
        ssh_value = host.get("ssh")
        ssh = mapping(ssh_value)

        reason_text = ", ".join(reasons)

        if (
            not isinstance(ssh_value, dict)
            or not ssh
            or ssh.get("enabled", True) is False
        ):
            errors.append(
                f"host '{display_name}' requires SSH for {reason_text}, "
                "but its ssh section is missing or disabled"
            )
            continue

        user = str(ssh.get("user") or "").strip()
        key_value = str(ssh.get("key_file") or "").strip()

        if not user:
            errors.append(
                f"host '{display_name}' requires SSH for {reason_text}, "
                "but ssh.user is empty"
            )

        if not key_value:
            errors.append(
                f"host '{display_name}' requires SSH for {reason_text}, "
                "but ssh.key_file is empty"
            )
            continue

        key_path = Path(key_value).expanduser()

        if not key_path.exists():
            errors.append(
                f"SSH key for host '{display_name}' does not exist: "
                f"{key_path}"
            )
        elif not key_path.is_file():
            errors.append(
                f"SSH key for host '{display_name}' is not a regular file: "
                f"{key_path}"
            )
        elif not os.access(key_path, os.R_OK):
            errors.append(
                f"SSH key for host '{display_name}' is not readable: "
                f"{key_path}"
            )

    return errors


def run_preflight(config_path, output_path, log_path):
    errors = []
    config = None
    requirements = {}

    try:
        config = load_config(config_path)
    except ValueError as exc:
        errors.append(str(exc))

    errors.extend(
        check_writable_target(output_path, "dashboard output")
    )
    errors.extend(
        check_writable_target(log_path, "generator log")
    )

    if config is not None:
        requirements = collect_ssh_requirements(config)
        errors.extend(
            check_ssh_credentials(config, requirements)
        )

    return requirements, errors


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Check Sanity Node runtime paths and required SSH "
            "credentials before startup."
        )
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
        help="configuration file path",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="generated dashboard path",
    )
    parser.add_argument(
        "--log",
        default=str(DEFAULT_LOG),
        help="generator log path",
    )
    args = parser.parse_args()

    config_path = Path(args.config).expanduser()
    output_path = Path(args.output).expanduser()
    log_path = Path(args.log).expanduser()

    print("=== SANITY NODE STARTUP PREFLIGHT ===")
    print(f"Configuration:    {config_path}")
    print(f"Dashboard output: {output_path}")
    print(f"Generator log:    {log_path}")
    print()

    requirements, errors = run_preflight(
        config_path,
        output_path,
        log_path,
    )

    if requirements:
        print("SSH-backed hosts:")
        for host_id, reasons in sorted(requirements.items()):
            print(f"  {host_id}: {', '.join(reasons)}")
    else:
        print("SSH-backed hosts: none")

    print()

    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)

    if errors:
        print(
            f"Startup preflight failed with {len(errors)} error(s).",
            file=sys.stderr,
        )
        return 1

    print("Startup preflight passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
