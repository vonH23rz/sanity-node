#!/usr/bin/env python3

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
README = ROOT / "README.md"
CHANGELOG = ROOT / "CHANGELOG.md"
NOTES = ROOT / "docs" / "v0.3.0-release-notes.md"


class V030ReleaseDocumentationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.readme = README.read_text(encoding="utf-8")
        cls.changelog = CHANGELOG.read_text(encoding="utf-8")
        cls.notes = NOTES.read_text(encoding="utf-8")
        cls.readme_flat = re.sub(r"\s+", " ", cls.readme)
        cls.notes_flat = re.sub(r"\s+", " ", cls.notes)
        cls.changelog_flat = re.sub(r"\s+", " ", cls.changelog)

    def test_readme_records_release_candidate_and_final_count(self):
        required = (
            "Sanity Node `v0.3.0` is the completed "
            "configuration-driven public-runtime release line",
            "Phase 3C is complete",
            "322 deterministic standard-library regression tests",
            "the `v0.3.0` release candidate",
            "The existing `v0.2.0` tag remains unchanged",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.readme_flat)

        self.assertNotIn(
            "284 deterministic standard-library regression tests",
            self.readme,
        )

    def test_readme_links_public_release_documentation(self):
        required = (
            "[Docker Compose installation](docs/installation.md)",
            "[Advanced host-native deployment](docs/deployment.md)",
            "[v0.3.0 release notes](docs/v0.3.0-release-notes.md)",
            "[Changelog](CHANGELOG.md)",
            "docs/v0.3.0-installation-qualification.md",
            "## Repository structure",
            "CHANGELOG.md",
            "v0.3.0-release-notes.md",
            "run-public-production.sh",
            "run-public-rehearsal.sh",
            "test_changelog_docs.py",
            "test_v030_release_docs.py",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.readme)

    def test_release_notes_have_required_sections(self):
        required = (
            "# Sanity Node v0.3.0 release notes",
            "Release date: 2026-06-10",
            "## Highlights",
            "## Monitoring scope",
            "## Installation choices",
            "### Docker Compose",
            "### Host-native deployment",
            "## Fail-closed safety model",
            "## Security",
            "## Validation",
            "## Deployment boundaries",
            "## Upgrade guidance",
            "## Release publication contract",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.notes)

    def test_release_notes_record_monitoring_scope(self):
        required = (
            "Linux and TrueNAS host system information",
            "TrueNAS pool capacity and health",
            "disk temperatures and SMART health",
            "snapshot tasks and freshness",
            "replication tasks and execution state",
            "remote Linux Docker containers",
            "Diun and TrueNAS-native image-update state",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.notes_flat)

    def test_release_notes_record_fail_closed_security(self):
        required = (
            "configuration validation",
            "startup preflight",
            "dashboard generation",
            "does not activate the reference runtime",
            "does not replace the last successful dashboard",
            "Public mode does not invoke personal reference collectors",
            "SSH host-key verification must remain enabled",
            "use mode `0600`",
            "Output publication is atomic",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.notes_flat)

    def test_release_notes_record_validation_and_upgrade(self):
        required = (
            "304 deterministic standard-library tests",
            "322 deterministic standard-library tests",
            "zero-error and zero-warning validation",
            "complete rollback and restoration",
            "Back up configuration",
            "Run startup preflight",
            "The existing `v0.2.0` tag remains unchanged",
            "annotated `v0.3.0` release",
            "exact final commit",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.notes_flat)

    def test_release_notes_record_deployment_boundaries(self):
        required = (
            "collector-host Docker access",
            "collector-host filesystem checks",
            "collector-host systemd inspection",
            "persistent host-native SSH trust integration",
            "/opt/sanity-node",
            "port is `8088`",
            "/opt/sanity-node/run/generator.lock",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.notes_flat)

    def test_changelog_and_release_notes_agree_on_test_counts(self):
        for value in (
            "304 deterministic standard-library tests",
            "322 deterministic standard-library tests",
        ):
            with self.subTest(value=value):
                self.assertIn(value, self.changelog_flat)
                self.assertIn(value, self.notes_flat)

    def test_publication_contract_preserves_existing_tags(self):
        required = (
            "The existing `v0.2.0` tag remains unchanged",
            "release branch is merged into `main`",
            "complete merged-main validation passes",
            "annotated tag must point to that validated merged-main commit",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, self.notes_flat)

        self.assertIn(
            "The existing `v0.2.0` tag remains unchanged",
            self.changelog_flat,
        )

    def test_new_release_material_does_not_publish_private_inventory(self):
        status_start = self.readme.index("## Current project status")
        status_end = self.readme.index(
            "## What Sanity Node monitors",
            status_start,
        )
        docs_start = self.readme.index("## Documentation")
        docs_end = self.readme.index(
            "## Current reference implementation",
            docs_start,
        )

        public_text = "\n".join(
            (
                self.readme[status_start:status_end],
                self.readme[docs_start:docs_end],
                self.notes,
                self.changelog,
            )
        )

        forbidden = {
            "private IPv4 address": (
                r"\b192\.168\.\d{1,3}\.\d{1,3}\b"
            ),
            "personal home path": r"/home/[^/\s]+",
            "reference production path": r"/opt/homelab-dashboard",
            "private dataset prefix": r"\b(?:tank|backup|nvme)/",
            "private host model label": r"\bT(?:330|620)\b",
            "private hostname": r"homelabvonh23rz",
            "private SSH key filename": r"id_ed25519",
            "private deployment account": (
                r"(?:User=|Group=|\baccount\s+|\buser\s+|"
                r"\bgroup\s+)controls\b"
            ),
        }

        for label, pattern in forbidden.items():
            with self.subTest(label=label):
                self.assertIsNone(
                    re.search(pattern, public_text),
                    f"release material contains {label}",
                )


if __name__ == "__main__":
    unittest.main()
