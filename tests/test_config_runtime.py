#!/usr/bin/env python3

import ast
import html
import unittest
from datetime import datetime, timedelta
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
    "build_config_truenas_snapshot_preview",
    "build_config_truenas_replication_preview",
    "freshness_status",
    "config_replication_status",
    "collect_config_truenas_snapshot_checks",
    "collect_config_truenas_replication_checks",
    "parse_cron_field",
    "parse_clock",
    "inside_window",
    "matches_schedule",
    "previous_run",
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
        "datetime": datetime,
        "timedelta": timedelta,
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
build_config_truenas_snapshot_preview = FUNCTIONS[
    "build_config_truenas_snapshot_preview"
]
build_config_truenas_replication_preview = FUNCTIONS[
    "build_config_truenas_replication_preview"
]
freshness_status = FUNCTIONS[
    "freshness_status"
]
config_replication_status = FUNCTIONS[
    "config_replication_status"
]
collect_config_truenas_snapshot_checks = FUNCTIONS[
    "collect_config_truenas_snapshot_checks"
]
collect_config_truenas_replication_checks = FUNCTIONS[
    "collect_config_truenas_replication_checks"
]
parse_cron_field = FUNCTIONS[
    "parse_cron_field"
]
inside_window = FUNCTIONS[
    "inside_window"
]
matches_schedule = FUNCTIONS[
    "matches_schedule"
]
previous_run = FUNCTIONS[
    "previous_run"
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


class CronFieldParsingTests(unittest.TestCase):
    def test_wildcard_and_empty_values_cover_full_range(self):
        expected = set(range(0, 60))

        self.assertEqual(
            parse_cron_field("*", 0, 59),
            expected,
        )
        self.assertEqual(
            parse_cron_field("", 0, 59),
            expected,
        )

    def test_lists_ranges_steps_and_bounds_are_normalized(self):
        self.assertEqual(
            parse_cron_field(
                "0,15,30-34/2,99",
                0,
                59,
            ),
            {0, 15, 30, 32, 34},
        )

    def test_wildcard_steps_and_nonzero_minimum(self):
        self.assertEqual(
            parse_cron_field("*/20", 0, 59),
            {0, 20, 40},
        )
        self.assertEqual(
            parse_cron_field("1-7/2", 1, 7),
            {1, 3, 5, 7},
        )


class ScheduleWindowTests(unittest.TestCase):
    def test_normal_window_is_inclusive(self):
        self.assertTrue(
            inside_window(
                datetime(2026, 6, 8, 8, 0),
                "08:00",
                "17:00",
            )
        )
        self.assertTrue(
            inside_window(
                datetime(2026, 6, 8, 17, 0),
                "08:00",
                "17:00",
            )
        )
        self.assertFalse(
            inside_window(
                datetime(2026, 6, 8, 7, 59),
                "08:00",
                "17:00",
            )
        )

    def test_overnight_window_wraps_across_midnight(self):
        self.assertTrue(
            inside_window(
                datetime(2026, 6, 8, 23, 30),
                "22:00",
                "06:00",
            )
        )
        self.assertTrue(
            inside_window(
                datetime(2026, 6, 9, 5, 30),
                "22:00",
                "06:00",
            )
        )
        self.assertFalse(
            inside_window(
                datetime(2026, 6, 9, 12, 0),
                "22:00",
                "06:00",
            )
        )

    def test_equal_begin_and_end_matches_only_that_minute(self):
        self.assertTrue(
            inside_window(
                datetime(2026, 6, 8, 12, 30),
                "12:30",
                "12:30",
            )
        )
        self.assertFalse(
            inside_window(
                datetime(2026, 6, 8, 12, 31),
                "12:30",
                "12:30",
            )
        )


class ScheduleMatchingTests(unittest.TestCase):
    def test_matching_schedule_checks_all_fields(self):
        candidate = datetime(2026, 6, 8, 14, 30)

        schedule = {
            "minute": "30",
            "hour": "14",
            "dom": "8",
            "month": "6",
            "dow": "1",
            "begin": "14:00",
            "end": "15:00",
        }

        self.assertTrue(
            matches_schedule(candidate, schedule)
        )

    def test_truenas_weekday_mapping_uses_monday_one_sunday_seven(self):
        monday = datetime(2026, 6, 8, 14, 30)
        sunday = datetime(2026, 6, 7, 14, 30)

        monday_schedule = {
            "minute": "30",
            "hour": "14",
            "dow": "1",
        }
        sunday_schedule = {
            "minute": "30",
            "hour": "14",
            "dow": "7",
        }

        self.assertTrue(
            matches_schedule(monday, monday_schedule)
        )
        self.assertFalse(
            matches_schedule(sunday, monday_schedule)
        )
        self.assertTrue(
            matches_schedule(sunday, sunday_schedule)
        )

    def test_time_window_can_reject_otherwise_matching_cron_fields(self):
        candidate = datetime(2026, 6, 8, 14, 30)

        schedule = {
            "minute": "30",
            "hour": "14",
            "begin": "15:00",
            "end": "16:00",
        }

        self.assertFalse(
            matches_schedule(candidate, schedule)
        )


class PreviousRunTests(unittest.TestCase):
    class FrozenDateTime(datetime):
        current = datetime(2026, 6, 8, 14, 37)

        @classmethod
        def now(cls, tz=None):
            return cls.current

    def setUp(self):
        self.original_datetime = FUNCTIONS.get("datetime")
        FUNCTIONS["datetime"] = self.FrozenDateTime

    def tearDown(self):
        if self.original_datetime is None:
            FUNCTIONS.pop("datetime", None)
        else:
            FUNCTIONS["datetime"] = self.original_datetime

    def test_current_minute_is_returned_when_it_matches(self):
        self.FrozenDateTime.current = datetime(
            2026,
            6,
            8,
            14,
            37,
            42,
        )

        result = previous_run(
            {
                "minute": "37",
                "hour": "14",
            }
        )

        self.assertEqual(
            result,
            datetime(2026, 6, 8, 14, 37),
        )

    def test_searches_back_to_previous_matching_minute(self):
        self.FrozenDateTime.current = datetime(
            2026,
            6,
            8,
            14,
            37,
        )

        result = previous_run(
            {
                "minute": "30",
                "hour": "14",
            }
        )

        self.assertEqual(
            result,
            datetime(2026, 6, 8, 14, 30),
        )

    def test_search_crosses_midnight(self):
        self.FrozenDateTime.current = datetime(
            2026,
            6,
            8,
            0,
            3,
        )

        result = previous_run(
            {
                "minute": "55",
                "hour": "23",
            }
        )

        self.assertEqual(
            result,
            datetime(2026, 6, 7, 23, 55),
        )


class SnapshotCollectorTests(unittest.TestCase):
    dependency_names = (
        "remote_json",
        "collect_snapshots",
        "latest_snapshot",
        "freshness_status",
        "short_snapshot",
        "fmt_dt",
    )

    def setUp(self):
        self.original_dependencies = {
            name: FUNCTIONS.get(name)
            for name in self.dependency_names
        }

    def tearDown(self):
        for name, value in self.original_dependencies.items():
            if value is None:
                FUNCTIONS.pop(name, None)
            else:
                FUNCTIONS[name] = value

    @staticmethod
    def host(address="192.0.2.10"):
        return {
            "id": "t620",
            "display_name": "T620 TrueNAS",
            "address": address,
        }

    def test_missing_address_returns_unknown_row_and_error(self):
        rows, errors = collect_config_truenas_snapshot_checks(
            [self.host(address=None)]
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["host_id"], "t620")
        self.assertEqual(rows[0]["task_enabled"], None)
        self.assertEqual(rows[0]["label"], "UNKNOWN")
        self.assertEqual(rows[0]["raw"], "missing host address")
        self.assertEqual(errors, ["t620: missing host address"])

    def test_query_failure_and_malformed_response_return_error_rows(self):
        cases = [
            (
                (None, "SSH connection timed out"),
                "snapshot task query failed",
                "t620: SSH connection timed out",
            ),
            (
                ({"unexpected": "mapping"}, None),
                "unexpected snapshot task response",
                "t620: snapshot task query did not return a list",
            ),
        ]

        for remote_result, expected_raw, expected_error in cases:
            with self.subTest(remote_result=remote_result):
                FUNCTIONS["remote_json"] = (
                    lambda ip, command, result=remote_result: result
                )

                rows, errors = collect_config_truenas_snapshot_checks(
                    [self.host()]
                )

                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["task_enabled"], None)
                self.assertEqual(rows[0]["label"], "UNKNOWN")
                self.assertEqual(rows[0]["raw"], expected_raw)
                self.assertEqual(errors, [expected_error])

    def test_empty_task_inventory_returns_info_row(self):
        FUNCTIONS["remote_json"] = lambda ip, command: ([], None)
        FUNCTIONS["collect_snapshots"] = lambda ip: ({}, None)

        rows, errors = collect_config_truenas_snapshot_checks(
            [self.host()]
        )

        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["task_enabled"], None)
        self.assertEqual(rows[0]["label"], "INFO")
        self.assertEqual(
            rows[0]["raw"],
            "no snapshot tasks configured",
        )

    def test_snapshot_inventory_failure_marks_tasks_unknown(self):
        FUNCTIONS["remote_json"] = lambda ip, command: (
            [
                {
                    "dataset": "tank/apps",
                    "enabled": True,
                }
            ],
            None,
        )
        FUNCTIONS["collect_snapshots"] = lambda ip: (
            {},
            "zfs snapshot query failed",
        )
        FUNCTIONS["short_snapshot"] = lambda name: "-"
        FUNCTIONS["fmt_dt"] = lambda value: "-"

        rows, errors = collect_config_truenas_snapshot_checks(
            [self.host()]
        )

        self.assertEqual(
            errors,
            ["t620: zfs snapshot query failed"],
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["dataset"], "tank/apps")
        self.assertTrue(rows[0]["task_enabled"])
        self.assertEqual(rows[0]["label"], "UNKNOWN")
        self.assertEqual(rows[0]["css"], "info")
        self.assertEqual(
            rows[0]["raw"],
            "snapshot inventory query failed",
        )

    def test_successful_tasks_are_sorted_and_assembled(self):
        apps_dt = datetime(2026, 6, 7, 11, 55)
        media_dt = datetime(2026, 6, 7, 11, 50)

        FUNCTIONS["remote_json"] = lambda ip, command: (
            [
                {
                    "dataset": "tank/media",
                    "enabled": False,
                },
                {
                    "dataset": "tank/apps",
                    "enabled": True,
                },
            ],
            None,
        )
        FUNCTIONS["collect_snapshots"] = lambda ip: (
            {"inventory": "available"},
            None,
        )

        latest_by_dataset = {
            "tank/apps": ("tank/apps@auto-apps", apps_dt),
            "tank/media": ("tank/media@auto-media", media_dt),
        }
        FUNCTIONS["latest_snapshot"] = (
            lambda snapshots, dataset: latest_by_dataset[dataset]
        )
        FUNCTIONS["freshness_status"] = (
            lambda task, latest_dt: (
                ("OK", "ok", "fresh enough")
                if task.get("enabled")
                else (
                    "DISABLED",
                    "disabled",
                    "snapshot task disabled",
                )
            )
        )
        FUNCTIONS["short_snapshot"] = (
            lambda name: name.split("@", 1)[1]
        )
        FUNCTIONS["fmt_dt"] = (
            lambda value: value.strftime("%Y-%m-%d %H:%M")
        )

        rows, errors = collect_config_truenas_snapshot_checks(
            [self.host()]
        )

        self.assertEqual(errors, [])
        self.assertEqual(
            [row["dataset"] for row in rows],
            ["tank/apps", "tank/media"],
        )
        self.assertEqual(rows[0]["latest"], "auto-apps")
        self.assertEqual(
            rows[0]["latest_time"],
            "2026-06-07 11:55",
        )
        self.assertEqual(rows[0]["label"], "OK")
        self.assertTrue(rows[0]["task_enabled"])
        self.assertEqual(rows[1]["latest"], "auto-media")
        self.assertEqual(rows[1]["label"], "DISABLED")
        self.assertFalse(rows[1]["task_enabled"])


