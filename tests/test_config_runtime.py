#!/usr/bin/env python3

import ast
import html
import unittest
from pathlib import Path


GENERATOR = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "generate-dashboard.py"
)

FUNCTIONS_UNDER_TEST = {
    "cfg_get",
    "enabled_items",
    "config_image_reference_aliases",
    "apply_config_image_update_overlay",
    "configured_host_key",
    "configured_host_display_name",
    "configured_host_sort_key",
    "config_error_indicates_host_unreachable",
    "classify_collector_error",
    "build_collector_errors_section",
    "config_host_service_unreachable",
    "build_service_summary",
    "normalize_public_summary_cards",
    "build_compact_host_service_details",
    "build_public_host_summary_preview",
    "status_text_class",
    "h",
    "badge",
    "build_public_summary_card",
    "public_summary_text_class",
    "build_public_summary_detail",
    "public_card_css",
    "config_system_host_status",
    "build_public_systems_summary_card",
    "build_public_storage_summary_card",
    "build_public_protection_summary_card",
    "build_public_services_summary_card",
    "build_public_four_card_summary_preview",
    "config_replication_row_matches_relationship",
    "apply_config_protection_replication_overlay",
}


def load_generator_functions():
    """Load selected pure functions without executing generator module scope."""
    source = GENERATOR.read_text()
    parsed = ast.parse(source, filename=str(GENERATOR))

    selected_nodes = [
        node
        for node in parsed.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name in FUNCTIONS_UNDER_TEST
    ]

    selected_names = {node.name for node in selected_nodes}
    missing = FUNCTIONS_UNDER_TEST - selected_names

    if missing:
        raise RuntimeError(
            "Generator functions not found: "
            + ", ".join(sorted(missing))
        )

    module = ast.Module(body=selected_nodes, type_ignores=[])
    ast.fix_missing_locations(module)

    namespace = {
        "html": html,
        "CONFIG": {
            "collector": {
                "id": "collector",
            }
        },
    }
    exec(
        compile(module, filename=str(GENERATOR), mode="exec"),
        namespace,
    )
    return namespace


FUNCTIONS = load_generator_functions()

config_image_reference_aliases = FUNCTIONS[
    "config_image_reference_aliases"
]
apply_config_image_update_overlay = FUNCTIONS[
    "apply_config_image_update_overlay"
]
config_error_indicates_host_unreachable = FUNCTIONS[
    "config_error_indicates_host_unreachable"
]
classify_collector_error = FUNCTIONS[
    "classify_collector_error"
]
build_collector_errors_section = FUNCTIONS[
    "build_collector_errors_section"
]
config_host_service_unreachable = FUNCTIONS[
    "config_host_service_unreachable"
]
normalize_public_summary_cards = FUNCTIONS[
    "normalize_public_summary_cards"
]
build_compact_host_service_details = FUNCTIONS[
    "build_compact_host_service_details"
]
build_public_host_summary_preview = FUNCTIONS[
    "build_public_host_summary_preview"
]
config_system_host_status = FUNCTIONS[
    "config_system_host_status"
]
build_public_systems_summary_card = FUNCTIONS[
    "build_public_systems_summary_card"
]
build_public_storage_summary_card = FUNCTIONS[
    "build_public_storage_summary_card"
]
build_public_protection_summary_card = FUNCTIONS[
    "build_public_protection_summary_card"
]
build_public_services_summary_card = FUNCTIONS[
    "build_public_services_summary_card"
]
build_public_four_card_summary_preview = FUNCTIONS[
    "build_public_four_card_summary_preview"
]
config_replication_row_matches_relationship = FUNCTIONS[
    "config_replication_row_matches_relationship"
]
apply_config_protection_replication_overlay = FUNCTIONS[
    "apply_config_protection_replication_overlay"
]


class ImageReferenceAliasTests(unittest.TestCase):
    def test_docker_hub_library_aliases_are_normalized(self):
        self.assertEqual(
            config_image_reference_aliases(
                "docker.io/library/redis:7-alpine"
            ),
            {
                "docker.io/library/redis",
                "library/redis",
                "redis",
            },
        )

    def test_short_docker_hub_reference_is_normalized(self):
        self.assertEqual(
            config_image_reference_aliases("redis:7"),
            {"redis"},
        )

    def test_digest_is_removed(self):
        self.assertEqual(
            config_image_reference_aliases(
                "index.docker.io/library/redis@sha256:abc123"
            ),
            {
                "index.docker.io/library/redis",
                "library/redis",
                "redis",
            },
        )

    def test_registry_qualified_repository_stays_distinct(self):
        self.assertEqual(
            config_image_reference_aliases(
                "ghcr.io/example/redis:latest"
            ),
            {"ghcr.io/example/redis"},
        )

    def test_empty_reference_returns_empty_set(self):
        self.assertEqual(
            config_image_reference_aliases(""),
            set(),
        )


