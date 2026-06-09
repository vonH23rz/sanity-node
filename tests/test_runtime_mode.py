#!/usr/bin/env python3

import ast
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
GENERATOR = REPOSITORY_ROOT / "scripts" / "generate-dashboard.py"
VALIDATOR = REPOSITORY_ROOT / "scripts" / "validate-config.py"
STARTER = REPOSITORY_ROOT / "examples" / "config.starter.yaml"


def load_runtime_normalizer():
    source = GENERATOR.read_text()
    parsed = ast.parse(source, filename=str(GENERATOR))

    selected = []

    for node in parsed.body:
        if (
            isinstance(node, ast.Assign)
            and any(
                isinstance(target, ast.Name)
                and target.id == "SUPPORTED_RUNTIME_MODES"
                for target in node.targets
            )
        ):
            selected.append(node)

        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "normalize_runtime_mode"
        ):
            selected.append(node)

    if len(selected) != 2:
        raise RuntimeError(
            "Could not extract runtime-mode constant and normalizer"
        )

    module = ast.Module(body=selected, type_ignores=[])
    ast.fix_missing_locations(module)

    namespace = {}
    exec(
        compile(module, filename=str(GENERATOR), mode="exec"),
        namespace,
    )

    return namespace["normalize_runtime_mode"]


normalize_runtime_mode = load_runtime_normalizer()


class RuntimeModeNormalizationTests(unittest.TestCase):
    def test_missing_value_defaults_to_reference(self):
        self.assertEqual(
            normalize_runtime_mode(None),
            "reference",
        )

    def test_reference_mode_is_accepted_case_insensitively(self):
        self.assertEqual(
            normalize_runtime_mode(" Reference "),
            "reference",
        )

    def test_public_mode_is_accepted_case_insensitively(self):
        self.assertEqual(
            normalize_runtime_mode(" PUBLIC "),
            "public",
        )

    def test_invalid_value_fails_safe_to_reference(self):
        self.assertEqual(
            normalize_runtime_mode("mixed"),
            "reference",
        )