class ReplicationCollectorTests(unittest.TestCase):
    dependency_names = (
        "remote_json",
        "config_replication_status",
        "parse_datetime",
        "fmt_dt",
    )

    def setUp(self):
        self.original_dependencies = {
            name: FUNCTIONS.get(name)
            for name in self.dependency_names
        }

    def tearDown(self):
        for name, value in self.original_dependencies.items():
            if value is None:
                FUNCTIONS.pop(name, None)
            else:
                FUNCTIONS[name] = value

    @staticmethod
    def host(address="192.0.2.10"):
        return {
            "id": "t620",
            "display_name": "T620 TrueNAS",
            "address": address,
        }

    def test_missing_address_returns_unknown_row_and_error(self):
        rows, errors = collect_config_truenas_replication_checks(
            [self.host(address=None)]
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["host_id"], "t620")
        self.assertEqual(rows[0]["task_enabled"], None)
        self.assertEqual(rows[0]["label"], "UNKNOWN")
        self.assertEqual(rows[0]["raw"], "missing host address")
        self.assertEqual(errors, ["t620: missing host address"])

    def test_query_failure_and_malformed_response_return_error_rows(self):
        cases = [
            (
                (None, "No route to host"),
                "replication task query failed",
                "t620: No route to host",
            ),
            (
                ({"unexpected": "mapping"}, None),
                "unexpected replication task response",
                "t620: replication task query did not return a list",
            ),
        ]

        for remote_result, expected_raw, expected_error in cases:
            with self.subTest(remote_result=remote_result):
                FUNCTIONS["remote_json"] = (
                    lambda ip, command, result=remote_result: result
                )

                rows, errors = collect_config_truenas_replication_checks(
                    [self.host()]
                )

                self.assertEqual(len(rows), 1)
                self.assertEqual(rows[0]["task_enabled"], None)
                self.assertEqual(rows[0]["label"], "UNKNOWN")
                self.assertEqual(rows[0]["raw"], expected_raw)
                self.assertEqual(errors, [expected_error])

    def test_empty_task_inventory_returns_info_row(self):
        FUNCTIONS["remote_json"] = lambda ip, command: ([], None)

        rows, errors = collect_config_truenas_replication_checks(
            [self.host()]
        )

        self.assertEqual(errors, [])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["task_enabled"], None)
        self.assertEqual(rows[0]["label"], "INFO")
        self.assertEqual(
            rows[0]["raw"],
            "no replication tasks configured",
        )

    def test_successful_tasks_are_sorted_and_normalized(self):
        FUNCTIONS["remote_json"] = lambda ip, command: (
            [
                {
                    "id": 20,
                    "name": "Zeta replication",
                    "enabled": False,
                    "direction": "push",
                    "transport": "ssh",
                    "source_datasets": "tank/media",
                    "target_dataset": "backup/t620/media",
                    "state": {
                        "state": "PAUSED",
                        "datetime": "zeta-time",
                        "last_snapshot": "tank/media@zeta",
                    },
                },
                {
                    "name": "alpha replication",
                    "enabled": True,
                    "direction": "pull",
                    "transport": "local",
                    "source_datasets": [
                        "tank/apps",
                        "",
                    ],
                    "target_dataset": "backup/t620/apps",
                    "state": {
                        "state": "FINISHED",
                        "datetime": "alpha-time",
                        "last_snapshot": "tank/apps@alpha",
                    },
                },
            ],
            None,
        )
        FUNCTIONS["parse_datetime"] = (
            lambda value: f"parsed:{value}"
        )
        FUNCTIONS["fmt_dt"] = (
            lambda value: f"formatted:{value}"
        )
        FUNCTIONS["config_replication_status"] = (
            config_replication_status
        )

        rows, errors = collect_config_truenas_replication_checks(
            [self.host()]
        )

        self.assertEqual(errors, [])
        self.assertEqual(
            [row["name"] for row in rows],
            ["alpha replication", "Zeta replication"],
        )

        alpha, zeta = rows

        self.assertEqual(alpha["task_id"], "1")
        self.assertTrue(alpha["task_enabled"])
        self.assertEqual(alpha["direction"], "PULL")
        self.assertEqual(alpha["transport"], "LOCAL")
        self.assertEqual(alpha["source_datasets"], ["tank/apps"])
        self.assertEqual(alpha["execution_state"], "FINISHED")
        self.assertEqual(alpha["label"], "OK")
        self.assertEqual(
            alpha["execution_time"],
            "formatted:parsed:alpha-time",
        )
        self.assertEqual(
            alpha["last_snapshot"],
            "tank/apps@alpha",
        )

        self.assertEqual(zeta["task_id"], "20")
        self.assertFalse(zeta["task_enabled"])
        self.assertEqual(zeta["direction"], "PUSH")
        self.assertEqual(zeta["transport"], "SSH")
        self.assertEqual(
            zeta["source_datasets"],
            ["tank/media"],
        )
        self.assertEqual(zeta["execution_state"], "PAUSED")
        self.assertEqual(zeta["label"], "DISABLED")
        self.assertEqual(zeta["css"], "disabled")
        self.assertEqual(
            zeta["raw"],
            "replication task disabled",
        )