class ImageUpdateOverlayTests(unittest.TestCase):
    def test_diun_update_overlays_matching_healthy_docker_service(self):
        services = [
            {
                "id": "redis",
                "host": "collector",
                "check": "docker",
            }
        ]
        statuses = {
            "redis": {
                "label": "UP",
                "css": "ok",
                "raw": "running",
                "image": "redis:7-alpine",
            }
        }
        update_rows = [
            {
                "host_id": "collector",
                "provider": "diun",
                "update_images": [
                    "docker.io/library/redis:latest"
                ],
            }
        ]

        result, count = apply_config_image_update_overlay(
            services,
            statuses,
            update_rows,
        )

        self.assertEqual(count, 1)
        self.assertEqual(result["redis"]["label"], "UPDATE")
        self.assertEqual(result["redis"]["css"], "info")
        self.assertIn(
            "update available for redis:7-alpine",
            result["redis"]["raw"],
        )

    def test_truenas_update_overlays_matching_healthy_app(self):
        services = [
            {
                "id": "redis-service",
                "host": "t620",
                "check": "truenas_app",
                "app_id": "redis",
            }
        ]
        statuses = {
            "redis-service": {
                "label": "UP",
                "css": "ok",
                "raw": "RUNNING",
            }
        }
        update_rows = [
            {
                "host_id": "t620",
                "provider": "truenas",
                "update_apps": ["Redis"],
            }
        ]

        result, count = apply_config_image_update_overlay(
            services,
            statuses,
            update_rows,
        )

        self.assertEqual(count, 1)
        self.assertEqual(
            result["redis-service"]["label"],
            "UPDATE",
        )

    def test_existing_unhealthy_status_takes_precedence(self):
        services = [
            {
                "id": "redis",
                "host": "collector",
                "check": "docker",
            }
        ]
        statuses = {
            "redis": {
                "label": "DOWN",
                "css": "bad",
                "raw": "exited",
                "image": "redis:7",
            }
        }
        update_rows = [
            {
                "host_id": "collector",
                "provider": "diun",
                "update_images": ["redis:latest"],
            }
        ]

        result, count = apply_config_image_update_overlay(
            services,
            statuses,
            update_rows,
        )

        self.assertEqual(count, 0)
        self.assertEqual(result["redis"]["label"], "DOWN")
        self.assertEqual(result["redis"]["css"], "bad")

    def test_update_is_scoped_to_configured_host(self):
        services = [
            {
                "id": "redis",
                "host": "collector",
                "check": "docker",
            }
        ]
        statuses = {
            "redis": {
                "label": "UP",
                "css": "ok",
                "raw": "running",
                "image": "redis:7",
            }
        }
        update_rows = [
            {
                "host_id": "other-host",
                "provider": "diun",
                "update_images": ["redis:latest"],
            }
        ]

        result, count = apply_config_image_update_overlay(
            services,
            statuses,
            update_rows,
        )

        self.assertEqual(count, 0)
        self.assertEqual(result["redis"]["label"], "UP")

    def test_input_statuses_are_not_mutated(self):
        services = [
            {
                "id": "redis",
                "host": "collector",
                "check": "docker",
            }
        ]
        statuses = {
            "redis": {
                "label": "UP",
                "css": "ok",
                "raw": "running",
                "image": "redis:7",
            }
        }
        update_rows = [
            {
                "host_id": "collector",
                "provider": "diun",
                "update_images": ["redis:latest"],
            }
        ]

        result, count = apply_config_image_update_overlay(
            services,
            statuses,
            update_rows,
        )

        self.assertEqual(count, 1)
        self.assertEqual(statuses["redis"]["label"], "UP")
        self.assertEqual(result["redis"]["label"], "UPDATE")


class CollectorErrorClassificationTests(unittest.TestCase):
    def test_error_families_are_classified(self):
        cases = (
            ("Connection timed out", "TIMEOUT", "bad"),
            ("No route to host", "NETWORK", "bad"),
            ("Host key verification failed", "HOST KEY", "warning"),
            ("Permission denied (publickey)", "AUTH", "warning"),
            ("Connection refused", "REFUSED", "bad"),
            ("Failed to parse JSON response", "PARSE", "warning"),
            ("midclt call app.query failed", "COMMAND", "warning"),
        )

        for message, expected_label, expected_css in cases:
            with self.subTest(message=message):
                result = classify_collector_error(message)
                self.assertEqual(result["label"], expected_label)
                self.assertEqual(result["css"], expected_css)

    def test_empty_error_is_unknown(self):
        self.assertEqual(
            classify_collector_error(""),
            {"label": "UNKNOWN", "css": "info"},
        )
        self.assertEqual(
            classify_collector_error(None),
            {"label": "UNKNOWN", "css": "info"},
        )

    def test_unmatched_error_uses_other_fallback(self):
        self.assertEqual(
            classify_collector_error("Unexpected collector response"),
            {"label": "OTHER", "css": "info"},
        )

    def test_timeout_precedence_wins_over_authentication_text(self):
        result = classify_collector_error(
            "Permission denied after connection timed out"
        )

        self.assertEqual(result["label"], "TIMEOUT")
        self.assertEqual(result["css"], "bad")


