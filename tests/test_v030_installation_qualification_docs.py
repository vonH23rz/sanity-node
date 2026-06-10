#!/usr/bin/env python3

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = (
    REPO_ROOT
    / "docs"
    / "v0.3.0-installation-qualification.md"
)


class V030InstallationQualificationDocumentationTests(
    unittest.TestCase
):
    def test_document_records_completed_qualification_contract(self):
        text = DOCUMENT.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "Status: complete; Docker installation path qualified.",
            "## Qualification environment",
            "## Acceptance criteria",
            "## Fresh-clone procedure",
            "## Initial startup and restart evidence",
            "## Defect discovered and correction",
            "## Invalid-refresh rejection",
            "## Automatic recovery",
            "## Cleanup verification",
            "## Production safeguards",
            "## Deterministic regression coverage",
            "## Qualification result",
            "## Release boundary",
            "does not create or move a release tag",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_document_records_qualified_revision_and_environment(self):
        text = DOCUMENT.read_text(encoding="utf-8")

        required = (
            "release-v0.3.0-install-qualification",
            "commit: `9954b91`",
            "Fail closed on invalid Docker refresh configuration",
            "Docker Engine `29.5.3`, build `d1c06ef`",
            "Docker Compose `v5.1.4`",
            "sanity-node-v030-fixed-qualification",
            "host TCP port `18099`",
            "container TCP port `8099`",
            "five-second refresh interval",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_document_records_fail_closed_refresh_and_recovery(self):
        text = DOCUMENT.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "validate configuration → run startup preflight → run "
            "generator",
            "Configuration validation failed; generator was not run",
            "Keeping the last successfully generated dashboard",
            "the generator invocation count did not increase",
            "the dashboard content hash did not change",
            "HTTP continued serving the last successful dashboard",
            "reference collectors were not enabled",
            "runtime mode did not fall back to `reference`",
            "Generation resumed automatically",
            "No manual output restoration was required",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_document_records_cleanup_and_runtime_protection(self):
        text = DOCUMENT.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "No qualification container, image, network, workspace, "
            "or listener remained.",
            "/opt/sanity-node/html/index.html",
            "permanent web service remained active and enabled",
            "generation timer remained active and enabled",
            "retained reference and public-rehearsal outputs remained "
            "byte-for-byte and metadata-identical",
            "No production configuration, generator, service, timer, "
            "output, credential, reverse-proxy route, or fallback "
            "resource was modified.",
            "The corrected public Docker installation path is "
            "technically qualified.",
            "test_entrypoint_revalidates_before_scheduled_refresh",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_document_records_release_boundary(self):
        text = DOCUMENT.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "satisfies the isolated fresh-install qualification gate "
            "for `v0.3.0`",
            "public installation documentation",
            "deployment guidance",
            "changelog and release notes",
            "merged-main validation",
            "final publication verification",
            "The `v0.3.0` tag must be created only after those "
            "remaining gates pass on the final merged `main`.",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_document_does_not_publish_private_inventory(self):
        text = DOCUMENT.read_text(encoding="utf-8")

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
                    f"qualification document contains {label}",
                )


if __name__ == "__main__":
    unittest.main()