class SnapshotFreshnessStatusTests(unittest.TestCase):
    def setUp(self):
        self.previous_run = datetime(2026, 6, 7, 12, 0)
        self.original_previous_run = FUNCTIONS.get("previous_run")
        FUNCTIONS["previous_run"] = lambda schedule: self.previous_run

    def tearDown(self):
        if self.original_previous_run is None:
            FUNCTIONS.pop("previous_run", None)
        else:
            FUNCTIONS["previous_run"] = self.original_previous_run

    def test_missing_task_is_unknown(self):
        self.assertEqual(
            freshness_status(None, None),
            ("UNKNOWN", "warning", "-"),
        )

    def test_disabled_task_takes_precedence(self):
        self.assertEqual(
            freshness_status(
                {"enabled": False},
                self.previous_run,
            ),
            (
                "DISABLED",
                "disabled",
                "snapshot task disabled",
            ),
        )

    def test_enabled_task_without_snapshot_is_missing(self):
        self.assertEqual(
            freshness_status(
                {"enabled": True},
                None,
            ),
            (
                "MISSING",
                "bad",
                "no snapshot found",
            ),
        )

    def test_unavailable_previous_run_is_unknown(self):
        FUNCTIONS["previous_run"] = lambda schedule: None

        self.assertEqual(
            freshness_status(
                {
                    "enabled": True,
                    "schedule": {"hour": "12"},
                },
                self.previous_run,
            ),
            (
                "UNKNOWN",
                "warning",
                "cannot calculate previous run",
            ),
        )

    def test_snapshot_at_five_minute_grace_boundary_is_ok(self):
        latest = self.previous_run - timedelta(minutes=5)

        self.assertEqual(
            freshness_status(
                {
                    "enabled": True,
                    "schedule": {"hour": "12"},
                },
                latest,
            ),
            (
                "OK",
                "ok",
                "fresh enough",
            ),
        )

    def test_older_snapshot_with_allow_empty_false_is_ok(self):
        latest = self.previous_run - timedelta(hours=2)

        self.assertEqual(
            freshness_status(
                {
                    "enabled": True,
                    "allow_empty": False,
                    "schedule": {"hour": "12"},
                },
                latest,
            ),
            (
                "OK",
                "ok",
                "no changes since last schedule; allow_empty=false",
            ),
        )

    def test_older_snapshot_with_allow_empty_enabled_is_old(self):
        latest = self.previous_run - timedelta(hours=2)

        for allow_empty in (True, None):
            with self.subTest(allow_empty=allow_empty):
                task = {
                    "enabled": True,
                    "schedule": {"hour": "12"},
                }

                if allow_empty is not None:
                    task["allow_empty"] = allow_empty

                self.assertEqual(
                    freshness_status(task, latest),
                    (
                        "OLD",
                        "warning",
                        "older than last scheduled run",
                    ),
                )