class CollectorErrorsRenderingTests(unittest.TestCase):
    def test_empty_error_list_renders_no_section(self):
        self.assertEqual(
            build_collector_errors_section([]),
            "",
        )

    def test_error_section_renders_type_badges_and_escaped_content(self):
        section = build_collector_errors_section(
            [
                (
                    "Configured TrueNAS app query",
                    "Connection timed out",
                ),
                (
                    "Parser <check>",
                    "Failed to parse <json>",
                ),
            ]
        )

        self.assertIn("<h2>Collector Errors</h2>", section)
        self.assertIn("<th>Type</th>", section)
        self.assertIn('class="badge bad">TIMEOUT</span>', section)
        self.assertIn('class="badge warning">PARSE</span>', section)
        self.assertIn("Parser &lt;check&gt;", section)
        self.assertIn("Failed to parse &lt;json&gt;", section)
        self.assertEqual(section.count('<tr class="bad">'), 2)
        self.assertIn(
            "does not change Overall Status handling",
            section,
        )


class HostUnreachableClassifierTests(unittest.TestCase):
    def test_recognized_network_failures(self):
        messages = [
            "ssh: connect to host 192.0.2.10 port 22: No route to host",
            "Network is unreachable",
            "Host is down",
            "Connection timed out",
            "Operation timed out",
            "Connection timeout while connecting",
            "Command timed out after 30 seconds",
        ]

        for message in messages:
            with self.subTest(message=message):
                self.assertTrue(
                    config_error_indicates_host_unreachable(
                        message
                    )
                )

    def test_non_network_failures_are_not_unreachable(self):
        messages = [
            "Permission denied (publickey)",
            "Host key verification failed",
            "Connection refused",
            "Failed to parse JSON",
            "midclt returned invalid output",
            "",
            None,
        ]

        for message in messages:
            with self.subTest(message=message):
                self.assertFalse(
                    config_error_indicates_host_unreachable(
                        message
                    )
                )


class HostServiceUnreachableTests(unittest.TestCase):
    def setUp(self):
        self.host = {
            "id": "t620",
            "type": "truenas",
        }
        self.services = [
            {
                "id": "jellyfin",
                "check": "truenas_app",
            },
            {
                "id": "redis",
                "check": "truenas_app",
            },
        ]

    def test_all_unknown_timeout_statuses_collapse_host(self):
        statuses = {
            "jellyfin": {
                "label": "UNKNOWN",
                "raw": "Connection timed out",
            },
            "redis": {
                "label": "UNKNOWN",
                "raw": "Connection timed out",
            },
        }

        self.assertTrue(
            config_host_service_unreachable(
                self.host,
                self.services,
                statuses,
            )
        )

    def test_partial_service_success_prevents_collapse(self):
        statuses = {
            "jellyfin": {
                "label": "UNKNOWN",
                "raw": "Connection timed out",
            },
            "redis": {
                "label": "UP",
                "raw": "RUNNING",
            },
        }

        self.assertFalse(
            config_host_service_unreachable(
                self.host,
                self.services,
                statuses,
            )
        )

    def test_authentication_failure_does_not_collapse_host(self):
        statuses = {
            "jellyfin": {
                "label": "UNKNOWN",
                "raw": "Permission denied (publickey)",
            },
            "redis": {
                "label": "UNKNOWN",
                "raw": "Permission denied (publickey)",
            },
        }

        self.assertFalse(
            config_host_service_unreachable(
                self.host,
                self.services,
                statuses,
            )
        )

    def test_linux_host_does_not_collapse(self):
        statuses = {
            "jellyfin": {
                "label": "UNKNOWN",
                "raw": "Connection timed out",
            },
            "redis": {
                "label": "UNKNOWN",
                "raw": "Connection timed out",
            },
        }

        linux_host = {
            "id": "collector",
            "type": "linux",
        }

        self.assertFalse(
            config_host_service_unreachable(
                linux_host,
                self.services,
                statuses,
            )
        )

    def test_http_only_services_do_not_collapse(self):
        services = [
            {
                "id": "web-ui",
                "check": "http",
            }
        ]
        statuses = {
            "web-ui": {
                "label": "UNKNOWN",
                "raw": "Connection timed out",
            }
        }

        self.assertFalse(
            config_host_service_unreachable(
                self.host,
                services,
                statuses,
            )
        )

    def test_missing_service_status_prevents_collapse(self):
        statuses = {
            "jellyfin": {
                "label": "UNKNOWN",
                "raw": "Connection timed out",
            }
        }

        self.assertFalse(
            config_host_service_unreachable(
                self.host,
                self.services,
                statuses,
            )
        )


