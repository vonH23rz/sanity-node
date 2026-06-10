import ast
import html
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPO_ROOT / "scripts" / "generate-dashboard.py"

FUNCTION_NAMES = {
    "cfg_get",
    "enabled_items",
    "h",
    "badge",
    "status_text_class",
    "info_item",
    "configured_host_key",
    "configured_host_display_name",
    "configured_host_sort_key",
    "config_system_info_empty_data",
    "config_system_info_display_os",
    "config_system_info_activity_value",
    "config_pool_integer",
    "config_format_bytes",
    "config_format_df_kib_blocks",
    "build_public_host_system_information_card",
    "build_public_host_storage_card",
    "build_public_host_operations_card",
    "build_public_host_system_rows",
}


def load_functions():
    source = GENERATOR.read_text(encoding="utf-8")
    parsed = ast.parse(source, filename=str(GENERATOR))

    selected_nodes = [
        node
        for node in parsed.body
        if isinstance(node, ast.FunctionDef)
        and node.name in FUNCTION_NAMES
    ]

    namespace = {
        "html": html,
        "CONFIG": {
            "collector": {
                "id": "collector",
            }
        },
    }

    exec(
        compile(
            ast.Module(body=selected_nodes, type_ignores=[]),
            filename=str(GENERATOR),
            mode="exec",
        ),
        namespace,
    )

    return namespace


FUNCTIONS = load_functions()
BUILDER = FUNCTIONS.get("build_public_host_system_rows")


class PublicHostSystemRowContractTests(unittest.TestCase):
    def test_renderer_exists(self):
        self.assertIsNotNone(
            BUILDER,
            "build_public_host_system_rows is not implemented yet",
        )