class ReplicationStatusClassificationTests(unittest.TestCase):
    def test_disabled_task_takes_precedence(self):
        self.assertEqual(
            config_replication_status(
                {
                    "enabled": False,
                    "state": ["unexpected"],
                }
            ),
            (
                "DISABLED",
                "disabled",
                "replication task disabled",
            ),
        )

    def test_non_mapping_state_is_unknown(self):
        self.assertEqual(
            config_replication_status(
                {
                    "enabled": True,
                    "state": ["FAILED"],
                }
            ),
            (
                "UNKNOWN",
                "warning",
                "unexpected replication state response",
            ),
        )

    def test_success_states_are_ok(self):
        for state in ("FINISHED", "SUCCESS"):
            with self.subTest(state=state):
                self.assertEqual(
                    config_replication_status(
                        {
                            "enabled": True,
                            "state": {"state": state},
                        }
                    ),
                    (
                        "OK",
                        "ok",
                        "last execution finished",
                    ),
                )

    def test_active_states_are_informational(self):
        for state in ("RUNNING", "PENDING", "WAITING"):
            with self.subTest(state=state):
                self.assertEqual(
                    config_replication_status(
                        {
                            "enabled": True,
                            "state": {"state": state.lower()},
                        }
                    ),
                    (
                        state,
                        "info",
                        f"replication task is {state.lower()}",
                    ),
                )

    def test_paused_states_are_warnings(self):
        for state in ("HOLD", "PAUSED"):
            with self.subTest(state=state):
                self.assertEqual(
                    config_replication_status(
                        {
                            "enabled": True,
                            "state": {"state": state},
                        }
                    ),
                    (
                        state,
                        "warning",
                        f"replication task is {state.lower()}",
                    ),
                )

    def test_failure_states_use_reported_error(self):
        for state in ("FAILED", "ERROR", "ABORTED"):
            with self.subTest(state=state):
                self.assertEqual(
                    config_replication_status(
                        {
                            "enabled": True,
                            "state": {
                                "state": state,
                                "error": "remote transport failed",
                            },
                        }
                    ),
                    (
                        "CRITICAL",
                        "bad",
                        "remote transport failed",
                    ),
                )

    def test_failure_without_error_uses_state_fallback(self):
        self.assertEqual(
            config_replication_status(
                {
                    "enabled": True,
                    "state": {"state": "FAILED"},
                }
            ),
            (
                "CRITICAL",
                "bad",
                "last execution state: failed",
            ),
        )

    def test_missing_or_unrecognized_state_is_unknown(self):
        cases = [
            ({}, "execution state: unknown"),
            ({"state": {"state": "BROKEN"}}, "execution state: broken"),
        ]

        for task, expected_note in cases:
            with self.subTest(task=task):
                self.assertEqual(
                    config_replication_status(task),
                    (
                        "UNKNOWN",
                        "warning",
                        expected_note,
                    ),
                )


