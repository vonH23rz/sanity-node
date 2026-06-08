#!/usr/bin/env python3
"""Regression tests for the safe first-run workspace bootstrap."""

from __future__ import annotations

import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
BOOTSTRAP = REPOSITORY_ROOT / "scripts" / "bootstrap-workspace.py"
VALIDATOR = REPOSITORY_ROOT / "scripts" / "validate-config.py"
PREFLIGHT = REPOSITORY_ROOT / "scripts" / "startup-preflight.py"
STARTER = REPOSITORY_ROOT / "examples" / "config.starter.yaml"


class BootstrapWorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(
            prefix="sanity-node-bootstrap-test-"
        )
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def run_bootstrap(self, *arguments):
        return subprocess.run(
            [
                sys.executable,
                str(BOOTSTRAP),
                "--root",
                str(self.root),
                *arguments,
            ],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_creates_safe_workspace_and_starter_config(self):
        result = self.run_bootstrap()

        self.assertEqual(result.returncode, 0, result.stderr)

        for directory in ("config", "html", "logs", "ssh"):
            self.assertTrue((self.root / directory).is_dir())

        config_path = self.root / "config" / "config.yaml"
        self.assertEqual(
            config_path.read_text(),
            STARTER.read_text(),
        )
        self.assertFalse((self.root / ".env").exists())

        self.assertEqual(
            stat.S_IMODE((self.root / "ssh").stat().st_mode),
            0o700,
        )
        self.assertIn("CREATED: file", result.stdout)
        self.assertIn(
            "Alternate workspace initialized.",
            result.stdout,
        )
        self.assertNotIn(
            "docker compose up",
            result.stdout,
        )

    def test_second_run_preserves_existing_config(self):
        first = self.run_bootstrap()
        self.assertEqual(first.returncode, 0, first.stderr)

        config_path = self.root / "config" / "config.yaml"
        config_path.write_text("user-owned: true\n")

        second = self.run_bootstrap()

        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(
            config_path.read_text(),
            "user-owned: true\n",
        )
        self.assertIn(
            f"PRESERVED: file {config_path}",
            second.stdout,
        )

    def test_force_replaces_bootstrap_managed_config(self):
        first = self.run_bootstrap()
        self.assertEqual(first.returncode, 0, first.stderr)

        config_path = self.root / "config" / "config.yaml"
        config_path.write_text("replace-me: true\n")

        result = self.run_bootstrap("--force")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            config_path.read_text(),
            STARTER.read_text(),
        )
        self.assertIn(
            f"REPLACED: file {config_path}",
            result.stdout,
        )

    def test_create_env_uses_current_uid_and_gid(self):
        result = self.run_bootstrap("--create-env")

        self.assertEqual(result.returncode, 0, result.stderr)

        env_content = (self.root / ".env").read_text()
        self.assertIn(f"PUID={os.getuid()}\n", env_content)
        self.assertIn(f"PGID={os.getgid()}\n", env_content)

    def test_existing_env_is_preserved_without_force(self):
        first = self.run_bootstrap("--create-env")
        self.assertEqual(first.returncode, 0, first.stderr)

        env_path = self.root / ".env"
        env_path.write_text("USER_VALUE=preserve\n")

        second = self.run_bootstrap("--create-env")

        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertEqual(
            env_path.read_text(),
            "USER_VALUE=preserve\n",
        )
        self.assertIn(
            f"PRESERVED: file {env_path}",
            second.stdout,
        )

    def test_directory_collision_fails_without_modifying_file(self):
        collision = self.root / "config"
        collision.write_text("do-not-touch\n")

        result = self.run_bootstrap()

        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            collision.read_text(),
            "do-not-touch\n",
        )
        self.assertIn(
            "managed directory path is not a directory",
            result.stderr,
        )

    def test_managed_file_symlink_is_rejected(self):
        (self.root / "config").mkdir()
        outside = self.root / "outside.yaml"
        outside.write_text("outside: unchanged\n")

        config_path = self.root / "config" / "config.yaml"
        config_path.symlink_to(outside)

        result = self.run_bootstrap("--force")

        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            outside.read_text(),
            "outside: unchanged\n",
        )
        self.assertTrue(config_path.is_symlink())
        self.assertIn(
            "managed file must not be a symbolic link",
            result.stderr,
        )

    def test_force_preserves_unrelated_workspace_files(self):
        first = self.run_bootstrap("--create-env")
        self.assertEqual(first.returncode, 0, first.stderr)

        unrelated_paths = {
            self.root / "config" / "custom.yaml": "custom\n",
            self.root / "html" / "keep.html": "dashboard\n",
            self.root / "logs" / "keep.log": "log\n",
            self.root / "ssh" / "keep-key": "key\n",
        }

        for path, content in unrelated_paths.items():
            path.write_text(content)

        result = self.run_bootstrap("--create-env", "--force")

        self.assertEqual(result.returncode, 0, result.stderr)

        for path, content in unrelated_paths.items():
            self.assertEqual(path.read_text(), content)

    def test_starter_configuration_passes_validator(self):
        result = subprocess.run(
            [
                sys.executable,
                str(VALIDATOR),
                str(STARTER),
            ],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(
            "Validation result: 0 error(s), 0 warning(s)",
            result.stdout,
        )

    def test_bootstrapped_workspace_passes_startup_preflight(self):
        bootstrap_result = self.run_bootstrap()
        self.assertEqual(
            bootstrap_result.returncode,
            0,
            bootstrap_result.stderr,
        )

        result = subprocess.run(
            [
                sys.executable,
                str(PREFLIGHT),
                "--config",
                str(self.root / "config" / "config.yaml"),
                "--output",
                str(self.root / "html" / "index.html"),
                "--log",
                str(self.root / "logs" / "generator.log"),
            ],
            cwd=REPOSITORY_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("SSH-backed hosts: none", result.stdout)
        self.assertIn("Startup preflight passed.", result.stdout)


if __name__ == "__main__":
    unittest.main()
