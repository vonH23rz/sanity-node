#!/usr/bin/env python3

import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "run-public-rehearsal.sh"
SERVICE = (
    REPO_ROOT
    / "systemd"
    / "sanity-node-public-rehearsal.service"
)
TIMER = (
    REPO_ROOT
    / "systemd"
    / "sanity-node-public-rehearsal.timer"
)


class PublicRehearsalRunnerTests(unittest.TestCase):
    def make_executable(self, path, content):
        path.write_text(
            textwrap.dedent(content).lstrip(),
            encoding="utf-8",
        )
        path.chmod(0o755)

    def make_runtime(self, runtime_mode="public"):
        temporary = tempfile.TemporaryDirectory()
        base = Path(temporary.name)
        root = base / "rehearsal"
        app = root / "app"
        scripts = app / "scripts"

        scripts.mkdir(parents=True)
        (root / "config").mkdir()
        (root / "html").mkdir()
        (root / "logs").mkdir()

        config_path = root / "config" / "config.yaml"
        output_path = root / "html" / "index.html"
        log_path = root / "logs" / "generator.log"

        config_path.write_text(
            textwrap.dedent(
                f"""
                dashboard:
                  runtime_mode: {runtime_mode}
                  title: Sanity Node
                  subtitle: Rehearsal
                  refresh_minutes: 5

                collector:
                  id: collector
                  display_name: Collector
                  hostname: collector
                  type: linux

                hosts: []
                services: []
                protection: []
                local_storage: []
                backup_checks: []

                image_updates:
                  enabled: false
                  sources: []

                summary_cards:
                  - systems
                  - storage
                  - protection
                  - services
                """
            ).lstrip(),
            encoding="utf-8",
        )

        self.make_executable(
            scripts / "validate-config.py",
            """
            #!/usr/bin/env bash
            set -euo pipefail
            test -f "$1"
            echo "Validation result: 0 error(s), 0 warning(s)"
            """,
        )

        self.make_executable(
            scripts / "startup-preflight.py",
            """
            #!/usr/bin/env bash
            set -euo pipefail
            echo "Startup preflight passed."
            """,
        )

        self.make_executable(
            scripts / "generate-dashboard.py",
            """
            #!/usr/bin/env bash
            set -euo pipefail

            cat > "$SANITY_NODE_OUTPUT" <<'HTML'
            <!doctype html>
            <html>
            <body>
            <h2>Dashboard Summary</h2>
            <h2>Runtime Detail</h2>
            </body>
            </html>
            HTML

            echo "Wrote $SANITY_NODE_OUTPUT"
            """,
        )

        environment = os.environ.copy()
        environment.update(
            {
                "SANITY_NODE_REHEARSAL_ROOT": str(root),
                "SANITY_NODE_APP_ROOT": str(app),
                "SANITY_NODE_CONFIG": str(config_path),
                "SANITY_NODE_OUTPUT": str(output_path),
                "SANITY_NODE_LOG": str(log_path),
                "SANITY_NODE_PROTECTED_ROOT": str(
                    base / "protected-production"
                ),
            }
        )

        return (
            temporary,
            base,
            root,
            output_path,
            log_path,
            environment,
        )

    def run_runner(self, environment):
        return subprocess.run(
            [str(RUNNER)],
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

    def test_successful_run_atomically_publishes_output(self):
        runtime = self.make_runtime()
        temporary, _, root, output, log, environment = runtime
        self.addCleanup(temporary.cleanup)

        result = self.run_runner(environment)

        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertTrue(output.is_file())
        self.assertGreater(output.stat().st_size, 0)
        self.assertEqual(output.stat().st_mode & 0o777, 0o664)

        html = output.read_text(encoding="utf-8")
        self.assertIn("Dashboard Summary", html)
        self.assertIn("Runtime Detail", html)
        self.assertNotIn("Config Preview", html)

        log_text = log.read_text(encoding="utf-8")
        self.assertIn(
            "Public rehearsal generation completed successfully",
            log_text,
        )
        self.assertIn("Runtime seconds:", log_text)

        self.assertEqual(
            list((root / "html").glob("index.html.next.*")),
            [],
        )

    def test_reference_mode_is_rejected(self):
        runtime = self.make_runtime(runtime_mode="reference")
        temporary, _, _, output, _, environment = runtime
        self.addCleanup(temporary.cleanup)

        result = self.run_runner(environment)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "must set dashboard.runtime_mode: public",
            result.stdout,
        )
        self.assertFalse(output.exists())

    def test_output_outside_rehearsal_root_is_rejected(self):
        runtime = self.make_runtime()
        temporary, base, _, _, _, environment = runtime
        self.addCleanup(temporary.cleanup)

        escaped_output = base / "escaped-index.html"
        environment["SANITY_NODE_OUTPUT"] = str(escaped_output)

        result = self.run_runner(environment)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "runtime path escapes the rehearsal root",
            result.stdout,
        )
        self.assertFalse(escaped_output.exists())

    def test_rehearsal_root_overlapping_production_is_rejected(self):
        runtime = self.make_runtime()
        temporary, _, root, _, _, environment = runtime
        self.addCleanup(temporary.cleanup)

        environment["SANITY_NODE_PROTECTED_ROOT"] = str(root)

        result = self.run_runner(environment)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "rehearsal root overlaps the protected production root",
            result.stdout,
        )

    def test_obsolete_preview_wording_is_not_published(self):
        runtime = self.make_runtime()
        temporary, _, root, output, _, environment = runtime
        self.addCleanup(temporary.cleanup)

        generator = root / "app" / "scripts" / "generate-dashboard.py"
        self.make_executable(
            generator,
            """
            #!/usr/bin/env bash
            set -euo pipefail

            cat > "$SANITY_NODE_OUTPUT" <<'HTML'
            Dashboard Summary
            Runtime Detail
            Config Preview
            HTML
            """,
        )

        result = self.run_runner(environment)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "contains obsolete Config Preview wording",
            result.stdout,
        )
        self.assertFalse(output.exists())
        self.assertEqual(
            list((root / "html").glob("index.html.next.*")),
            [],
        )


class PublicRehearsalUnitContractTests(unittest.TestCase):
    def test_runner_has_valid_bash_syntax(self):
        result = subprocess.run(
            ["bash", "-n", str(RUNNER)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_service_template_is_isolated_and_generic(self):
        text = SERVICE.read_text(encoding="utf-8")

        required = (
            "User=sanity-node",
            "Group=sanity-node",
            "/opt/sanity-node-public-rehearsal",
            "SANITY_NODE_PROTECTED_ROOT=/opt/homelab-dashboard",
            "ReadOnlyPaths=/opt/homelab-dashboard",
            "ReadWritePaths=/opt/sanity-node-public-rehearsal",
            "run-public-rehearsal.sh",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

        self.assertNotIn("User=controls", text)
        self.assertNotIn("Group=controls", text)
        self.assertNotIn("homelab-dashboard-generate", text)

    def test_timer_uses_distinct_five_minute_schedule(self):
        text = TIMER.read_text(encoding="utf-8")

        self.assertIn(
            "Unit=sanity-node-public-rehearsal.service",
            text,
        )
        self.assertIn("OnUnitActiveSec=5min", text)
        self.assertIn("AccuracySec=1s", text)
        self.assertIn("Persistent=false", text)
        self.assertNotIn("homelab-dashboard-generate", text)


if __name__ == "__main__":
    unittest.main()