class SnapshotPreviewRenderingTests(unittest.TestCase):
    def test_empty_snapshot_rows_render_no_section(self):
        self.assertEqual(
            build_config_truenas_snapshot_preview([]),
            "",
        )

    def test_snapshot_preview_renders_counts_states_and_escaped_values(self):
        rows = [
            {
                "host_id": "t620",
                "host_name": "T620 <Primary>",
                "dataset": "tank/apps<prod>",
                "task_enabled": True,
                "label": "OK",
                "css": "ok",
                "latest": "auto<daily>",
                "latest_time": "2026-06-07 10:00",
                "raw": "fresh & current",
            },
            {
                "host_id": "t620",
                "host_name": "T620 <Primary>",
                "dataset": "tank/media",
                "task_enabled": False,
                "label": "DISABLED",
                "css": "info",
                "latest": "-",
                "latest_time": "-",
                "raw": "snapshot task disabled",
            },
            {
                "host_id": "t330",
                "host_name": "T330 Backup",
                "dataset": "-",
                "task_enabled": None,
                "label": "UNKNOWN",
                "css": "info",
                "latest": "-",
                "latest_time": "-",
                "raw": "snapshot query failed",
            },
        ]

        preview = build_config_truenas_snapshot_preview(rows)

        self.assertIn(
            "<h3>Configured TrueNAS Snapshot Tasks</h3>",
            preview,
        )
        self.assertIn("2 hosts · 2 tasks", preview)
        self.assertIn("T620 &lt;Primary&gt;", preview)
        self.assertIn("tank/apps&lt;prod&gt;", preview)
        self.assertIn("auto&lt;daily&gt;", preview)
        self.assertIn("2026-06-07 10:00", preview)
        self.assertIn("fresh &amp; current", preview)
        self.assertIn(">ENABLED</span>", preview)
        self.assertIn(">DISABLED</span>", preview)
        self.assertIn(">UNKNOWN</span>", preview)

    def test_snapshot_non_task_rows_are_excluded_from_task_count(self):
        rows = [
            {
                "host_id": "t620",
                "host_name": "T620",
                "dataset": "-",
                "task_enabled": None,
                "label": "INFO",
                "css": "info",
                "latest": "-",
                "latest_time": "-",
                "raw": "no snapshot tasks configured",
            },
            {
                "host_id": "t330",
                "host_name": "T330",
                "dataset": "-",
                "task_enabled": None,
                "label": "UNKNOWN",
                "css": "info",
                "latest": "-",
                "latest_time": "-",
                "raw": "snapshot task query failed",
            },
        ]

        preview = build_config_truenas_snapshot_preview(rows)

        self.assertIn("2 hosts · 0 tasks", preview)


