#!/usr/bin/env python3

import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
RUNNER = REPO_ROOT / "scripts" / "run-public-production.sh"
SERVICE = REPO_ROOT / "systemd" / "sanity-node-generate.service"
TIMER = REPO_ROOT / "systemd" / "sanity-node-generate.timer"
WEB_SERVICE = REPO_ROOT / "systemd" / "sanity-node-web.service"


class PublicProductionRunnerTests(unittest.TestCase):
    def make_executable(self, path, content):
        path.write_text(
            textwrap.dedent(content).lstrip(),
            encoding="utf-8",
        )
        path.chmod(0o755)

    def make_runtime(self, runtime_mode="public"):
        temporary = tempfile.TemporaryDirectory()
        base = Path(temporary.name)

        root = base / "production"
        app = root / "app"
        scripts = app / "scripts"

        reference = base / "reference"
        rehearsal = base / "rehearsal"

        scripts.mkdir(parents=True)
        (root / "config").mkdir()
        (root / "html").mkdir()
        (root / "logs").mkdir()
        reference.mkdir()
        rehearsal.mkdir()

        reference_sentinel = reference / "sentinel.txt"
        rehearsal_sentinel = rehearsal / "sentinel.txt"

        reference_sentinel.write_text(
            "reference unchanged\n",
            encoding="utf-8",
        )
        rehearsal_sentinel.write_text(
            "rehearsal unchanged\n",
            encoding="utf-8",
        )

        config_path = root / "config" / "config.yaml"
        output_path = root / "html" / "index.html"
        log_path = root / "logs" / "generator.log"

        config_path.write_text(
            textwrap.dedent(
                f"""
                dashboard:
                  runtime_mode: {runtime_mode}
                  title: Sanity Node
                  subtitle: Production
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
            <section>Utility Node Services</section>
            <section>T330 Services</section>
            <section>T620 Services</section>
            <section id="public-systems-section"></section>
            <table><tr><th>Drive</th></tr></table>
            </body>
            </html>
            HTML

            echo "Wrote $SANITY_NODE_OUTPUT"
            """,
        )

        environment = os.environ.copy()
        environment.update(
            {
                "SANITY_NODE_PRODUCTION_ROOT": str(root),
                "SANITY_NODE_APP_ROOT": str(app),
                "SANITY_NODE_CONFIG": str(config_path),
                "SANITY_NODE_OUTPUT": str(output_path),
                "SANITY_NODE_LOG": str(log_path),
                "SANITY_NODE_REFERENCE_ROOT": str(reference),
                "SANITY_NODE_REHEARSAL_ROOT": str(rehearsal),
            }
        )

        return {
            "temporary": temporary,
            "base": base,
            "root": root,
            "app": app,
            "output": output_path,
            "log": log_path,
            "reference": reference,
            "rehearsal": rehearsal,
            "reference_sentinel": reference_sentinel,
            "rehearsal_sentinel": rehearsal_sentinel,
            "environment": environment,
        }

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
        self.addCleanup(runtime["temporary"].cleanup)

        result = self.run_runner(runtime["environment"])

        self.assertEqual(result.returncode, 0, result.stdout)

        output = runtime["output"]
        log = runtime["log"]

        self.assertTrue(output.is_file())
        self.assertGreater(output.stat().st_size, 0)
        self.assertEqual(output.stat().st_mode & 0o777, 0o664)

        html = output.read_text(encoding="utf-8")
        self.assertIn("Utility Node Services", html)
        self.assertIn("T330 Services", html)
        self.assertIn("T620 Services", html)
        self.assertIn("public-systems-section", html)
        self.assertIn("<th>Drive</th>", html)
        self.assertNotIn("Runtime Detail", html)
        self.assertNotIn("<h2>Details</h2>", html)
        self.assertNotIn("Config Preview", html)

        log_text = log.read_text(encoding="utf-8")
        self.assertIn(
            "Public production generation completed successfully",
            log_text,
        )
        self.assertIn("Output SHA-256:", log_text)
        self.assertRegex(
            log_text,
            r"Runtime seconds: \d+\.\d{3}",
        )

        self.assertEqual(
            list((runtime["root"] / "html").glob("index.html.next.*")),
            [],
        )

        self.assertEqual(
            runtime["reference_sentinel"].read_text(encoding="utf-8"),
            "reference unchanged\n",
        )
        self.assertEqual(
            runtime["rehearsal_sentinel"].read_text(encoding="utf-8"),
            "rehearsal unchanged\n",
        )

    def test_reference_mode_is_rejected(self):
        runtime = self.make_runtime(runtime_mode="reference")
        self.addCleanup(runtime["temporary"].cleanup)

        result = self.run_runner(runtime["environment"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "must set dashboard.runtime_mode: public",
            result.stdout,
        )
        self.assertFalse(runtime["output"].exists())

    def test_output_outside_production_root_is_rejected(self):
        runtime = self.make_runtime()
        self.addCleanup(runtime["temporary"].cleanup)

        escaped_output = runtime["base"] / "escaped-index.html"
        runtime["environment"]["SANITY_NODE_OUTPUT"] = str(
            escaped_output
        )

        result = self.run_runner(runtime["environment"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "runtime path escapes the production root",
            result.stdout,
        )
        self.assertFalse(escaped_output.exists())

    def test_production_root_overlapping_reference_is_rejected(self):
        runtime = self.make_runtime()
        self.addCleanup(runtime["temporary"].cleanup)

        runtime["environment"]["SANITY_NODE_REFERENCE_ROOT"] = str(
            runtime["root"]
        )

        result = self.run_runner(runtime["environment"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "production root overlaps a protected runtime root",
            result.stdout,
        )

    def test_production_root_overlapping_rehearsal_is_rejected(self):
        runtime = self.make_runtime()
        self.addCleanup(runtime["temporary"].cleanup)

        runtime["environment"]["SANITY_NODE_REHEARSAL_ROOT"] = str(
            runtime["root"]
        )

        result = self.run_runner(runtime["environment"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "production root overlaps a protected runtime root",
            result.stdout,
        )

    def test_failed_render_preserves_last_successful_output(self):
        runtime = self.make_runtime()
        self.addCleanup(runtime["temporary"].cleanup)

        previous_output = "last successful dashboard\n"
        runtime["output"].write_text(
            previous_output,
            encoding="utf-8",
        )

        generator = (
            runtime["app"]
            / "scripts"
            / "generate-dashboard.py"
        )

        self.make_executable(
            generator,
            """
            #!/usr/bin/env bash
            set -euo pipefail

            cat > "$SANITY_NODE_OUTPUT" <<'HTML'
            Utility Node Services
            T330 Services
            T620 Services
            public-systems-section
            <th>Drive</th>
            Config Preview
            HTML
            """,
        )

        result = self.run_runner(runtime["environment"])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn(
            "contains obsolete GUI marker: Config Preview",
            result.stdout,
        )
        self.assertEqual(
            runtime["output"].read_text(encoding="utf-8"),
            previous_output,
        )
        self.assertEqual(
            list((runtime["root"] / "html").glob("index.html.next.*")),
            [],
        )


class PublicProductionUnitContractTests(unittest.TestCase):
    def test_runner_has_valid_bash_syntax(self):
        result = subprocess.run(
            ["bash", "-n", str(RUNNER)],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stdout)

    def test_runner_contains_fail_closed_contract(self):
        text = RUNNER.read_text(encoding="utf-8")

        required = (
            "flock -n",
            "dashboard.runtime_mode: public",
            "Running startup preflight",
            "temporary_output=",
            "Utility Node Services",
            "T330 Services",
            "T620 Services",
            "public-systems-section",
            "<th>Drive</th>",
            "Config Preview",
            "chmod 0664",
            "mv -f",
            "LC_ALL=C awk",
            "Output SHA-256:",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_generation_service_is_hardened_and_generic(self):
        text = SERVICE.read_text(encoding="utf-8")

        required = (
            "User=sanity-node",
            "Group=sanity-node",
            "WorkingDirectory=/opt/sanity-node/app",
            "run-public-production.sh",
            "SANITY_NODE_PRODUCTION_ROOT=/opt/sanity-node",
            "SANITY_NODE_REFERENCE_ROOT=/opt/homelab-dashboard",
            (
                "SANITY_NODE_REHEARSAL_ROOT="
                "/opt/sanity-node-public-rehearsal"
            ),
            (
                "ReadOnlyPaths=-/opt/homelab-dashboard "
                "-/opt/sanity-node-public-rehearsal"
            ),
            "ReadWritePaths=/opt/sanity-node",
            "NoNewPrivileges=true",
            "PrivateTmp=true",
            "ProtectSystem=full",
            "ProtectHome=read-only",
            "RestrictSUIDSGID=true",
            "LockPersonality=true",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

        self.assertNotIn("User=controls", text)
        self.assertNotIn("Group=controls", text)
        self.assertNotIn("homelab-dashboard-generate", text)

    def test_timer_has_permanent_five_minute_contract(self):
        text = TIMER.read_text(encoding="utf-8")

        required = (
            "Unit=sanity-node-generate.service",
            "OnBootSec=1min",
            "OnUnitActiveSec=5min",
            "AccuracySec=1s",
            "RandomizedDelaySec=0",
            "Persistent=true",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

        self.assertNotIn("public-rehearsal", text)
        self.assertNotIn("homelab-dashboard-generate", text)

    def test_web_service_serves_only_permanent_output(self):
        text = WEB_SERVICE.read_text(encoding="utf-8")

        required = (
            "User=sanity-node",
            "Group=sanity-node",
            "After=network-online.target",
            "Wants=network-online.target",
            "ConditionPathExists=/opt/sanity-node/html/index.html",
            "WorkingDirectory=/opt/sanity-node/html",
            "ExecStartPre=/usr/bin/test -s /opt/sanity-node/html/index.html",
            (
                "ExecStart=/usr/bin/python3 -m http.server 8088 "
                "--directory /opt/sanity-node/html"
            ),
            "ReadOnlyPaths=/opt/sanity-node",
            "NoNewPrivileges=true",
            "ProtectSystem=full",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

        self.assertNotIn("/opt/homelab-dashboard/html", text)
        self.assertNotIn("/opt/sanity-node-public-rehearsal/html", text)
        self.assertNotIn("sanity-node-generate.service", text)
        self.assertNotIn("User=controls", text)


if __name__ == "__main__":
    unittest.main()