class PublicSummaryCardNormalizationTests(unittest.TestCase):
    def test_valid_cards_are_normalized_and_deduplicated(self):
        self.assertEqual(
            normalize_public_summary_cards(
                [
                    " Services ",
                    "systems",
                    "SERVICES",
                    "unknown",
                    "storage",
                ]
            ),
            ["services", "systems", "storage"],
        )

    def test_empty_or_invalid_selection_uses_default_cards(self):
        expected = [
            "systems",
            "storage",
            "protection",
            "services",
        ]

        self.assertEqual(
            normalize_public_summary_cards([]),
            expected,
        )
        self.assertEqual(
            normalize_public_summary_cards(None),
            expected,
        )
        self.assertEqual(
            normalize_public_summary_cards(["unknown"]),
            expected,
        )


class CompactHostServiceDetailsTests(unittest.TestCase):
    def setUp(self):
        self.services = [
            {
                "id": "healthy",
                "host": "collector",
                "display": "Healthy Service",
                "type": "app",
                "check": "http",
            },
            {
                "id": "update",
                "host": "collector",
                "display": "Update Service",
                "type": "app",
                "check": "docker",
                "url": "http://example.test/update",
            },
            {
                "id": "down",
                "host": "collector",
                "display": "Down Service",
                "type": "helper",
                "check": "docker",
            },
        ]

    def test_compact_details_show_only_non_up_services(self):
        statuses = {
            "healthy": {
                "label": "UP",
                "css": "ok",
                "raw": "healthy",
            },
            "update": {
                "label": "UPDATE",
                "css": "info",
                "raw": "update available",
            },
            "down": {
                "label": "DOWN",
                "css": "bad",
                "raw": "stopped",
            },
        }

        result = build_compact_host_service_details(
            self.services,
            statuses,
        )

        self.assertEqual(result["exceptions"], 2)
        self.assertNotIn("Healthy Service", result["details"])
        self.assertIn("Update Service", result["details"])
        self.assertIn("UPDATE", result["details"])
        self.assertIn("Down Service", result["details"])
        self.assertIn("DOWN", result["details"])
        self.assertIn(
            'href="http://example.test/update"',
            result["details"],
        )

    def test_all_up_services_render_one_compact_success_line(self):
        statuses = {
            service["id"]: {
                "label": "UP",
                "css": "ok",
                "raw": "healthy",
            }
            for service in self.services
        }

        result = build_compact_host_service_details(
            self.services,
            statuses,
        )

        self.assertEqual(result["exceptions"], 0)
        self.assertIn("Configured services", result["details"])
        self.assertIn("ALL UP", result["details"])
        self.assertNotIn("Healthy Service", result["details"])
        self.assertNotIn("Update Service", result["details"])
        self.assertNotIn("Down Service", result["details"])

    def test_empty_service_list_returns_empty_details(self):
        self.assertEqual(
            build_compact_host_service_details([], {}),
            {
                "details": "",
                "details_class": "",
                "exceptions": 0,
            },
        )


