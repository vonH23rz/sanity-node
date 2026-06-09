#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    import yaml
except ImportError as exc:
    print(f"ERROR: PyYAML is required: {exc}", file=sys.stderr)
    raise SystemExit(1)


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = REPO_ROOT / "examples" / "config.example.yaml"

SUPPORTED_HOST_TYPES = {"linux", "truenas"}
SUPPORTED_SERVICE_TYPES = {"app", "helper"}
SUPPORTED_SERVICE_CHECKS = {"http", "docker", "truenas_app"}
SUPPORTED_IMAGE_UPDATE_PROVIDERS = {"diun", "truenas"}
SUPPORTED_SUMMARY_CARDS = {"systems", "storage", "protection", "services"}
SUPPORTED_RUNTIME_MODES = {"reference", "public"}
SUPPORTED_TOP_LEVEL_KEYS = {
    "dashboard",
    "collector",
    "hosts",
    "services",
    "local_storage",
    "backup_checks",
    "protection",
    "image_updates",
    "summary_cards",
}

ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class Validator:
    def __init__(self) -> None:
        self.errors: list[tuple[str, str]] = []
        self.warnings: list[tuple[str, str]] = []

    def error(self, path: str, message: str) -> None:
        self.errors.append((path, message))

    def warning(self, path: str, message: str) -> None:
        self.warnings.append((path, message))

    def validate_enabled(self, item: dict, path: str) -> bool:
        value = item.get("enabled", True)

        if not isinstance(value, bool):
            self.error(f"{path}.enabled", "must be true or false")
            return True

        return value

    def validate_id(self, value: object, path: str, required: bool = True) -> str | None:
        if value is None:
            if required:
                self.error(path, "is required")
            return None

        if not isinstance(value, str) or not value.strip():
            self.error(path, "must be a non-empty string")
            return None

        value = value.strip()

        if not ID_PATTERN.fullmatch(value):
            self.error(
                path,
                "must use only letters, numbers, dots, underscores, and hyphens",
            )

        return value

    def validate_non_empty_string(
        self,
        value: object,
        path: str,
        required: bool = True,
    ) -> str | None:
        if value is None:
            if required:
                self.error(path, "is required")
            return None

        if not isinstance(value, str) or not value.strip():
            self.error(path, "must be a non-empty string")
            return None

        return value.strip()

    def validate_integer(
        self,
        value: object,
        path: str,
        minimum: int | None = None,
        maximum: int | None = None,
    ) -> int | None:
        if isinstance(value, bool) or not isinstance(value, int):
            self.error(path, "must be an integer")
            return None

        if minimum is not None and value < minimum:
            self.error(path, f"must be at least {minimum}")

        if maximum is not None and value > maximum:
            self.error(path, f"must be at most {maximum}")

        return value

    def validate_http_url(self, value: object, path: str, required: bool = False) -> None:
        if value is None:
            if required:
                self.error(path, "is required")
            return

        if not isinstance(value, str) or not value.strip():
            self.error(path, "must be a non-empty HTTP or HTTPS URL")
            return

        parsed = urlparse(value.strip())

        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            self.error(path, "must be a valid HTTP or HTTPS URL")

    def validate_mapping(self, value: object, path: str) -> dict | None:
        if not isinstance(value, dict):
            self.error(path, "must be a YAML mapping")
            return None

        return value

    def validate_list(self, value: object, path: str) -> list | None:
        if not isinstance(value, list):
            self.error(path, "must be a YAML list")
            return None

        return value