@unittest.skipIf(
    BUILDER is None,
    "host system-row renderer not implemented yet",
)
class PublicHostSystemRowRenderingTests(unittest.TestCase):
    def setUp(self):
        self.hosts = [
            {
                "id": "t620",
                "display_name": "T620 TrueNAS",
                "type": "truenas",
                "enabled": True,
            },
            {
                "id": "t330",
                "display_name": "T330 TrueNAS",
                "type": "truenas",
                "enabled": True,
            },
            {
                "id": "collector",
                "display_name": "Utility Node",
                "type": "linux",
                "enabled": True,
            },
        ]

        self.system_statuses = {
            "collector": {
                "label": "OK",
                "css": "ok",
                "host_type": "linux",
                "hostname": "controls",
                "os": "Ubuntu 26.04 LTS",
                "kernel": "7.0.0-test",
                "uptime": "up 1 day",
                "cpu_model": "Utility CPU",
                "cpu_cores": "8",
                "memory_total": "30 GiB",
                "load": "0.10, 0.20, 0.30",
                "activity": "containers",
                "containers_running": 8,
                "containers_total": 8,
                "raw": "collector-local system information collected",
            },
            "t330": {
                "label": "OK",
                "css": "ok",
                "host_type": "truenas",
                "hostname": "t330-truenas",
                "kernel": "6.12-test",
                "uptime": "up 2 days",
                "cpu_model": "T330 CPU",
                "cpu_cores": "8",
                "memory_total": "63 GiB",
                "load": "0.00, 0.01, 0.02",
                "activity": "apps",
                "apps_running": 0,
                "apps_total": 0,
                "raw": "remote system information collected",
            },
            "t620": {
                "label": "OK",
                "css": "ok",
                "host_type": "truenas",
                "hostname": "t620-truenas",
                "kernel": "6.12-test",
                "uptime": "up 3 days",
                "cpu_model": "T620 CPU",
                "cpu_cores": "32",
                "memory_total": "157 GiB",
                "load": "1.00, 1.10, 1.20",
                "activity": "apps",
                "apps_running": 11,
                "apps_total": 11,
                "raw": "remote system information collected",
            },
        }

        self.pool_rows = [
            {
                "host_key": "t330",
                "host_name": "T330 TrueNAS",
                "pool_name": "backup",
                "label": "OK",
                "css": "ok",
                "status": "ONLINE",
                "size_bytes": 10_000,
                "used_percent": 16.0,
            },
            {
                "host_key": "t620",
                "host_name": "T620 TrueNAS",
                "pool_name": "tank",
                "label": "OK",
                "css": "ok",
                "status": "ONLINE",
                "size_bytes": 20_000,
                "used_percent": 57.0,
            },
        ]

        self.disk_rows = [
            {
                "host_key": "t330",
                "pool_name": "backup",
                "label": "OK",
                "css": "ok",
                "temperature": {
                    "label": "OK",
                    "css": "ok",
                    "raw": "35°C avg / 36°C max",
                },
                "smart": {
                    "label": "OK",
                    "css": "ok",
                    "raw": "OK",
                },
            },
            {
                "host_key": "t620",
                "pool_name": "tank",
                "label": "OK",
                "css": "ok",
                "temperature": {
                    "label": "OK",
                    "css": "ok",
                    "raw": "30°C avg / 31°C max",
                },
                "smart": {
                    "label": "OK",
                    "css": "ok",
                    "raw": "OK",
                },
            },
        ]

        self.local_storage_checks = [
            {
                "id": "root",
                "host": "collector",
                "label": "Root",
                "mount": "/",
            },
            {
                "id": "vm-storage",
                "host": "collector",
                "label": "VM Storage",
                "mount": "/mnt/vm-storage",
            },
        ]

        self.local_storage_statuses = {
            "root": {
                "label": "OK",
                "css": "ok",
                "size": "1048576",
                "used": "262144",
                "available": "786432",
                "used_percent": 3,
            },
            "vm-storage": {
                "label": "OK",
                "css": "ok",
                "size": "2097152",
                "used": "524288",
                "available": "1572864",
                "used_percent": 3,
            },
        }

        self.backup_checks = [
            {
                "id": "utility-backup",
                "host": "collector",
                "name": "Utility Node Backup",
                "marker_file": "/private/marker",
            },
        ]

        self.backup_statuses = {
            "utility-backup": {
                "label": "OK",
                "css": "ok",
                "raw": "marker 2.0h old · timer active",
            },
        }

        self.snapshot_rows = [
            {
                "host_id": "t330",
                "host_name": "T330 TrueNAS",
                "dataset": "backup/admin",
                "task_enabled": True,
                "latest_time": "2026-06-10 00:00",
                "label": "OK",
                "css": "ok",
                "raw": "fresh enough",
            },
            {
                "host_id": "t620",
                "host_name": "T620 TrueNAS",
                "dataset": "tank/stacks",
                "task_enabled": True,
                "latest_time": "2026-06-10 00:00",
                "label": "OK",
                "css": "ok",
                "raw": "fresh enough",
            },
        ]

        self.replication_rows = [
            {
                "host_id": "t620",
                "host_name": "T620 TrueNAS",
                "name": "T620 to T330",
                "task_enabled": True,
                "execution_state": "FINISHED",
                "execution_time": "2026-06-10 00:05",
                "label": "OK",
                "css": "ok",
                "raw": "replication finished",
            },
        ]

    def render(self):
        return BUILDER(
            self.hosts,
            self.system_statuses,
            self.pool_rows,
            {},
            self.disk_rows,
            {},
            self.local_storage_checks,
            self.local_storage_statuses,
            self.backup_checks,
            self.backup_statuses,
            self.snapshot_rows,
            self.replication_rows,
        )

    def test_renders_three_rows_in_required_host_order(self):
        rendered = self.render()

        markers = [
            'data-system-row="collector"',
            'data-system-row="t330"',
            'data-system-row="t620"',
        ]

        self.assertEqual(rendered.count("data-system-row="), 3)

        positions = [
            rendered.index(marker)
            for marker in markers
        ]

        self.assertEqual(positions, sorted(positions))

    def test_utility_row_uses_local_storage_and_backup_cards(self):
        rendered = self.render()

        self.assertIn("Utility Node", rendered)
        self.assertIn("Local Storage", rendered)
        self.assertIn("Backup Status", rendered)

        for header in (
            "Drive",
            "Size",
            "Cap",
            "Used",
            "Free",
            "Health",
        ):
            self.assertIn(f"<th>{header}</th>", rendered)

        self.assertNotIn("<th>Mount</th>", rendered)
        self.assertIn("/mnt/vm-storage", rendered)
        self.assertIn("1.0 GiB", rendered)
        self.assertIn("256.0 MiB", rendered)
        self.assertIn("Utility Node Backup", rendered)

    def test_t330_row_uses_pool_and_snapshot_cards(self):
        rendered = self.render()

        self.assertIn("T330 TrueNAS", rendered)
        self.assertIn("Pool Status", rendered)
        self.assertIn("backup", rendered)
        self.assertIn("backup/admin", rendered)
        self.assertIn("Snapshot / Replication", rendered)

    def test_t620_row_combines_snapshot_and_replication_status(self):
        rendered = self.render()

        self.assertIn("T620 TrueNAS", rendered)
        self.assertIn("tank", rendered)
        self.assertIn("tank/stacks", rendered)
        self.assertIn("T620 to T330", rendered)
        self.assertIn("FINISHED", rendered)

    def test_rows_reuse_legacy_three_column_shell(self):
        rendered = self.render()

        self.assertEqual(
            rendered.count(
                'class="system-row three-column public-system-row"'
            ),
            3,
        )
        self.assertIn("System Information", rendered)
        self.assertNotIn("Configured System Information", rendered)


if __name__ == "__main__":
    unittest.main()