class HostSummaryCompactRenderingTests(unittest.TestCase):
    def setUp(self):
        self.host = {
            "id": "collector",
            "type": "linux",
            "display_name": "Utility Node",
            "enabled": True,
        }
        self.services = [
            {
                "id": "healthy",
                "host": "collector",
                "display": "Healthy Service",
                "type": "app",
                "check": "http",
            },
            {
                "id": "update",
                "host": "collector",
                "display": "Update Service",
                "type": "helper",
                "check": "docker",
            },
        ]
        self.statuses = {
            "healthy": {
                "label": "UP",
                "css": "ok",
                "raw": "HTTP 200",
            },
            "update": {
                "label": "UPDATE",
                "css": "info",
                "raw": "update available",
            },
        }
        self.web_statuses = {
            "collector": {
                "label": "OK",
                "css": "ok",
                "raw": "HTTP 200",
            }
        }

    def test_services_card_active_compacts_host_details(self):
        html_output = build_public_host_summary_preview(
            [self.host],
            self.services,
            self.statuses,
            self.web_statuses,
            ["systems", "services"],
        )

        self.assertIn(
            "1 Apps · 1 Helpers · 1 UP · 0 DOWN · 1 UPDATE",
            html_output,
        )
        self.assertIn("Update Service", html_output)
        self.assertNotIn("Healthy Service", html_output)

    def test_services_card_disabled_preserves_full_host_details(self):
        html_output = build_public_host_summary_preview(
            [self.host],
            self.services,
            self.statuses,
            self.web_statuses,
            ["systems"],
        )

        self.assertIn("Healthy Service", html_output)
        self.assertIn("Update Service", html_output)

    def test_default_card_fallback_compacts_host_details(self):
        html_output = build_public_host_summary_preview(
            [self.host],
            self.services,
            self.statuses,
            self.web_statuses,
            [],
        )

        self.assertIn("Update Service", html_output)
        self.assertNotIn("Healthy Service", html_output)

    def test_unreachable_host_collapse_takes_precedence(self):
        host = {
            "id": "t620",
            "type": "truenas",
            "display_name": "T620 TrueNAS",
            "enabled": True,
        }
        services = [
            {
                "id": "jellyfin",
                "host": "t620",
                "display": "Jellyfin",
                "type": "app",
                "check": "truenas_app",
            },
            {
                "id": "redis",
                "host": "t620",
                "display": "Redis",
                "type": "helper",
                "check": "truenas_app",
            },
        ]
        statuses = {
            "jellyfin": {
                "label": "UNKNOWN",
                "css": "info",
                "raw": "Connection timed out",
            },
            "redis": {
                "label": "UNKNOWN",
                "css": "info",
                "raw": "Connection timed out",
            },
        }

        html_output = build_public_host_summary_preview(
            [host],
            services,
            statuses,
            {
                "t620": {
                    "label": "OK",
                    "css": "ok",
                    "raw": "HTTP 200",
                }
            },
            ["services"],
        )

        self.assertIn("Host unreachable", html_output)
        self.assertIn("UNREACHABLE", html_output)
        self.assertIn("UNAVAILABLE", html_output)
        self.assertNotIn("Jellyfin", html_output)
        self.assertNotIn("Redis", html_output)


class StorageSummaryCardTests(unittest.TestCase):
    def test_empty_storage_configuration_renders_info_card(self):
        card = build_public_storage_summary_card([], {})

        self.assertIn("No storage checks configured yet", card)
        self.assertIn("summary-card info", card)
        self.assertIn("local_storage", card)

    def test_storage_counts_and_bad_precedence(self):
        checks = [
            {"id": "root", "label": "Root"},
            {"id": "archive", "label": "Archive"},
            {"id": "backup", "label": "Backup"},
            {"id": "remote", "mount": "/mnt/remote"},
        ]
        statuses = {
            "root": {
                "label": "OK",
                "css": "ok",
                "raw": "42%",
            },
            "archive": {
                "label": "WARNING",
                "css": "warning",
                "raw": "82%",
            },
            "backup": {
                "label": "CRITICAL",
                "css": "bad",
                "raw": "96%",
            },
            "remote": {
                "label": "NOT CHECKED",
                "css": "info",
                "raw": "-",
            },
        }

        card = build_public_storage_summary_card(checks, statuses)

        self.assertIn(
            "4 Checks · 1 OK · 1 WARNING · 1 CRITICAL · 1 INFO",
            card,
        )
        self.assertIn("summary-card bad", card)
        self.assertIn("Root", card)
        self.assertIn("Archive", card)
        self.assertIn("Backup", card)
        self.assertIn("/mnt/remote", card)

    def test_storage_details_use_two_columns_above_six_checks(self):
        checks = [
            {"id": f"disk-{index}", "label": f"Disk {index}"}
            for index in range(7)
        ]
        statuses = {
            check["id"]: {
                "label": "OK",
                "css": "ok",
                "raw": "healthy",
            }
            for check in checks
        }

        card = build_public_storage_summary_card(checks, statuses)

        self.assertIn("service-details two-column", card)
        self.assertIn(
            "7 Checks · 7 OK · 0 WARNING · 0 CRITICAL",
            card,
        )