def safe_service_id(name: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return value or "service"


def validate_config(config: dict) -> Validator:
    validator = Validator()

    for key in config:
        if key not in SUPPORTED_TOP_LEVEL_KEYS:
            validator.warning(str(key), "unknown top-level configuration key")

    dashboard = validator.validate_mapping(config.get("dashboard"), "dashboard")

    if dashboard is not None:
        validator.validate_non_empty_string(
            dashboard.get("title"),
            "dashboard.title",
        )

        if "subtitle" in dashboard:
            validator.validate_non_empty_string(
                dashboard.get("subtitle"),
                "dashboard.subtitle",
            )

        if "runtime_mode" in dashboard:
            runtime_mode = validator.validate_non_empty_string(
                dashboard.get("runtime_mode"),
                "dashboard.runtime_mode",
            )

            if (
                runtime_mode is not None
                and runtime_mode.lower() not in SUPPORTED_RUNTIME_MODES
            ):
                validator.error(
                    "dashboard.runtime_mode",
                    "must be one of: public, reference",
                )

        validator.validate_integer(
            dashboard.get("refresh_minutes"),
            "dashboard.refresh_minutes",
            minimum=1,
        )

        validator.validate_integer(
            dashboard.get("port"),
            "dashboard.port",
            minimum=1,
            maximum=65535,
        )

    collector = validator.validate_mapping(config.get("collector"), "collector")
    collector_id: str | None = None

    if collector is not None:
        collector_id = validator.validate_id(
            collector.get("id"),
            "collector.id",
        )

        validator.validate_non_empty_string(
            collector.get("display_name"),
            "collector.display_name",
        )

        validator.validate_non_empty_string(
            collector.get("hostname"),
            "collector.hostname",
        )

        collector_type = validator.validate_non_empty_string(
            collector.get("type"),
            "collector.type",
        )

        if collector_type is not None and collector_type.lower() != "linux":
            validator.error(
                "collector.type",
                "must be linux for the Phase 2 collector runtime",
            )

    hosts_value = config.get("hosts")
    hosts = validator.validate_list(hosts_value, "hosts")
    host_ids: set[str] = set()
    enabled_host_ids: set[str] = set()
    host_types: dict[str, str] = {}

    if hosts is not None:
        if not hosts:
            validator.error("hosts", "must contain at least one host")

        for index, host_value in enumerate(hosts):
            path = f"hosts[{index}]"
            host = validator.validate_mapping(host_value, path)

            if host is None:
                continue

            enabled = validator.validate_enabled(host, path)
            host_id = validator.validate_id(host.get("id"), f"{path}.id")

            if host_id is not None:
                if host_id in host_ids:
                    validator.error(f"{path}.id", f"duplicate host id: {host_id}")
                else:
                    host_ids.add(host_id)

                if enabled:
                    enabled_host_ids.add(host_id)

            validator.validate_non_empty_string(
                host.get("display_name"),
                f"{path}.display_name",
            )

            validator.validate_non_empty_string(
                host.get("hostname"),
                f"{path}.hostname",
            )

            host_type = validator.validate_non_empty_string(
                host.get("type"),
                f"{path}.type",
            )

            if (
                host_type is not None
                and host_type.lower() not in SUPPORTED_HOST_TYPES
            ):
                validator.error(
                    f"{path}.type",
                    "must be linux or truenas",
                )
            elif host_id is not None and host_type is not None:
                host_types[host_id] = host_type.lower()

            if enabled and host_type and host_type.lower() == "truenas":
                validator.validate_non_empty_string(
                    host.get("address"),
                    f"{path}.address",
                )

            if "web_url" in host:
                validator.validate_http_url(
                    host.get("web_url"),
                    f"{path}.web_url",
                )

            ssh = host.get("ssh")

            if ssh is not None:
                ssh = validator.validate_mapping(ssh, f"{path}.ssh")

                if ssh is not None:
                    ssh_enabled = validator.validate_enabled(ssh, f"{path}.ssh")

                    if ssh_enabled:
                        validator.validate_non_empty_string(
                            ssh.get("user"),
                            f"{path}.ssh.user",
                        )
                        validator.validate_non_empty_string(
                            ssh.get("key_file"),
                            f"{path}.ssh.key_file",
                        )

            modules = host.get("modules")

            if modules is not None:
                modules = validator.validate_mapping(
                    modules,
                    f"{path}.modules",
                )

                if modules is not None:
                    for module_name, module_enabled in modules.items():
                        if not isinstance(module_enabled, bool):
                            validator.error(
                                f"{path}.modules.{module_name}",
                                "must be true or false",
                            )

            system_info_enabled = (
                isinstance(modules, dict)
                and modules.get("system_info") is True
            )
            is_collector_host = (
                host_id is not None
                and host_id in {
                    collector_id,
                    "collector",
                }
            )

            if (
                enabled
                and system_info_enabled
                and not is_collector_host
                and host_type is not None
                and host_type.lower() in SUPPORTED_HOST_TYPES
            ):
                if host_type.lower() == "linux":
                    validator.validate_non_empty_string(
                        host.get("address"),
                        f"{path}.address",
                    )

                ssh_value = host.get("ssh")

                if not isinstance(ssh_value, dict):
                    validator.error(
                        f"{path}.ssh",
                        "is required when modules.system_info is true "
                        "for a remote host",
                    )
                elif ssh_value.get("enabled") is not True:
                    validator.error(
                        f"{path}.ssh.enabled",
                        "must be true when modules.system_info is true "
                        "for a remote host",
                    )

            pools_enabled = (
                isinstance(modules, dict)
                and modules.get("pools") is True
            )

            if enabled and pools_enabled:
                if (
                    host_type is None
                    or host_type.lower() != "truenas"
                ):
                    validator.error(
                        f"{path}.modules.pools",
                        "requires host type: truenas",
                    )
                else:
                    ssh_value = host.get("ssh")

                    if not isinstance(ssh_value, dict):
                        validator.error(
                            f"{path}.ssh",
                            "is required when modules.pools is true",
                        )
                    elif ssh_value.get("enabled") is not True:
                        validator.error(
                            f"{path}.ssh.enabled",
                            "must be true when modules.pools is true",
                        )

        if not enabled_host_ids:
            validator.error("hosts", "must contain at least one enabled host")

    if collector_id and collector_id not in enabled_host_ids:
        validator.warning(
            "collector.id",
            "does not match an enabled host entry; collector monitoring is optional",
        )

    services = validator.validate_list(
        config.get("services", []),
        "services",
    )
    service_ids: set[str] = set()

    if services is not None:
        for index, service_value in enumerate(services):
            path = f"services[{index}]"
            service = validator.validate_mapping(service_value, path)

            if service is None:
                continue

            enabled = validator.validate_enabled(service, path)
            name = validator.validate_non_empty_string(
                service.get("name"),
                f"{path}.name",
                required=enabled,
            )

            service_id_value = service.get("id")

            if service_id_value is not None:
                service_id = validator.validate_id(
                    service_id_value,
                    f"{path}.id",
                )
            elif name is not None:
                service_id = safe_service_id(name)
            else:
                service_id = None

            if service_id is not None:
                if service_id in service_ids:
                    validator.error(
                        f"{path}.id",
                        f"duplicate effective service id: {service_id}",
                    )
                else:
                    service_ids.add(service_id)

            host_id = validator.validate_non_empty_string(
                service.get("host"),
                f"{path}.host",
                required=enabled,
            )

            if enabled and host_id is not None:
                if host_id not in host_ids:
                    validator.error(
                        f"{path}.host",
                        f"references unknown host: {host_id}",
                    )
                elif host_id not in enabled_host_ids:
                    validator.error(
                        f"{path}.host",
                        f"references disabled host: {host_id}",
                    )

            service_type = service.get("type")

            if service_type is None and enabled:
                validator.error(f"{path}.type", "is required")
            elif service_type is not None:
                if not isinstance(service_type, str):
                    validator.error(f"{path}.type", "must be app or helper")
                elif service_type.lower() not in SUPPORTED_SERVICE_TYPES:
                    validator.error(f"{path}.type", "must be app or helper")

            check_type = service.get("check")

            if check_type is None and enabled:
                validator.error(f"{path}.check", "is required")
            elif check_type is not None:
                if not isinstance(check_type, str):
                    validator.error(
                        f"{path}.check",
                        "must be http, docker, or truenas_app",
                    )
                elif check_type.lower() not in SUPPORTED_SERVICE_CHECKS:
                    validator.error(
                        f"{path}.check",
                        "must be http, docker, or truenas_app",
                    )

            if enabled and isinstance(check_type, str):
                normalized_check = check_type.lower()

                if normalized_check == "http":
                    validator.validate_http_url(
                        service.get("url"),
                        f"{path}.url",
                        required=True,
                    )
                elif normalized_check == "docker":
                    validator.validate_non_empty_string(
                        service.get("container"),
                        f"{path}.container",
                    )
                elif normalized_check == "truenas_app":
                    validator.validate_non_empty_string(
                        service.get("app_id"),
                        f"{path}.app_id",
                    )

                if normalized_check != "http" and "url" in service:
                    validator.validate_http_url(
                        service.get("url"),
                        f"{path}.url",
                    )
            elif "url" in service:
                validator.validate_http_url(
                    service.get("url"),
                    f"{path}.url",
                )

    local_storage = validator.validate_list(
        config.get("local_storage", []),
        "local_storage",
    )
    local_storage_ids: set[str] = set()

    if local_storage is not None:
        for index, check_value in enumerate(local_storage):
            path = f"local_storage[{index}]"
            check = validator.validate_mapping(check_value, path)

            if check is None:
                continue

            enabled = validator.validate_enabled(check, path)

            explicit_id = check.get("id")

            if explicit_id is not None:
                check_id = validator.validate_id(explicit_id, f"{path}.id")

                if check_id is not None:
                    if check_id in local_storage_ids:
                        validator.error(
                            f"{path}.id",
                            f"duplicate local storage id: {check_id}",
                        )
                    else:
                        local_storage_ids.add(check_id)

            host_id = validator.validate_non_empty_string(
                check.get("host"),
                f"{path}.host",
                required=enabled,
            )

            if enabled and host_id is not None:
                if host_id not in host_ids:
                    validator.error(
                        f"{path}.host",
                        f"references unknown host: {host_id}",
                    )
                elif host_id not in enabled_host_ids:
                    validator.error(
                        f"{path}.host",
                        f"references disabled host: {host_id}",
                    )

            validator.validate_non_empty_string(
                check.get("mount"),
                f"{path}.mount",
                required=enabled,
            )

            warning_percent = check.get("warning_percent", 80)
            critical_percent = check.get("critical_percent", 90)

            warning_value = validator.validate_integer(
                warning_percent,
                f"{path}.warning_percent",
                minimum=0,
                maximum=100,
            )
            critical_value = validator.validate_integer(
                critical_percent,
                f"{path}.critical_percent",
                minimum=0,
                maximum=100,
            )

            if (
                warning_value is not None
                and critical_value is not None
                and warning_value >= critical_value
            ):
                validator.error(
                    path,
                    "warning_percent must be lower than critical_percent",
                )

    backup_checks = validator.validate_list(
        config.get("backup_checks", []),
        "backup_checks",
    )
    backup_ids: set[str] = set()

    if backup_checks is not None:
        for index, check_value in enumerate(backup_checks):
            path = f"backup_checks[{index}]"
            check = validator.validate_mapping(check_value, path)

            if check is None:
                continue

            enabled = validator.validate_enabled(check, path)

            explicit_id = check.get("id")

            if explicit_id is not None:
                check_id = validator.validate_id(explicit_id, f"{path}.id")

                if check_id is not None:
                    if check_id in backup_ids:
                        validator.error(
                            f"{path}.id",
                            f"duplicate backup check id: {check_id}",
                        )
                    else:
                        backup_ids.add(check_id)

            host_id = validator.validate_non_empty_string(
                check.get("host"),
                f"{path}.host",
                required=enabled,
            )

            if enabled and host_id is not None:
                if host_id not in host_ids:
                    validator.error(
                        f"{path}.host",
                        f"references unknown host: {host_id}",
                    )
                elif host_id not in enabled_host_ids:
                    validator.error(
                        f"{path}.host",
                        f"references disabled host: {host_id}",
                    )

            validator.validate_non_empty_string(
                check.get("name"),
                f"{path}.name",
                required=enabled,
            )

            validator.validate_non_empty_string(
                check.get("marker_file"),
                f"{path}.marker_file",
                required=enabled,
            )

            validator.validate_integer(
                check.get("max_age_hours", 36),
                f"{path}.max_age_hours",
                minimum=1,
            )

    protection = validator.validate_list(
        config.get("protection", []),
        "protection",
    )
    protection_ids: set[str] = set()

    if protection is not None:
        for index, relationship_value in enumerate(protection):
            path = f"protection[{index}]"
            relationship = validator.validate_mapping(
                relationship_value,
                path,
            )

            if relationship is None:
                continue

            enabled = validator.validate_enabled(relationship, path)

            explicit_id = relationship.get("id")

            if explicit_id is not None:
                relationship_id = validator.validate_id(
                    explicit_id,
                    f"{path}.id",
                )

                if relationship_id is not None:
                    if relationship_id in protection_ids:
                        validator.error(
                            f"{path}.id",
                            f"duplicate protection id: {relationship_id}",
                        )
                    else:
                        protection_ids.add(relationship_id)

            relationship_type = relationship.get("type")

            if relationship_type is None and enabled:
                validator.error(f"{path}.type", "is required")
            elif relationship_type is not None:
                if not isinstance(relationship_type, str):
                    validator.error(f"{path}.type", "must be a string")
                elif enabled and relationship_type.lower() != "replication":
                    validator.warning(
                        f"{path}.type",
                        "only replication relationships have active preview logic",
                    )

            source_host = validator.validate_non_empty_string(
                relationship.get("source_host"),
                f"{path}.source_host",
                required=enabled,
            )
            target_host = validator.validate_non_empty_string(
                relationship.get("target_host"),
                f"{path}.target_host",
                required=enabled,
            )

            for field_name, host_id in (
                ("source_host", source_host),
                ("target_host", target_host),
            ):
                if enabled and host_id is not None:
                    if host_id not in host_ids:
                        validator.error(
                            f"{path}.{field_name}",
                            f"references unknown host: {host_id}",
                        )
                    elif host_id not in enabled_host_ids:
                        validator.error(
                            f"{path}.{field_name}",
                            f"references disabled host: {host_id}",
                        )

            datasets = relationship.get("datasets")

            if datasets is not None:
                if not isinstance(datasets, list):
                    validator.error(f"{path}.datasets", "must be a YAML list")
                else:
                    for dataset_index, dataset in enumerate(datasets):
                        validator.validate_non_empty_string(
                            dataset,
                            f"{path}.datasets[{dataset_index}]",
                        )

    image_updates = config.get("image_updates")

    if image_updates is not None:
        image_updates = validator.validate_mapping(
            image_updates,
            "image_updates",
        )

        if image_updates is not None:
            image_updates_enabled = validator.validate_enabled(
                image_updates,
                "image_updates",
            )

            if "provider" in image_updates or "hosts" in image_updates:
                validator.warning(
                    "image_updates",
                    "legacy provider/hosts fields are ignored; use image_updates.sources",
                )

            sources = image_updates.get("sources", [])

            if not isinstance(sources, list):
                validator.error(
                    "image_updates.sources",
                    "must be a YAML list",
                )
            else:
                if image_updates_enabled and not sources:
                    validator.error(
                        "image_updates.sources",
                        "must contain at least one source when image updates are enabled",
                    )

                source_ids: set[str] = set()

                for index, source_value in enumerate(sources):
                    source_path = f"image_updates.sources[{index}]"
                    source = validator.validate_mapping(
                        source_value,
                        source_path,
                    )

                    if source is None:
                        continue

                    source_id_value = source.get("id")

                    if source_id_value is not None:
                        source_id = validator.validate_id(
                            source_id_value,
                            f"{source_path}.id",
                        )

                        if source_id is not None:
                            if source_id in source_ids:
                                validator.error(
                                    f"{source_path}.id",
                                    f"duplicate image update source id: {source_id}",
                                )
                            else:
                                source_ids.add(source_id)

                    host_id = validator.validate_non_empty_string(
                        source.get("host"),
                        f"{source_path}.host",
                    )

                    if host_id is not None:
                        if host_id not in host_ids:
                            validator.error(
                                f"{source_path}.host",
                                f"references unknown host: {host_id}",
                            )
                        elif host_id not in enabled_host_ids:
                            validator.error(
                                f"{source_path}.host",
                                f"references disabled host: {host_id}",
                            )

                    provider = validator.validate_non_empty_string(
                        source.get("provider"),
                        f"{source_path}.provider",
                    )

                    normalized_provider = (
                        provider.lower()
                        if provider is not None
                        else None
                    )

                    if (
                        normalized_provider is not None
                        and normalized_provider
                        not in SUPPORTED_IMAGE_UPDATE_PROVIDERS
                    ):
                        validator.error(
                            f"{source_path}.provider",
                            "must be diun or truenas",
                        )

                    if normalized_provider == "diun":
                        validator.validate_http_url(
                            source.get("url"),
                            f"{source_path}.url",
                            required=True,
                        )
                    elif normalized_provider == "truenas":
                        if (
                            host_id is not None
                            and host_id in host_types
                            and host_types[host_id] != "truenas"
                        ):
                            validator.error(
                                f"{source_path}.provider",
                                "truenas provider requires a type: truenas host",
                            )

                        if "url" in source:
                            validator.validate_http_url(
                                source.get("url"),
                                f"{source_path}.url",
                            )

    summary_cards = validator.validate_list(
        config.get(
            "summary_cards",
            ["systems", "storage", "protection", "services"],
        ),
        "summary_cards",
    )

    if summary_cards is not None:
        seen_cards: set[str] = set()
        valid_cards = 0

        for index, card_value in enumerate(summary_cards):
            path = f"summary_cards[{index}]"

            if not isinstance(card_value, str) or not card_value.strip():
                validator.error(path, "must be a non-empty string")
                continue

            card = card_value.strip().lower()

            if card not in SUPPORTED_SUMMARY_CARDS:
                validator.warning(
                    path,
                    f"unknown card '{card}' will be ignored",
                )
                continue

            valid_cards += 1

            if card in seen_cards:
                validator.warning(
                    path,
                    f"duplicate card '{card}' will be ignored",
                )
            else:
                seen_cards.add(card)

        if valid_cards == 0:
            validator.warning(
                "summary_cards",
                "contains no valid cards; the default four cards will be used",
            )

    return validator


def load_config(path: Path) -> dict:
    if not path.exists():
        print(f"ERROR: Configuration file not found: {path}", file=sys.stderr)
        raise SystemExit(1)

    try:
        data = yaml.safe_load(path.read_text())
    except Exception as exc:
        print(f"ERROR: Could not parse YAML: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if data is None:
        data = {}

    if not isinstance(data, dict):
        print(
            "ERROR: Top-level configuration must be a YAML mapping.",
            file=sys.stderr,
        )
        raise SystemExit(1)

    return data


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate a Sanity Node Phase 2 configuration file.",
    )
    parser.add_argument(
        "config",
        nargs="?",
        default=str(DEFAULT_CONFIG),
        help="configuration file to validate",
    )
    args = parser.parse_args()

    config_path = Path(args.config).expanduser().resolve()

    print("=== SANITY NODE CONFIGURATION VALIDATION ===")
    print(f"Configuration: {config_path}")
    print()

    config = load_config(config_path)
    validator = validate_config(config)

    for path, message in validator.errors:
        print(f"ERROR   {path}: {message}")

    for path, message in validator.warnings:
        print(f"WARNING {path}: {message}")

    print()
    print(
        f"Validation result: "
        f"{len(validator.errors)} error(s), "
        f"{len(validator.warnings)} warning(s)"
    )

    if validator.errors:
        print("Configuration validation failed.")
        return 1

    print("Configuration validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
