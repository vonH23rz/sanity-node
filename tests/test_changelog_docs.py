#!/usr/bin/env python3

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = REPO_ROOT / "CHANGELOG.md"


class ChangelogDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = CHANGELOG.read_text(encoding="utf-8")
        cls.normalized = re.sub(r"\s+", " ", cls.text)

    def test_changelog_has_required_release_order(self):
        headings = (
            "## [Unreleased]",
            "## [0.3.0] - 2026-06-10",
            "## [0.2.0] - 2026-06-07",
            "## [0.1.1] - 2026-05-31",
            "## [0.1.0] - 2026-05-31",
        )

        positions = [self.text.index(value) for value in headings]
        self.assertEqual(positions, sorted(positions))

    def test_v030_has_required_sections_in_order(self):
        start = self.text.index("## [0.3.0] - 2026-06-10")
        end = self.text.index("## [0.2.0] - 2026-06-07")
        release = self.text[start:end]

        headings = (
            "### Added",
            "### Changed",
            "### Fixed",
            "### Security",
            "### Documentation",
            "### Validation",
            "### Deployment notes",
            "### Upgrade notes",
        )

        positions = [release.index(value) for value in headings]
        self.assertEqual(positions, sorted(positions))

    def test_v030_records_runtime_and_monitoring_scope(self):
        required = (
            "safe first-run workspace bootstrap",
            "fail-closed startup preflight",
            "public and reference runtime modes",
            "Configuration-driven host system information",
            "TrueNAS pool capacity and health monitoring",
            "TrueNAS temperature and SMART monitoring",
            "remote Linux SSH-backed checks",
            "Public Overall Status",
            "snapshot and replication evidence",
            "atomic output publication",
            "last successfully generated dashboard",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.normalized)

    def test_v030_records_security_and_ssh_boundaries(self):
        required = (
            "fails closed",
            "prevents reference collectors and private inventory",
            "persistent verified `known_hosts` entries",
            "rejects disabling host-key verification",
            "restricted to mode `0600`",
            "dedicated unprivileged service account",
            "Atomic output replacement",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.normalized)

    def test_v030_records_documentation_and_validation(self):
        required = (
            "docs/installation.md",
            "docs/deployment.md",
            "docs/v0.3.0-installation-qualification.md",
            "Phase 3C migration parity audit",
            "304 deterministic standard-library tests",
            "322 deterministic standard-library tests",
            "privacy-boundary coverage",
            "zero errors and zero warnings",
            "clean-clone Docker installation",
            "invalid-configuration rejection",
            "rollback restoration",
            "legitimate scheduled generation",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.normalized)

    def test_v030_records_deployment_and_upgrade_contract(self):
        required = (
            "does not automatically provide collector-host Docker access",
            "Host-native deployment is the advanced path",
            "/opt/sanity-node",
            "TCP port `8088`",
            "/opt/sanity-node/run/generator.lock",
            "Run `scripts/validate-config.py`",
            "`scripts/startup-preflight.py`",
            "The existing `v0.2.0` tag remains unchanged",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.normalized)

    def test_previous_releases_and_comparison_links_are_present(self):
        required = (
            "The first configuration-driven runtime and Docker scaffold.",
            "Remote Linux Docker, storage, and backup checks",
            "Clarified the README, installation status, project maturity",
            "The initial homelab-tested Sanity Node release.",
            "[Unreleased]: https://github.com/vonH23rz/sanity-node/"
            "compare/v0.3.0...HEAD",
            "[0.3.0]: https://github.com/vonH23rz/sanity-node/"
            "compare/v0.2.0...v0.3.0",
            "[0.2.0]: https://github.com/vonH23rz/sanity-node/"
            "compare/v0.1.1...v0.2.0",
            "[0.1.1]: https://github.com/vonH23rz/sanity-node/"
            "compare/v0.1.0...v0.1.1",
            "[0.1.0]: https://github.com/vonH23rz/sanity-node/"
            "releases/tag/v0.1.0",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.normalized)

    def test_changelog_does_not_publish_private_inventory(self):
        forbidden_patterns = {
            "private IPv4 address": (
                r"\b192\.168\.\d{1,3}\.\d{1,3}\b"
            ),
            "personal home path": r"/home/[^/\s]+",
            "reference production path": r"/opt/homelab-dashboard",
            "private dataset prefix": r"\b(?:tank|backup|nvme)/",
            "private host model label": r"\bT(?:330|620)\b",
            "private deployment hostname": r"homelabvonh23rz",
            "private SSH key filename": r"id_ed25519",
            "private deployment account": (
                r"(?:User=|Group=|\baccount\s+|\buser\s+|"
                r"\bgroup\s+)controls\b"
            ),
        }

        for label, pattern in forbidden_patterns.items():
            with self.subTest(label=label):
                self.assertIsNone(
                    re.search(pattern, self.text),
                    f"CHANGELOG.md contains {label}",
                )


if __name__ == "__main__":
    unittest.main()