class ProtectionReplicationOverlayTests(unittest.TestCase):
    def setUp(self):
        self.relationship = {
            "id": "t620-to-t330",
            "name": "T620 to T330",
            "type": "replication",
            "source_host": "t620",
            "target_host": "t330",
            "target_prefix": "backup/t620/zfs-replication",
            "datasets": [
                "tank/stacks",
                "tank/configs",
            ],
        }
        self.statuses = {
            "t620-to-t330": {
                "label": "CONFIGURED",
                "css": "info",
                "raw": "replication preview",
            }
        }
        self.row = {
            "host_id": "t620",
            "host_name": "T620 TrueNAS",
            "task_id": "7",
            "name": "T620 replication",
            "task_enabled": True,
            "direction": "PUSH",
            "transport": "SSH",
            "source_datasets": [
                "tank/stacks",
                "tank/configs",
                "tank/media",
            ],
            "target_dataset": "backup/t620/zfs-replication",
            "execution_state": "FINISHED",
            "label": "OK",
            "css": "ok",
            "raw": "last execution finished",
        }

    def test_exact_and_child_targets_match(self):
        exact_row = dict(self.row)

        self.assertTrue(
            config_replication_row_matches_relationship(
                self.relationship,
                exact_row,
            )
        )

        child_row = dict(
            self.row,
            target_dataset=(
                "backup/t620/zfs-replication/"
                "tank/stacks"
            ),
        )

        self.assertTrue(
            config_replication_row_matches_relationship(
                self.relationship,
                child_row,
            )
        )

    def test_dataset_and_path_trailing_slashes_are_normalized(self):
        relationship = dict(
            self.relationship,
            target_prefix="backup/t620/zfs-replication/",
            datasets=[
                "tank/stacks/",
                "tank/configs/",
            ],
        )
        row = dict(
            self.row,
            source_datasets=[
                "tank/stacks/",
                "tank/configs",
            ],
            target_dataset=(
                "backup/t620/zfs-replication/"
                "tank"
            ),
        )

        self.assertTrue(
            config_replication_row_matches_relationship(
                relationship,
                row,
            )
        )

    def test_non_confident_candidates_do_not_match(self):
        candidates = (
            (
                "wrong host",
                self.relationship,
                dict(self.row, host_id="t330"),
            ),
            (
                "no configured datasets",
                dict(self.relationship, datasets=[]),
                self.row,
            ),
            (
                "missing configured dataset",
                self.relationship,
                dict(
                    self.row,
                    source_datasets=["tank/stacks"],
                ),
            ),
            (
                "wrong target prefix",
                self.relationship,
                dict(
                    self.row,
                    target_dataset="backup/other",
                ),
            ),
            (
                "collector failure row",
                self.relationship,
                dict(self.row, task_enabled=None),
            ),
            (
                "non-replication relationship",
                dict(self.relationship, type="backup"),
                self.row,
            ),
        )

        for name, relationship, row in candidates:
            with self.subTest(name=name):
                self.assertFalse(
                    config_replication_row_matches_relationship(
                        relationship,
                        row,
                    )
                )

    def test_matching_live_row_overlays_configured_status(self):
        updated = apply_config_protection_replication_overlay(
            [self.relationship],
            self.statuses,
            [self.row],
        )

        self.assertEqual(
            updated["t620-to-t330"]["label"],
            "OK",
        )
        self.assertEqual(
            updated["t620-to-t330"]["css"],
            "ok",
        )
        self.assertIn(
            "1 matching task",
            updated["t620-to-t330"]["raw"],
        )
        self.assertIn(
            "T620 replication",
            updated["t620-to-t330"]["raw"],
        )
        self.assertIn(
            "last execution finished",
            updated["t620-to-t330"]["raw"],
        )

        self.assertEqual(
            self.statuses["t620-to-t330"]["label"],
            "CONFIGURED",
        )

    def test_worst_matching_severity_wins(self):
        warning_row = dict(
            self.row,
            task_id="8",
            name="Paused replication",
            label="PAUSED",
            css="warning",
            raw="replication task is paused",
        )
        failed_row = dict(
            self.row,
            task_id="9",
            name="Failed replication",
            label="CRITICAL",
            css="bad",
            raw="network failure",
        )

        updated = apply_config_protection_replication_overlay(
            [self.relationship],
            self.statuses,
            [
                self.row,
                warning_row,
                failed_row,
            ],
        )

        status = updated["t620-to-t330"]

        self.assertEqual(status["label"], "CRITICAL")
        self.assertEqual(status["css"], "bad")
        self.assertIn("3 matching tasks", status["raw"])
        self.assertIn("Failed replication", status["raw"])
        self.assertIn("network failure", status["raw"])

    def test_unmatched_and_incomplete_statuses_are_preserved(self):
        unmatched = apply_config_protection_replication_overlay(
            [self.relationship],
            self.statuses,
            [dict(self.row, host_id="other")],
        )

        self.assertEqual(
            unmatched["t620-to-t330"],
            self.statuses["t620-to-t330"],
        )

        incomplete_statuses = {
            "t620-to-t330": {
                "label": "INCOMPLETE",
                "css": "warning",
                "raw": "missing target host",
            }
        }
        incomplete = apply_config_protection_replication_overlay(
            [self.relationship],
            incomplete_statuses,
            [self.row],
        )

        self.assertEqual(
            incomplete["t620-to-t330"],
            incomplete_statuses["t620-to-t330"],
        )

    def test_live_ok_still_counts_as_configured(self):
        updated = apply_config_protection_replication_overlay(
            [self.relationship],
            self.statuses,
            [self.row],
        )
        card = build_public_protection_summary_card(
            [self.relationship],
            updated,
        )

        self.assertIn(
            "1 Relationships · 1 CONFIGURED · 0 INCOMPLETE",
            card,
        )
        self.assertNotIn(" · 1 INFO", card)
        self.assertIn(">OK</span>", card)


