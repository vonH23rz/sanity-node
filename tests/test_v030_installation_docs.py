#!/usr/bin/env python3

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GUIDE = REPO_ROOT / "docs" / "installation.md"


class V030InstallationDocumentationTests(unittest.TestCase):
    def test_guide_records_complete_public_installation_contract(self):
        text = GUIDE.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "# Installing Sanity Node",
            "## Supported installation path",
            "## Qualification status",
            "## Prerequisites",
            "## Clone the repository",
            "## Create the first-run workspace",
            "## Review `.env`",
            "## Validate the starter configuration",
            "## Validate Docker Compose configuration",
            "## Start Sanity Node",
            "## Open the dashboard",
            "## Inspect logs",
            "## Update Sanity Node",
            "## Uninstall Sanity Node",
            "## Troubleshooting",
            "## Security notes",
            "## Recommended installation sequence",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_guide_records_supported_first_run_commands(self):
        text = GUIDE.read_text(encoding="utf-8")

        required = (
            "git clone https://github.com/vonH23rz/sanity-node.git",
            "cd sanity-node",
            "git checkout v0.3.0",
            "./scripts/bootstrap-workspace.py --create-env",
            "./scripts/validate-config.py config/config.yaml",
            "docker compose --env-file .env config",
            "docker compose up --build --wait",
            "docker compose ps",
            "http://<collector-ip>:8099",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_guide_records_bootstrap_and_port_semantics(self):
        text = GUIDE.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "config/ html/ logs/ ssh/ config/config.yaml .env",
            "examples/config.starter.yaml",
            "Existing files are preserved by default.",
            "The bootstrap does not overwrite an existing configuration "
            "or `.env` unless `--force` is supplied.",
            "SANITY_NODE_PORT=8099",
            "The Compose deployment always serves port `8099` inside "
            "the container.",
            "`SANITY_NODE_PORT` in `.env` controls the host-side "
            "published port.",
            "Do not change the `/app/...` runtime paths for a normal "
            "installation.",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_guide_records_fail_closed_refresh_behavior(self):
        text = GUIDE.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "configuration validation → startup preflight → dashboard "
            "generation",
            "the generator does not publish invalid output",
            "the last successful dashboard remains served",
            "a later valid configuration recovers automatically",
            "requires one successful dashboard generation before "
            "starting the web server",
            "A restart removes the previously generated dashboard "
            "before requiring a new successful initial render.",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_guide_records_container_and_ssh_boundaries(self):
        text = GUIDE.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "It did not qualify every optional SSH-backed or "
            "collector-host-integrated check through the unmodified "
            "Compose boundary.",
            "The standard Docker Compose installation does not mount "
            "the collector host's Docker socket",
            "In the standard container deployment, `/` refers to the "
            "container filesystem",
            "Inside a container, `127.0.0.1` refers to the Sanity Node "
            "container itself.",
            "the base Compose file does not mount a persistent verified "
            "`known_hosts` location",
            "A private key alone is therefore not sufficient for a new "
            "SSH target.",
            "Do not run the host-side preflight against a Docker "
            "configuration that contains `/app/...` key paths.",
            "Never disable `StrictHostKeyChecking` to bypass deployment "
            "setup.",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_guide_records_update_backup_and_cleanup_contracts(self):
        text = GUIDE.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "back up `config/`, `.env`, and `ssh/`",
            "git fetch --tags origin",
            "docker compose up --detach --build --wait",
            "Do not use `git pull` blindly",
            "config/config.yaml .env ssh/",
            "docker compose down",
            "docker compose down --rmi local",
            "The Compose commands do not remove the bind-mounted "
            "runtime directories.",
            "Confirm the path carefully before running a recursive "
            "removal command.",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_guide_does_not_publish_private_inventory(self):
        text = GUIDE.read_text(encoding="utf-8")

        forbidden_patterns = {
            "private IPv4 address": (
                r"\b192\.168\.\d{1,3}\.\d{1,3}\b"
            ),
            "personal home path": r"/home/[^/\s]+",
            "reference production path": (
                r"/opt/homelab-dashboard"
            ),
            "private dataset prefix": (
                r"\b(?:tank|backup|nvme)/"
            ),
            "private host model label": r"\bT(?:330|620)\b",
            "private deployment hostname": (
                r"homelabvonh23rz"
            ),
            "private deployment account": (
                r"(?:User=|Group=|\baccount\s+|\buser\s+|"
                r"\bgroup\s+)controls\b"
            ),
        }

        for label, pattern in forbidden_patterns.items():
            with self.subTest(label=label):
                self.assertIsNone(
                    re.search(pattern, text),
                    f"installation guide contains {label}",
                )


if __name__ == "__main__":
    unittest.main()
