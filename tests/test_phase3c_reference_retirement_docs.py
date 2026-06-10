#!/usr/bin/env python3

import re
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DOCUMENT = (
    REPO_ROOT
    / "docs"
    / "phase3c-reference-retirement-decision.md"
)
README = REPO_ROOT / "README.md"
AUDIT = REPO_ROOT / "docs" / "phase3c-migration-parity-audit.md"


class Phase3C10DecisionDocumentationTests(unittest.TestCase):
    def test_document_records_selected_option_b(self):
        text = DOCUMENT.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "Status: decision complete; controlled production cutover pending.",
            "## Retirement options",
            "### Option A — immediate retirement",
            "### Option B — disabled reference fallback",
            "This option is selected.",
            "### Option C — continued parallel rehearsal",
            "## Selected production architecture",
            "## Controlled cutover sequence",
            "## Rollback triggers",
            "## Rollback procedure",
            "## Reference retention period",
            "## Release boundary",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_document_records_permanent_runtime_contract(self):
        text = DOCUMENT.read_text(encoding="utf-8")

        required = (
            "/opt/sanity-node",
            "/opt/sanity-node/app",
            "/opt/sanity-node/config/config.yaml",
            "/opt/sanity-node/html/index.html",
            "/opt/sanity-node/logs/generator.log",
            "/opt/sanity-node/run/generator.lock",
            "sanity-node-generate.service",
            "sanity-node-generate.timer",
            "sanity-node-web.service",
            "scripts/run-public-production.sh",
            "TCP port 8088",
            "starts independently from the generator",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_document_records_fail_closed_generation(self):
        text = DOCUMENT.read_text(encoding="utf-8")

        required = (
            "requires `dashboard.runtime_mode: public`",
            "non-blocking execution lock",
            "runs startup preflight",
            "process-specific temporary file",
            "Dashboard Summary and Runtime Detail markers",
            "rejects obsolete Config Preview wording",
            "atomically replaces the last successful production output",
            "A failed run does not replace the last successful",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, text)

    def test_document_records_reference_fallback_state(self):
        text = DOCUMENT.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "reference generator timer: inactive and disabled",
            "reference web service: inactive and disabled",
            "public rehearsal timer: inactive and disabled",
            "retained reference implementation",
            "without deleting the new workspace",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_document_records_retention_and_release_boundary(self):
        text = DOCUMENT.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "at least 30 days",
            "at least one release after `v0.3.0`",
            "The later of those two milestones",
            "requires a separate explicit decision",
            "close Phase 3C",
            "the `v0.3.0` release candidate",
            "leave the existing `v0.2.0` tag unchanged",
            "does not create or move a release tag",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

    def test_document_does_not_claim_cutover_completed(self):
        text = DOCUMENT.read_text(encoding="utf-8")

        self.assertNotIn("Status: complete.", text)
        self.assertNotIn("production cutover complete", text.lower())
        self.assertIn(
            "controlled production cutover pending",
            text,
        )

    def test_readme_records_decision_complete_cutover_pending(self):
        text = README.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "Phase 3C.10 has now completed the explicit "
            "reference-retirement decision",
            "Option B is selected",
            "docs/phase3c-reference-retirement-decision.md",
            "Decision complete; controlled cutover pending",
            "Reference mode remains the served known-good path until "
            "the controlled cutover succeeds",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

        self.assertNotIn(
            "Phase 3C.10 is the next step.",
            text,
        )
        self.assertNotIn(
            "The remaining Phase 3C decision is:",
            text,
        )

    def test_migration_audit_records_selected_boundary(self):
        text = AUDIT.read_text(encoding="utf-8")
        normalized = re.sub(r"\s+", " ", text)

        required = (
            "## Phase 3C.10 decision — reference retirement",
            "Option B is selected",
            "The retirement decision is complete.",
            "controlled production cutover",
            "rollback verification",
            "post-cutover scheduled observation",
            "Decision complete; controlled cutover pending",
            "the `v0.3.0` release candidate",
        )

        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, normalized)

        self.assertNotIn(
            "make a separate, explicit reference-retirement decision",
            normalized,
        )

    def test_document_does_not_publish_private_inventory(self):
        text = DOCUMENT.read_text(encoding="utf-8")

        forbidden_patterns = {
            "private IPv4 address": (
                r"\b192\.168\.\d{1,3}\.\d{1,3}\b"
            ),
            "personal home path": r"/home/[^/\s]+",
            "private dataset prefix": (
                r"\b(?:tank|backup|nvme)/"
            ),
            "private host model label": r"\bT(?:330|620)\b",
            "private deployment account": (
                r"(?:\bcontrols\b\s+(?:account|user|group)\b|"
                r"(?:User=|Group=|\baccount\s+|\buser\s+|"
                r"\bgroup\s+)controls\b)"
            ),
            "private deployment hostname": (
                r"homelabvonh23rz"
            ),
            "private SSH key filename": r"id_ed25519",
        }

        for label, pattern in forbidden_patterns.items():
            with self.subTest(label=label):
                self.assertIsNone(
                    re.search(pattern, text),
                    f"decision document contains {label}",
                )


if __name__ == "__main__":
    unittest.main()
