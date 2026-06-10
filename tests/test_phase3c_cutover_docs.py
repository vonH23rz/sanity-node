#!/usr/bin/env python3

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
AUDIT = REPO_ROOT / "docs" / "phase3c-migration-parity-audit.md"
DOCUMENT = (
    REPO_ROOT
    / "docs"
    / "phase3c-public-cutover-rehearsal.md"
)


class Phase3C9DocumentationTests(unittest.TestCase):
    def test_document_records_completed_rehearsal_contract(self):
        text = DOCUMENT.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "Status: complete.",
            "## Isolation contract",
            "## Fail-closed execution",
            "## Systemd contract",
            "## Production safeguards",
            "## Activation sequence",
            "## Scheduled observation",
            "## Lifecycle tests",
            "## Rollback procedure",
            "## Rehearsal result",
            "three consecutive scheduled public generations",
            "A full rollback and restore rehearsal",
            "Both timers finished active, enabled, and waiting",
            "## Completion boundary",
            "technically ready for a controlled production cutover",
            "Phase 3C.10",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_roadmap_marks_phase3c9_complete(self):
        readme = README.read_text(encoding="utf-8")
        audit = AUDIT.read_text(encoding="utf-8")

        expected = (
            "Phase 3C.9  Public-mode production cutover rehearsal\n"
            "                 Complete"
        )

        self.assertIn(expected, readme)
        self.assertIn(expected, audit)
        self.assertIn(
            "Phase 3C.9 completion — public-mode production "
            "cutover rehearsal",
            audit,
        )
        self.assertNotIn(
            "The remaining Phase 3C decision is:",
            readme,
        )
        self.assertNotIn(
            "1. make a separate, explicit reference-retirement "
            "decision.",
            audit,
        )
        self.assertIn(
            "Phase 3C.10 Reference retirement and production cutover\n"
            "                 Complete",
            readme,
        )
        self.assertIn(
            "## Phase 3C.10 completion — reference retirement and "
            "production cutover",
            audit,
        )

    def test_document_records_distinct_rehearsal_resources(self):
        text = DOCUMENT.read_text(encoding="utf-8")

        required = (
            "scripts/run-public-rehearsal.sh",
            "sanity-node-public-rehearsal.service",
            "sanity-node-public-rehearsal.timer",
            "/opt/sanity-node-public-rehearsal",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_document_records_fail_closed_public_render(self):
        text = DOCUMENT.read_text(encoding="utf-8")

        required = (
            "requires `dashboard.runtime_mode: public`",
            "renders to a temporary file",
            "rejects obsolete Config Preview wording",
            "atomically publishes only the isolated output",
            "never replaces the last successful rehearsal output",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_document_preserves_reference_runtime(self):
        text = DOCUMENT.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "does not replace, stop, or retire the reference",
            "stop or disable the reference timer",
            "reference runtime requires no recovery action",
            "That decision remains Phase 3C.10.",
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
            "private deployment account": r"\bcontrols\b",
        }

        for label, pattern in forbidden_patterns.items():
            with self.subTest(label=label):
                self.assertIsNone(
                    re.search(pattern, text),
                    f"cutover document contains {label}",
                )


if __name__ == "__main__":
    unittest.main()
