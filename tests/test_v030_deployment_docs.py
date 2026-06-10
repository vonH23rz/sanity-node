#!/usr/bin/env python3

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GUIDE = REPO_ROOT / "docs" / "deployment.md"


class V030DeploymentDocumentationTests(unittest.TestCase):
    def test_guide_records_complete_host_native_contract(self):
        text = GUIDE.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "# Deploying Sanity Node",
            "## Deployment choices",
            "### Docker Compose",
            "### Host-native systemd",
            "## Host-native qualification boundary",
            "## Permanent workspace layout",
            "## Runtime path contract",
            "## Create the service account",
            "## Install an immutable application snapshot",
            "## Install the production configuration",
            "## Install SSH identities",
            "## Establish verified SSH host trust",
            "## Install the systemd units",
            "## Fail-closed generation contract",
            "## Update the host-native deployment",
            "## Roll back an application update",
            "## Uninstall the host-native deployment",
            "## Deployment verification checklist",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_guide_distinguishes_docker_and_host_native_deployment(self):
        text = GUIDE.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "New users should normally start with the supported Docker "
            "Compose installation",
            "Docker Compose host port: 8099",
            "Host-native systemd port: 8088",
            "User=sanity-node Group=sanity-node /opt/sanity-node "
            "TCP port 8088",
            "This is advanced deployment guidance, not a universal "
            "host installer.",
            "Do not confuse the Docker `.env` setting with the "
            "host-native systemd web service.",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_guide_records_workspace_and_systemd_contract(self):
        text = GUIDE.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "/opt/sanity-node/app",
            "/opt/sanity-node/config/config.yaml",
            "/opt/sanity-node/html/index.html",
            "/opt/sanity-node/logs/generator.log",
            "/opt/sanity-node/run/generator.lock",
            "/opt/sanity-node/.ssh/known_hosts",
            "sanity-node-generate.service",
            "sanity-node-generate.timer",
            "sanity-node-web.service",
            "OnBootSec=1min OnUnitActiveSec=5min AccuracySec=1s "
            "RandomizedDelaySec=0 Persistent=true",
            "The web service starts independently from the generator.",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_guide_records_fail_closed_generation_and_activation(self):
        text = GUIDE.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "requires `dashboard.runtime_mode: public`",
            "acquires a non-blocking lock",
            "renders to a process-specific temporary file",
            "requires `Utility Node Services`",
            "requires `public-systems-section`",
            "rejects obsolete `Config Preview` wording",
            "atomically replaces the previous successful output",
            "A failed generation does not replace the last successful "
            "dashboard.",
            "Do not enable the timer before a successful manual "
            "generation.",
            "Enable it only after manual generation and web validation",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_guide_records_secure_ssh_identity_and_trust_contract(self):
        text = GUIDE.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "sudo install -o sanity-node -g sanity-node -m 0600 "
            "/secure/source/storage-server-key "
            "/opt/sanity-node/ssh/storage-server",
            "OpenSSH rejects private keys that are readable by another "
            "user or group.",
            "owner: sanity-node group: sanity-node mode: 0600",
            "A root-owned, group-readable `0640` key is therefore not "
            "a valid model",
            "Compare the fingerprint through an independent trusted "
            "source before installing it.",
            "Never use `StrictHostKeyChecking=no` as a deployment "
            "shortcut.",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

        self.assertNotIn(
            "sudo install -o root -g sanity-node -m 0640 "
            "/secure/source/storage-server-key",
            normalized,
        )

    def test_guide_records_update_rollback_and_uninstall_safeguards(self):
        text = GUIDE.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "Treat updates as controlled application-snapshot "
            "replacement.",
            "sudo systemctl stop sanity-node-generate.timer",
            "/opt/sanity-node/app.next",
            "/opt/sanity-node/app.previous",
            "/opt/sanity-node/app.failed",
            "Do not delete the failed snapshot until the regression is "
            "understood.",
            "Scheduled generation protects the previous dashboard from "
            "failed output, but it does not version the configuration "
            "for you.",
            "Do not remove retained reference or rehearsal runtimes as "
            "part of a generic uninstall",
            "Remove the workspace only after confirming the path and "
            "backups",
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
            "private host model label": r"\bT(?:330|620)\b",
            "private deployment hostname": (
                r"homelabvonh23rz"
            ),
            "private SSH key filename": r"id_ed25519",
            "private deployment account": (
                r"(?:User=|Group=|\baccount\s+|\buser\s+|"
                r"\bgroup\s+)controls\b"
            ),
        }

        for label, pattern in forbidden_patterns.items():
            with self.subTest(label=label):
                self.assertIsNone(
                    re.search(pattern, text),
                    f"deployment guide contains {label}",
                )


if __name__ == "__main__":
    unittest.main()