class ReplicationPreviewRenderingTests(unittest.TestCase):
    def test_empty_replication_rows_render_no_section(self):
        self.assertEqual(
            build_config_truenas_replication_preview([]),
            "",
        )

    def test_replication_preview_renders_singular_counts_and_details(self):
        rows = [
            {
                "host_id": "t620",
                "host_name": "T620 <Primary>",
                "task_id": "12",
                "name": "T620 & T330 replication",
                "task_enabled": True,
                "direction": "PUSH",
                "transport": "SSH",
                "source_datasets": [
                    "tank/apps",
                    "tank/media<archive>",
                ],
                "target_dataset": "backup/t620/zfs-replication",
                "execution_state": "FINISHED",
                "execution_time": "2026-06-07 09:30",
                "last_snapshot": "auto-2026-06-07_09-00",
                "label": "OK",
                "css": "ok",
                "raw": "last execution finished & verified",
            },
        ]

        preview = build_config_truenas_replication_preview(rows)

        self.assertIn(
            "<h3>Configured TrueNAS Replication Tasks</h3>",
            preview,
        )
        self.assertIn("1 host · 1 task", preview)
        self.assertIn("T620 &lt;Primary&gt;", preview)
        self.assertIn("T620 &amp; T330 replication", preview)
        self.assertIn("tank/apps</span><br><span", preview)
        self.assertIn("tank/media&lt;archive&gt;", preview)
        self.assertIn("backup/t620/zfs-replication", preview)
        self.assertIn(">PUSH</span>", preview)
        self.assertIn(">SSH</span>", preview)
        self.assertIn(">ENABLED</span>", preview)
        self.assertIn(">FINISHED</span>", preview)
        self.assertIn("2026-06-07 09:30", preview)
        self.assertIn("auto-2026-06-07_09-00", preview)
        self.assertIn(
            "last execution finished &amp; verified",
            preview,
        )

    def test_replication_preview_renders_plural_counts_and_state_badges(self):
        rows = [
            {
                "host_id": "t620",
                "host_name": "T620",
                "task_id": "21",
                "name": "Paused replication",
                "task_enabled": False,
                "direction": "PUSH",
                "transport": "SSH",
                "source_datasets": ["tank/apps"],
                "target_dataset": "backup/t620/apps",
                "execution_state": "PAUSED",
                "execution_time": "-",
                "last_snapshot": "-",
                "label": "PAUSED",
                "css": "warning",
                "raw": "replication task is paused",
            },
            {
                "host_id": "t330",
                "host_name": "T330",
                "task_id": "22",
                "name": "Failed replication",
                "task_enabled": True,
                "direction": "PULL",
                "transport": "LOCAL",
                "source_datasets": ["backup/incoming"],
                "target_dataset": "backup/archive",
                "execution_state": "FAILED",
                "execution_time": "-",
                "last_snapshot": "-",
                "label": "CRITICAL",
                "css": "bad",
                "raw": "remote failure",
            },
            {
                "host_id": "t330",
                "host_name": "T330",
                "task_id": "-",
                "name": "-",
                "task_enabled": None,
                "direction": "-",
                "transport": "-",
                "source_datasets": [],
                "target_dataset": "-",
                "execution_state": "-",
                "execution_time": "-",
                "last_snapshot": "-",
                "label": "UNKNOWN",
                "css": "info",
                "raw": "replication query failed",
            },
        ]

        preview = build_config_truenas_replication_preview(rows)

        self.assertIn("2 hosts · 2 tasks", preview)
        self.assertIn(">DISABLED</span>", preview)
        self.assertIn(">PAUSED</span>", preview)
        self.assertIn(">FAILED</span>", preview)
        self.assertIn(">CRITICAL</span>", preview)
        self.assertIn("replication query failed", preview)


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