class ProtectionSummaryCardTests(unittest.TestCase):
    def test_empty_protection_configuration_renders_info_card(self):
        card = build_public_protection_summary_card([], {})

        self.assertIn(
            "No protection relationships configured yet",
            card,
        )
        self.assertIn("summary-card info", card)
        self.assertIn("protection", card)

    def test_protection_counts_and_bad_precedence(self):
        relationships = [
            {"id": "configured", "name": "Primary Backup"},
            {"id": "incomplete", "name": "Archive Backup"},
            {"id": "failed", "name": "Remote Backup"},
            {"id": "unknown", "name": "Cold Backup"},
        ]
        statuses = {
            "configured": {
                "label": "CONFIGURED",
                "css": "ok",
                "raw": "ready",
            },
            "incomplete": {
                "label": "INCOMPLETE",
                "css": "warning",
                "raw": "missing dataset",
            },
            "failed": {
                "label": "FAILED",
                "css": "bad",
                "raw": "task failed",
            },
            "unknown": {
                "label": "UNKNOWN",
                "css": "info",
                "raw": "-",
            },
        }

        card = build_public_protection_summary_card(
            relationships,
            statuses,
        )

        self.assertIn(
            "4 Relationships · 1 CONFIGURED · 1 INCOMPLETE"
            " · 1 BAD · 1 INFO",
            card,
        )
        self.assertIn("summary-card bad", card)
        self.assertIn("Primary Backup", card)
        self.assertIn("Archive Backup", card)
        self.assertIn("Remote Backup", card)
        self.assertIn("Cold Backup", card)


class ServicesSummaryCardTests(unittest.TestCase):
    def test_empty_services_configuration_renders_info_card(self):
        card = build_public_services_summary_card([], {})

        self.assertIn("No services configured yet", card)
        self.assertIn("summary-card info", card)

    def test_service_counts_and_bad_precedence(self):
        services = [
            {
                "id": "web",
                "display": "Web",
                "type": "app",
            },
            {
                "id": "database",
                "display": "Database",
                "type": "helper",
            },
            {
                "id": "media",
                "display": "Media",
                "type": "app",
            },
            {
                "id": "cache",
                "display": "Cache",
                "type": "helper",
            },
        ]
        statuses = {
            "web": {
                "label": "UP",
                "css": "ok",
                "raw": "healthy",
            },
            "database": {
                "label": "DOWN",
                "css": "bad",
                "raw": "stopped",
            },
            "media": {
                "label": "UPDATE",
                "css": "info",
                "raw": "update available",
            },
            "cache": {
                "label": "UNKNOWN",
                "css": "info",
                "raw": "-",
            },
        }

        card = build_public_services_summary_card(
            services,
            statuses,
        )

        self.assertIn(
            "2 Apps · 2 Helpers · 1 UP · 1 DOWN"
            " · 1 UPDATE · 1 INFO",
            card,
        )
        self.assertIn("summary-card bad", card)
        self.assertIn("Web", card)
        self.assertIn("Database", card)
        self.assertIn("Media", card)
        self.assertIn("Cache", card)