class RuntimeModeValidationTests(unittest.TestCase):
    def validate(self, content):
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = (
                Path(temporary_directory)
                / "config.yaml"
            )
            config_path.write_text(content)

            return subprocess.run(
                [
                    sys.executable,
                    str(VALIDATOR),
                    str(config_path),
                ],
                text=True,
                capture_output=True,
                check=False,
            )

    def starter_with_runtime_mode(self, value):
        content = STARTER.read_text()
        marker = "  runtime_mode: public\n"

        self.assertEqual(
            content.count(marker),
            1,
            "starter configuration runtime_mode marker changed",
        )

        return content.replace(
            marker,
            f"  runtime_mode: {value}\n",
            1,
        )

    def test_public_mode_passes_validation(self):
        result = self.validate(
            self.starter_with_runtime_mode("public")
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stdout + result.stderr,
        )

    def test_reference_mode_passes_validation(self):
        result = self.validate(
            self.starter_with_runtime_mode("reference")
        )

        self.assertEqual(
            result.returncode,
            0,
            result.stdout + result.stderr,
        )

    def test_missing_mode_passes_validation_for_compatibility(self):
        content = STARTER.read_text().replace(
            "  runtime_mode: public\n",
            "",
            1,
        )

        result = self.validate(content)

        self.assertEqual(
            result.returncode,
            0,
            result.stdout + result.stderr,
        )

    def test_invalid_mode_fails_validation(self):
        result = self.validate(
            self.starter_with_runtime_mode("mixed")
        )
        output = result.stdout + result.stderr

        self.assertEqual(result.returncode, 1, output)
        self.assertIn("dashboard.runtime_mode", output)
        self.assertIn("public", output)
        self.assertIn("reference", output)

    def test_non_string_mode_fails_validation(self):
        result = self.validate(
            self.starter_with_runtime_mode("123")
        )
        output = result.stdout + result.stderr

        self.assertEqual(result.returncode, 1, output)
        self.assertIn("dashboard.runtime_mode", output)
        self.assertIn("non-empty string", output)

    def test_remote_linux_system_info_requires_address_and_ssh(self):
        result = self.validate(
            """
dashboard:
  runtime_mode: public
collector:
  id: collector
  display_name: Collector
  hostname: collector
  type: linux
hosts:
  - id: collector
    enabled: true
    display_name: Collector
    hostname: collector
    type: linux
    modules:
      system_info: true
  - id: remote
    enabled: true
    display_name: Remote Linux
    hostname: remote
    type: linux
    modules:
      system_info: true
services: []
local_storage: []
backup_checks: []
protection: []
image_updates:
  enabled: false
  sources: []
"""
        )
        output = result.stdout + result.stderr

        self.assertEqual(result.returncode, 1, output)
        self.assertIn("hosts[1].address", output)
        self.assertIn("hosts[1].ssh", output)

    def test_remote_system_info_requires_explicit_ssh_enablement(self):
        result = self.validate(
            """
dashboard:
  runtime_mode: public
collector:
  id: collector
  display_name: Collector
  hostname: collector
  type: linux
hosts:
  - id: collector
    enabled: true
    display_name: Collector
    hostname: collector
    type: linux
    modules:
      system_info: true
  - id: nas
    enabled: true
    display_name: NAS
    hostname: nas
    address: 192.0.2.20
    type: truenas
    ssh:
      user: monitor
      key_file: /tmp/key
    modules:
      system_info: true
services: []
local_storage: []
backup_checks: []
protection: []
image_updates:
  enabled: false
  sources: []
"""
        )
        output = result.stdout + result.stderr

        self.assertEqual(result.returncode, 1, output)
        self.assertIn("hosts[1].ssh.enabled", output)
        self.assertIn("must be true", output)


