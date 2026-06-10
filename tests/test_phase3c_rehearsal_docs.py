#!/usr/bin/env python3

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
README = REPO_ROOT / "README.md"
AUDIT = REPO_ROOT / "docs" / "phase3c-migration-parity-audit.md"
REHEARSAL = (
    REPO_ROOT
    / "docs"
    / "phase3c-production-configuration-rehearsal.md"
)


class Phase3C8DocumentationTests(unittest.TestCase):
    def test_rehearsal_document_records_completion_and_boundaries(self):
        text = REHEARSAL.read_text(encoding="utf-8")

        required = (
            "Status: complete",
            "## Host-native rehearsal result",
            "## Standard container rehearsal result",
            "## Confirmed deployment blockers",
            "## Phase 3C.9 boundary",
            "Production remained unchanged throughout the rehearsal.",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_roadmap_marks_phase3c8_complete(self):
        readme = README.read_text(encoding="utf-8")
        audit = AUDIT.read_text(encoding="utf-8")

        expected = (
            "Phase 3C.8  Production configuration migration rehearsal\n"
            "                 Complete"
        )

        self.assertIn(expected, readme)
        self.assertIn(expected, audit)
        self.assertIn(
            "Phase 3C.8 completion — production configuration "
            "migration rehearsal",
            audit,
        )

    def test_rehearsal_document_does_not_publish_private_inventory(self):
        text = REHEARSAL.read_text(encoding="utf-8")

        forbidden_patterns = {
            "private IPv4 subnet": r"\b192\.168\.\d{1,3}\.\d{1,3}\b",
            "personal home path": r"/home/[^/\s]+",
            "production dashboard path": r"/opt/homelab-dashboard",
            "private dataset prefix": r"\b(?:tank|backup|nvme)/",
            "private host model label": r"\bT(?:330|620)\b",
        }

        for label, pattern in forbidden_patterns.items():
            with self.subTest(label=label):
                self.assertIsNone(
                    re.search(pattern, text),
                    f"published rehearsal document contains {label}",
                )


if __name__ == "__main__":
    unittest.main()