class FourCardSummaryPreviewTests(unittest.TestCase):
    def setUp(self):
        self.hosts = [
            {
                "id": "collector",
                "display_name": "Utility Node",
                "type": "linux",
                "enabled": True,
            }
        ]
        self.web_statuses = {
            "collector": {
                "label": "OK",
                "css": "ok",
                "raw": "HTTP 200",
            }
        }
        self.storage_checks = [
            {
                "id": "root",
                "label": "Root",
            }
        ]
        self.storage_statuses = {
            "root": {
                "label": "OK",
                "css": "ok",
                "raw": "42%",
            }
        }
        self.relationships = [
            {
                "id": "backup",
                "name": "Primary Backup",
            }
        ]
        self.protection_statuses = {
            "backup": {
                "label": "CONFIGURED",
                "css": "ok",
                "raw": "ready",
            }
        }
        self.services = [
            {
                "id": "web",
                "host": "collector",
                "display": "Web",
                "type": "app",
                "check": "http",
            }
        ]
        self.service_statuses = {
            "web": {
                "label": "UP",
                "css": "ok",
                "raw": "HTTP 200",
            }
        }

    def render(self, summary_cards):
        return build_public_four_card_summary_preview(
            self.hosts,
            self.web_statuses,
            self.storage_checks,
            self.storage_statuses,
            self.relationships,
            self.protection_statuses,
            self.services,
            self.service_statuses,
            summary_cards,
        )

    def test_selected_cards_follow_normalized_order(self):
        preview = self.render(
            [
                "services",
                "systems",
                "SERVICES",
                "unknown",
                "storage",
            ]
        )

        self.assertIn(
            "Active cards: Services · Systems · Storage",
            preview,
        )
        self.assertLess(
            preview.index('<div class="title">Services</div>'),
            preview.index('<div class="title">Systems</div>'),
        )
        self.assertLess(
            preview.index('<div class="title">Systems</div>'),
            preview.index('<div class="title">Storage</div>'),
        )
        self.assertNotIn(
            '<div class="title">Protection</div>',
            preview,
        )

    def test_invalid_selection_renders_default_four_cards(self):
        preview = self.render(["unknown"])

        self.assertIn(
            "Active cards: Systems · Storage · Protection · Services",
            preview,
        )
        self.assertIn('<div class="title">Systems</div>', preview)
        self.assertIn('<div class="title">Storage</div>', preview)
        self.assertIn('<div class="title">Protection</div>', preview)
        self.assertIn('<div class="title">Services</div>', preview)


class SystemsSummaryHostHealthTests(unittest.TestCase):
    def setUp(self):
        self.host = {
            "id": "t620",
            "type": "truenas",
            "display_name": "T620 TrueNAS",
            "enabled": True,
        }
        self.web_ok = {
            "label": "OK",
            "css": "ok",
            "raw": "HTTP 200",
        }

    def test_unreachable_services_override_healthy_web_ui(self):
        services = [
            {
                "id": "jellyfin",
                "host": "t620",
                "check": "truenas_app",
            },
            {
                "id": "redis",
                "host": "t620",
                "check": "truenas_app",
            },
        ]
        statuses = {
            "jellyfin": {
                "label": "UNKNOWN",
                "raw": "Connection timed out",
            },
            "redis": {
                "label": "UNKNOWN",
                "raw": "Connection timed out",
            },
        }

        result = config_system_host_status(
            self.host,
            services,
            statuses,
            self.web_ok,
        )

        self.assertEqual(result["label"], "UNREACHABLE")
        self.assertEqual(result["css"], "bad")

        card = build_public_systems_summary_card(
            [self.host],
            {"t620": self.web_ok},
            services,
            statuses,
        )

        self.assertIn("1 Systems · 0 OK · 1 DOWN", card)
        self.assertIn("UNREACHABLE", card)
        self.assertIn("summary-card bad", card)

    def test_healthy_app_status_preserves_web_ui_status(self):
        services = [
            {
                "id": "jellyfin",
                "host": "t620",
                "check": "truenas_app",
            }
        ]
        statuses = {
            "jellyfin": {
                "label": "UP",
                "raw": "RUNNING",
            }
        }

        result = config_system_host_status(
            self.host,
            services,
            statuses,
            self.web_ok,
        )

        self.assertEqual(result, self.web_ok)

        card = build_public_systems_summary_card(
            [self.host],
            {"t620": self.web_ok},
            services,
            statuses,
        )

        self.assertIn("1 Systems · 1 OK · 0 DOWN", card)
        self.assertNotIn("UNREACHABLE", card)

    def test_authentication_error_preserves_web_ui_status(self):
        services = [
            {
                "id": "jellyfin",
                "host": "t620",
                "check": "truenas_app",
            }
        ]
        statuses = {
            "jellyfin": {
                "label": "UNKNOWN",
                "raw": "Permission denied (publickey)",
            }
        }

        result = config_system_host_status(
            self.host,
            services,
            statuses,
            self.web_ok,
        )

        self.assertEqual(result, self.web_ok)

    def test_mixed_http_and_truenas_checks_follow_host_collapse_rule(self):
        services = [
            {
                "id": "jellyfin",
                "host": "t620",
                "check": "truenas_app",
            },
            {
                "id": "web-ui-service",
                "host": "t620",
                "check": "http",
            },
        ]
        statuses = {
            "jellyfin": {
                "label": "UNKNOWN",
                "raw": "Operation timed out",
            },
            "web-ui-service": {
                "label": "UP",
                "raw": "HTTP 200",
            },
        }

        result = config_system_host_status(
            self.host,
            services,
            statuses,
            self.web_ok,
        )

        self.assertEqual(result["label"], "UNREACHABLE")
        self.assertEqual(result["css"], "bad")


if __name__ == "__main__":
    unittest.main()