class RuntimeModeFullRenderTests(unittest.TestCase):
    def render_starter(self, runtime_mode):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            config_path = root / "config.yaml"
            output_path = root / "index.html"
            command_marker = root / "external-commands.log"
            fake_bin = root / "bin"
            fake_bin.mkdir()

            config_content = STARTER.read_text()
            runtime_marker = "  runtime_mode: public\n"

            self.assertEqual(
                config_content.count(runtime_marker),
                1,
                "starter runtime_mode marker changed",
            )

            if runtime_mode is None:
                config_content = config_content.replace(
                    runtime_marker,
                    "",
                    1,
                )
            else:
                config_content = config_content.replace(
                    runtime_marker,
                    f"  runtime_mode: {runtime_mode}\n",
                    1,
                )

            config_path.write_text(config_content)

            fake_command = """#!/bin/sh
printf '%s\\n' "$0 $*" >> "$SANITY_NODE_COMMAND_MARKER"
exit 97
"""

            for command_name in ("ssh", "curl", "docker"):
                command_path = fake_bin / command_name
                command_path.write_text(fake_command)
                command_path.chmod(0o755)

            environment = os.environ.copy()
            environment.update(
                {
                    "SANITY_NODE_CONFIG": str(config_path),
                    "SANITY_NODE_OUTPUT": str(output_path),
                    "SANITY_NODE_COMMAND_MARKER": str(
                        command_marker
                    ),
                    "PATH": (
                        str(fake_bin)
                        + os.pathsep
                        + environment.get("PATH", "")
                    ),
                }
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(GENERATOR),
                ],
                cwd=REPOSITORY_ROOT,
                env=environment,
                text=True,
                capture_output=True,
                timeout=60,
                check=False,
            )

            rendered = (
                output_path.read_text()
                if output_path.exists()
                else ""
            )
            commands = (
                command_marker.read_text()
                if command_marker.exists()
                else ""
            )

            return result, rendered, commands

    def test_public_mode_skips_reference_collectors_and_output(self):
        result, rendered, commands = self.render_starter(
            "public"
        )
        output = result.stdout + result.stderr

        self.assertEqual(result.returncode, 0, output)
        self.assertTrue(rendered, output)
        self.assertIn(
            "Dashboard runtime mode: public",
            output,
        )
        self.assertIn(
            "Reference runtime collectors: skipped",
            output,
        )
        self.assertEqual(commands, "")

        self.assertIn(
            "Dashboard Summary",
            rendered,
        )
        self.assertIn(
            "System Overview",
            rendered,
        )
        self.assertIn(
            "Active cards: Systems · Storage · Protection · Services",
            rendered,
        )
        self.assertIn(
            "<h2>Details</h2>",
            rendered,
        )
        self.assertIn(
            "Runtime Detail",
            rendered,
        )
        self.assertIn(
            "Configured System Information",
            rendered,
        )
        self.assertIn(
            "collector-local system information collected",
            rendered,
        )
        self.assertIn(
            "1 Systems · 1 OK · 0 DOWN",
            rendered,
        )
        self.assertNotIn(
            '<div class="systems-list">',
            rendered,
        )

        for obsolete_label in (
            "Public Four-Card Preview",
            "Public Layout Preview",
            "Host-based summary direction",
            "Config Preview",
            "Preview only · existing summary cards unchanged",
            "<h2>1. Systems</h2>",
        ):
            self.assertNotIn(
                obsolete_label,
                rendered,
            )

        self.assertIn(
            "Overall Status: OK",
            rendered,
        )

        for personal_value in (
            "T330 Snapshot Tasks",
            "T620 Snapshot Tasks",
            "T620 Replication",
            "T620 Services",
            "Familienbudget",
            "Wiki.js Private",
            "192.168.30.10",
            "192.168.30.33",
        ):
            self.assertNotIn(
                personal_value,
                rendered,
            )

    def test_reference_mode_preserves_legacy_presentation(self):
        result, rendered, commands = self.render_starter(
            "reference"
        )
        output = result.stdout + result.stderr

        self.assertEqual(result.returncode, 0, output)
        self.assertTrue(rendered, output)
        self.assertTrue(commands.strip())

        for expected_label in (
            "Public Four-Card Preview",
            "Public Layout Preview",
            "Host-based summary direction",
            "Config Preview",
            "Preview only · existing summary cards unchanged",
            "<h2>1. Systems</h2>",
            '<div class="systems-list">',
        ):
            self.assertIn(
                expected_label,
                rendered,
            )

        self.assertNotIn(
            "Dashboard Summary",
            rendered,
        )
        self.assertNotIn(
            "<h2>Details</h2>",
            rendered,
        )

    def test_missing_mode_preserves_reference_runtime_default(self):
        result, rendered, commands = self.render_starter(
            None
        )
        output = result.stdout + result.stderr

        self.assertEqual(result.returncode, 0, output)
        self.assertTrue(rendered, output)
        self.assertIn(
            "Dashboard runtime mode: reference",
            output,
        )
        self.assertIn(
            "Reference runtime collectors: enabled",
            output,
        )
        self.assertTrue(
            commands.strip(),
            "reference mode did not invoke the fake collectors",
        )
        self.assertIn("ssh", commands)
        self.assertIn("docker", commands)

        self.assertIn(
            "\nimport json\nimport os\nimport subprocess\n",
            commands,
        )
        self.assertIn(
            "\nREMOTE_PY\n",
            commands,
        )
        self.assertNotIn(
            "\n    import json\n",
            commands,
        )

        self.assertIn(
            "T330 Snapshot Tasks",
            rendered,
        )
        self.assertIn(
            "T620 Snapshot Tasks",
            rendered,
        )
        self.assertIn(
            "T620 Replication",
            rendered,
        )
        self.assertIn(
            "T620 Services",
            rendered,
        )


if __name__ == "__main__":
    unittest.main()
